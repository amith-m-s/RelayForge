"""Audit logging service — writes structured audit trail entries."""

from __future__ import annotations

import json
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog


class AuditService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def log(
        self,
        action: str,
        resource_type: str,
        resource_id: str | UUID | None = None,
        organization_id: UUID | None = None,
        actor_user_id: UUID | None = None,
        metadata: dict[str, Any] | None = None,
        request_id: str | None = None,
    ) -> AuditLog:
        """Write an audit log entry."""
        entry = AuditLog(
            organization_id=organization_id,
            actor_user_id=actor_user_id,
            action=action,
            resource_type=resource_type,
            resource_id=str(resource_id) if resource_id else None,
            metadata_json=json.dumps(metadata) if metadata else "{}",
            request_id=request_id,
        )
        self.session.add(entry)
        await self.session.flush()
        return entry

    async def list_for_organization(
        self,
        organization_id: UUID,
        limit: int = 50,
        offset: int = 0,
        action: str | None = None,
        resource_type: str | None = None,
    ) -> tuple[list[AuditLog], int]:
        base = select(AuditLog).where(
            AuditLog.organization_id == organization_id,
            AuditLog.deleted_at.is_(None),
        )
        if action:
            base = base.where(AuditLog.action == action)
        if resource_type:
            base = base.where(AuditLog.resource_type == resource_type)

        count_stmt = select(func.count()).select_from(base.subquery())
        total = (await self.session.execute(count_stmt)).scalar_one()

        stmt = base.order_by(AuditLog.created_at.desc()).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return list(result.scalars().all()), int(total)
