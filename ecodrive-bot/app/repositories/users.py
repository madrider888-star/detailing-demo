from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import Role
from app.models import User


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_telegram_id(
        self, telegram_id: int, *, for_update: bool = False
    ) -> User | None:
        stmt = select(User).where(User.telegram_id == telegram_id)
        if for_update:
            stmt = stmt.with_for_update()
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def get(self, user_id: int, *, for_update: bool = False) -> User | None:
        stmt = select(User).where(User.id == user_id)
        if for_update:
            stmt = stmt.with_for_update()
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def create(
        self,
        *,
        telegram_id: int,
        role: Role = Role.EMPLOYEE,
        username: str | None = None,
        full_name: str | None = None,
        is_active: bool = True,
    ) -> User:
        user = User(
            telegram_id=telegram_id,
            role=role,
            username=username,
            full_name=full_name,
            is_active=is_active,
        )
        self.session.add(user)
        await self.session.flush()
        return user

    async def list_all(self, limit: int = 100) -> Sequence[User]:
        stmt = select(User).order_by(User.id).limit(limit)
        return (await self.session.execute(stmt)).scalars().all()

    async def list_staff(self) -> Sequence[User]:
        """Активные модераторы и администраторы — получатели уведомлений."""
        stmt = select(User).where(
            User.is_active.is_(True), User.role.in_([Role.ADMIN, Role.MODERATOR])
        )
        return (await self.session.execute(stmt)).scalars().all()
