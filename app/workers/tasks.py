from __future__ import annotations

import json
import time
from datetime import UTC, datetime, timedelta
from uuid import UUID

import httpx
from asgiref.sync import async_to_sync
from celery import shared_task
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.config import get_settings
from app.core.security import sign_webhook_payload
from app.db.session import AsyncSessionLocal
from app.models.dead_letter_event import DeadLetterEvent
from app.models.delivery import Delivery
from app.models.delivery_attempt import DeliveryAttempt
from app.models.event import Event
from app.models.retry_policy import RetryPolicy
from app.models.webhook_endpoint import WebhookEndpoint


def _retry_delay_seconds(
    attempt_count: int,
    policy: RetryPolicy | None = None,
) -> int:
    base_delay = policy.base_delay_seconds if policy else 30
    max_delay = policy.max_delay_seconds if policy else 3600

    delay = min(
        max_delay,
        base_delay * (2 ** max(attempt_count - 1, 0)),
    )

    return int(delay)


async def _dispatch_delivery_async(
    delivery_id: str,
) -> dict[str, str]:

    async with AsyncSessionLocal() as session:

        delivery = await session.get(
            Delivery,
            UUID(delivery_id),
        )

        if delivery is None or delivery.deleted_at is not None:
            return {
                "delivery_id": delivery_id,
                "status": "not_found",
            }

        if delivery.status in {"succeeded", "dead_letter"}:
            return {
                "delivery_id": delivery_id,
                "status": delivery.status,
            }

        event = await session.get(Event, delivery.event_id)

        endpoint_stmt = (
            select(WebhookEndpoint)
            .options(
                selectinload(WebhookEndpoint.retry_policy)
            )
            .where(
                WebhookEndpoint.id
                == delivery.webhook_endpoint_id
            )
        )

        endpoint_result = await session.execute(
            endpoint_stmt
        )

        endpoint = endpoint_result.scalars().first()

        if (
            event is None
            or endpoint is None
            or endpoint.deleted_at is not None
        ):
            delivery.status = "dead_letter"
            delivery.last_error = (
                "Missing event or endpoint"
            )

            await session.commit()

            return {
                "delivery_id": delivery_id,
                "status": "dead_letter",
            }

        retry_policy = endpoint.retry_policy

        if (
            retry_policy is None
            and endpoint.retry_policy_id is not None
        ):
            retry_policy = await session.get(
                RetryPolicy,
                endpoint.retry_policy_id,
            )

        payload_json = (
            event.payload
            if isinstance(event.payload, str)
            else json.dumps(event.payload)
        )

        payload_bytes = payload_json.encode("utf-8")

        timestamp = str(
            int(datetime.now(UTC).timestamp())
        )

        signature = sign_webhook_payload(
            payload_bytes,
            timestamp,
            secret=endpoint.secret_hash,
        )

        headers = {
            "Content-Type": "application/json",
            "X-RelayForge-Event": str(event.id),
            "X-RelayForge-Delivery-ID": str(delivery.id),
            "X-RelayForge-Timestamp": timestamp,
            "X-RelayForge-Signature": signature,
        }

        start = time.perf_counter()

        response_text: str | None = None
        status_code: int | None = None

        try:

            async with httpx.AsyncClient(
                timeout=10.0
            ) as client:

                response = await client.post(
                    endpoint.url,
                    content=payload_bytes,
                    headers=headers,
                )

            duration_ms = int(
                (time.perf_counter() - start) * 1000
            )

            status_code = response.status_code

            response_text = response.text[:4000]

            attempt = DeliveryAttempt(
                delivery_id=delivery.id,
                attempt_number=delivery.attempt_count + 1,
                request_body=payload_json,
                http_status=response.status_code,
                response_body=response_text,
                error_message=(
                    None
                    if 200 <= response.status_code < 300
                    else response.text[:1000]
                ),
                duration_ms=duration_ms,
            )

            delivery.attempt_count += 1
            delivery.last_attempt_at = datetime.now(UTC)
            delivery.last_status_code = response.status_code
            delivery.last_response_body = response_text

            if 200 <= response.status_code < 300:

                delivery.status = "succeeded"
                delivery.last_error = None

                session.add(attempt)

                await session.commit()

                return {
                    "delivery_id": delivery_id,
                    "status": "succeeded",
                }

            retryable = (
                response.status_code >= 500
                or response.status_code == 429
            )

            if retryable and delivery.attempt_count < (
                retry_policy.max_attempts
                if retry_policy
                else 8
            ):

                delivery.status = "retry_scheduled"

                delay = _retry_delay_seconds(
                    delivery.attempt_count,
                    retry_policy,
                )

                delivery.next_attempt_at = (
                    datetime.now(UTC)
                    + timedelta(seconds=delay)
                )

                delivery.last_error = (
                    f"HTTP {response.status_code}"
                )

                session.add(attempt)

                await session.commit()

                retry_delivery.apply_async(
                    args=[delivery_id],
                    countdown=delay,
                )

                return {
                    "delivery_id": delivery_id,
                    "status": "retry_scheduled",
                }

            delivery.status = "dead_letter"

            delivery.last_error = (
                f"HTTP {response.status_code}"
            )

            session.add(attempt)

            session.add(
                DeadLetterEvent(
                    organization_id=delivery.organization_id,
                    delivery_id=delivery.id,
                    reason=delivery.last_error,
                    payload_snapshot=payload_json,
                )
            )

            await session.commit()

            return {
                "delivery_id": delivery_id,
                "status": "dead_letter",
            }

        except Exception as exc:
            await session.rollback()
            error_message = str(exc)

            duration_ms = int(
                (time.perf_counter() - start) * 1000
            )

            attempt = DeliveryAttempt(
                delivery_id=delivery.id,
                attempt_number=delivery.attempt_count + 1,
                request_body=payload_json,
                http_status=status_code,
                response_body=response_text,
                error_message=error_message,
                duration_ms=duration_ms,
            )

            delivery.attempt_count += 1

            delivery.last_attempt_at = datetime.now(UTC)

            delivery.last_error = error_message

            if delivery.attempt_count < (
                retry_policy.max_attempts
                if retry_policy
                else 8
            ):

                delivery.status = "retry_scheduled"

                delay = _retry_delay_seconds(
                    delivery.attempt_count,
                    retry_policy,
                )

                delivery.next_attempt_at = (
                    datetime.now(UTC)
                    + timedelta(seconds=delay)
                )

                session.add(attempt)

                await session.commit()

                retry_delivery.apply_async(
                    args=[delivery_id],
                    countdown=delay,
                )

                return {
                    "delivery_id": delivery_id,
                    "status": "retry_scheduled",
                }

            delivery.status = "dead_letter"

            session.add(attempt)

            session.add(
                DeadLetterEvent(
                    organization_id=delivery.organization_id,
                    delivery_id=delivery.id,
                    reason=error_message,
                    payload_snapshot=payload_json,
                )
            )

            await session.commit()

            return {
                "delivery_id": delivery_id,
                "status": "dead_letter",
            }


@shared_task(
    bind=True,
    max_retries=8,
    default_retry_delay=30,
)
def dispatch_delivery(
    self,
    delivery_id: str,
) -> dict[str, str]:
    return async_to_sync(_dispatch_delivery_async)(delivery_id)


@shared_task(bind=True)
def retry_delivery(
    self,
    delivery_id: str,
):

    dispatch_delivery.delay(delivery_id)

    return {
        "delivery_id": delivery_id,
        "status": "retry_enqueued",
    }


@shared_task
def aggregate_delivery_metrics() -> dict[str, str]:

    settings = get_settings()

    return {
        "status": "ok",
        "service": settings.app_name,
    }