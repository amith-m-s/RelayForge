"""Expanded delivery service — filtering, replay, DLQ management."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dead_letter_event import DeadLetterEvent
from app.models.delivery import Delivery
from app.models.delivery_attempt import DeliveryAttempt


class DeliveryService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_for_organization(
        self,
        organization_id: UUID,
        limit: int = 20,
        offset: int = 0,
        status_filter: str | None = None,
        endpoint_id: UUID | None = None,
    ) -> tuple[list[Delivery], int]:
        base = select(Delivery).where(
            Delivery.organization_id == organization_id,
            Delivery.deleted_at.is_(None),
        )
        if status_filter:
            base = base.where(Delivery.status == status_filter)
        if endpoint_id:
            base = base.where(Delivery.webhook_endpoint_id == endpoint_id)

        count_stmt = select(func.count()).select_from(base.subquery())
        total = (await self.session.execute(count_stmt)).scalar_one()

        stmt = base.order_by(desc(Delivery.created_at)).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return list(result.scalars().all()), int(total)

    async def get_for_organization(
        self, organization_id: UUID, delivery_id: UUID
    ) -> Delivery | None:
        stmt = select(Delivery).where(
            Delivery.id == delivery_id,
            Delivery.organization_id == organization_id,
            Delivery.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_attempts(self, delivery_id: UUID) -> list[DeliveryAttempt]:
        stmt = (
            select(DeliveryAttempt)
            .where(DeliveryAttempt.delivery_id == delivery_id)
            .order_by(desc(DeliveryAttempt.created_at))
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def replay(self, delivery: Delivery) -> Delivery:
        """Reset a delivery for replay."""
        delivery.status = "pending"
        delivery.last_error = None
        await self.session.flush()
        return delivery

    # --- Dead Letter Queue ---

    async def list_dead_letter(
        self,
        organization_id: UUID,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[DeadLetterEvent], int]:
        base = select(DeadLetterEvent).where(
            DeadLetterEvent.organization_id == organization_id,
            DeadLetterEvent.deleted_at.is_(None),
        )
        count_stmt = select(func.count()).select_from(base.subquery())
        total = (await self.session.execute(count_stmt)).scalar_one()

        stmt = base.order_by(desc(DeadLetterEvent.created_at)).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return list(result.scalars().all()), int(total)

    async def get_dead_letter(
        self, organization_id: UUID, dlq_id: UUID
    ) -> DeadLetterEvent | None:
        stmt = select(DeadLetterEvent).where(
            DeadLetterEvent.id == dlq_id,
            DeadLetterEvent.organization_id == organization_id,
            DeadLetterEvent.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def replay_dead_letter(self, dlq_event: DeadLetterEvent) -> Delivery | None:
        """Re-enqueue the delivery associated with a dead letter event."""
        delivery = await self.get_for_organization(
            dlq_event.organization_id, dlq_event.delivery_id
        )
        if delivery is None:
            return None
        delivery.status = "pending"
        delivery.last_error = None
        dlq_event.deleted_at = datetime.now(UTC)
        await self.session.flush()
        return delivery

    async def purge_dead_letter(self, organization_id: UUID, dlq_id: UUID) -> bool:
        dlq_event = await self.get_dead_letter(organization_id, dlq_id)
        if dlq_event is None:
            return False
        dlq_event.deleted_at = datetime.now(UTC)
        await self.session.flush()
        return True

    async def purge_all_dead_letter(self, organization_id: UUID) -> int:
        from sqlalchemy import update
        now = datetime.now(UTC)
        stmt = (
            update(DeadLetterEvent)
            .where(
                DeadLetterEvent.organization_id == organization_id,
                DeadLetterEvent.deleted_at.is_(None),
            )
            .values(deleted_at=now)
            .execution_options(synchronize_session="fetch")
        )
        result = await self.session.execute(stmt)
        await self.session.flush()
        return int(result.rowcount)
