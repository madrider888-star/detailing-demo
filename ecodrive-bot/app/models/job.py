from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import BigInteger, Enum, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import JobStatus, Operation
from app.database.base import Base, utcnow

if TYPE_CHECKING:
    from app.models.asset import Asset
    from app.models.user import User


def _values(enum: type[Operation] | type[JobStatus]) -> list[str]:
    return [m.value for m in enum]


class Job(Base):
    __tablename__ = "jobs"
    __table_args__ = (Index("ix_jobs_user_status", "user_id", "status"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    operation: Mapped[Operation] = mapped_column(
        Enum(
            Operation, native_enum=False, create_constraint=True, length=32, values_callable=_values
        )
    )
    status: Mapped[JobStatus] = mapped_column(
        Enum(
            JobStatus, native_enum=False, create_constraint=True, length=16, values_callable=_values
        ),
        default=JobStatus.QUEUED,
        index=True,
    )
    parameters: Mapped[dict[str, Any]] = mapped_column(default=dict)
    error_message: Mapped[str | None] = mapped_column(Text)
    provider: Mapped[str | None] = mapped_column(String(64))
    # Служебные поля: защита от двойного создания и обновление одного статус-сообщения.
    idempotency_key: Mapped[str | None] = mapped_column(String(64), unique=True)
    attempts: Mapped[int] = mapped_column(default=0)
    telegram_chat_id: Mapped[int | None] = mapped_column(BigInteger)
    status_message_id: Mapped[int | None] = mapped_column(BigInteger)

    created_at: Mapped[datetime] = mapped_column(default=utcnow)
    started_at: Mapped[datetime | None] = mapped_column()
    completed_at: Mapped[datetime | None] = mapped_column()

    user: Mapped[User] = relationship(back_populates="jobs")
    assets: Mapped[list[Asset]] = relationship(
        back_populates="job", cascade="all, delete-orphan", order_by="Asset.id"
    )

    @property
    def number(self) -> str:
        return f"#{self.id:04d}"
