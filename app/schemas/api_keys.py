"""API Key schemas."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class ApiKeyCreate(BaseModel):
    name: str = Field(min_length=2, max_length=255)


class ApiKeyCreated(BaseModel):
    """Returned once on creation — the only time the full key is visible."""
    id: UUID
    name: str
    key_prefix: str
    full_key: str
    created_at: datetime


class ApiKeyOut(ORMModel):
    id: UUID
    name: str
    key_prefix: str
    is_active: bool
    last_used_at: datetime | None = None
    created_at: datetime


class ApiKeyList(BaseModel):
    items: list[ApiKeyOut]
    total: int
