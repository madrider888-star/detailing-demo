"""Воркер: смена статусов, ошибки провайдера, защита от повторной обработки."""

from __future__ import annotations

import io
from dataclasses import dataclass, field

import pytest
from PIL import Image
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import Settings
from app.core.enums import AssetType, JobStatus, Operation
from app.models import Job, User
from app.repositories.assets import AssetRepository
from app.repositories.jobs import JobRepository
from app.services.export.normalizer import ExportResult
from app.services.image_editing.base import ProviderRejectedError
from app.services.image_editing.factory import ProviderRegistry, build_plate_provider
from app.services.image_editing.mock import MockImageProvider
from app.services.image_validation import validate_image
from app.services.jobs import JobImage, JobService
from app.services.storage import LocalStorage
from app.workers.processor import JobProcessor
from tests.conftest import provider_names


@dataclass
class RecordingNotifier:
    events: list[tuple[str, int, str]] = field(default_factory=list)
    results: list[ExportResult] = field(default_factory=list)

    async def job_status(self, job: Job) -> None:
        self.events.append(("status", job.id, job.status.value))

    async def job_completed(self, job: Job, result: ExportResult, filename: str) -> None:
        self.events.append(("completed", job.id, filename))
        self.results.append(result)

    async def job_needs_review(self, job: Job, reason: str) -> None:
        self.events.append(("needs_review", job.id, reason))

    async def job_failed(self, job: Job, user_message: str) -> None:
        self.events.append(("failed", job.id, user_message))


async def _create_job(
    session: AsyncSession,
    storage: LocalStorage,
    settings: Settings,
    user: User,
    image: bytes,
    operation: Operation = Operation.BACKGROUND,
    raw: dict[str, object] | None = None,
) -> Job:
    validated = validate_image(image, max_bytes=10**8, max_pixels=10**8, min_side=100)
    job = await JobService(session, storage, settings, provider_names).create_job(
        user=user,
        operation=operation,
        raw_params=raw if raw is not None else {"background": "white_studio"},
        images=[JobImage(AssetType.ORIGINAL, validated)],
        idempotency_key=None,
        chat_id=user.telegram_id,
    )
    await session.commit()
    return job


def _processor(
    session_factory: async_sessionmaker[AsyncSession],
    storage: LocalStorage,
    settings: Settings,
    provider: MockImageProvider,
    notifier: RecordingNotifier,
) -> JobProcessor:
    registry = ProviderRegistry(default=provider, plate=build_plate_provider(settings))
    return JobProcessor(
        session_factory=session_factory,
        storage=storage,
        registry=registry,
        notifier=notifier,
        settings=settings,
    )


async def test_job_completes_with_mock_provider(
    session: AsyncSession,
    session_factory: async_sessionmaker[AsyncSession],
    storage: LocalStorage,
    settings: Settings,
    employee: User,
    car_jpeg: bytes,
) -> None:
    job = await _create_job(session, storage, settings, employee, car_jpeg)
    notifier = RecordingNotifier()
    processor = _processor(session_factory, storage, settings, MockImageProvider(), notifier)

    assert await processor.process(job.id) is JobStatus.COMPLETED
    assert [e[0] for e in notifier.events] == ["status", "completed"]
    assert notifier.events[0][2] == "processing"

    async with session_factory() as s:
        stored = await JobRepository(s).get(job.id)
        result = await AssetRepository(s).latest(job.id, AssetType.RESULT)
        original = await AssetRepository(s).latest(job.id, AssetType.ORIGINAL)
    assert stored is not None and stored.status is JobStatus.COMPLETED
    assert stored.started_at is not None and stored.completed_at is not None
    assert result is not None and original is not None
    # Оригинал и результат хранятся раздельно.
    assert result.storage_key.startswith("results/")
    assert original.storage_key.startswith("originals/")
    data = await storage.get(result.storage_key)
    assert Image.open(io.BytesIO(data)).format == "JPEG"
    assert notifier.results[0].labeled  # фон — существенное изменение → «Візуалізація»


async def test_job_is_not_processed_twice(
    session: AsyncSession,
    session_factory: async_sessionmaker[AsyncSession],
    storage: LocalStorage,
    settings: Settings,
    employee: User,
    car_jpeg: bytes,
) -> None:
    job = await _create_job(session, storage, settings, employee, car_jpeg)
    provider = MockImageProvider()
    processor = _processor(session_factory, storage, settings, provider, RecordingNotifier())
    assert await processor.process(job.id) is JobStatus.COMPLETED
    assert await processor.process(job.id) is None
    assert provider.calls == 1


