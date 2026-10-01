from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import AssetType
from app.database.base import Base, utcnow

if TYPE_CHECKING:
    from app.models.job import Job


class Asset(Base):
    __tablename__ = "assets"

    id: Mapped[int] = mapped_column(primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id", ondelete="CASCADE"), index=True)
    asset_type: Mapped[AssetType] = mapped_column(
        Enum(
            AssetType,
            native_enum=False,
            create_constraint=True,
            length=16,
            values_callable=lambda e: [m.value for m in e],
        )
    )
    storage_key: Mapped[str] = mapped_column(String(512))
    mime_type: Mapped[str] = mapped_column(String(64))
    width: Mapped[int | None] = mapped_column()
    height: Mapped[int | None] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(default=utcnow)

    job: Mapped[Job] = relationship(back_populates="assets")
