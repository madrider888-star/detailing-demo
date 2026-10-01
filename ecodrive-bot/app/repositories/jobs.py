from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import Any

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.enums import ACTIVE_JOB_STATUSES, JobStatus, Operation
from app.database.base import utcnow
from app.models import Job


class JobRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        *,
        user_id: int,
        operation: Operation,
        parameters: dict[str, Any],
        provider: str | None,
        idempotency_key: str | None = None,
        telegram_chat_id: int | None = None,
    ) -> Job:
        job = Job(
            user_id=user_id,
            operation=operation,
            status=JobStatus.QUEUED,
            parameters=parameters,
            provider=provider,
            idempotency_key=idempotency_key,
            telegram_chat_id=telegram_chat_id,
        )
        self.session.add(job)
        await self.session.flush()
        return job

    async def get(self, job_id: int, *, with_assets: bool = False) -> Job | None:
        stmt = select(Job).where(Job.id == job_id)
        if with_assets:
            stmt = stmt.options(selectinload(Job.assets), selectinload(Job.user))
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def count_active_for_user(self, user_id: int) -> int:
        stmt = select(func.count(Job.id)).where(
            Job.user_id == user_id, Job.status.in_(ACTIVE_JOB_STATUSES)
        )
        return int((await self.session.execute(stmt)).scalar_one())

    async def list_for_user(self, user_id: int, limit: int = 10) -> Sequence[Job]:
        stmt = select(Job).where(Job.user_id == user_id).order_by(Job.id.desc()).limit(limit)
        return (await self.session.execute(stmt)).scalars().all()

    async def list_recent(
        self, limit: int = 15, statuses: Iterable[JobStatus] | None = None
    ) -> Sequence[Job]:
        stmt = select(Job).options(selectinload(Job.user)).order_by(Job.id.desc()).limit(limit)
        if statuses is not None:
            stmt = stmt.where(Job.status.in_(list(statuses)))
        return (await self.session.execute(stmt)).scalars().all()

    async def transition(
        self,
        job_id: int,
        *,
        from_statuses: Iterable[JobStatus],
        to: JobStatus,
        **values: Any,
    ) -> bool:
        """Атомарный условный переход статуса.

        Обновление выполняется одним `UPDATE ... WHERE status IN (...)`, поэтому две
        конкурентные попытки взять одну задачу не могут обе завершиться успехом.
        """
        if to == JobStatus.PROCESSING:
            values.setdefault("started_at", utcnow())
        if to in (JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.NEEDS_REVIEW):
            values.setdefault("completed_at", utcnow())
        stmt = (
            update(Job)
            .where(Job.id == job_id, Job.status.in_(list(from_statuses)))
            .values(status=to, **values)
            .execution_options(synchronize_session=False)
        )
        result = await self.session.execute(stmt)
        changed = bool(result.rowcount)  # type: ignore[attr-defined]
        if changed:
            # Сбрасываем закешированное в identity map состояние.
            cached = await self.session.get(Job, job_id)
            if cached is not None:
                await self.session.refresh(cached)
        return changed

    async def set_status_message(self, job_id: int, chat_id: int, message_id: int) -> None:
        await self.session.execute(
            update(Job)
            .where(Job.id == job_id)
            .values(telegram_chat_id=chat_id, status_message_id=message_id)
        )

    async def counts_by_operation(self) -> dict[str, int]:
        stmt = select(Job.operation, func.count(Job.id)).group_by(Job.operation)
        rows = (await self.session.execute(stmt)).all()
        return {str(op): int(n) for op, n in rows}

    async def counts_by_status(self) -> dict[str, int]:
        stmt = select(Job.status, func.count(Job.id)).group_by(Job.status)
        rows = (await self.session.execute(stmt)).all()
        return {str(status): int(n) for status, n in rows}
