from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.membership import Membership
from app.models.organization import Organization
from app.utils.text import slugify


class OrganizationService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, owner_user_id: UUID, name: str) -> Organization:
        slug = slugify(name)
        suffix = 2
        while True:
            result = await self.session.execute(
                select(Organization).where(Organization.slug == slug)
            )
            if result.scalars().first() is None:
                break
            slug = f"{slugify(name)}-{suffix}"
            suffix += 1

        organization = Organization(name=name.strip(), slug=slug, owner_user_id=owner_user_id)
        membership = Membership(user_id=owner_user_id, organization=organization, role="owner")
        self.session.add_all([organization, membership])
        await self.session.flush()
        return organization

    async def list_for_user(self, user_id: UUID) -> list[Organization]:
        stmt = (
            select(Organization)
            .join(Membership, Membership.organization_id == Organization.id)
            .where(
                Membership.user_id == user_id,
                Membership.is_active.is_(True),
                Organization.deleted_at.is_(None),
            )
            .order_by(Organization.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_for_user(self, user_id: UUID, organization_id: UUID) -> Organization | None:
        stmt = (
            select(Organization)
            .join(Membership, Membership.organization_id == Organization.id)
            .where(
                Membership.user_id == user_id,
                Membership.organization_id == organization_id,
                Membership.is_active.is_(True),
                Organization.deleted_at.is_(None),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()
