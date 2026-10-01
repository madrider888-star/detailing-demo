"""Создание заданий, повторный запуск, жалобы на результат."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.enums import AssetType, JobStatus, Operation
from app.core.errors import (
    AppError,
    DuplicateJobError,
    InvalidStatusTransitionError,
    TooManyActiveJobsError,
)
from app.core.logging import get_logger
from app.models import Job, User
from app.repositories.assets import AssetRepository
from app.repositories.audit import AuditRepository
from app.repositories.jobs import JobRepository
from app.repositories.users import UserRepository
from app.services.image_validation import ValidatedImage
from app.services.job_status import sources_for
from app.services.operations import build_parameters, required_images
from app.services.storage import Storage, build_object_key

log = get_logger(__name__)


@dataclass(frozen=True)
class JobImage:
    asset_type: AssetType
    image: ValidatedImage


class JobNotFoundError(AppError):
    user_message = "Задание не найдено."


class JobService:
    def __init__(
        self,
        session: AsyncSession,
        storage: Storage,
        settings: Settings,
        provider_name: Callable[[Operation], str],
    ) -> None:
        self.session = session
        self.storage = storage
        self.settings = settings
        self.provider_name = provider_name
        self.jobs = JobRepository(session)
        self.assets = AssetRepository(session)
        self.users = UserRepository(session)
        self.audit = AuditRepository(session)

    async def _ensure_capacity(self, user: User) -> None:
        # Блокировка строки пользователя сериализует параллельные подтверждения.
        await self.users.get(user.id, for_update=True)
        active = await self.jobs.count_active_for_user(user.id)
        if active >= self.settings.max_active_jobs_per_user:
            raise TooManyActiveJobsError(f"user {user.id} has {active} active jobs")

    async def create_job(
        self,
        *,
        user: User,
        operation: Operation,
        raw_params: dict[str, Any],
        images: Sequence[JobImage],
        idempotency_key: str | None,
        chat_id: int | None,
    ) -> Job:
        params = build_parameters(operation, raw_params)
        expected = required_images(operation, params)
        if len(images) != expected:
            raise ValueError(f"{operation} expects {expected} images, got {len(images)}")
        if sum(1 for i in images if i.asset_type is AssetType.ORIGINAL) != 1:
            raise ValueError("exactly one original image is required")

        await self._ensure_capacity(user)
        try:
            async with self.session.begin_nested():
                job = await self.jobs.create(
                    user_id=user.id,
                    operation=operation,
                    parameters=params,
                    provider=self.provider_name(operation),
                    idempotency_key=idempotency_key,
                    telegram_chat_id=chat_id,
                )
        except IntegrityError as exc:
            raise DuplicateJobError(f"duplicate idempotency key {idempotency_key}") from exc

        for item in images:
            key = build_object_key(item.asset_type, job.id, item.image.extension)
            await self.storage.put(key, item.image.data, item.image.mime_type)
            await self.assets.add(
                job_id=job.id,
                asset_type=item.asset_type,
                storage_key=key,
                mime_type=item.image.mime_type,
                width=item.image.width,
                height=item.image.height,
            )
        await self.audit.log(
            "job.created", user_id=user.id, job_id=job.id, operation=operation.value
        )
        log.info("job.created", job_id=job.id, operation=operation.value, user_id=user.id)
        return job

    async def get_owned(self, user: User, job_id: int) -> Job:
        job = await self.jobs.get(job_id, with_assets=True)
        if job is None or job.user_id != user.id:
            raise JobNotFoundError(f"job {job_id} not found for user {user.id}")
        return job

    async def redo(self, user: User, job_id: int, chat_id: int | None) -> Job:
        """Новое задание с теми же исходниками и параметрами."""
        source = await self.get_owned(user, job_id)
        await self._ensure_capacity(user)
        job = await self.jobs.create(
            user_id=user.id,
            operation=source.operation,
            parameters=dict(source.parameters),
            provider=self.provider_name(source.operation),
            telegram_chat_id=chat_id,
        )
        for asset in source.assets:
            if asset.asset_type is AssetType.RESULT:
                continue
            await self.assets.add(
                job_id=job.id,
                asset_type=asset.asset_type,
                storage_key=asset.storage_key,
                mime_type=asset.mime_type,
                width=asset.width,
                height=asset.height,
            )
        await self.audit.log("job.redo", user_id=user.id, job_id=job.id, source_job_id=job_id)
        return job

    async def retry(self, actor: User, job_id: int) -> Job:
        """Повторный запуск администратором (failed / needs_review → queued)."""
        job = await self.jobs.get(job_id)
        if job is None:
            raise JobNotFoundError(f"job {job_id} not found")
        changed = await self.jobs.transition(
            job_id,
            from_statuses=sources_for(JobStatus.QUEUED),
            to=JobStatus.QUEUED,
            error_message=None,
            attempts=job.attempts + 1,
            started_at=None,
            completed_at=None,
            provider=self.provider_name(job.operation),
        )
        if not changed:
            raise InvalidStatusTransitionError(f"job {job_id} in {job.status} cannot be retried")
        await self.audit.log("job.retry", user_id=actor.id, job_id=job_id)
        refreshed = await self.jobs.get(job_id)
        assert refreshed is not None
        return refreshed

    async def report_problem(self, user: User, job_id: int, comment: str | None) -> Job:
        job = await self.get_owned(user, job_id)
        if job.status is JobStatus.COMPLETED:
            await self.jobs.transition(
                job_id, from_statuses=[JobStatus.COMPLETED], to=JobStatus.NEEDS_REVIEW
            )
        await self.audit.log(
            "job.problem_reported",
            user_id=user.id,
            job_id=job_id,
            comment=(comment or "")[:1000],
        )
        return job

    async def handoff_to_operator(self, user: User, job_id: int) -> Job:
        job = await self.get_owned(user, job_id)
        await self.audit.log("job.handoff_operator", user_id=user.id, job_id=job_id)
        return job
