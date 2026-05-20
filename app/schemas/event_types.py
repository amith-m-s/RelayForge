"""Event type schemas."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class EventTypeCreate(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    description: str | None = Field(default=None, max_length=1000)


class EventTypeUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=255)
    description: str | None = Field(default=None, max_length=1000)


class EventTypeOut(ORMModel):
    id: UUID
    organization_id: UUID
    name: str
    description: str | None = None
    created_at: datetime


class EventTypeList(BaseModel):
    items: list[EventTypeOut]
    total: int
