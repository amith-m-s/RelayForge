"""Upgraded main.py — CORS, structured errors, OpenAPI metadata, proper lifecycle."""

from __future__ import annotations

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.errors import register_exception_handlers
from app.core.logging import configure_logging
from app.middleware.idempotency import IdempotencyMiddleware
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.request_id import RequestIdMiddleware

configure_logging()
settings = get_settings()


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncIterator[None]:
    """Application lifecycle — startup and shutdown hooks."""
    import structlog
    log = structlog.get_logger()
    log.info("relayforge_starting", environment=settings.environment)
    yield
    log.info("relayforge_stopping")


app = FastAPI(
    title="RelayForge",
    version="0.1.0",
    description=(
        "Production-grade, multi-tenant webhook delivery and API automation platform. "
        "RelayForge provides reliable event intake, fan-out delivery with HMAC signing, "
        "automatic retries with exponential backoff, dead-letter queues, "
        "and real-time analytics."
    ),
    openapi_url="/api/v1/openapi.json",
    docs_url="/api/v1/docs",
    redoc_url="/api/v1/redoc",
    default_response_class=ORJSONResponse,
    lifespan=lifespan,
    contact={
        "name": "RelayForge Engineering",
        "email": "engineering@relayforge.io",
    },
    license_info={
        "name": "MIT",
    },
)

# --- Middleware (order matters — outermost first) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["x-request-id", "x-ratelimit-remaining"],
)
app.add_middleware(RequestIdMiddleware)
app.add_middleware(IdempotencyMiddleware)
app.add_middleware(RateLimitMiddleware)

# --- Exception handlers ---
register_exception_handlers(app)

# --- Routes ---
app.include_router(api_router)


@app.get("/", tags=["root"])
async def root() -> dict[str, str]:
    return {"service": "RelayForge", "version": "0.1.0", "status": "running"}
