"""Обработка одного задания: взять → обработать → нормализовать → сохранить → уведомить."""

from __future__ import annotations

import asyncio
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import Settings
from app.core.enums import AssetType, JobStatus, Operation
from app.core.errors import AppError
from app.core.logging import get_logger
from app.database.session import session_scope
from app.models import Job
from app.prompts.builder import build_prompt
from app.repositories.assets import AssetRepository
from app.repositories.audit import AuditRepository
from app.repositories.jobs import JobRepository
from app.services.export.c2pa import extract_c2pa
from app.services.export.normalizer import ExportOptions, ExportResult, normalize_for_export
from app.services.image_editing.base import EditRequest, ProviderError, ReferenceImage
from app.services.image_editing.factory import ProviderRegistry
from app.services.notifier import JobNotifier
from app.services.operations import BACKGROUND_PRESETS, CUSTOM
from app.services.storage import Storage, build_object_key

log = get_logger(__name__)

GENERIC_FAILURE = "Не удалось обработать фотографию. Попробуйте ещё раз или сообщите о проблеме."
TIMEOUT_FAILURE = "Обработка заняла слишком много времени. Попробуйте ещё раз чуть позже."
REVIEW_MESSAGES = {
    "plate_low_confidence": "номер на фото не найден с достаточной уверенностью",
}


