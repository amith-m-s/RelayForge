"""Dead letter event schemas."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.schemas.common import ORMModel


class DeadLetterOut(ORMModel):
    id: UUID
    organization_id: UUID
    delivery_id: UUID
    reason: str
    payload_snapshot: str
    created_at: datetime


class DeadLetterList(BaseModel):
    items: list[DeadLetterOut]
    total: int


class DeadLetterReplay(BaseModel):
    reason: str | None = None
