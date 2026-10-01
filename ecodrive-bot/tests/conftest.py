from __future__ import annotations

from collections.abc import AsyncIterator
from pathlib import Path

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import Settings
from app.core.enums import Operation, Role
from app.database.base import Base
from app.models import User
from app.repositories.users import UserRepository
from app.services.storage import LocalStorage
from tests.synthetic import make_scene, to_jpeg_bytes

ADMIN_ID = 1001
EMPLOYEE_ID = 2002
STRANGER_ID = 9999


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    return Settings(
        _env_file=None,  # type: ignore[call-arg]
        app_env="test",
        bot_token="123456:" + "A" * 35,
        admin_telegram_ids=[ADMIN_ID],
        allowed_telegram_ids=[EMPLOYEE_ID],
        database_url=f"sqlite+aiosqlite:///{tmp_path / 'test.db'}",
        storage_backend="local",
        local_storage_path=tmp_path / "storage",
        image_provider="mock",
        plate_provider="opencv",
        max_active_jobs_per_user=2,
        provider_max_retries=3,
        provider_timeout_seconds=5,
    )


@pytest.fixture
async def session_factory(settings: Settings) -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    engine = create_async_engine(settings.database_url)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield async_sessionmaker(engine, expire_on_commit=False)
    await engine.dispose()


@pytest.fixture
async def session(
    session_factory: async_sessionmaker[AsyncSession],
) -> AsyncIterator[AsyncSession]:
    async with session_factory() as s:
        yield s


@pytest.fixture
def storage(settings: Settings) -> LocalStorage:
    return LocalStorage(settings.local_storage_path)


@pytest.fixture
async def employee(session: AsyncSession) -> User:
    user = await UserRepository(session).create(
        telegram_id=EMPLOYEE_ID, role=Role.EMPLOYEE, username="employee"
    )
    await session.commit()
    return user


@pytest.fixture
async def admin(session: AsyncSession) -> User:
    user = await UserRepository(session).create(
        telegram_id=ADMIN_ID, role=Role.ADMIN, username="boss"
    )
    await session.commit()
    return user


@pytest.fixture(scope="session")
def car_jpeg() -> bytes:
    scene, _ = make_scene()
    return to_jpeg_bytes(scene)


def provider_names(_: Operation) -> str:
    return "mock"
