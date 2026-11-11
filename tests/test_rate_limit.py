from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from starlette.requests import Request
from starlette.responses import PlainTextResponse, Response

import app.middleware.rate_limit as rate_limit
from app.middleware.rate_limit import RateLimitMiddleware


class FakeRedis:
    def __init__(self) -> None:
        self.counts: dict[str, int] = {}
        self.keys: list[str] = []
        self.expirations: dict[str, int] = {}

    async def incr(self, key: str) -> int:
        self.keys.append(key)
        self.counts[key] = self.counts.get(key, 0) + 1
        return self.counts[key]

    async def expire(self, key: str, seconds: int) -> bool:
        self.expirations[key] = seconds
        return True


def make_request(client_host: str, organization_id: str) -> Request:
    return Request(
        {
            "type": "http",
            "http_version": "1.1",
            "method": "GET",
            "scheme": "http",
            "path": "/",
            "raw_path": b"/",
            "query_string": b"",
            "headers": [(b"x-organization-id", organization_id.encode("ascii"))],
            "client": (client_host, 12345),
            "server": ("testserver", 80),
        }
    )


async def call_next(_: Request) -> Response:
    return PlainTextResponse("ok")


@pytest.mark.asyncio
async def test_changing_untrusted_organization_header_does_not_bypass_limit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    redis = FakeRedis()
    monkeypatch.setattr(rate_limit, "get_redis", lambda: redis)
    monkeypatch.setattr(
        rate_limit,
        "get_settings",
        lambda: SimpleNamespace(rate_limit_default=1),
    )
    middleware = RateLimitMiddleware(FastAPI())

    first = await middleware.dispatch(
        make_request("203.0.113.10", "org-a"),
        call_next,
    )
    second = await middleware.dispatch(
        make_request("203.0.113.10", "org-b"),
        call_next,
    )

    assert first.status_code == 200
    assert second.status_code == 429
    assert redis.keys == ["rate:203.0.113.10", "rate:203.0.113.10"]
    assert redis.expirations == {"rate:203.0.113.10": 60}


@pytest.mark.asyncio
async def test_rate_limit_keeps_separate_buckets_for_different_clients(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    redis = FakeRedis()
    monkeypatch.setattr(rate_limit, "get_redis", lambda: redis)
    monkeypatch.setattr(
        rate_limit,
        "get_settings",
        lambda: SimpleNamespace(rate_limit_default=1),
    )
    middleware = RateLimitMiddleware(FastAPI())

    first = await middleware.dispatch(
        make_request("203.0.113.10", "same-org"),
        call_next,
    )
    second = await middleware.dispatch(
        make_request("203.0.113.11", "same-org"),
        call_next,
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert redis.keys == ["rate:203.0.113.10", "rate:203.0.113.11"]
