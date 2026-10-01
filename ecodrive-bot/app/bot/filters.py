from __future__ import annotations

from typing import Any

from aiogram.filters import BaseFilter
from aiogram.types import TelegramObject

from app.core.enums import Role
from app.models import User
from app.services.access import has_role


class RoleFilter(BaseFilter):
    """Пропускает только пользователей с ролью не ниже `required`."""

    def __init__(self, required: Role) -> None:
        self.required = required

    async def __call__(self, event: TelegramObject, db_user: User | None = None, **_: Any) -> bool:
        return db_user is not None and has_role(db_user, self.required)
