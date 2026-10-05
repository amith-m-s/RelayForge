from __future__ import annotations

from redis.asyncio import Redis

from app.core.config import get_settings

_settings = get_settings()
_redis: Redis[str] = Redis.from_url(_settings.redis_url, decode_responses=True)


def get_redis() -> Redis[str]:
    return _redis
