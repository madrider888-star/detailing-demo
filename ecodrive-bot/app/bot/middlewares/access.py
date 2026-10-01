"""Белый список: посторонние не могут пользоваться корпоративным ботом."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject, Update
from aiogram.types import User as TgUser

from app.bot import texts
from app.core.config import Settings
from app.core.logging import get_logger
from app.services.access import AccessService

log = get_logger(__name__)


class AccessMiddleware(BaseMiddleware):
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        tg_user: TgUser | None = data.get("event_from_user")
        if tg_user is None or tg_user.is_bot:
            return None
        service = AccessService(data["session"], self.settings)
        decision, user = await service.authenticate(tg_user.id, tg_user.username, tg_user.full_name)
        if not decision.allowed or user is None:
            log.warning("access.denied", telegram_id=tg_user.id, reason=decision.reason.value)
            await self._deny(event, tg_user.id)
            return None
        data["db_user"] = user
        return await handler(event, data)

    @staticmethod
    async def _deny(event: TelegramObject, telegram_id: int) -> None:
        text = texts.ACCESS_DENIED.format(telegram_id=telegram_id)
        inner = event.event if isinstance(event, Update) else event
        if isinstance(inner, Message) and inner.chat.type == "private":
            await inner.answer(text)
        elif isinstance(inner, CallbackQuery):
            await inner.answer("⛔ Доступ запрещён", show_alert=True)
