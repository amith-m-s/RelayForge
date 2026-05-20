"""API Key service — create, verify, list, revoke."""

from __future__ import annotations

import secrets
from datetime import UTC, datetime
from hashlib import sha256
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.api_key import ApiKey


class ApiKeyService:
    PREFIX_LENGTH = 8
    KEY_LENGTH = 32

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, organization_id: UUID, name: str) -> tuple[ApiKey, str]:
        """Create a new API key. Returns (model, plaintext_key).

        The plaintext key is only available at creation time.
        """
        raw_key = secrets.token_urlsafe(self.KEY_LENGTH)
        prefix = raw_key[: self.PREFIX_LENGTH]
        key_hash = sha256(raw_key.encode("utf-8")).hexdigest()

        api_key = ApiKey(
            organization_id=organization_id,
            key_prefix=prefix,
            key_hash=key_hash,
            name=name.strip(),
        )
        self.session.add(api_key)
        await self.session.flush()
        return api_key, raw_key

    async def verify(self, raw_key: str) -> ApiKey | None:
        """Verify an API key and return the matching model, or None."""
        prefix = raw_key[: self.PREFIX_LENGTH]
        key_hash = sha256(raw_key.encode("utf-8")).hexdigest()

        stmt = select(ApiKey).where(
            ApiKey.key_prefix == prefix,
            ApiKey.key_hash == key_hash,
            ApiKey.is_active.is_(True),
            ApiKey.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        api_key = result.scalars().first()

        if api_key is not None:
            api_key.last_used_at = datetime.now(UTC)
            await self.session.flush()

        return api_key

    async def list_for_organization(
        self, organization_id: UUID, limit: int = 20, offset: int = 0
    ) -> tuple[list[ApiKey], int]:
        count_stmt = (
            select(func.count())
            .select_from(ApiKey)
            .where(
                ApiKey.organization_id == organization_id,
                ApiKey.deleted_at.is_(None),
            )
        )
        total = (await self.session.execute(count_stmt)).scalar_one()

        stmt = (
            select(ApiKey)
            .where(
                ApiKey.organization_id == organization_id,
                ApiKey.deleted_at.is_(None),
            )
            .order_by(ApiKey.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all()), int(total)

    async def revoke(self, organization_id: UUID, key_id: UUID) -> ApiKey | None:
        """Soft-delete an API key."""
        stmt = select(ApiKey).where(
            ApiKey.id == key_id,
            ApiKey.organization_id == organization_id,
            ApiKey.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        api_key = result.scalars().first()
        if api_key is None:
            return None
        api_key.is_active = False
        api_key.deleted_at = datetime.now(UTC)
        await self.session.flush()
        return api_key
