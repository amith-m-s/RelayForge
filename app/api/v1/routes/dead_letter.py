"""Dead letter queue management routes."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import db_session, get_current_membership, require_role
from app.models.membership import Membership
from app.schemas.common import Paging
from app.schemas.dead_letter import DeadLetterList, DeadLetterOut
from app.services.audit_service import AuditService
from app.services.delivery_service import DeliveryService
from app.workers.tasks import dispatch_delivery

router = APIRouter(prefix="/dead-letter", tags=["dead-letter"])


@router.get("", response_model=DeadLetterList)
async def list_dead_letter_events(
    paging: Paging = Depends(),
    session: AsyncSession = Depends(db_session),
    membership: Membership = Depends(get_current_membership),
) -> DeadLetterList:
    service = DeliveryService(session)
    items, total = await service.list_dead_letter(
        membership.organization_id, paging.limit, paging.offset
    )
    return DeadLetterList(
        items=[DeadLetterOut.model_validate(item) for item in items],
        total=total,
    )


@router.post("/{dlq_id}/replay", status_code=status.HTTP_200_OK)
async def replay_dead_letter(
    dlq_id: UUID,
    session: AsyncSession = Depends(db_session),
    membership: Membership = Depends(require_role("owner", "admin", "developer")),
) -> dict[str, str]:
    service = DeliveryService(session)
    dlq_event = await service.get_dead_letter(membership.organization_id, dlq_id)
    if dlq_event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Dead letter event not found"
        )

    delivery = await service.replay_dead_letter(dlq_event)
    if delivery is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Associated delivery not found"
        )

    audit = AuditService(session)
    await audit.log(
        action="dead_letter.replayed",
        resource_type="dead_letter_event",
        resource_id=dlq_id,
        organization_id=membership.organization_id,
        actor_user_id=membership.user_id,
        metadata={"delivery_id": str(delivery.id)},
    )
    await session.commit()

    dispatch_delivery.delay(str(delivery.id))

    return {
        "message": "Dead letter event replayed",
        "delivery_id": str(delivery.id),
        "status": "queued",
    }


@router.delete("/{dlq_id}", status_code=status.HTTP_200_OK)
async def purge_dead_letter(
    dlq_id: UUID,
    session: AsyncSession = Depends(db_session),
    membership: Membership = Depends(require_role("owner", "admin")),
) -> dict[str, str]:
    service = DeliveryService(session)
    success = await service.purge_dead_letter(membership.organization_id, dlq_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Dead letter event not found"
        )

    audit = AuditService(session)
    await audit.log(
        action="dead_letter.purged",
        resource_type="dead_letter_event",
        resource_id=dlq_id,
        organization_id=membership.organization_id,
        actor_user_id=membership.user_id,
    )
    await session.commit()

    return {"message": "Dead letter event purged", "dlq_id": str(dlq_id)}


@router.post("/purge", status_code=status.HTTP_200_OK)
async def purge_all_dead_letter(
    session: AsyncSession = Depends(db_session),
    membership: Membership = Depends(require_role("owner", "admin")),
) -> dict[str, int | str]:
    service = DeliveryService(session)
    count = await service.purge_all_dead_letter(membership.organization_id)

    audit = AuditService(session)
    await audit.log(
        action="dead_letter.purge_all",
        resource_type="dead_letter_event",
        organization_id=membership.organization_id,
        actor_user_id=membership.user_id,
        metadata={"purged_count": count},
    )
    await session.commit()

    return {"message": "All dead letter events purged", "purged_count": count}
