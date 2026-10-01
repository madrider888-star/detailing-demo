"""Сборка Dispatcher: middlewares и роутеры."""

from __future__ import annotations

from aiogram import Dispatcher
from aiogram.fsm.storage.base import BaseStorage

from app.bot.context import AppContext
from app.bot.handlers import admin, common, flow, jobs, start
from app.bot.middlewares.access import AccessMiddleware
from app.bot.middlewares.db import DbSessionMiddleware


def create_dispatcher(ctx: AppContext, storage: BaseStorage) -> Dispatcher:
    dp = Dispatcher(storage=storage)
    dp["ctx"] = ctx
    # Порядок важен: сначала сессия БД, затем проверка доступа.
    dp.update.outer_middleware(DbSessionMiddleware(ctx.session_factory))
    dp.update.outer_middleware(AccessMiddleware(ctx.settings))
    routers = (admin.router, start.router, flow.router, jobs.router, common.router)
    for router in routers:
        # Роутеры — синглтоны модулей; отвязываем их, чтобы Dispatcher можно было
        # собрать повторно (тесты, пересоздание при перезапуске polling).
        router._parent_router = None
    dp.include_routers(*routers)
    return dp
