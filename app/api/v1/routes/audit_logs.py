"""Audit log routes — using proper schemas."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import db_session, get_current_membership
from app.models.membership import Membership
from app.schemas.audit_logs import AuditLogList, AuditLogOut
from app.schemas.common import Paging
from app.services.audit_service import AuditService

router = APIRouter(prefix="/audit-logs", tags=["audit-logs"])


@router.get("", response_model=AuditLogList)
async def list_audit_logs(
    paging: Paging = Depends(),
    action: str | None = Query(default=None),
    resource_type: str | None = Query(default=None),
    session: AsyncSession = Depends(db_session),
    membership: Membership = Depends(get_current_membership),
) -> AuditLogList:
    service = AuditService(session)
    items, total = await service.list_for_organization(
        organization_id=membership.organization_id,
        limit=paging.limit,
        offset=paging.offset,
        action=action,
        resource_type=resource_type,
    )
    return AuditLogList(
        items=[AuditLogOut.model_validate(entry) for entry in items],
        total=total,
    )
