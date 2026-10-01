"""Telegram-реализация `JobNotifier`: одно статус-сообщение на задание."""

from __future__ import annotations

import html

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.types import BufferedInputFile, InlineKeyboardMarkup
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.bot import texts
from app.bot.keyboards.jobs import failed_kb, plate_review_kb, result_kb
from app.bot.telegram_io import tg_call
from app.core.enums import Operation
from app.core.logging import get_logger
from app.database.session import session_scope
from app.models import Job
from app.repositories.jobs import JobRepository
from app.services.export.normalizer import ExportResult

log = get_logger(__name__)


class TelegramNotifier:
    def __init__(self, bot: Bot, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self.bot = bot
        self.session_factory = session_factory

    async def _update_status(
        self, job: Job, extra: str | None = None, markup: InlineKeyboardMarkup | None = None
    ) -> None:
        if job.telegram_chat_id is None:
            return
        chat_id = job.telegram_chat_id
        text = texts.job_status_text(job, extra)
        if job.status_message_id is not None:
            message_id = job.status_message_id
            try:
                await tg_call(
                    lambda: self.bot.edit_message_text(
                        text=text, chat_id=chat_id, message_id=message_id, reply_markup=markup
                    )
                )
                return
            except TelegramBadRequest as exc:
                if "message is not modified" in str(exc):
                    return
                log.info("notify.edit_failed_send_new", job_id=job.id, error=str(exc))
            except TelegramForbiddenError:
                log.warning("notify.forbidden", job_id=job.id)
                return
        sent = await tg_call(lambda: self.bot.send_message(chat_id, text, reply_markup=markup))
        async with session_scope(self.session_factory) as session:
            await JobRepository(session).set_status_message(job.id, chat_id, sent.message_id)
        job.status_message_id = sent.message_id

    async def job_status(self, job: Job) -> None:
        await self._update_status(job)

    async def job_completed(self, job: Job, result: ExportResult, filename: str) -> None:
        await self._update_status(job)
        if job.telegram_chat_id is None:
            return
        chat_id = job.telegram_chat_id
        size_mb = len(result.data) / (1024 * 1024)
        caption = (
            f"✅ Задание <b>{job.number}</b> готово\n"
            f"{result.width}×{result.height}, JPEG sRGB, {size_mb:.1f} МБ"
        )
        if result.labeled:
            caption += "\nℹ️ Добавлена отметка «Візуалізація»."
        document = BufferedInputFile(result.data, filename=filename)
        await tg_call(
            lambda: self.bot.send_document(
                chat_id,
                document,
                caption=caption,
                reply_markup=result_kb(job.id),
                disable_content_type_detection=True,
            )
        )

    async def job_needs_review(self, job: Job, reason: str) -> None:
        if job.operation is Operation.PLATE:
            extra = (
                f"⚠️ Не удалось заменить номер: {html.escape(reason)}.\n"
                "Можно отправить другую фотографию (номер крупнее, без бликов), "
                "дождаться ручного выделения в будущей версии или передать фото оператору."
            )
            await self._update_status(job, extra, plate_review_kb(job.id))
        else:
            await self._update_status(job, f"⚠️ {html.escape(reason)}", failed_kb(job.id))

    async def job_failed(self, job: Job, user_message: str) -> None:
        await self._update_status(job, f"❌ {html.escape(user_message)}", failed_kb(job.id))
