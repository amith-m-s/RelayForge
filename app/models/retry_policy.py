from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, func, text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.organization import Organization


class RetryPolicy(Base):
    __tablename__ = "retry_policies"
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    max_attempts: Mapped[int] = mapped_column(Integer, server_default=text("8"), nullable=False)
    base_delay_seconds: Mapped[int] = mapped_column(Integer, server_default=text("30"), nullable=False)
    max_delay_seconds: Mapped[int] = mapped_column(Integer, server_default=text("3600"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    organization: Mapped[Organization] = relationship()
    __table_args__ = (
        Index("ix_retry_policies_org_name", "organization_id", "name", unique=True),
        UniqueConstraint("organization_id", "name", name="uq_retry_policies_org_name"),
    )
