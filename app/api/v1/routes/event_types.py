"""Event type CRUD routes."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import db_session, get_current_membership, require_role
from app.models.event_type import EventType
from app.models.membership import Membership
from app.schemas.common import Paging
from app.schemas.event_types import (
    EventTypeCreate,
    EventTypeList,
    EventTypeOut,
    EventTypeUpdate,
)
from app.services.audit_service import AuditService

router = APIRouter(prefix="/event-types", tags=["event-types"])


@router.post("", response_model=EventTypeOut, status_code=status.HTTP_201_CREATED)
async def create_event_type(
    payload: EventTypeCreate,
    session: AsyncSession = Depends(db_session),
    membership: Membership = Depends(require_role("owner", "admin", "developer")),
) -> EventTypeOut:
    # Check uniqueness
    existing = await session.execute(
        select(EventType).where(
            EventType.organization_id == membership.organization_id,
            EventType.name == payload.name.strip(),
            EventType.deleted_at.is_(None),
        )
    )
    if existing.scalars().first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Event type already exists")

    event_type = EventType(
        organization_id=membership.organization_id,
        name=payload.name.strip(),
        description=payload.description,
    )
    session.add(event_type)

    audit = AuditService(session)
    await audit.log(
        action="event_type.created",
        resource_type="event_type",
        resource_id=event_type.id,
        organization_id=membership.organization_id,
        actor_user_id=membership.user_id,
    )
    await session.commit()
    await session.refresh(event_type)
    return EventTypeOut.model_validate(event_type)


@router.get("", response_model=EventTypeList)
async def list_event_types(
    paging: Paging = Depends(),
    session: AsyncSession = Depends(db_session),
    membership: Membership = Depends(get_current_membership),
) -> EventTypeList:
    base = select(EventType).where(
        EventType.organization_id == membership.organization_id,
        EventType.deleted_at.is_(None),
    )
    count_stmt = select(func.count()).select_from(base.subquery())
    total = (await session.execute(count_stmt)).scalar_one()

    stmt = base.order_by(EventType.name).limit(paging.limit).offset(paging.offset)
    result = await session.execute(stmt)
    items = result.scalars().all()

    return EventTypeList(
        items=[EventTypeOut.model_validate(et) for et in items],
        total=int(total),
    )


@router.get("/{event_type_id}", response_model=EventTypeOut)
async def get_event_type(
    event_type_id: UUID,
    session: AsyncSession = Depends(db_session),
    membership: Membership = Depends(get_current_membership),
) -> EventTypeOut:
    stmt = select(EventType).where(
        EventType.id == event_type_id,
        EventType.organization_id == membership.organization_id,
        EventType.deleted_at.is_(None),
    )
    result = await session.execute(stmt)
    event_type = result.scalars().first()
    if event_type is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event type not found")
    return EventTypeOut.model_validate(event_type)


@router.patch("/{event_type_id}", response_model=EventTypeOut)
async def update_event_type(
    event_type_id: UUID,
    payload: EventTypeUpdate,
    session: AsyncSession = Depends(db_session),
    membership: Membership = Depends(require_role("owner", "admin", "developer")),
) -> EventTypeOut:
    stmt = select(EventType).where(
        EventType.id == event_type_id,
        EventType.organization_id == membership.organization_id,
        EventType.deleted_at.is_(None),
    )
    result = await session.execute(stmt)
    event_type = result.scalars().first()
    if event_type is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event type not found")

    if payload.name is not None:
        event_type.name = payload.name.strip()
    if payload.description is not None:
        event_type.description = payload.description

    audit = AuditService(session)
    await audit.log(
        action="event_type.updated",
        resource_type="event_type",
        resource_id=event_type_id,
        organization_id=membership.organization_id,
        actor_user_id=membership.user_id,
    )
    await session.commit()
    await session.refresh(event_type)
    return EventTypeOut.model_validate(event_type)


@router.delete("/{event_type_id}", status_code=status.HTTP_200_OK)
async def delete_event_type(
    event_type_id: UUID,
    session: AsyncSession = Depends(db_session),
    membership: Membership = Depends(require_role("owner", "admin")),
) -> dict[str, str]:
    stmt = select(EventType).where(
        EventType.id == event_type_id,
        EventType.organization_id == membership.organization_id,
        EventType.deleted_at.is_(None),
    )
    result = await session.execute(stmt)
    event_type = result.scalars().first()
    if event_type is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event type not found")

    event_type.deleted_at = datetime.now(UTC)

    audit = AuditService(session)
    await audit.log(
        action="event_type.deleted",
        resource_type="event_type",
        resource_id=event_type_id,
        organization_id=membership.organization_id,
        actor_user_id=membership.user_id,
    )
    await session.commit()

    return {"message": "Event type deleted", "event_type_id": str(event_type_id)}
