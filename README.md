[![CI](https://github.com/amith-m-s/RelayForge/actions/workflows/ci.yml/badge.svg)](https://github.com/amith-m-s/RelayForge/actions/workflows/ci.yml)
[![Top Language](https://img.shields.io/github/languages/top/amith-m-s/RelayForge)](https://github.com/amith-m-s/RelayForge)
[![Code Size](https://img.shields.io/github/languages/code-size/amith-m-s/RelayForge)](https://github.com/amith-m-s/RelayForge)
[![Repo Size](https://img.shields.io/github/repo-size/amith-m-s/RelayForge)](https://github.com/amith-m-s/RelayForge)
[![Last Commit](https://img.shields.io/github/last-commit/amith-m-s/RelayForge)](https://github.com/amith-m-s/RelayForge/commits/main)
[![Issues](https://img.shields.io/github/issues/amith-m-s/RelayForge)](https://github.com/amith-m-s/RelayForge/issues)
[![Stars](https://img.shields.io/github/stars/amith-m-s/RelayForge)](https://github.com/amith-m-s/RelayForge/stargazers)

# RelayForge

**Multi-tenant webhook delivery and event-routing engine built with FastAPI, PostgreSQL, Redis, and Celery.**

RelayForge models the reliability problems that appear in webhook infrastructure: duplicate event ingestion, asynchronous delivery, retries, downstream failures, dead-letter handling, replay, signing, rate limiting, and audit history.

## What is implemented

- Multi-tenant organizations and memberships.
- Webhook endpoint registration and event-pattern routing.
- PostgreSQL-backed event and delivery records.
- Database-backed idempotency for event ingestion.
- Celery workers for asynchronous outbound delivery.
- Exponential retry scheduling with bounded jitter.
- Dead-letter records and replay workflows.
- HMAC-SHA256 payload signing.
- Redis fixed-window rate limiting.
- Request IDs, structured errors, audit logging, and analytics endpoints.
- Alembic migrations and automated tests.

## Reliability model

~~~
Client
  |
  v
FastAPI
  |
  +--> validate/authenticate
  |
  +--> create event + delivery rows in one DB transaction
  |
  v
Celery queue
  |
  v
Delivery worker
  |
  +--> 2xx       -> succeeded
  +--> 429/5xx   -> retry with bounded backoff
  +--> permanent/max-attempt failure -> dead letter
~~~

### Idempotency

The event API uses an organization-scoped idempotency key backed by a **PostgreSQL uniqueness guarantee**. This is stronger than a read-then-write cache check because concurrent requests are resolved by the database.

This should be described as **duplicate-event suppression / idempotent event creation**, not an absolute claim of exactly-once delivery to arbitrary external HTTP receivers.

### Retry behavior

Retries use exponential backoff with a maximum delay and bounded random jitter to reduce synchronized retry bursts.

### Rate limiting

The current middleware uses a Redis fixed-window counter. It is deliberately documented as fixed-window rate limiting rather than a token bucket.

## Local development

~~~
cp .env.example .env
docker compose up --build -d
docker compose ps
cd frontend
npm install
npm run dev
~~~

API: http://localhost:8001  
Dashboard: http://localhost:5173

## Testing

~~~
pytest -q
~~~

## Honest scope

RelayForge is a **production-oriented engineering reference implementation**. It is not presented here as a service handling verified external production traffic. Performance numbers should be treated as local benchmark targets unless independently measured and published.

## Core stack

FastAPI · PostgreSQL · SQLAlchemy 2.x · Alembic · Redis · Celery · Docker · React/Vite
