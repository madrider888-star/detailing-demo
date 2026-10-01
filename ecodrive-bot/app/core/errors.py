"""Исключения предметной области. `user_message` — то, что можно показать сотруднику."""

from __future__ import annotations


class AppError(Exception):
    user_message = "Произошла ошибка. Попробуйте ещё раз или обратитесь к администратору."

    def __init__(self, message: str = "", *, user_message: str | None = None) -> None:
        super().__init__(message or self.user_message)
        if user_message is not None:
            self.user_message = user_message


class ImageValidationError(AppError):
    user_message = "Файл не подходит."


class TooManyActiveJobsError(AppError):
    user_message = "У вас уже есть задания в обработке. Дождитесь их завершения и попробуйте снова."


class DuplicateJobError(AppError):
    user_message = "Это задание уже создано — повторная отправка не нужна."


class InvalidStatusTransitionError(AppError):
    user_message = "Задание уже обрабатывается или завершено."


class StorageError(AppError):
    user_message = "Не удалось сохранить файл. Попробуйте ещё раз чуть позже."
