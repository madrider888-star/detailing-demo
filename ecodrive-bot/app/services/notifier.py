"""Интерфейс уведомлений о ходе задания (реализация для Telegram — в app.bot.notifier)."""

from __future__ import annotations

from typing import Protocol

from app.models import Job
from app.services.export.normalizer import ExportResult


class JobNotifier(Protocol):
    async def job_status(self, job: Job) -> None:
        """Обновить единственное статус-сообщение задания."""

    async def job_completed(self, job: Job, result: ExportResult, filename: str) -> None:
        """Отправить результат документом и кнопки после обработки."""

    async def job_needs_review(self, job: Job, reason: str) -> None:
        """Задание требует участия человека (например, номер не найден уверенно)."""

    async def job_failed(self, job: Job, user_message: str) -> None:
        """Понятное сообщение об ошибке."""
