"""Audit log schemas."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.schemas.common import ORMModel


class AuditLogOut(ORMModel):
    id: UUID
    organization_id: UUID | None = None
    actor_user_id: UUID | None = None
    action: str
    resource_type: str
    resource_id: str | None = None
    metadata_json: str = "{}"
    request_id: str | None = None
    created_at: datetime


class AuditLogList(BaseModel):
    items: list[AuditLogOut]
    total: int
