from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import Select
from sqlalchemy.ext.asyncio import AsyncSession


class BaseRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_all(self, stmt: Select) -> Sequence[object]:
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_one(self, stmt: Select) -> object | None:
        result = await self.session.execute(stmt)
        return result.scalars().first()
