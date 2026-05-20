from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    TokenError,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    hash_token,
    verify_password,
)
from app.models.membership import Membership
from app.models.organization import Organization
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.utils.text import slugify


class AuthService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.users = UserRepository(session)

    async def _unique_org_slug(self, name: str) -> str:
        base = slugify(name)
        slug = base
        suffix = 2
        while True:
            result = await self.session.execute(
                select(Organization).where(Organization.slug == slug)
            )
            if result.scalars().first() is None:
                return slug
            slug = f"{base}-{suffix}"
            suffix += 1

    async def register(
        self, email: str, full_name: str, password: str, organization_name: str
    ) -> User:
        existing = await self.users.get_by_email(email)
        if existing is not None:
            raise ValueError("Email already registered")

        user = User(
            email=email.lower(), full_name=full_name.strip(), password_hash=hash_password(password)
        )
        org = Organization(
            name=organization_name.strip(),
            slug=await self._unique_org_slug(organization_name),
            owner_user=user,
        )
        membership = Membership(user=user, organization=org, role="owner")
        self.session.add_all([user, org, membership])
        await self.session.flush()
        return user

    async def authenticate(self, email: str, password: str) -> User | None:
        user = await self.users.get_by_email(email.lower())
        if user is None or not user.is_active or user.deleted_at is not None:
            return None
        if not verify_password(password, user.password_hash):
            return None
        user.last_login_at = datetime.now(UTC)
        await self.session.flush()
        return user

    async def default_membership(self, user: User) -> Membership | None:
        stmt = (
            select(Membership)
            .where(
                Membership.user_id == user.id,
                Membership.is_active.is_(True),
                Membership.deleted_at.is_(None),
            )
            .order_by(Membership.created_at.asc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def issue_tokens(
        self, user: User, organization_id: UUID | None = None, role: str | None = None
    ) -> dict[str, str]:
        if organization_id is None:
            membership = await self.default_membership(user)
            organization_id = membership.organization_id if membership else None
            role = membership.role if membership else role
        refresh_row_id = uuid4()
        refresh_token = create_refresh_token(subject=str(user.id), token_id=str(refresh_row_id))
        token_row = RefreshToken(
            id=refresh_row_id,
            user_id=user.id,
            token_hash=hash_token(refresh_token),
            expires_at=datetime.now(UTC) + timedelta(days=30),
        )
        self.session.add(token_row)
        await self.session.flush()
        return {
            "access_token": create_access_token(
                subject=str(user.id),
                organization_id=str(organization_id) if organization_id else None,
                role=role,
            ),
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }

    async def rotate_refresh_token(self, refresh_token_value: str) -> dict[str, str]:
        payload = decode_token(refresh_token_value, expected_type="refresh")
        token_id = payload.get("token_id")
        if not token_id:
            raise TokenError("Missing refresh token id")

        token_hash = hash_token(refresh_token_value)
        stmt = select(RefreshToken).where(
            RefreshToken.id == UUID(str(token_id)), RefreshToken.token_hash == token_hash
        )
        result = await self.session.execute(stmt)
        token_row = result.scalars().first()
        if (
            token_row is None
            or token_row.revoked_at is not None
            or token_row.expires_at < datetime.now(UTC)
        ):
            raise TokenError("Refresh token revoked or expired")

        user = await self.session.get(User, UUID(str(payload["sub"])))
        if user is None:
            raise TokenError("User not found")

        membership = await self.default_membership(user)
        token_row.revoked_at = datetime.now(UTC)
        new_token_row_id = uuid4()
        new_refresh_token = create_refresh_token(
            subject=str(user.id), token_id=str(new_token_row_id)
        )
        new_token_row = RefreshToken(
            id=new_token_row_id,
            user_id=user.id,
            token_hash=hash_token(new_refresh_token),
            expires_at=datetime.now(UTC) + timedelta(days=30),
            replaced_by_token_id=token_row.id,
        )
        self.session.add(new_token_row)
        await self.session.flush()

        return {
            "access_token": create_access_token(
                subject=str(user.id),
                organization_id=str(membership.organization_id) if membership else None,
                role=membership.role if membership else None,
            ),
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
        }

    async def revoke_refresh_token(self, refresh_token_value: str) -> None:
        try:
            payload = decode_token(refresh_token_value, expected_type="refresh")
        except TokenError:
            return

        token_id = payload.get("token_id")
        if not token_id:
            return

        token_hash = hash_token(refresh_token_value)
        stmt = select(RefreshToken).where(
            RefreshToken.id == UUID(str(token_id)), RefreshToken.token_hash == token_hash
        )
        result = await self.session.execute(stmt)
        token_row = result.scalars().first()
        if token_row is None:
            return
        token_row.revoked_at = datetime.now(UTC)
        await self.session.flush()
