"""Работа с Telegram API: файлы, редактирование сообщений, повтор при RetryAfter."""

from __future__ import annotations

import asyncio
import io
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from aiogram import Bot
from aiogram.exceptions import (
    TelegramBadRequest,
    TelegramNetworkError,
    TelegramRetryAfter,
)
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message

from app.core.errors import ImageValidationError
from app.core.logging import get_logger

log = get_logger(__name__)


@dataclass(frozen=True)
class IncomingFile:
    file_id: str
    file_size: int | None
    declared_mime: str | None
    compressed: bool


def extract_incoming_file(message: Message) -> IncomingFile | None:
    if message.photo:
        biggest = message.photo[-1]
        return IncomingFile(biggest.file_id, biggest.file_size, "image/jpeg", compressed=True)
    if message.document:
        doc = message.document
        return IncomingFile(doc.file_id, doc.file_size, doc.mime_type, compressed=False)
    return None


async def tg_call[T](factory: Callable[[], Awaitable[T]], attempts: int = 3) -> T:
    """Повтор вызова Telegram при flood-control и сетевых сбоях."""
    for attempt in range(1, attempts + 1):
        try:
            return await factory()
        except TelegramRetryAfter as exc:
            if attempt == attempts:
                raise
            await asyncio.sleep(min(exc.retry_after, 30))
        except TelegramNetworkError:
            if attempt == attempts:
                raise
            await asyncio.sleep(2**attempt)
    raise AssertionError("unreachable")  # pragma: no cover


async def download_file(bot: Bot, incoming: IncomingFile, max_bytes: int) -> bytes:
    if incoming.file_size is not None and incoming.file_size > max_bytes:
        raise ImageValidationError(
            "too large",
            user_message=f"Файл слишком большой (максимум {max_bytes // (1024 * 1024)} МБ).",
        )
    buffer = io.BytesIO()
    try:
        await tg_call(lambda: bot.download(incoming.file_id, destination=buffer, timeout=60))
    except TelegramBadRequest as exc:
        # Например, «file is too big» — Bot API отдаёт ботам файлы до 20 МБ.
        raise ImageValidationError(
            f"download failed: {exc}",
            user_message="Не удалось загрузить файл из Telegram. Попробуйте файл меньшего размера.",
        ) from exc
    data = buffer.getvalue()
    if len(data) > max_bytes:
        raise ImageValidationError("too large", user_message="Файл слишком большой.")
    return data


async def show(
    target: Message | CallbackQuery,
    text: str,
    reply_markup: InlineKeyboardMarkup | None = None,
) -> Message | None:
    """Для callback — редактирует сообщение с кнопками, иначе отправляет новое."""
    if isinstance(target, CallbackQuery):
        message = target.message
        if isinstance(message, Message):
            try:
                edited = await message.edit_text(text, reply_markup=reply_markup)
                return edited if isinstance(edited, Message) else message
            except TelegramBadRequest as exc:
                if "message is not modified" in str(exc):
                    return message
                log.debug("show.edit_failed", error=str(exc))
            return await message.answer(text, reply_markup=reply_markup)
        return None
    return await target.answer(text, reply_markup=reply_markup)
