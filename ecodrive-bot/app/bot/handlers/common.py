"""Сообщения вне сценария и глобальный обработчик ошибок."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, ErrorEvent, Message

from app.bot import texts
from app.bot.keyboards.menu import main_menu_kb
from app.core.logging import get_logger

log = get_logger(__name__)
router = Router(name="common")

ERROR_TEXT = "😔 Что-то пошло не так. Попробуйте ещё раз или откройте меню: /start"


@router.message(F.photo | F.document)
async def media_outside_flow(message: Message) -> None:
    await message.answer(
        "Сначала выберите операцию — затем бот попросит нужные фото.",
        reply_markup=main_menu_kb(),
    )


@router.message()
async def fallback(message: Message) -> None:
    await message.answer(texts.MAIN_MENU, reply_markup=main_menu_kb())


@router.callback_query()
async def stale_callback(callback: CallbackQuery) -> None:
    await callback.answer("Кнопка устарела. Откройте меню: /start", show_alert=True)


@router.errors()
async def on_error(event: ErrorEvent) -> bool:
    exc = event.exception
    if isinstance(exc, TelegramBadRequest) and "message is not modified" in str(exc):
        return True
    log.error("bot.unhandled_error", error=type(exc).__name__, detail=str(exc)[:500], exc_info=exc)
    update = event.update
    try:
        if update.callback_query is not None:
            await update.callback_query.answer(ERROR_TEXT, show_alert=True)
        elif update.message is not None:
            await update.message.answer(ERROR_TEXT)
    except Exception:
        log.warning("bot.error_reply_failed")
    return True
