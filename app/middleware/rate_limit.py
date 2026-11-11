from __future__ import annotations

from redis.exceptions import RedisError
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.config import get_settings
from app.core.redis_client import get_redis


def _rate_limit_key(request: Request) -> str:
    """Build a bucket from the network peer, not caller-controlled tenant headers.

    Authentication and organization membership are resolved later by FastAPI
    dependencies, so X-Organization-ID is not trusted at middleware time.
    """
    client_host = request.client.host if request.client else "unknown"
    return f"rate:{client_host}"


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        settings = get_settings()
        key = _rate_limit_key(request)
        try:
            redis = get_redis()
            current = await redis.incr(key)
            if current == 1:
                await redis.expire(key, 60)
            if current > settings.rate_limit_default:
                return JSONResponse({"detail": "Rate limit exceeded"}, status_code=429)
        except RedisError:
            pass
        return await call_next(request)
