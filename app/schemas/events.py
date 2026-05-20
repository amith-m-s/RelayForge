from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class EventCreate(BaseModel):
    source: str = Field(min_length=2, max_length=255)
    event_type: str = Field(min_length=2, max_length=255)
    payload: dict
    event_key: str | None = None
    idempotency_key: str | None = None


class EventOut(ORMModel):
    id: UUID
    organization_id: UUID
    event_type_id: UUID | None
    source: str
    event_key: str | None
    idempotency_key: str | None
    created_at: datetime


class EventList(BaseModel):
    items: list[EventOut]
    limit: int
    offset: int
    total: int
