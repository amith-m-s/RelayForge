# RelayForge

RelayForge is a production-oriented, multi-tenant webhook delivery and API automation platform built with FastAPI, PostgreSQL, Redis, Celery, SQLAlchemy 2.x, and Alembic.

## Included in this scaffold

- Multi-tenant organizations and memberships
- JWT access tokens and refresh-token rotation
- API key support
- Event intake and webhook delivery orchestration
- HMAC webhook signing
- Delivery attempt tracking and retry scheduling
- Redis-backed request idempotency and rate limiting
- Celery worker and beat wiring
- Request tracing and structured logging
- Docker and GitHub Actions setup
- Tests for authentication and health checks

## Architecture

The project is organized using a layered backend architecture:

- `app/api`: request routing and response contracts
- `app/services`: business logic and orchestration
- `app/repositories`: persistence access
- `app/models`: SQLAlchemy domain models
- `app/schemas`: Pydantic request and response models
- `app/core`: config, security, logging, and Redis
- `app/middleware`: request ID, idempotency, rate limiting
- `app/workers`: Celery tasks
- `app/analytics` and `app/monitoring`: observability extensions

## Running locally

1. Copy `.env.example` to `.env`
2. Start PostgreSQL and Redis
3. Install dependencies
4. Run migrations
5. Start the API and worker

This is the foundation for the full RelayForge build; the core wiring is in place and ready for deeper domain implementation.
