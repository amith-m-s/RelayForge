"""Delivery routes — fixed to use proper auth, service layer, and Pydantic schemas."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import db_session, get_current_membership, require_role
from app.models.membership import Membership
from app.schemas.common import Paging
from app.schemas.deliveries import DeliveryList, DeliveryOut
from app.services.audit_service import AuditService
from app.services.delivery_service import DeliveryService
from app.workers.tasks import dispatch_delivery

router = APIRouter(prefix="/deliveries", tags=["deliveries"])


@router.get("", response_model=DeliveryList)
async def list_deliveries(
    paging: Paging = Depends(),
    status_filter: str | None = Query(default=None, alias="status"),
    endpoint_id: UUID | None = Query(default=None),
    session: AsyncSession = Depends(db_session),
    membership: Membership = Depends(get_current_membership),
) -> DeliveryList:
    service = DeliveryService(session)
    items, total = await service.list_for_organization(
        organization_id=membership.organization_id,
        limit=paging.limit,
        offset=paging.offset,
        status_filter=status_filter,
        endpoint_id=endpoint_id,
    )
    return DeliveryList(
        items=[DeliveryOut.model_validate(d) for d in items],
        limit=paging.limit,
        offset=paging.offset,
        total=total,
    )


@router.get("/{delivery_id}", response_model=DeliveryOut)
async def get_delivery(
    delivery_id: UUID,
    session: AsyncSession = Depends(db_session),
    membership: Membership = Depends(get_current_membership),
) -> DeliveryOut:
    service = DeliveryService(session)
    delivery = await service.get_for_organization(membership.organization_id, delivery_id)
    if delivery is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Delivery not found")
    return DeliveryOut.model_validate(delivery)


@router.get("/{delivery_id}/attempts")
async def get_delivery_attempts(
    delivery_id: UUID,
    session: AsyncSession = Depends(db_session),
    membership: Membership = Depends(get_current_membership),
) -> dict:
    service = DeliveryService(session)
    delivery = await service.get_for_organization(membership.organization_id, delivery_id)
    if delivery is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Delivery not found")

    attempts = await service.get_attempts(delivery_id)
    return {
        "delivery_id": str(delivery_id),
        "count": len(attempts),
        "items": [
            {
                "id": str(a.id),
                "attempt_number": a.attempt_number,
                "http_status": a.http_status,
                "duration_ms": a.duration_ms,
                "error_message": a.error_message,
                "created_at": a.created_at.isoformat() if a.created_at else None,
            }
            for a in attempts
        ],
    }


@router.post("/{delivery_id}/replay")
async def replay_delivery(
    delivery_id: UUID,
    session: AsyncSession = Depends(db_session),
    membership: Membership = Depends(require_role("owner", "admin", "developer")),
) -> dict[str, str]:
    service = DeliveryService(session)
    delivery = await service.get_for_organization(membership.organization_id, delivery_id)
    if delivery is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Delivery not found")

    await service.replay(delivery)

    audit = AuditService(session)
    await audit.log(
        action="delivery.replayed",
        resource_type="delivery",
        resource_id=delivery_id,
        organization_id=membership.organization_id,
        actor_user_id=membership.user_id,
    )
    await session.commit()

    dispatch_delivery.delay(str(delivery.id))

    return {
        "message": "Replay scheduled",
        "delivery_id": str(delivery.id),
        "status": "queued",
    }