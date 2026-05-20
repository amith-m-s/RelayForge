from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl

from app.schemas.common import ORMModel


class WebhookEndpointCreate(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    url: HttpUrl
    secret: str = Field(min_length=12, max_length=255)
    event_filter: str = "*"
    retry_policy_id: UUID | None = None


class WebhookEndpointUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=255)
    url: HttpUrl | None = None
    secret: str | None = Field(default=None, min_length=12, max_length=255)
    event_filter: str | None = None
    status: str | None = Field(default=None, min_length=2, max_length=50)
    retry_policy_id: UUID | None = None


class WebhookEndpointOut(ORMModel):
    id: UUID
    organization_id: UUID
    name: str
    url: str
    status: str
    event_filter: str
    created_at: datetime


class WebhookEndpointList(BaseModel):
    items: list[WebhookEndpointOut]
    limit: int
    offset: int
    total: int
