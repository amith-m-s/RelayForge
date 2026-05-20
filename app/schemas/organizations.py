"""Organization schemas — moved from inline route definitions."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.schemas.common import ORMModel


class OrganizationCreate(BaseModel):
    name: str = Field(min_length=2, max_length=255)


class OrganizationUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=255)


class OrganizationOut(ORMModel):
    id: UUID
    name: str
    slug: str
    owner_user_id: UUID
    is_active: bool
    created_at: datetime | None = None


class OrganizationList(BaseModel):
    items: list[OrganizationOut]
    total: int


# --- Membership schemas ---


class MemberInvite(BaseModel):
    email: EmailStr
    role: str = Field(default="viewer", pattern="^(owner|admin|developer|viewer)$")


class MemberOut(ORMModel):
    id: UUID
    user_id: UUID
    organization_id: UUID
    role: str
    is_active: bool
    email: str | None = None
    full_name: str | None = None
    created_at: datetime | None = None


class MemberList(BaseModel):
    items: list[MemberOut]
    total: int
