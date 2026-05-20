"""Health and readiness endpoints with real dependency checks."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import ORJSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import db_session
from app.core.redis_client import get_redis

router = APIRouter(tags=["health"])


async def _check_database(session: AsyncSession) -> dict[str, str]:
    """Verify the database connection is alive."""
    try:
        await session.execute(text("SELECT 1"))
        return {"status": "healthy", "latency": "ok"}
    except Exception as exc:
        return {"status": "unhealthy", "error": str(exc)[:200]}


async def _check_redis() -> dict[str, str]:
    """Verify the Redis connection is alive."""
    try:
        redis = get_redis()
        pong = await redis.ping()
        return {"status": "healthy" if pong else "degraded"}
    except Exception as exc:
        return {"status": "unhealthy", "error": str(exc)[:200]}


@router.get("/health")
async def health() -> ORJSONResponse:
    """Lightweight liveness probe — always returns 200."""
    return ORJSONResponse({"status": "ok", "service": "relayforge"})


@router.get("/ready")
async def ready(
    session: AsyncSession = Depends(db_session),
) -> ORJSONResponse:
    """Deep readiness probe — checks DB and Redis connectivity."""
    db_status = await _check_database(session)
    redis_status = await _check_redis()

    components = {
        "database": db_status,
        "redis": redis_status,
    }

    all_healthy = all(c["status"] == "healthy" for c in components.values())
    overall = "ready" if all_healthy else "degraded"
    status_code = 200 if all_healthy else 503

    return ORJSONResponse(
        status_code=status_code,
        content={
            "status": overall,
            "service": "relayforge",
            "components": components,
        },
    )
