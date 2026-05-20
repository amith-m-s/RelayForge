from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.schemas.common import ORMModel


class DeliveryOut(ORMModel):
    id: UUID
    organization_id: UUID
    webhook_endpoint_id: UUID
    event_id: UUID
    status: str
    attempt_count: int
    next_attempt_at: datetime | None
    last_attempt_at: datetime | None
    last_status_code: int | None
    last_error: str | None
    created_at: datetime


class DeliveryList(BaseModel):
    items: list[DeliveryOut]
    limit: int
    offset: int
    total: int


class RetryRequest(BaseModel):
    reason: str | None = None
