"""FastAPI: healthcheck и задел для будущего API.

Запуск: `uvicorn app.api.main:app --host 0.0.0.0 --port 8080`
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Response, status
from redis.asyncio import Redis
from sqlalchemy import text

from app import __version__
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.database.session import create_engine
from app.services.storage import create_storage


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    configure_logging(settings.log_level, settings.log_format, settings.secret_values())
    app.state.engine = create_engine(settings.database_url)
    app.state.redis = Redis.from_url(settings.redis_url)
    app.state.storage = create_storage(settings)
    yield
    await app.state.redis.aclose()
    await app.state.engine.dispose()


app = FastAPI(title="EcoDrive Auto Bot API", version=__version__, lifespan=lifespan)


@app.get("/health")
async def health() -> dict[str, str]:
    """Liveness: процесс жив."""
    return {"status": "ok"}


@app.get("/ready")
async def ready(response: Response) -> dict[str, Any]:
    """Readiness: доступны БД, Redis и хранилище."""
    checks: dict[str, bool] = {}
    try:
        async with app.state.engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        checks["database"] = True
    except Exception:
        checks["database"] = False
    try:
        checks["redis"] = bool(await app.state.redis.ping())
    except Exception:
        checks["redis"] = False
    try:
        checks["storage"] = await app.state.storage.healthcheck()
    except Exception:
        checks["storage"] = False
    ok = all(checks.values())
    if not ok:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return {"status": "ok" if ok else "degraded", "checks": checks}


@app.get("/version")
async def version() -> dict[str, str]:
    return {"version": __version__}
