"""Webhook endpoint routes — cleaned up, duplicate event endpoint removed, DELETE added."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import db_session, get_current_membership, require_role
from app.core.security import hash_token
from app.models.membership import Membership
from app.models.webhook_endpoint import WebhookEndpoint
from app.schemas.common import Paging
from app.schemas.webhooks import (
    WebhookEndpointCreate,
    WebhookEndpointList,
    WebhookEndpointOut,
    WebhookEndpointUpdate,
)
from app.services.audit_service import AuditService
from app.services.webhook_service import WebhookService

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/endpoints", response_model=WebhookEndpointOut, status_code=status.HTTP_201_CREATED)
async def create_endpoint(
    payload: WebhookEndpointCreate,
    session: AsyncSession = Depends(db_session),
    membership: Membership = Depends(require_role("owner", "admin", "developer")),
) -> WebhookEndpointOut:
    service = WebhookService(session)
    endpoint = await service.create_endpoint(
        organization_id=membership.organization_id,
        name=payload.name,
        url=str(payload.url),
        secret=payload.secret,
        event_filter=payload.event_filter,
        retry_policy_id=payload.retry_policy_id,
    )

    audit = AuditService(session)
    await audit.log(
        action="webhook_endpoint.created",
        resource_type="webhook_endpoint",
        resource_id=endpoint.id,
        organization_id=membership.organization_id,
        actor_user_id=membership.user_id,
    )
    await session.commit()
    return WebhookEndpointOut.model_validate(endpoint)


@router.get("/endpoints", response_model=WebhookEndpointList)
async def list_endpoints(
    paging: Paging = Depends(),
    session: AsyncSession = Depends(db_session),
    membership: Membership = Depends(get_current_membership),
) -> WebhookEndpointList:
    service = WebhookService(session)
    items, total = await service.list_endpoints(
        membership.organization_id, paging.limit, paging.offset
    )
    return WebhookEndpointList(
        items=[WebhookEndpointOut.model_validate(item) for item in items],
        limit=paging.limit,
        offset=paging.offset,
        total=total,
    )


@router.patch("/endpoints/{endpoint_id}", response_model=WebhookEndpointOut)
async def update_endpoint(
    endpoint_id: UUID,
    payload: WebhookEndpointUpdate,
    session: AsyncSession = Depends(db_session),
    membership: Membership = Depends(require_role("owner", "admin", "developer")),
) -> WebhookEndpointOut:
    stmt = select(WebhookEndpoint).where(
        WebhookEndpoint.id == endpoint_id,
        WebhookEndpoint.organization_id == membership.organization_id,
        WebhookEndpoint.deleted_at.is_(None),
    )
    result = await session.execute(stmt)
    endpoint = result.scalars().first()
    if endpoint is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Webhook endpoint not found"
        )

    service = WebhookService(session)
    endpoint = await service.update_endpoint(
        endpoint,
        name=payload.name,
        url=str(payload.url) if payload.url else None,
        secret_hash=hash_token(payload.secret) if payload.secret else None,
        event_filter=payload.event_filter,
        status=payload.status,
        retry_policy_id=payload.retry_policy_id,
    )

    audit = AuditService(session)
    await audit.log(
        action="webhook_endpoint.updated",
        resource_type="webhook_endpoint",
        resource_id=endpoint_id,
        organization_id=membership.organization_id,
        actor_user_id=membership.user_id,
    )
    await session.commit()
    return WebhookEndpointOut.model_validate(endpoint)


@router.delete("/endpoints/{endpoint_id}", status_code=status.HTTP_200_OK)
async def delete_endpoint(
    endpoint_id: UUID,
    session: AsyncSession = Depends(db_session),
    membership: Membership = Depends(require_role("owner", "admin")),
) -> dict[str, str]:
    stmt = select(WebhookEndpoint).where(
        WebhookEndpoint.id == endpoint_id,
        WebhookEndpoint.organization_id == membership.organization_id,
        WebhookEndpoint.deleted_at.is_(None),
    )
    result = await session.execute(stmt)
    endpoint = result.scalars().first()
    if endpoint is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Webhook endpoint not found"
        )

    endpoint.deleted_at = datetime.now(UTC)
    endpoint.status = "disabled"

    audit = AuditService(session)
    await audit.log(
        action="webhook_endpoint.deleted",
        resource_type="webhook_endpoint",
        resource_id=endpoint_id,
        organization_id=membership.organization_id,
        actor_user_id=membership.user_id,
    )
    await session.commit()

    return {"message": "Webhook endpoint deleted", "endpoint_id": str(endpoint_id)}
