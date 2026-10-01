"""Проверка доступа: белый список, роли, блокировка."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.enums import Role
from app.models import User
from app.services.access import AccessReason, AccessService, has_role, resolve_access
from tests.conftest import ADMIN_ID, EMPLOYEE_ID, STRANGER_ID


def _user(telegram_id: int, role: Role = Role.EMPLOYEE, active: bool = True) -> User:
    return User(telegram_id=telegram_id, role=role, is_active=active)


def test_stranger_is_denied(settings: Settings) -> None:
    decision = resolve_access(STRANGER_ID, None, settings)
    assert not decision.allowed
    assert decision.reason is AccessReason.NOT_WHITELISTED


def test_whitelisted_employee_is_auto_created(settings: Settings) -> None:
    decision = resolve_access(EMPLOYEE_ID, None, settings)
    assert decision.allowed and decision.create_user
    assert decision.role is Role.EMPLOYEE


def test_blocked_user_overrides_env_whitelist(settings: Settings) -> None:
    decision = resolve_access(EMPLOYEE_ID, _user(EMPLOYEE_ID, active=False), settings)
    assert not decision.allowed
    assert decision.reason is AccessReason.BLOCKED


def test_bootstrap_admin_always_allowed(settings: Settings) -> None:
    decision = resolve_access(ADMIN_ID, _user(ADMIN_ID, Role.EMPLOYEE, active=False), settings)
    assert decision.allowed
    assert decision.role is Role.ADMIN


def test_user_added_by_admin_is_allowed(settings: Settings) -> None:
    decision = resolve_access(STRANGER_ID, _user(STRANGER_ID, Role.MODERATOR), settings)
    assert decision.allowed and decision.role is Role.MODERATOR


def test_role_hierarchy() -> None:
    assert has_role(_user(1, Role.ADMIN), Role.MODERATOR)
    assert has_role(_user(1, Role.MODERATOR), Role.MODERATOR)
    assert not has_role(_user(1, Role.EMPLOYEE), Role.MODERATOR)
    assert not has_role(_user(1, Role.ADMIN, active=False), Role.EMPLOYEE)


async def test_authenticate_registers_and_promotes(
    session: AsyncSession, settings: Settings
) -> None:
    service = AccessService(session, settings)
    decision, user = await service.authenticate(EMPLOYEE_ID, "ivan", "Иван")
    assert decision.allowed and user is not None
    assert user.role is Role.EMPLOYEE and user.username == "ivan"

    decision, admin = await service.authenticate(ADMIN_ID, "boss", "Boss")
    assert admin is not None and admin.role is Role.ADMIN

    denied, nobody = await service.authenticate(STRANGER_ID, None, None)
    assert not denied.allowed and nobody is None


async def test_allow_and_block_user(session: AsyncSession, settings: Settings, admin: User) -> None:
    service = AccessService(session, settings)
    added = await service.allow_user(admin, STRANGER_ID, Role.MODERATOR)
    assert added.is_active and added.role is Role.MODERATOR
    decision, _ = await service.authenticate(STRANGER_ID, None, None)
    assert decision.allowed

    await service.block_user(admin, STRANGER_ID)
    decision, _ = await service.authenticate(STRANGER_ID, None, None)
    assert not decision.allowed
    # Администратора из .env заблокировать нельзя.
    assert await service.block_user(admin, ADMIN_ID) is None
