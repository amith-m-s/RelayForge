# RelayForge

**Multi-tenant webhook delivery and API automation platform. FastAPI · PostgreSQL · Redis · Celery · Alembic.**

[![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white)](https://github.com/amith-m-s/RelayForge)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)](https://github.com/amith-m-s/RelayForge)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=flat-square&logo=postgresql&logoColor=white)](https://github.com/amith-m-s/RelayForge)
[![Redis](https://img.shields.io/badge/Redis-DC382D?style=flat-square&logo=redis&logoColor=white)](https://github.com/amith-m-s/RelayForge)
[![Celery](https://img.shields.io/badge/Celery-37814A?style=flat-square&logo=celery&logoColor=white)](https://github.com/amith-m-s/RelayForge)

---

## What This Is

The infrastructure layer that powers event-driven integrations — the same class of system that Stripe uses to deliver payment webhooks, GitHub to deliver push events, and Twilio to deliver SMS status callbacks. Multi-tenant organizations, HMAC-signed delivery, retry scheduling, idempotency, and structured observability — all wired together in a production-oriented scaffold.

---

## Architecture

```
Inbound Event (HTTP POST)
        │
        ▼
┌──────────────────────────────────────────┐
│  API Layer  (FastAPI)                    │
│                                          │
│  Middleware:                             │
│  ├── Request ID injection (UUID)         │
│  ├── Structured access logging           │
│  ├── Redis idempotency key check  ──────▶ reject duplicate on hit
│  └── Rate limiting (per-tenant)          │
│                                          │
│  Routes:                                 │
│  ├── /auth     JWT + refresh rotation    │
│  ├── /orgs     Multi-tenant management   │
│  ├── /events   Event intake + validation │
│  └── /webhooks Endpoint registration     │
└─────────────────┬────────────────────────┘
                  │
        ┌─────────▼─────────┐
        │  Service Layer    │
        │                   │
        │  EventService     │ ──▶ validates, persists event
        │  DeliveryService  │ ──▶ selects endpoints, schedules tasks
        │  SigningService   │ ──▶ HMAC-SHA256 payload signing
        └─────────┬─────────┘
                  │
        ┌─────────▼─────────┐
        │  Worker Layer     │
        │  (Celery + Redis) │
        │                   │
        │  deliver_webhook  │ ──▶ HTTP POST to endpoint
        │  retry_failed     │ ──▶ exponential backoff schedule
        │  beat scheduler   │ ──▶ periodic retry sweeps
        └─────────┬─────────┘
                  │
        ┌─────────▼─────────┐
        │  Persistence      │
        │                   │
        │  PostgreSQL        │ ──▶ orgs, members, events, attempts
        │  Alembic          │ ──▶ versioned schema migrations
        │  Redis            │ ──▶ idempotency keys, rate limit counters
        └───────────────────┘
```

---

## Core Engineering Decisions

### HMAC Webhook Signing

Every outbound webhook delivery is signed:

```
X-RelayForge-Signature: sha256=<hmac_hex>
X-RelayForge-Timestamp: <unix_timestamp>
```

The HMAC is computed over `timestamp.payload_body` using the endpoint's secret key. Consumers verify this signature before processing. Replay attacks are mitigated by the timestamp window check.

This is how Stripe, GitHub, and Shopify sign webhooks. Unsigned webhooks let anyone POST to your endpoint and trigger business logic.

### Redis Idempotency

Duplicate event submissions are deduplicated before hitting any business logic:

```
1. Extract idempotency key from request header
2. Check Redis: SET key "processing" NX EX 86400
3. If key already exists → return 409 Conflict immediately
4. On success → store result against key
```

No database hit. No duplicate processing. No race condition.

### SQLAlchemy 2.x + Alembic

Schema changes are versioned and reversible:

```bash
alembic revision --autogenerate -m "add delivery_attempts table"
alembic upgrade head
alembic downgrade -1    # fully reversible
```

Every schema change has a corresponding migration file. No `CREATE TABLE IF NOT EXISTS` hacks. No manual SQL in deployment scripts.

### Repository Pattern

Persistence is fully decoupled from business logic:

```
app/api/routes/     ← HTTP contracts only
app/services/       ← business logic, calls repositories
app/repositories/   ← all SQL queries live here
app/models/         ← SQLAlchemy models
```

Services never import SQLAlchemy. Repositories never contain business logic. This makes both independently testable — mock the repository in service tests, mock the service in route tests.

---

## Project Structure

```
RelayForge/
├── .github/workflows/       # GitHub Actions CI
├── alembic/                 # Database migration versions
├── app/
│   ├── api/routes/          # FastAPI route handlers
│   ├── analytics/           # Usage metrics collection
│   ├── core/
│   │   ├── config.py        # Pydantic Settings
│   │   ├── logging.py       # Structured JSON logging
│   │   ├── middleware.py    # Request ID, idempotency, rate limiting
│   │   ├── redis.py         # Redis client + helpers
│   │   └── security.py     # JWT + bcrypt
│   ├── middleware/          # ASGI middleware stack
│   ├── models/              # SQLAlchemy ORM models
│   ├── monitoring/          # Prometheus + health checks
│   ├── repositories/        # Persistence layer (all SQL here)
│   ├── schemas/             # Pydantic request/response models
│   ├── services/            # Business logic orchestration
│   └── workers/             # Celery task definitions
├── frontend/                # React dashboard (in progress)
├── tests/                   # pytest test suite
├── .env.example
├── alembic.ini
├── docker-compose.yml
├── Dockerfile
└── pyproject.toml
```

---

## Running Locally

```bash
git clone https://github.com/amith-m-s/RelayForge
cd RelayForge
cp .env.example .env

docker compose up --build

# Apply migrations
docker compose exec app alembic upgrade head

# API:   http://localhost:8000
# Docs:  http://localhost:8000/docs
```

**Without Docker:**
```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload

# Separate terminal — Celery worker
celery -A app.workers worker --loglevel=info

# Separate terminal — Celery beat (scheduler)
celery -A app.workers beat --loglevel=info
```

---

## Testing

```bash
pytest tests/ -v
```

Current coverage: auth flows, health checks. Delivery and idempotency test coverage is in progress.

---

## CI

GitHub Actions pipeline (`.github/workflows/`) runs on every push:
- Dependency installation
- Linting
- Test suite

---

## Honest Limitations

This is a **production-oriented scaffold** — the core wiring is complete and correct, but several domain features are not fully implemented:

| Component | Status |
|---|---|
| JWT auth + refresh rotation | ✅ Complete |
| Multi-tenant org + membership | ✅ Complete |
| API key authentication | ✅ Complete |
| Redis idempotency + rate limiting | ✅ Complete |
| HMAC webhook signing | ✅ Complete |
| Celery worker + beat wiring | ✅ Complete |
| Alembic migrations | ✅ Complete |
| Delivery attempt tracking | 🔧 Schema in place, retry logic partial |
| Frontend dashboard | 🔧 In progress |
| Full delivery test coverage | 🔧 In progress |
| Tenant billing hooks | ❌ Not implemented |

**The `.env` file is committed to the repo.** This is a critical security issue that must be fixed before any real use: add `.env` to `.gitignore`, rotate any secrets that have been in that file, and use `.env.example` as the committed template only.