class JobProcessor:
    def __init__(
        self,
        *,
        session_factory: async_sessionmaker[AsyncSession],
        storage: Storage,
        registry: ProviderRegistry,
        notifier: JobNotifier,
        settings: Settings,
    ) -> None:
        self.session_factory = session_factory
        self.storage = storage
        self.registry = registry
        self.notifier = notifier
        self.settings = settings

    @property
    def hard_timeout(self) -> float:
        per_call = self.settings.provider_timeout_seconds
        return per_call * max(1, self.settings.provider_max_retries) + 60

    async def process(self, job_id: int, *, reclaim: bool = False) -> JobStatus | None:
        """Возвращает итоговый статус или None, если задание уже взято другим воркером."""
        bound = log.bind(job_id=job_id)
        async with session_scope(self.session_factory) as session:
            repo = JobRepository(session)
            sources = [JobStatus.QUEUED] + ([JobStatus.PROCESSING] if reclaim else [])
            if not await repo.transition(job_id, from_statuses=sources, to=JobStatus.PROCESSING):
                bound.info("job.skip_not_claimable")
                return None
            job = await repo.get(job_id, with_assets=True)
            assert job is not None
        bound = bound.bind(operation=job.operation.value)
        bound.info("job.processing")
        await self._safe_notify(self.notifier.job_status, job)

        try:
            return await asyncio.wait_for(self._run(job), timeout=self.hard_timeout)
        except TimeoutError:
            bound.warning("job.timeout")
            return await self._fail(job, TIMEOUT_FAILURE, "timeout")
        except ProviderError as exc:
            bound.warning("job.provider_error", error=type(exc).__name__, detail=str(exc))
            return await self._fail(job, exc.user_message, f"{type(exc).__name__}: {exc}")
        except AppError as exc:
            bound.warning("job.app_error", error=type(exc).__name__, detail=str(exc))
            return await self._fail(job, exc.user_message, f"{type(exc).__name__}: {exc}")
        except Exception as exc:
            bound.exception("job.unexpected_error")
            return await self._fail(job, GENERIC_FAILURE, f"{type(exc).__name__}: {exc}")

    async def _load_references(self, job: Job) -> tuple[ReferenceImage, ...]:
        refs: list[ReferenceImage] = []
        role = "wheel" if job.operation is Operation.WHEELS else "background"
        for asset in job.assets:
            if asset.asset_type is AssetType.REFERENCE:
                data = await self.storage.get(asset.storage_key)
                refs.append(ReferenceImage(data=data, mime_type=asset.mime_type, role=role))
        if job.operation is Operation.BACKGROUND:
            key = job.parameters.get("background")
            if key and key != CUSTOM:
                path = self.settings.backgrounds_path / BACKGROUND_PRESETS[key].filename
                if path.is_file():
                    data = await asyncio.to_thread(path.read_bytes)
                    refs.append(
                        ReferenceImage(data=data, mime_type="image/jpeg", role="background")
                    )
        return tuple(refs)

    def _export_options(self, operation: Operation) -> ExportOptions:
        s = self.settings
        label = (
            s.visualization_label_text
            if s.visualization_label_enabled and operation in s.visualization_label_operations
            else None
        )
        return ExportOptions(
            max_side=s.export_max_side,
            quality=s.export_jpeg_quality,
            min_quality=s.export_min_jpeg_quality,
            max_bytes=s.export_max_bytes,
            label=label,
            font_path=s.font_path,
        )

    async def _run(self, job: Job) -> JobStatus:
        original_asset = next(a for a in job.assets if a.asset_type is AssetType.ORIGINAL)
        original = await self.storage.get(original_asset.storage_key)
        provider = self.registry.for_operation(job.operation)
        request = EditRequest(
            job_id=job.id,
            operation=job.operation,
            image=original,
            mime_type=original_asset.mime_type,
            parameters=dict(job.parameters),
            prompt=build_prompt(job.operation, job.parameters),
            references=await self._load_references(job),
        )
        result = await provider.edit(request)

        if result.needs_review:
            reason = result.review_reason or "needs_review"
            async with session_scope(self.session_factory) as session:
                await JobRepository(session).transition(
                    job.id,
                    from_statuses=[JobStatus.PROCESSING],
                    to=JobStatus.NEEDS_REVIEW,
                    error_message=reason,
                    provider=result.provider,
                )
                await AuditRepository(session).log(
                    "job.needs_review",
                    user_id=job.user_id,
                    job_id=job.id,
                    reason=reason,
                    **_json_safe(result.metadata),
                )
                job = await self._reload(session, job.id)
            await self._safe_notify(
                self.notifier.job_needs_review, job, REVIEW_MESSAGES.get(reason, reason)
            )
            return JobStatus.NEEDS_REVIEW

        exported: ExportResult = await asyncio.to_thread(
            normalize_for_export,
            result.image,
            self._export_options(job.operation),
            provenance_fallback=extract_c2pa(original),
        )
        key = build_object_key(AssetType.RESULT, job.id, "jpg")
        await self.storage.put(key, exported.data, exported.mime_type)
        async with session_scope(self.session_factory) as session:
            await AssetRepository(session).add(
                job_id=job.id,
                asset_type=AssetType.RESULT,
                storage_key=key,
                mime_type=exported.mime_type,
                width=exported.width,
                height=exported.height,
            )
            await JobRepository(session).transition(
                job.id,
                from_statuses=[JobStatus.PROCESSING],
                to=JobStatus.COMPLETED,
                provider=result.provider,
                error_message=None,
            )
            await AuditRepository(session).log(
                "job.completed",
                user_id=job.user_id,
                job_id=job.id,
                provider=result.provider,
                labeled=exported.labeled,
                c2pa=exported.c2pa_preserved,
            )
            job = await self._reload(session, job.id)
        log.info("job.completed", job_id=job.id, provider=result.provider, bytes=len(exported.data))
        filename = f"ecodrive_{job.id:04d}_{job.operation.value}.jpg"
        await self._safe_notify(self.notifier.job_completed, job, exported, filename)
        return JobStatus.COMPLETED

    async def _fail(self, job: Job, user_message: str, detail: str) -> JobStatus:
        async with session_scope(self.session_factory) as session:
            await JobRepository(session).transition(
                job.id,
                from_statuses=[JobStatus.PROCESSING],
                to=JobStatus.FAILED,
                error_message=detail[:2000],
            )
            await AuditRepository(session).log(
                "job.failed", user_id=job.user_id, job_id=job.id, error=detail[:500]
            )
            job = await self._reload(session, job.id)
        await self._safe_notify(self.notifier.job_failed, job, user_message)
        return JobStatus.FAILED

    @staticmethod
    async def _reload(session: AsyncSession, job_id: int) -> Job:
        job = await JobRepository(session).get(job_id, with_assets=True)
        assert job is not None
        return job

    @staticmethod
    async def _safe_notify(func: Any, *args: Any) -> None:
        """Сбой Telegram не должен ронять обработку задания."""
        try:
            await func(*args)
        except Exception:
            log.exception("notify.failed", notifier=getattr(func, "__name__", "?"))


def _json_safe(meta: dict[str, Any]) -> dict[str, Any]:
    safe: dict[str, Any] = {}
    for key, value in meta.items():
        if isinstance(value, str | int | float | bool | list | dict) or value is None:
            safe[key] = value
    return safe
