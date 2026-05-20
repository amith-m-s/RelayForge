"""API dependencies — JWT and API key dual auth, role-based access."""

from __future__ import annotations

from collections.abc import AsyncIterator, Callable
from typing import Any
from uuid import UUID

from fastapi import Depends, Header, HTTPException, Security, status
from fastapi.security import APIKeyHeader, OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import TokenError, decode_token
from app.db.session import get_db
from app.models.api_key import ApiKey
from app.models.membership import Membership
from app.models.organization import Organization
from app.models.user import User
from app.services.api_key_service import ApiKeyService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def db_session() -> AsyncIterator[AsyncSession]:
    async for session in get_db():
        yield session


async def get_token_payload(token: str = Depends(oauth2_scheme)) -> dict[str, Any]:
    if token is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    try:
        return decode_token(token, expected_type="access")
    except TokenError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc


async def get_current_user(
    session: AsyncSession = Depends(db_session),
    payload: dict[str, Any] = Depends(get_token_payload),
) -> User:
    subject = payload.get("sub")
    if not subject:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing subject")
    try:
        user_id = UUID(str(subject))
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid subject"
        ) from exc
    user = await session.get(User, user_id)
    if user is None or not user.is_active or user.deleted_at is not None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


async def get_current_user_or_api_key(
    session: AsyncSession = Depends(db_session),
    token: str | None = Depends(oauth2_scheme),
    api_key: str | None = Security(api_key_header),
) -> tuple[User | None, ApiKey | None, UUID | None]:
    """Authenticate via JWT or API key. Returns (user, api_key_model, organization_id).

    At least one of JWT token or API key must be present.
    """
    # Try JWT first
    if token:
        try:
            payload = decode_token(token, expected_type="access")
            subject = payload.get("sub")
            if subject:
                user = await session.get(User, UUID(str(subject)))
                if user and user.is_active and user.deleted_at is None:
                    org_id = payload.get("organization_id")
                    return user, None, UUID(str(org_id)) if org_id else None
        except (TokenError, ValueError):
            pass

    # Try API key
    if api_key:
        service = ApiKeyService(session)
        key_model = await service.verify(api_key)
        if key_model:
            return None, key_model, key_model.organization_id

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Valid Bearer token or API key required",
    )


async def get_current_membership(
    session: AsyncSession = Depends(db_session),
    user: User = Depends(get_current_user),
    payload: dict[str, Any] = Depends(get_token_payload),
    x_organization_id: UUID | None = Header(default=None, alias="X-Organization-ID"),
) -> Membership:
    candidate_org_id = x_organization_id or payload.get("organization_id") or payload.get("tenant_id")
    stmt = select(Membership).where(
        Membership.user_id == user.id,
        Membership.is_active.is_(True),
        Membership.deleted_at.is_(None),
    )
    if candidate_org_id is not None:
        try:
            candidate_uuid = UUID(str(candidate_org_id))
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Invalid organization"
            ) from exc
        stmt = stmt.where(Membership.organization_id == candidate_uuid)
    stmt = stmt.order_by(Membership.created_at.asc())
    result = await session.execute(stmt)
    membership = result.scalars().first()
    if membership is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No active membership")
    return membership


def require_role(*allowed_roles: str) -> Callable[..., Any]:
    async def _dependency(membership: Membership = Depends(get_current_membership)) -> Membership:
        if membership.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions"
            )
        return membership

    return _dependency


async def get_current_organization(
    membership: Membership = Depends(get_current_membership),
) -> Organization:
    organization = membership.organization
    if organization is None or not organization.is_active or organization.deleted_at is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Organization not available"
        )
    return organization