async def test_unavailable_provider_marks_failed(
    session: AsyncSession,
    session_factory: async_sessionmaker[AsyncSession],
    storage: LocalStorage,
    settings: Settings,
    employee: User,
    car_jpeg: bytes,
) -> None:
    """Повторы с backoff делает сам провайдер (см. test_providers); если сервис так и не
    ответил, задание получает статус failed и понятное сообщение."""
    job = await _create_job(session, storage, settings, employee, car_jpeg)
    notifier = RecordingNotifier()
    processor = _processor(
        session_factory, storage, settings, MockImageProvider(fail_times=5), notifier
    )
    assert await processor.process(job.id) is JobStatus.FAILED
    assert notifier.events[-1][0] == "failed"
    assert "временно недоступен" in notifier.events[-1][2]


async def test_provider_rejection_marks_failed_with_message(
    session: AsyncSession,
    session_factory: async_sessionmaker[AsyncSession],
    storage: LocalStorage,
    settings: Settings,
    employee: User,
    car_jpeg: bytes,
) -> None:
    job = await _create_job(session, storage, settings, employee, car_jpeg)
    notifier = RecordingNotifier()
    provider = MockImageProvider(permanent_error=ProviderRejectedError("moderation_blocked"))
    processor = _processor(session_factory, storage, settings, provider, notifier)
    assert await processor.process(job.id) is JobStatus.FAILED
    async with session_factory() as s:
        stored = await JobRepository(s).get(job.id)
    assert stored is not None
    assert stored.error_message is not None and "ProviderRejectedError" in stored.error_message
    assert "отклонил изображение" in notifier.events[-1][2]


async def test_plate_without_plate_goes_to_review(
    session: AsyncSession,
    session_factory: async_sessionmaker[AsyncSession],
    storage: LocalStorage,
    settings: Settings,
    employee: User,
) -> None:
    buf = io.BytesIO()
    Image.new("RGB", (900, 600), (120, 130, 140)).save(buf, "JPEG")
    job = await _create_job(
        session, storage, settings, employee, buf.getvalue(), Operation.PLATE, {}
    )
    notifier = RecordingNotifier()
    processor = _processor(session_factory, storage, settings, MockImageProvider(), notifier)
    assert await processor.process(job.id) is JobStatus.NEEDS_REVIEW
    assert notifier.events[-1][0] == "needs_review"
    assert "уверенностью" in notifier.events[-1][2]


async def test_plate_job_completes_with_opencv(
    session: AsyncSession,
    session_factory: async_sessionmaker[AsyncSession],
    storage: LocalStorage,
    settings: Settings,
    employee: User,
    car_jpeg: bytes,
) -> None:
    job = await _create_job(session, storage, settings, employee, car_jpeg, Operation.PLATE, {})
    notifier = RecordingNotifier()
    processor = _processor(session_factory, storage, settings, MockImageProvider(), notifier)
    assert await processor.process(job.id) is JobStatus.COMPLETED
    result = notifier.results[0]
    assert (result.width, result.height) == (1280, 860)  # исходное разрешение сохранено
    assert not result.labeled  # замена номера не помечается как визуализация


@pytest.mark.parametrize("status", [JobStatus.FAILED, JobStatus.NEEDS_REVIEW])
async def test_admin_retry_requeues(
    session: AsyncSession,
    session_factory: async_sessionmaker[AsyncSession],
    storage: LocalStorage,
    settings: Settings,
    employee: User,
    admin: User,
    car_jpeg: bytes,
    status: JobStatus,
) -> None:
    job = await _create_job(session, storage, settings, employee, car_jpeg)
    repo = JobRepository(session)
    await repo.transition(job.id, from_statuses=[JobStatus.QUEUED], to=JobStatus.PROCESSING)
    await repo.transition(job.id, from_statuses=[JobStatus.PROCESSING], to=status)
    await session.commit()

    retried = await JobService(session, storage, settings, provider_names).retry(admin, job.id)
    await session.commit()
    assert retried.status is JobStatus.QUEUED
    assert retried.attempts == 1
    assert retried.error_message is None

    processor = _processor(
        session_factory, storage, settings, MockImageProvider(), RecordingNotifier()
    )
    assert await processor.process(job.id) is JobStatus.COMPLETED
