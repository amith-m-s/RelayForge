"""Retry policy schemas."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class RetryPolicyCreate(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    max_attempts: int = Field(default=8, ge=1, le=50)
    base_delay_seconds: int = Field(default=30, ge=1, le=3600)
    max_delay_seconds: int = Field(default=3600, ge=1, le=86400)


class RetryPolicyUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=255)
    max_attempts: int | None = Field(default=None, ge=1, le=50)
    base_delay_seconds: int | None = Field(default=None, ge=1, le=3600)
    max_delay_seconds: int | None = Field(default=None, ge=1, le=86400)


class RetryPolicyOut(ORMModel):
    id: UUID
    organization_id: UUID
    name: str
    max_attempts: int
    base_delay_seconds: int
    max_delay_seconds: int
    created_at: datetime


class RetryPolicyList(BaseModel):
    items: list[RetryPolicyOut]
    total: int
