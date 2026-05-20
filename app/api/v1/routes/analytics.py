"""Analytics routes — using proper service layer."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.analytics.service import AnalyticsService
from app.api.deps import db_session, get_current_membership
from app.models.membership import Membership

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/overview")
async def overview(
    session: AsyncSession = Depends(db_session),
    membership: Membership = Depends(get_current_membership),
) -> dict:
    service = AnalyticsService(session)
    return await service.get_overview(membership.organization_id)


@router.get("/delivery-metrics")
async def delivery_metrics(
    window: int = Query(default=24, ge=1, le=720, description="Window in hours"),
    session: AsyncSession = Depends(db_session),
    membership: Membership = Depends(get_current_membership),
) -> list[dict]:
    service = AnalyticsService(session)
    return await service.get_delivery_metrics(membership.organization_id, window)


@router.get("/endpoint-health")
async def endpoint_health(
    session: AsyncSession = Depends(db_session),
    membership: Membership = Depends(get_current_membership),
) -> list[dict]:
    service = AnalyticsService(session)
    return await service.get_endpoint_health(membership.organization_id)


@router.get("/event-volume")
async def event_volume(
    window: int = Query(default=24, ge=1, le=720, description="Window in hours"),
    session: AsyncSession = Depends(db_session),
    membership: Membership = Depends(get_current_membership),
) -> list[dict]:
    service = AnalyticsService(session)
    return await service.get_event_volume(membership.organization_id, window)
