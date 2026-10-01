"""Абстракция объектного хранилища."""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from datetime import UTC, datetime

from app.core.enums import AssetType

_PREFIX: dict[AssetType, str] = {
    AssetType.ORIGINAL: "originals",
    AssetType.REFERENCE: "references",
    AssetType.RESULT: "results",
}


def build_object_key(asset_type: AssetType, job_id: int, extension: str) -> str:
    """Уникальный ключ объекта. Оригиналы и результаты лежат в разных префиксах."""
    now = datetime.now(UTC)
    ext = extension.lower().lstrip(".")
    if not ext.isalnum():
        raise ValueError("invalid extension")
    return f"{_PREFIX[asset_type]}/{now:%Y/%m}/job-{job_id}/{uuid.uuid4().hex}.{ext}"


class Storage(ABC):
    @abstractmethod
    async def put(self, key: str, data: bytes, content_type: str) -> None: ...

    @abstractmethod
    async def get(self, key: str) -> bytes: ...

    @abstractmethod
    async def exists(self, key: str) -> bool: ...

    @abstractmethod
    async def delete(self, key: str) -> None: ...

    async def ensure_ready(self) -> None:  # noqa: B027 — необязательный хук
        """Подготовить хранилище при старте (например, создать бакет)."""

    async def healthcheck(self) -> bool:
        return True
