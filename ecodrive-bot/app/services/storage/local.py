"""Файловое хранилище для разработки и тестов."""

from __future__ import annotations

import asyncio
import os
import tempfile
from pathlib import Path

from app.core.errors import StorageError
from app.services.storage.base import Storage


class LocalStorage(Storage):
    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        path = (self.root / key).resolve()
        if not path.is_relative_to(self.root):
            raise StorageError(f"key escapes storage root: {key!r}")
        return path

    async def put(self, key: str, data: bytes, content_type: str) -> None:
        path = self._path(key)

        def _write() -> None:
            path.parent.mkdir(parents=True, exist_ok=True)
            # Атомарная запись: временный файл + rename. Временный файл удаляется при ошибке.
            fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".upload-")
            try:
                with os.fdopen(fd, "wb") as fh:
                    fh.write(data)
                os.replace(tmp, path)
            except BaseException:
                Path(tmp).unlink(missing_ok=True)
                raise

        await asyncio.to_thread(_write)

    async def get(self, key: str) -> bytes:
        path = self._path(key)
        try:
            return await asyncio.to_thread(path.read_bytes)
        except FileNotFoundError as exc:
            raise StorageError(f"object not found: {key}") from exc

    async def exists(self, key: str) -> bool:
        return self._path(key).is_file()

    async def delete(self, key: str) -> None:
        self._path(key).unlink(missing_ok=True)
