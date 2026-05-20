from __future__ import annotations

import json
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_token
from app.models.dead_letter_event import DeadLetterEvent
from app.models.delivery import Delivery
from app.models.delivery_attempt import DeliveryAttempt
from app.models.event import Event
from app.models.event_type import EventType
from app.models.webhook_endpoint import WebhookEndpoint


def _match_filter(event_filter: str, event_name: str) -> bool:
    normalized = event_filter.strip()
    if normalized == "*" or normalized == "":
        return True
    if normalized == event_name:
        return True
    parts = [item.strip() for item in normalized.split(",") if item.strip()]
    return event_name in parts


class WebhookService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_endpoint(
        self,
        organization_id: UUID,
        name: str,
        url: str,
        secret: str,
        event_filter: str = "*",
        retry_policy_id: UUID | None = None,
    ) -> WebhookEndpoint:
        endpoint = WebhookEndpoint(
            organization_id=organization_id,
            name=name.strip(),
            url=url,
            secret_hash=hash_token(secret),
            event_filter=event_filter,
            retry_policy_id=retry_policy_id,
            status="active",
        )
        self.session.add(endpoint)
        await self.session.flush()
        return endpoint

    async def list_endpoints(
        self, organization_id: UUID, limit: int = 20, offset: int = 0
    ) -> tuple[list[WebhookEndpoint], int]:
        count_stmt = select(WebhookEndpoint).where(
            WebhookEndpoint.organization_id == organization_id, WebhookEndpoint.deleted_at.is_(None)
        )
        result = await self.session.execute(count_stmt)
        items = list(result.scalars().all())
        total = len(items)
        return items[offset : offset + limit], total

    async def update_endpoint(self, endpoint: WebhookEndpoint, **fields: object) -> WebhookEndpoint:
        for key, value in fields.items():
            if value is not None and hasattr(endpoint, key):
                setattr(endpoint, key, value)
        await self.session.flush()
        return endpoint

    async def create_event(
        self,
        organization_id: UUID,
        source: str,
        event_type: str,
        payload_json: str,
        event_key: str | None = None,
        idempotency_key: str | None = None,
    ) -> tuple[Event, list[Delivery]]:
        event_type_row = await self._get_or_create_event_type(organization_id, event_type)
        event = Event(
            organization_id=organization_id,
            event_type_id=event_type_row.id,
            source=source,
            payload=payload_json,
            event_key=event_key,
            idempotency_key=idempotency_key,
        )
        self.session.add(event)
        await self.session.flush()

        stmt = select(WebhookEndpoint).where(
            WebhookEndpoint.organization_id == organization_id,
            WebhookEndpoint.deleted_at.is_(None),
            WebhookEndpoint.status == "active",
        )
        result = await self.session.execute(stmt)
        endpoints = [
            endpoint
            for endpoint in result.scalars().all()
            if _match_filter(endpoint.event_filter, event_type)
        ]

        deliveries: list[Delivery] = []
        for endpoint in endpoints:
            delivery = Delivery(
                organization_id=organization_id,
                webhook_endpoint_id=endpoint.id,
                event_id=event.id,
                status="pending",
                attempt_count=0,
            )
            self.session.add(delivery)
            deliveries.append(delivery)
        await self.session.flush()
        return event, deliveries

    async def retry_delivery(self, delivery: Delivery, reason: str | None = None) -> Delivery:
        delivery.status = "queued"
        delivery.next_attempt_at = datetime.now(UTC)
        delivery.last_error = reason
        await self.session.flush()
        return delivery

    async def record_attempt(
        self,
        delivery: Delivery,
        request_body: str,
        http_status: int | None,
        response_body: str | None,
        error_message: str | None,
        duration_ms: int | None,
    ) -> DeliveryAttempt:
        attempt = DeliveryAttempt(
            delivery_id=delivery.id,
            attempt_number=delivery.attempt_count + 1,
            request_body=request_body,
            http_status=http_status,
            response_body=response_body,
            error_message=error_message,
            duration_ms=duration_ms,
        )
        delivery.attempt_count += 1
        delivery.last_attempt_at = datetime.now(UTC)
        delivery.last_status_code = http_status
        delivery.last_response_body = response_body
        delivery.last_error = error_message
        self.session.add(attempt)
        await self.session.flush()
        return attempt

    async def dead_letter(self, delivery: Delivery, reason: str) -> DeadLetterEvent:
        snapshot = json.dumps(
            {
                "delivery_id": str(delivery.id),
                "event_id": str(delivery.event_id),
                "webhook_endpoint_id": str(delivery.webhook_endpoint_id),
                "reason": reason,
            }
        )
        event = DeadLetterEvent(
            organization_id=delivery.organization_id,
            delivery_id=delivery.id,
            reason=reason,
            payload_snapshot=snapshot,
        )
        self.session.add(event)
        await self.session.flush()
        return event

    async def _get_or_create_event_type(self, organization_id: UUID, name: str) -> EventType:
        stmt = select(EventType).where(
            EventType.organization_id == organization_id,
            EventType.name == name,
            EventType.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        event_type = result.scalars().first()
        if event_type is not None:
            return event_type
        event_type = EventType(organization_id=organization_id, name=name, description=None)
        self.session.add(event_type)
        await self.session.flush()
        return event_type
