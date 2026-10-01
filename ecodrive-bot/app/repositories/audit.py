from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AuditLog


class AuditRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def log(self, action: str, *, user_id: int | None, **metadata: Any) -> AuditLog:
        entry = AuditLog(user_id=user_id, action=action, metadata_=metadata)
        self.session.add(entry)
        await self.session.flush()
        return entry
