"""Тексты бота (HTML parse mode)."""

from __future__ import annotations

import html

from app.core.enums import OPERATION_TITLES, STATUS_TITLES, JobStatus
from app.models import Job

WELCOME = (
    "👋 <b>EcoDrive Auto — обработка фото автомобилей</b>\n\n"
    "Выберите, что нужно сделать. Бот подскажет, какие фотографии отправить, "
    "и пришлёт готовый файл в исходном качестве."
)

MAIN_MENU = "Главное меню. Выберите операцию:"

ACCESS_DENIED = (
    "⛔ Это корпоративный бот EcoDrive Auto. Доступ только для сотрудников.\n"
    "Ваш Telegram ID: <code>{telegram_id}</code> — передайте его администратору."
)

HELP = (
    "ℹ️ <b>Инструкция</b>\n\n"
    "1. Выберите операцию в главном меню.\n"
    "2. Отправьте фото <b>файлом</b> (📎 → Файл) — так сохраняется исходное качество. "
    "Сжатые фото тоже принимаются.\n"
    "3. На каждом шаге доступны кнопки: «Подтвердить» — перейти дальше, "
    "«Переделать» — повторить шаг, «Назад» и «Отмена».\n"
    "4. Проверьте сводку и подтвердите. Бот пришлёт номер задания и будет обновлять "
    "его статус в одном сообщении.\n"
    "5. Результат придёт документом JPEG (sRGB), готовым для объявления.\n\n"
    "<b>Советы по съёмке</b>\n"
    "• Номер: в кадре целиком, без сильных бликов, не меньше ~150 px в ширину.\n"
    "• Фон: автомобиль целиком, без обрезанных колёс и зеркал.\n"
    "• Диски: референс анфас, крупно, при ровном свете.\n"
    "• Салон: ровный свет, без пересветов на коже.\n\n"
    "<b>Важно.</b> Изменения цвета, дисков и фона — это визуализация. Используйте их "
    "только для реально предлагаемой конфигурации; такие фото получают отметку "
    "«Візуалізація», оригинал сохраняется. Форматы: JPEG, PNG, WEBP."
)

PHOTO_NOT_EXPECTED = "Сейчас фото не требуется — используйте кнопки под сообщением."
TEXT_NOT_EXPECTED = "Используйте кнопки под сообщением или отправьте фото, если бот его просит."
NO_ACTIVE_FLOW = "Нет активного диалога. Откройте главное меню: /start"
NEED_PHOTO_FIRST = "Сначала отправьте фото"
NEED_CHOICE_FIRST = "Сначала выберите вариант"
NEED_PARTS_FIRST = "Выберите хотя бы один элемент"
NEED_HEX_FIRST = "Сначала отправьте HEX-код"
INVALID_HEX = "Не похоже на HEX-код. Пример: <code>#8B4513</code> или <code>8B4513</code>."
CANCELLED = "Отменено."
MANUAL_SOON = "Ручное выделение номера появится в следующей версии."
COMPRESSED_PHOTO_NOTE = (
    "ℹ️ Фото пришло сжатым. Для лучшего качества отправьте его файлом и нажмите «Переделать»."
)


def job_status_text(job: Job, extra: str | None = None) -> str:
    lines = [
        f"Фотография принята в обработку. Номер задания: <b>{job.number}</b>",
        f"Операция: {OPERATION_TITLES[job.operation]}",
        f"Статус: {STATUS_TITLES[job.status]} <code>{job.status.value}</code>",
    ]
    if extra:
        lines += ["", extra]
    return "\n".join(lines)


def job_line(job: Job, with_user: bool = False) -> str:
    created = job.created_at.strftime("%d.%m %H:%M") if job.created_at else ""
    title, status = OPERATION_TITLES[job.operation], STATUS_TITLES[job.status]
    line = f"{job.number} · {title} · {status} · {created}"
    if with_user and job.user is not None:
        line += f" · {html.escape(job.user.display_name)}"
    if job.status is JobStatus.FAILED and job.error_message and with_user:
        line += f"\n   ↳ <i>{html.escape(job.error_message[:160])}</i>"
    return line
