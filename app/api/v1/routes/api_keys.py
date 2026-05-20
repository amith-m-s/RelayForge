"""API Key management routes."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import db_session, get_current_membership, require_role
from app.models.membership import Membership
from app.schemas.api_keys import ApiKeyCreate, ApiKeyCreated, ApiKeyList, ApiKeyOut
from app.schemas.common import Paging
from app.services.api_key_service import ApiKeyService
from app.services.audit_service import AuditService

router = APIRouter(prefix="/api-keys", tags=["api-keys"])


@router.post("", response_model=ApiKeyCreated, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    payload: ApiKeyCreate,
    session: AsyncSession = Depends(db_session),
    membership: Membership = Depends(require_role("owner", "admin")),
) -> ApiKeyCreated:
    service = ApiKeyService(session)
    api_key, full_key = await service.create(membership.organization_id, payload.name)

    # Audit log
    audit = AuditService(session)
    await audit.log(
        action="api_key.created",
        resource_type="api_key",
        resource_id=api_key.id,
        organization_id=membership.organization_id,
        actor_user_id=membership.user_id,
    )
    await session.commit()

    return ApiKeyCreated(
        id=api_key.id,
        name=api_key.name,
        key_prefix=api_key.key_prefix,
        full_key=full_key,
        created_at=api_key.created_at,
    )


@router.get("", response_model=ApiKeyList)
async def list_api_keys(
    paging: Paging = Depends(),
    session: AsyncSession = Depends(db_session),
    membership: Membership = Depends(get_current_membership),
) -> ApiKeyList:
    service = ApiKeyService(session)
    items, total = await service.list_for_organization(
        membership.organization_id, paging.limit, paging.offset
    )
    return ApiKeyList(
        items=[ApiKeyOut.model_validate(k) for k in items],
        total=total,
    )


@router.delete("/{key_id}", status_code=status.HTTP_200_OK)
async def revoke_api_key(
    key_id: UUID,
    session: AsyncSession = Depends(db_session),
    membership: Membership = Depends(require_role("owner", "admin")),
) -> dict[str, str]:
    service = ApiKeyService(session)
    api_key = await service.revoke(membership.organization_id, key_id)
    if api_key is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")

    audit = AuditService(session)
    await audit.log(
        action="api_key.revoked",
        resource_type="api_key",
        resource_id=key_id,
        organization_id=membership.organization_id,
        actor_user_id=membership.user_id,
    )
    await session.commit()

    return {"message": "API key revoked", "key_id": str(key_id)}
