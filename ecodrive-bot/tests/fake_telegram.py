"""Фейковая сессия Bot API: обработчики aiogram работают без сети.

Все запросы записываются в `session.requests`, ответы генерируются по типу
метода. Содержимое файлов для `bot.download` задаётся через `session.files`.
"""

from __future__ import annotations

import itertools
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from typing import Any

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.base import BaseSession
from aiogram.enums import ParseMode
from aiogram.methods import (
    EditMessageReplyMarkup,
    EditMessageText,
    GetFile,
    SendDocument,
    SendMessage,
    TelegramMethod,
)
from aiogram.types import (
    CallbackQuery,
    Chat,
    Document,
    File,
    Message,
    PhotoSize,
    Update,
    User,
)

BOT_TOKEN = "123456:" + "A" * 35  # фиктивный токен нужного формата


class FakeSession(BaseSession):
    def __init__(self) -> None:
        super().__init__()
        self.requests: list[TelegramMethod[Any]] = []
        self.files: dict[str, bytes] = {}
        self._ids = itertools.count(1000)

    async def close(self) -> None:
        return None

    async def make_request(
        self,
        bot: Bot,
        method: TelegramMethod[Any],
        timeout: int | None = None,  # noqa: ASYNC109 — сигнатура BaseSession
    ) -> Any:
        self.requests.append(method)
        chat = Chat(id=getattr(method, "chat_id", None) or 1, type="private")
        if isinstance(method, SendMessage | SendDocument):
            return Message(
                message_id=next(self._ids),
                date=datetime.now(UTC),
                chat=chat,
                text=getattr(method, "text", None),
                caption=getattr(method, "caption", None),
            )
        if isinstance(method, EditMessageText | EditMessageReplyMarkup):
            return Message(
                message_id=method.message_id or 1,
                date=datetime.now(UTC),
                chat=chat,
                text=getattr(method, "text", None),
            )
        if isinstance(method, GetFile):
            data = self.files.get(method.file_id, b"")
            return File(
                file_id=method.file_id,
                file_unique_id=method.file_id + "u",
                file_size=len(data),
                file_path=method.file_id,
            )
        return True

    async def stream_content(
        self,
        url: str,
        headers: dict[str, Any] | None = None,
        timeout: int = 30,  # noqa: ASYNC109 — сигнатура BaseSession
        chunk_size: int = 65536,
        raise_for_status: bool = True,
    ) -> AsyncGenerator[bytes, None]:
        file_id = url.rsplit("/", 1)[-1]
        yield self.files[file_id]

    # ── удобные выборки ──
    def sent(self, kind: type[TelegramMethod[Any]]) -> list[Any]:
        return [r for r in self.requests if isinstance(r, kind)]

    def texts(self) -> list[str]:
        out: list[str] = []
        for r in self.requests:
            if isinstance(r, SendMessage | EditMessageText):
                out.append(r.text)
        return out

    def last_text(self) -> str:
        return self.texts()[-1]


def make_bot() -> tuple[Bot, FakeSession]:
    session = FakeSession()
    bot = Bot(BOT_TOKEN, session=session, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    return bot, session


class UpdateFactory:
    def __init__(self, user_id: int, username: str = "employee") -> None:
        self.user = User(id=user_id, is_bot=False, first_name="Test", username=username)
        self.chat = Chat(id=user_id, type="private")
        self._ids = itertools.count(1)

    def _message(self, **kwargs: Any) -> Message:
        return Message(
            message_id=next(self._ids),
            date=datetime.now(UTC),
            chat=self.chat,
            from_user=self.user,
            **kwargs,
        )

    def text(self, text: str) -> Update:
        entities = None
        if text.startswith("/"):
            from aiogram.types import MessageEntity

            entities = [MessageEntity(type="bot_command", offset=0, length=len(text.split()[0]))]
        return Update(
            update_id=next(self._ids), message=self._message(text=text, entities=entities)
        )

    def document(self, file_id: str, size: int, mime: str = "image/jpeg") -> Update:
        doc = Document(
            file_id=file_id, file_unique_id=file_id + "u", file_size=size, mime_type=mime
        )
        return Update(update_id=next(self._ids), message=self._message(document=doc))

    def photo(self, file_id: str, size: int, w: int = 1280, h: int = 860) -> Update:
        photo = [
            PhotoSize(
                file_id=file_id, file_unique_id=file_id + "u", width=w, height=h, file_size=size
            )
        ]
        return Update(update_id=next(self._ids), message=self._message(photo=photo))

    def callback(self, data: str, message_id: int = 500) -> Update:
        message = Message(
            message_id=message_id, date=datetime.now(UTC), chat=self.chat, text="panel"
        )
        query = CallbackQuery(
            id=str(next(self._ids)),
            from_user=self.user,
            chat_instance="ci",
            message=message,
            data=data,
        )
        return Update(update_id=next(self._ids), callback_query=query)
