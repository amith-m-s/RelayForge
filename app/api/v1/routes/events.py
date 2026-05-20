from __future__ import annotations

import json

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import db_session, get_current_membership, require_role
from app.models.event import Event
from app.models.membership import Membership
from app.schemas.common import Paging
from app.schemas.events import EventCreate, EventList, EventOut
from app.services.webhook_service import WebhookService

router = APIRouter(prefix="/events", tags=["events"])


@router.post("", response_model=EventOut, status_code=status.HTTP_201_CREATED)
async def create_event(
    payload: EventCreate,
    session: AsyncSession = Depends(db_session),
    membership: Membership = Depends(require_role("owner", "admin", "developer")),
) -> EventOut:
    service = WebhookService(session)
    event, deliveries = await service.create_event(
        organization_id=membership.organization_id,
        source=payload.source,
        event_type=payload.event_type,
        payload_json=json.dumps(payload.payload),
        event_key=payload.event_key,
        idempotency_key=payload.idempotency_key,
    )
    await session.commit()
    for delivery in deliveries:
        from app.workers.tasks import dispatch_delivery

        dispatch_delivery.delay(str(delivery.id))
    return EventOut.model_validate(event)


@router.get("", response_model=EventList)
async def list_events(
    paging: Paging = Depends(),
    session: AsyncSession = Depends(db_session),
    membership: Membership = Depends(get_current_membership),
) -> EventList:
    stmt = (
        select(Event)
        .where(Event.organization_id == membership.organization_id, Event.deleted_at.is_(None))
        .order_by(Event.created_at.desc())
    )
    result = await session.execute(stmt)
    items = list(result.scalars().all())
    total = len(items)
    sliced = items[paging.offset : paging.offset + paging.limit]
    return EventList(
        items=[EventOut.model_validate(item) for item in sliced],
        limit=paging.limit,
        offset=paging.offset,
        total=total,
    )
