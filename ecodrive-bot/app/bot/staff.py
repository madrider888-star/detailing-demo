"""Уведомления модераторов и администраторов."""

from __future__ import annotations

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
from aiogram.types import BufferedInputFile, InlineKeyboardMarkup
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.logging import get_logger
from app.repositories.users import UserRepository

log = get_logger(__name__)


async def staff_chat_ids(session: AsyncSession, settings: Settings) -> set[int]:
    ids = {u.telegram_id for u in await UserRepository(session).list_staff()}
    return ids | set(settings.admin_telegram_ids)


async def notify_staff(
    bot: Bot,
    session: AsyncSession,
    settings: Settings,
    text: str,
    *,
    document: tuple[bytes, str] | None = None,
    markup: InlineKeyboardMarkup | None = None,
) -> int:
    sent = 0
    for chat_id in await staff_chat_ids(session, settings):
        try:
            if document is not None:
                data, filename = document
                await bot.send_document(
                    chat_id,
                    BufferedInputFile(data, filename=filename),
                    caption=text,
                    reply_markup=markup,
                )
            else:
                await bot.send_message(chat_id, text, reply_markup=markup)
            sent += 1
        except TelegramAPIError as exc:
            log.warning("staff.notify_failed", chat_id=chat_id, error=type(exc).__name__)
    return sent
