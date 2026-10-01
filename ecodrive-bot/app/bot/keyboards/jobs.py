from __future__ import annotations

from collections.abc import Sequence

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.bot.keyboards.callbacks import AdminCb, JobCb, MenuCb, ReportCb
from app.core.enums import JobStatus
from app.models import Job


def result_kb(job_id: int) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="📥 Скачать оригинал", callback_data=JobCb(action="original", job_id=job_id))
    b.button(text="🔄 Переделать", callback_data=JobCb(action="redo", job_id=job_id))
    b.button(text="🆕 Новая обработка", callback_data=MenuCb(action="home"))
    b.button(text="⚠️ Сообщить о проблеме", callback_data=JobCb(action="report", job_id=job_id))
    b.adjust(2)
    return b.as_markup()


def failed_kb(job_id: int) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="🔄 Переделать", callback_data=JobCb(action="redo", job_id=job_id))
    b.button(text="⚠️ Сообщить о проблеме", callback_data=JobCb(action="report", job_id=job_id))
    b.button(text="🆕 Новая обработка", callback_data=MenuCb(action="home"))
    b.adjust(2)
    return b.as_markup()


def plate_review_kb(job_id: int) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(
        text="📷 Отправить другое фото", callback_data=JobCb(action="other_photo", job_id=job_id)
    )
    b.button(
        text="✋ Выделить номер вручную (скоро)",
        callback_data=JobCb(action="manual", job_id=job_id),
    )
    b.button(text="👤 Передать оператору", callback_data=JobCb(action="operator", job_id=job_id))
    b.button(text="🏠 Главное меню", callback_data=MenuCb(action="home"))
    b.adjust(1)
    return b.as_markup()


def my_jobs_kb(jobs: Sequence[Job]) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for job in jobs:
        if job.status is JobStatus.COMPLETED:
            b.button(
                text=f"📥 Результат {job.number}",
                callback_data=JobCb(action="result", job_id=job.id),
            )
    b.button(text="🏠 Главное меню", callback_data=MenuCb(action="home"))
    b.adjust(2)
    return b.as_markup()


def report_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="⏭ Без комментария", callback_data=ReportCb(action="skip"))
    b.button(text="✖️ Отмена", callback_data=ReportCb(action="cancel"))
    b.adjust(2)
    return b.as_markup()


def admin_jobs_kb(jobs: Sequence[Job]) -> InlineKeyboardMarkup | None:
    b = InlineKeyboardBuilder()
    count = 0
    for job in jobs:
        if job.status in (JobStatus.FAILED, JobStatus.NEEDS_REVIEW):
            b.button(
                text=f"🔁 Перезапустить {job.number}",
                callback_data=AdminCb(action="retry", job_id=job.id),
            )
            count += 1
    if not count:
        return None
    b.adjust(2)
    return b.as_markup()
