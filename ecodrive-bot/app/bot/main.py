"""Точка входа Telegram-бота: `python -m app.bot.main`."""

from __future__ import annotations

import asyncio
from datetime import timedelta

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.types import BotCommand

from app.bot.context import AppContext
from app.bot.dispatcher import create_dispatcher
from app.core.config import get_settings
from app.core.enums import Operation
from app.core.logging import configure_logging, get_logger
from app.database.session import create_engine, create_session_factory
from app.services.image_editing.factory import build_registry
from app.services.storage import create_storage
from app.workers.queue import ArqJobQueue

COMMANDS = [
    BotCommand(command="start", description="Главное меню"),
    BotCommand(command="my", description="Мои обработки"),
    BotCommand(command="help", description="Инструкция"),
    BotCommand(command="cancel", description="Отменить текущий шаг"),
]


async def run() -> None:
    settings = get_settings()
    configure_logging(settings.log_level, settings.log_format, settings.secret_values())
    log = get_logger("bot")
    if not settings.bot_token.get_secret_value():
        raise SystemExit("BOT_TOKEN is not set — заполните .env (см. README)")

    engine = create_engine(settings.database_url)
    session_factory = create_session_factory(engine)
    storage = create_storage(settings)
    await storage.ensure_ready()
    queue = await ArqJobQueue.connect(settings.redis_url)
    # Провайдеры в боте нужны только для имени в задании; сама обработка — в воркере.
    registry = build_registry(settings)
    provider_names = {op: registry.name_for(op) for op in Operation}
    await registry.aclose()

    ctx = AppContext(
        settings=settings,
        session_factory=session_factory,
        storage=storage,
        queue=queue,
        provider_names=provider_names,
    )
    fsm_storage = RedisStorage.from_url(
        settings.redis_url, state_ttl=timedelta(days=1), data_ttl=timedelta(days=1)
    )
    dp = create_dispatcher(ctx, fsm_storage)
    bot = Bot(
        token=settings.bot_token.get_secret_value(),
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    try:
        await bot.set_my_commands(COMMANDS)
        log.info("bot.started", providers={k.value: v for k, v in provider_names.items()})
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()
        await fsm_storage.close()
        await queue.close()
        await engine.dispose()


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
