"""Создание задания, лимиты, идемпотентность, статусы."""

from __future__ import annotations

import io

import pytest
from PIL import Image
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.enums import AssetType, JobStatus, Operation
from app.core.errors import DuplicateJobError, InvalidStatusTransitionError, TooManyActiveJobsError
from app.models import User
from app.repositories.assets import AssetRepository
from app.repositories.jobs import JobRepository
from app.services.image_validation import ValidatedImage, validate_image
from app.services.job_status import can_transition, ensure_transition, sources_for
from app.services.jobs import JobImage, JobService
from app.services.storage import LocalStorage
from tests.conftest import provider_names


def _image() -> ValidatedImage:
    buf = io.BytesIO()
    Image.new("RGB", (800, 600), (50, 50, 50)).save(buf, "JPEG")
    return validate_image(buf.getvalue(), max_bytes=10**7, max_pixels=10**8, min_side=100)


def _service(session: AsyncSession, storage: LocalStorage, settings: Settings) -> JobService:
    return JobService(session, storage, settings, provider_names)


async def test_create_job_stores_assets(
    session: AsyncSession, storage: LocalStorage, settings: Settings, employee: User
) -> None:
    job = await _service(session, storage, settings).create_job(
        user=employee,
        operation=Operation.WHEELS,
        raw_params={"size_mode": "keep"},
        images=[JobImage(AssetType.ORIGINAL, _image()), JobImage(AssetType.REFERENCE, _image())],
        idempotency_key="abc",
        chat_id=employee.telegram_id,
    )
    await session.commit()
    assert job.status is JobStatus.QUEUED
    assert job.number == f"#{job.id:04d}"
    assert job.provider == "mock"
    assets = await AssetRepository(session).list_for_job(job.id)
    assert [a.asset_type for a in assets] == [AssetType.ORIGINAL, AssetType.REFERENCE]
    keys = {a.storage_key for a in assets}
    assert len(keys) == 2  # уникальные имена объектов
    for asset in assets:
        assert await storage.exists(asset.storage_key)
        assert asset.width == 800 and asset.height == 600


async def test_wrong_image_count_rejected(
    session: AsyncSession, storage: LocalStorage, settings: Settings, employee: User
) -> None:
    with pytest.raises(ValueError, match="expects 2 images"):
        await _service(session, storage, settings).create_job(
            user=employee,
            operation=Operation.WHEELS,
            raw_params={"size_mode": "keep"},
            images=[JobImage(AssetType.ORIGINAL, _image())],
            idempotency_key=None,
            chat_id=None,
        )


async def test_idempotency_key_prevents_duplicates(
    session: AsyncSession, storage: LocalStorage, settings: Settings, employee: User
) -> None:
    service = _service(session, storage, settings)
    kwargs = {
        "user": employee,
        "operation": Operation.PLATE,
        "raw_params": {},
        "images": [JobImage(AssetType.ORIGINAL, _image())],
        "idempotency_key": "same-key",
        "chat_id": None,
    }
    await service.create_job(**kwargs)  # type: ignore[arg-type]
    await session.commit()
    with pytest.raises(DuplicateJobError):
        await service.create_job(**kwargs)  # type: ignore[arg-type]


async def test_active_jobs_limit(
    session: AsyncSession, storage: LocalStorage, settings: Settings, employee: User
) -> None:
    service = _service(session, storage, settings)
    for _ in range(settings.max_active_jobs_per_user):
        await service.create_job(
            user=employee,
            operation=Operation.PLATE,
            raw_params={},
            images=[JobImage(AssetType.ORIGINAL, _image())],
            idempotency_key=None,
            chat_id=None,
        )
    with pytest.raises(TooManyActiveJobsError):
        await service.create_job(
            user=employee,
            operation=Operation.PLATE,
            raw_params={},
            images=[JobImage(AssetType.ORIGINAL, _image())],
            idempotency_key=None,
            chat_id=None,
        )


def test_status_machine() -> None:
    assert can_transition(JobStatus.QUEUED, JobStatus.PROCESSING)
    assert can_transition(JobStatus.PROCESSING, JobStatus.COMPLETED)
    assert can_transition(JobStatus.PROCESSING, JobStatus.NEEDS_REVIEW)
    assert can_transition(JobStatus.FAILED, JobStatus.QUEUED)
    assert can_transition(JobStatus.COMPLETED, JobStatus.NEEDS_REVIEW)
    assert not can_transition(JobStatus.COMPLETED, JobStatus.PROCESSING)
    assert not can_transition(JobStatus.QUEUED, JobStatus.COMPLETED)
    assert sources_for(JobStatus.QUEUED) == {JobStatus.FAILED, JobStatus.NEEDS_REVIEW}
    with pytest.raises(InvalidStatusTransitionError):
        ensure_transition(JobStatus.COMPLETED, JobStatus.QUEUED)


async def test_conditional_transition_is_atomic(
    session: AsyncSession, storage: LocalStorage, settings: Settings, employee: User
) -> None:
    job = await _service(session, storage, settings).create_job(
        user=employee,
        operation=Operation.PLATE,
        raw_params={},
        images=[JobImage(AssetType.ORIGINAL, _image())],
        idempotency_key=None,
        chat_id=None,
    )
    repo = JobRepository(session)
    assert await repo.transition(job.id, from_statuses=[JobStatus.QUEUED], to=JobStatus.PROCESSING)
    # Второй воркер не может взять ту же задачу.
    assert not await repo.transition(
        job.id, from_statuses=[JobStatus.QUEUED], to=JobStatus.PROCESSING
    )
    assert await repo.transition(
        job.id, from_statuses=[JobStatus.PROCESSING], to=JobStatus.COMPLETED
    )
    stored = await repo.get(job.id)
    assert stored is not None
    assert stored.status is JobStatus.COMPLETED
    assert stored.started_at is not None and stored.completed_at is not None


async def test_redo_and_report(
    session: AsyncSession, storage: LocalStorage, settings: Settings, employee: User
) -> None:
    service = _service(session, storage, settings)
    job = await service.create_job(
        user=employee,
        operation=Operation.BACKGROUND,
        raw_params={"background": "road"},
        images=[JobImage(AssetType.ORIGINAL, _image())],
        idempotency_key=None,
        chat_id=None,
    )
    repo = JobRepository(session)
    await repo.transition(job.id, from_statuses=[JobStatus.QUEUED], to=JobStatus.PROCESSING)
    await repo.transition(job.id, from_statuses=[JobStatus.PROCESSING], to=JobStatus.COMPLETED)

    redo = await service.redo(employee, job.id, chat_id=None)
    assert redo.id != job.id and redo.parameters == job.parameters
    originals = await AssetRepository(session).list_for_job(redo.id, AssetType.ORIGINAL)
    assert len(originals) == 1

    reported = await service.report_problem(employee, job.id, "диски кривые")
    assert reported.status is JobStatus.NEEDS_REVIEW
