from __future__ import annotations

from redis.exceptions import RedisError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.config import get_settings
from app.core.redis_client import get_redis


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        settings = get_settings()
        tenant = request.headers.get("X-Organization-ID", "global")
        key = f"rate:{tenant}:{request.client.host if request.client else 'unknown'}"
        try:
            redis = get_redis()
            current = await redis.incr(key)
            if current == 1:
                await redis.expire(key, 60)
            if current > settings.rate_limit_default:
                return JSONResponse({"detail": "Rate limit exceeded"}, status_code=429)
        except Exception:
            pass
        return await call_next(request)
