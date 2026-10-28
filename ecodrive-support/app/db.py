"""Хранилище диалогов: SQLAlchemy 2 (async). По умолчанию SQLite, в проде можно PostgreSQL."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, Text, select
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

Role = Literal["user", "assistant", "manager", "system"]


def utcnow() -> datetime:
    return datetime.now(UTC)


class Base(DeclarativeBase):
    pass


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: uuid.uuid4().hex)
    channel: Mapped[str] = mapped_column(String(16), default="web")
    lang: Mapped[str] = mapped_column(String(8), default="uk")
    page_url: Mapped[str | None] = mapped_column(Text)
    client_phone: Mapped[str | None] = mapped_column(String(32))
    client_name: Mapped[str | None] = mapped_column(String(128))
    # Диалог передан менеджеру: ИИ молчит, сообщения клиента уходят в Telegram
    handed_off: Mapped[bool] = mapped_column(Boolean, default=False)
    # id уведомления в чате менеджеров — по нему находим диалог при ответе менеджера
    manager_message_id: Mapped[int | None] = mapped_column(Integer, index=True)
    # Последний ответ OpenAI — чтобы продолжать диалог через previous_response_id
    openai_response_id: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    conversation_id: Mapped[str] = mapped_column(ForeignKey("conversations.id"), index=True)
    role: Mapped[str] = mapped_column(String(16))
    content: Mapped[str] = mapped_column(Text)
    meta: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Store:
    """Все обращения к базе — через этот класс, чтобы API и Telegram не знали о сессиях."""

    def __init__(self, database_url: str) -> None:
        self._url = database_url
        self._engine = create_async_engine(database_url, pool_pre_ping=True)
        self._sessions = async_sessionmaker(self._engine, expire_on_commit=False)

    async def init(self) -> None:
        url = make_url(self._url)
        if url.get_backend_name() == "sqlite" and url.database and url.database != ":memory:":
            Path(url.database).parent.mkdir(parents=True, exist_ok=True)
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def close(self) -> None:
        await self._engine.dispose()

    def session(self) -> AsyncSession:
        return self._sessions()

    async def get_conversation(self, conversation_id: str) -> Conversation | None:
        async with self.session() as s:
            return await s.get(Conversation, conversation_id)

    async def get_or_create_conversation(
        self,
        conversation_id: str | None,
        *,
        channel: str = "web",
        lang: str = "uk",
        page_url: str | None = None,
    ) -> Conversation:
        async with self.session() as s:
            if conversation_id:
                existing = await s.get(Conversation, conversation_id)
                if existing is not None:
                    return existing
            conv = Conversation(channel=channel, lang=lang, page_url=page_url)
            s.add(conv)
            await s.commit()
            return conv

    async def update_conversation(self, conversation_id: str, **fields: Any) -> None:
        async with self.session() as s:
            conv = await s.get(Conversation, conversation_id)
            if conv is None:
                return
            for key, value in fields.items():
                setattr(conv, key, value)
            await s.commit()

    async def add_message(
        self, conversation_id: str, role: Role, content: str, meta: dict[str, Any] | None = None
    ) -> Message:
        async with self.session() as s:
            msg = Message(conversation_id=conversation_id, role=role, content=content, meta=meta)
            s.add(msg)
            await s.commit()
            return msg

    async def history(self, conversation_id: str, limit: int) -> list[Message]:
        """Последние `limit` сообщений диалога в хронологическом порядке."""
        async with self.session() as s:
            stmt = (
                select(Message)
                .where(Message.conversation_id == conversation_id)
                .order_by(Message.id.desc())
                .limit(limit)
            )
            rows = list((await s.scalars(stmt)).all())
            rows.reverse()
            return rows

    async def messages_after(
        self, conversation_id: str, after_id: int, roles: tuple[str, ...]
    ) -> list[Message]:
        async with self.session() as s:
            stmt = (
                select(Message)
                .where(
                    Message.conversation_id == conversation_id,
                    Message.id > after_id,
                    Message.role.in_(roles),
                )
                .order_by(Message.id)
            )
            return list((await s.scalars(stmt)).all())

    async def find_by_manager_message(self, manager_message_id: int) -> Conversation | None:
        async with self.session() as s:
            stmt = select(Conversation).where(Conversation.manager_message_id == manager_message_id)
            return (await s.scalars(stmt)).first()
