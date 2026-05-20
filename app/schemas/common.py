from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class Paging(BaseModel):
    limit: int = Field(ge=1, le=100, default=20)
    offset: int = Field(ge=0, default=0)


class SuccessResponse(BaseModel):
    success: bool = True
