"""Analytics service — real metrics computation for the dashboard."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import case, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.delivery import Delivery
from app.models.event import Event
from app.models.webhook_endpoint import WebhookEndpoint


class AnalyticsService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_overview(self, organization_id: UUID) -> dict[str, Any]:
        """Dashboard overview metrics."""
        now = datetime.now(UTC)
        day_ago = now - timedelta(days=1)

        # Delivery counts by status
        delivery_stmt = (
            select(Delivery.status, func.count())
            .where(
                Delivery.organization_id == organization_id,
                Delivery.deleted_at.is_(None),
            )
            .group_by(Delivery.status)
        )
        result = await self.session.execute(delivery_stmt)
        delivery_counts = dict(result.all())

        # Total events
        event_count = (
            await self.session.execute(
                select(func.count())
                .select_from(Event)
                .where(Event.organization_id == organization_id, Event.deleted_at.is_(None))
            )
        ).scalar_one()

        # Total endpoints
        endpoint_count = (
            await self.session.execute(
                select(func.count())
                .select_from(WebhookEndpoint)
                .where(
                    WebhookEndpoint.organization_id == organization_id,
                    WebhookEndpoint.deleted_at.is_(None),
                )
            )
        ).scalar_one()

        # Recent 24h deliveries
        recent = (
            await self.session.execute(
                select(func.count())
                .select_from(Delivery)
                .where(
                    Delivery.organization_id == organization_id,
                    Delivery.created_at >= day_ago,
                    Delivery.deleted_at.is_(None),
                )
            )
        ).scalar_one()

        total_deliveries = int(sum(delivery_counts.values())) if delivery_counts else 0
        succeeded = int(delivery_counts.get("succeeded", 0))
        failed = int(delivery_counts.get("failed", 0))

        return {
            "events": {"total": int(event_count)},
            "webhooks": {"total": int(endpoint_count)},
            "deliveries": {
                "total": total_deliveries,
                "pending": int(delivery_counts.get("pending", 0)),
                "succeeded": succeeded,
                "failed": failed,
                "dead_letter": int(delivery_counts.get("dead_letter", 0)),
                "recent_24h": int(recent),
                "success_rate": round(succeeded / total_deliveries * 100, 1) if total_deliveries > 0 else 0.0,
            },
        }

    async def get_delivery_metrics(
        self, organization_id: UUID, window_hours: int = 24
    ) -> list[dict[str, Any]]:
        """Time-bucketed delivery metrics for charts using SQL grouping."""
        now = datetime.now(UTC)
        start = now - timedelta(hours=window_hours)

        trunc_precision = "hour" if window_hours <= 168 else "day"

        stmt = (
            select(
                func.date_trunc(trunc_precision, Delivery.created_at).label("bucket"),
                Delivery.status,
                func.count().label("count")
            )
            .where(
                Delivery.organization_id == organization_id,
                Delivery.created_at >= start,
                Delivery.deleted_at.is_(None),
            )
            .group_by(text("bucket"), Delivery.status)
            .order_by("bucket")
        )
        result = await self.session.execute(stmt)
        rows = result.all()

        buckets: dict[str, dict[str, int]] = {}
        for bucket, status_val, count in rows:
            key = bucket.isoformat()
            if key not in buckets:
                buckets[key] = {"succeeded": 0, "failed": 0, "pending": 0, "dead_letter": 0}
            if status_val in buckets[key]:
                buckets[key][status_val] = int(count)

        return [
            {"timestamp": ts, **counts}
            for ts, counts in sorted(buckets.items())
        ]

    async def get_endpoint_health(self, organization_id: UUID) -> list[dict[str, Any]]:
        """Per-endpoint success rates."""
        stmt = (
            select(
                WebhookEndpoint.id,
                WebhookEndpoint.name,
                WebhookEndpoint.url,
                WebhookEndpoint.status,
                func.count(Delivery.id).label("total_deliveries"),
                func.count(
                    case((Delivery.status == "succeeded", Delivery.id))
                ).label("succeeded"),
                func.count(
                    case((Delivery.status == "failed", Delivery.id))
                ).label("failed"),
            )
            .outerjoin(Delivery, Delivery.webhook_endpoint_id == WebhookEndpoint.id)
            .where(
                WebhookEndpoint.organization_id == organization_id,
                WebhookEndpoint.deleted_at.is_(None),
            )
            .group_by(WebhookEndpoint.id, WebhookEndpoint.name, WebhookEndpoint.url, WebhookEndpoint.status)
        )
        result = await self.session.execute(stmt)
        rows = result.all()

        return [
            {
                "endpoint_id": str(row.id),
                "name": row.name,
                "url": row.url,
                "status": row.status,
                "total_deliveries": int(row.total_deliveries),
                "succeeded": int(row.succeeded),
                "failed": int(row.failed),
                "success_rate": round(
                    int(row.succeeded) / int(row.total_deliveries) * 100, 1
                )
                if int(row.total_deliveries) > 0
                else 0.0,
            }
            for row in rows
        ]

    async def get_event_volume(
        self, organization_id: UUID, window_hours: int = 24
    ) -> list[dict[str, Any]]:
        """Event ingestion rate over time using SQL grouping."""
        now = datetime.now(UTC)
        start = now - timedelta(hours=window_hours)

        trunc_precision = "hour" if window_hours <= 168 else "day"

        stmt = (
            select(
                func.date_trunc(trunc_precision, Event.created_at).label("bucket"),
                func.count().label("count")
            )
            .where(
                Event.organization_id == organization_id,
                Event.created_at >= start,
                Event.deleted_at.is_(None),
            )
            .group_by(text("bucket"))
            .order_by("bucket")
        )
        result = await self.session.execute(stmt)
        rows = result.all()

        return [
            {"timestamp": row.bucket.isoformat(), "count": int(row.count)}
            for row in rows
        ]
