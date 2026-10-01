"""ARQ-воркер: `arq app.workers.worker.WorkerSettings`."""

from __future__ import annotations

from typing import Any, ClassVar

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from arq.connections import RedisSettings

from app.bot.notifier import TelegramNotifier
from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.database.session import create_engine, create_session_factory
from app.services.image_editing.factory import build_registry
from app.services.storage import create_storage
from app.workers.processor import JobProcessor

log = get_logger("worker")
_settings = get_settings()


async def startup(ctx: dict[str, Any]) -> None:
    settings = get_settings()
    configure_logging(settings.log_level, settings.log_format, settings.secret_values())
    # Ресурсы кладём в ctx сразу после создания, чтобы shutdown их закрыл даже при сбое.
    ctx["engine"] = create_engine(settings.database_url)
    session_factory = create_session_factory(ctx["engine"])
    ctx["bot"] = Bot(
        token=settings.bot_token.get_secret_value(),
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    ctx["registry"] = build_registry(settings)
    storage = create_storage(settings)
    await storage.ensure_ready()
    ctx["processor"] = JobProcessor(
        session_factory=session_factory,
        storage=storage,
        registry=ctx["registry"],
        notifier=TelegramNotifier(ctx["bot"], session_factory),
        settings=settings,
    )
    log.info(
        "worker.started", image_provider=settings.image_provider, plate=settings.plate_provider
    )


async def shutdown(ctx: dict[str, Any]) -> None:
    # startup мог упасть на полпути — закрываем только то, что успели создать.
    if "registry" in ctx:
        await ctx["registry"].aclose()
    if "bot" in ctx:
        await ctx["bot"].session.close()
    if "engine" in ctx:
        await ctx["engine"].dispose()


async def process_job(ctx: dict[str, Any], job_id: int) -> str | None:
    processor: JobProcessor = ctx["processor"]
    # job_try > 1 — ARQ перезапускает задачу после падения воркера: разрешаем
    # повторно взять задание, застрявшее в статусе processing.
    status = await processor.process(job_id, reclaim=ctx.get("job_try", 1) > 1)
    return status.value if status else None


class WorkerSettings:
    functions: ClassVar[list[Any]] = [process_job]
    on_startup = startup
    on_shutdown = shutdown
    redis_settings = RedisSettings.from_dsn(_settings.redis_url)
    max_jobs = 4
    job_timeout = int(
        _settings.provider_timeout_seconds * max(1, _settings.provider_max_retries) + 180
    )
    max_tries = 2
    keep_result = 3600
