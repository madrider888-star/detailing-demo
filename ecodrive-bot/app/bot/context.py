"""Общие зависимости бота, передаются в обработчики как `ctx`."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import Settings
from app.core.enums import Operation
from app.services.storage import Storage
from app.workers.queue import JobQueue


@dataclass
class AppContext:
    settings: Settings
    session_factory: async_sessionmaker[AsyncSession]
    storage: Storage
    queue: JobQueue
    provider_names: dict[Operation, str]

    def provider_name(self, operation: Operation) -> str:
        return self.provider_names.get(operation, "unknown")
