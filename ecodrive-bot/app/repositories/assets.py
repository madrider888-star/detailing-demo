from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import AssetType
from app.models import Asset


class AssetRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(
        self,
        *,
        job_id: int,
        asset_type: AssetType,
        storage_key: str,
        mime_type: str,
        width: int | None,
        height: int | None,
    ) -> Asset:
        asset = Asset(
            job_id=job_id,
            asset_type=asset_type,
            storage_key=storage_key,
            mime_type=mime_type,
            width=width,
            height=height,
        )
        self.session.add(asset)
        await self.session.flush()
        return asset

    async def list_for_job(
        self, job_id: int, asset_type: AssetType | None = None
    ) -> Sequence[Asset]:
        stmt = select(Asset).where(Asset.job_id == job_id).order_by(Asset.id)
        if asset_type is not None:
            stmt = stmt.where(Asset.asset_type == asset_type)
        return (await self.session.execute(stmt)).scalars().all()

    async def latest(self, job_id: int, asset_type: AssetType) -> Asset | None:
        stmt = (
            select(Asset)
            .where(Asset.job_id == job_id, Asset.asset_type == asset_type)
            .order_by(Asset.id.desc())
            .limit(1)
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()
