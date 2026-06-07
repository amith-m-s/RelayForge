from __future__ import annotations

from redis.exceptions import RedisError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.redis_client import get_redis


class IdempotencyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        if request.method not in {"POST", "PATCH"}:
            return await call_next(request)
        key = request.headers.get("Idempotency-Key")
        if not key:
            return await call_next(request)
        try:
            redis = get_redis()
            cache_key = f"idempotency:{request.url.path}:{key}"
            existing = await redis.get(cache_key)
            if existing:
                return JSONResponse({"detail": "Duplicate request"}, status_code=409)
            response = await call_next(request)
            if 200 <= response.status_code < 300:
                await redis.set(cache_key, "1", ex=24 * 3600)
            return response
        except RedisError:
            return await call_next(request)
