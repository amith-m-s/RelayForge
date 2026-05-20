"""API v1 router — registers all route modules."""

from fastapi import APIRouter

from app.api.v1.routes.analytics import router as analytics_router
from app.api.v1.routes.api_keys import router as api_keys_router
from app.api.v1.routes.audit_logs import router as audit_router
from app.api.v1.routes.auth import router as auth_router
from app.api.v1.routes.dead_letter import router as dead_letter_router
from app.api.v1.routes.deliveries import router as deliveries_router
from app.api.v1.routes.event_types import router as event_types_router
from app.api.v1.routes.events import router as events_router
from app.api.v1.routes.health import router as health_router
from app.api.v1.routes.organizations import router as org_router
from app.api.v1.routes.retry_policies import router as retry_policies_router
from app.api.v1.routes.users import router as users_router
from app.api.v1.routes.webhooks import router as webhooks_router

api_router = APIRouter(prefix="/api/v1")

# --- Core ---
api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(org_router)

# --- Webhook domain ---
api_router.include_router(webhooks_router)
api_router.include_router(events_router)
api_router.include_router(event_types_router)
api_router.include_router(deliveries_router)
api_router.include_router(dead_letter_router)

# --- Configuration ---
api_router.include_router(api_keys_router)
api_router.include_router(retry_policies_router)

# --- Observability ---
api_router.include_router(analytics_router)
api_router.include_router(audit_router)