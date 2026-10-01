"""Постановка заданий в очередь ARQ (Redis)."""

from __future__ import annotations

from typing import Protocol

from arq.connections import ArqRedis, RedisSettings, create_pool

TASK_NAME = "process_job"
DEFAULT_QUEUE = "arq:queue"


class JobQueue(Protocol):
    async def enqueue(self, job_id: int, attempt: int = 0) -> None: ...

    async def size(self) -> int: ...


class ArqJobQueue:
    def __init__(self, redis: ArqRedis) -> None:
        self.redis = redis

    @classmethod
    async def connect(cls, redis_url: str) -> ArqJobQueue:
        return cls(await create_pool(RedisSettings.from_dsn(redis_url)))

    async def enqueue(self, job_id: int, attempt: int = 0) -> None:
        # Уникальный _job_id: ARQ не поставит одну и ту же попытку дважды.
        await self.redis.enqueue_job(TASK_NAME, job_id, _job_id=f"job:{job_id}:{attempt}")

    async def size(self) -> int:
        return int(await self.redis.zcard(DEFAULT_QUEUE))

    async def close(self) -> None:
        await self.redis.aclose()


class InMemoryJobQueue:
    """Очередь для тестов и локальной отладки."""

    def __init__(self) -> None:
        self.items: list[tuple[int, int]] = []

    async def enqueue(self, job_id: int, attempt: int = 0) -> None:
        if (job_id, attempt) not in self.items:
            self.items.append((job_id, attempt))

    async def size(self) -> int:
        return len(self.items)

    async def close(self) -> None:
        return None
