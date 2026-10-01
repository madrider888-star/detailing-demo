"""Контроль доступа: белый список Telegram ID и роли."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.enums import Role
from app.models import User
from app.repositories.audit import AuditRepository
from app.repositories.users import UserRepository

ROLE_RANK: dict[Role, int] = {Role.EMPLOYEE: 0, Role.MODERATOR: 1, Role.ADMIN: 2}


class AccessReason(StrEnum):
    BOOTSTRAP_ADMIN = "bootstrap_admin"
    ACTIVE_USER = "active_user"
    BLOCKED = "blocked"
    WHITELISTED = "whitelisted"
    NOT_WHITELISTED = "not_whitelisted"


@dataclass(frozen=True)
class AccessDecision:
    allowed: bool
    reason: AccessReason
    role: Role | None = None
    create_user: bool = False


def resolve_access(telegram_id: int, user: User | None, settings: Settings) -> AccessDecision:
    """Чистая функция принятия решения о доступе.

    Порядок:
    1. ID из ADMIN_TELEGRAM_IDS — всегда администратор (нельзя заблокировать себя насовсем).
    2. Пользователь есть в БД — решает флаг is_active (блокировка из /block_user сильнее
       белого списка в .env).
    3. ID из ALLOWED_TELEGRAM_IDS — создаётся сотрудник.
    4. Иначе — доступ запрещён.
    """
    if telegram_id in settings.admin_telegram_ids:
        return AccessDecision(
            True, AccessReason.BOOTSTRAP_ADMIN, Role.ADMIN, create_user=user is None
        )
    if user is not None:
        if user.is_active:
            return AccessDecision(True, AccessReason.ACTIVE_USER, user.role)
        return AccessDecision(False, AccessReason.BLOCKED, user.role)
    if telegram_id in settings.allowed_telegram_ids:
        return AccessDecision(True, AccessReason.WHITELISTED, Role.EMPLOYEE, create_user=True)
    return AccessDecision(False, AccessReason.NOT_WHITELISTED)


def has_role(user: User, required: Role) -> bool:
    return user.is_active and ROLE_RANK[user.role] >= ROLE_RANK[required]


class AccessService:
    def __init__(self, session: AsyncSession, settings: Settings) -> None:
        self.users = UserRepository(session)
        self.audit = AuditRepository(session)
        self.settings = settings

    async def authenticate(
        self, telegram_id: int, username: str | None, full_name: str | None
    ) -> tuple[AccessDecision, User | None]:
        user = await self.users.get_by_telegram_id(telegram_id)
        decision = resolve_access(telegram_id, user, self.settings)
        if not decision.allowed:
            return decision, user
        if user is None:
            assert decision.role is not None
            user = await self.users.create(
                telegram_id=telegram_id,
                role=decision.role,
                username=username,
                full_name=full_name,
            )
            await self.audit.log("user.auto_registered", user_id=user.id, reason=decision.reason)
        else:
            if decision.reason is AccessReason.BOOTSTRAP_ADMIN and (
                user.role is not Role.ADMIN or not user.is_active
            ):
                user.role, user.is_active = Role.ADMIN, True
            # Обновляем профиль, если сотрудник сменил username / имя.
            if username != user.username or full_name != user.full_name:
                user.username, user.full_name = username, full_name
        return decision, user

    async def allow_user(self, actor: User, telegram_id: int, role: Role = Role.EMPLOYEE) -> User:
        user = await self.users.get_by_telegram_id(telegram_id)
        if user is None:
            user = await self.users.create(telegram_id=telegram_id, role=role)
        else:
            user.is_active, user.role = True, role
        await self.audit.log(
            "admin.allow_user", user_id=actor.id, target_telegram_id=telegram_id, role=role
        )
        return user

    async def block_user(self, actor: User, telegram_id: int) -> User | None:
        if telegram_id in self.settings.admin_telegram_ids:
            return None
        user = await self.users.get_by_telegram_id(telegram_id)
        if user is None:
            user = await self.users.create(telegram_id=telegram_id, is_active=False)
        else:
            user.is_active = False
        await self.audit.log("admin.block_user", user_id=actor.id, target_telegram_id=telegram_id)
        return user
