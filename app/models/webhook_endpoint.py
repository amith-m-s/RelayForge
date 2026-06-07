from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, func, text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.delivery import Delivery
    from app.models.organization import Organization
    from app.models.retry_policy import RetryPolicy


class WebhookEndpoint(Base):
    __tablename__ = "webhook_endpoints"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    secret_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, server_default=text("'active'"))
    event_filter: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'*'"))
    retry_policy_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("retry_policies.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    organization: Mapped[Organization] = relationship(back_populates="webhook_endpoints")
    retry_policy: Mapped[RetryPolicy | None] = relationship()
    deliveries: Mapped[list[Delivery]] = relationship(
        back_populates="webhook_endpoint", cascade="all, delete-orphan"
    )

    __table_args__ = (Index("ix_webhook_endpoints_org_status", "organization_id", "status"),)
