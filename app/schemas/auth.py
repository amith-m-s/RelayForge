from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.schemas.common import ORMModel


class RegisterRequest(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=255)
    password: str = Field(min_length=12, max_length=128)
    organization_name: str = Field(min_length=2, max_length=255)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str


class UserOut(ORMModel):
    id: UUID
    email: EmailStr
    full_name: str
    is_active: bool
    is_verified: bool
    last_login_at: datetime | None
    created_at: datetime


class AuthContext(BaseModel):
    user_id: UUID
    organization_id: UUID | None = None
    role: str | None = None
