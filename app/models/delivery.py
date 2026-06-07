from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, func, text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.delivery_attempt import DeliveryAttempt
    from app.models.event import Event
    from app.models.webhook_endpoint import WebhookEndpoint


class Delivery(Base):
    __tablename__ = "deliveries"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False
    )
    webhook_endpoint_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("webhook_endpoints.id"), nullable=False
    )
    event_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("events.id"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(50), nullable=False, server_default=text("'pending'"))
    attempt_count: Mapped[int] = mapped_column(Integer, server_default=text("0"), nullable=False)
    next_attempt_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_attempt_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_status_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    last_response_body: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    webhook_endpoint: Mapped[WebhookEndpoint] = relationship(back_populates="deliveries")
    event: Mapped[Event] = relationship(back_populates="deliveries")
    attempts: Mapped[list[DeliveryAttempt]] = relationship(
        back_populates="delivery", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_deliveries_org_status", "organization_id", "status"),
        Index("ix_deliveries_endpoint_status", "webhook_endpoint_id", "status"),
    )
