# ⚡ RelayForge — Enterprise-Grade Webhook Orchestration Engine

RelayForge is a high-throughput, multi-tenant webhook delivery and event routing engine. It is designed to ingest events from upstream applications, match them against routing rules, calculate secure payload signatures, and execute downstream callbacks with exponential backoff retry scheduling, dead-letter quarantining, rate limiting, and idempotency guarantees.

Built with **FastAPI**, **PostgreSQL**, **Redis**, and **Celery**, it is hardened to meet enterprise scalability, low-latency delivery, and strict data consistency requirements.

---

## 🚀 Key Platform Capabilities

### 1. Webhook Intake & Event Routing
- **Event Intake**: Accepting events with validated Pydantic schemas, auto-generating unique tracing identifiers, and checking for duplicate event ingestion.
- **Pattern Matching**: Webhook routing utilizes event filter matching patterns. Endpoints can subscribe to specific events (e.g. `order.created`), sub-patterns (e.g. `order.*`), or glob patterns (`*`).
- **Transactional Delivery Queue**: When an event is ingested, `Delivery` rows are created atomically within the same transaction to guarantee data integrity, preventing lost events.

### 2. High-Performance Celery Dispatcher
- **Decoupled Architecture**: Offloads HTTP request processing to dedicated Celery worker pools, freeing the API from I/O network bottlenecks.
- **Execution Queues**: Isolates new webhook attempts (`deliveries`) from retry attempts (`retries`) to prevent failed endpoints from clogging the throughput of new incoming deliveries.
- **Periodic Computations**: A Celery Beat scheduler drives periodic metric compilation and cleanup tasks.

### 3. Resilient Retries & Dead Letter Queue (DLQ)
- **Exponential Backoff with Jitter**: Computes next attempt delays using the formula:
  $$\text{delay} = \min(\text{max\_delay}, \text{base\_delay} \times 2^{\text{attempt}})$$
  Combined with randomized jitter to prevent downstream service denial-of-service (Thundering Herd problem).
- **Dead Letter Quarantine**: Webhooks exceeding their linked `RetryPolicy` attempts are quarantined in the Dead Letter Queue.
- **Replay Engine**: Allows programmatic or dashboard-driven execution replays for individual dead-letter payloads, retaining full historical attempts.

### 4. Redis-Backed Idempotency & Rate Limiting
- **Strict Idempotency**: Identifies incoming events using the `X-Idempotency-Key` header. Standardized to cache only successful 2xx responses in Redis to allow retrying client or server errors without blocking duplicates.
- **Token Bucket Rate Limiting**: Employs a sliding-window token bucket in Redis to rate-limit tenants and API keys. Gracefully handles Redis connection exceptions to maintain high uptime.

### 5. Secure Per-Endpoint Signing
- **HMAC HMAC-SHA256**: Generates signature hashes per endpoint using endpoint-specific secrets.
- **Payload Headers**: Dispatches `X-RelayForge-Signature` (with epoch timestamp `t=` and version signature `v1=`) alongside request headers, allowing target servers to prevent replay attacks and verify payload source authenticity.

### 6. Interactive Developer Sandbox
- **Live Trace Terminal**: Developers can select active endpoints, load payload templates, fire simulated events, and watch network attempts log in real time.
- **Payload Inspection**: Full sent-request header/body and received-response header/body inspection directly inside the UI.

---

## 🏗️ Layered System Architecture

```
d:/project/
├── app/
│   ├── analytics/       # SQL-level date-truncated analytics service
│   ├── api/             # FastAPI routers, dependencies (deps.py), schemas
│   ├── core/            # Config variables, security hashing, logging, Redis client
│   ├── db/              # SQLAlchemy session initialization and connection pool configuration
│   ├── middleware/      # Idempotency, rate limiting, and request ID middlewares
│   ├── models/          # Declarative SQLAlchemy domain models
│   ├── repositories/    # Database query abstractions
│   ├── services/        # Webhook delivery orchestration and business logic
│   └── workers/         # Celery task execution handlers (tasks.py)
└── frontend/            # React/Vite development and build directories
```

### Database Entity Relationship Schema

```
[User] (1) <─────── (N) [Membership] (N) ───────> (1) [Organization] (1)
                                                            │
                               ┌────────────────────────────┴───────────────────────────┐
                               ▼                                                        ▼
                    [WebhookEndpoint] (1)                                            [Event] (1)
                               │                                                        │
                               ▼                                                        ▼
                        [RetryPolicy] (1) ─────────── (N) [Delivery] (N) <──────────────┘
                                                              │
                                        ┌─────────────────────┴─────────────────────┐
                                        ▼                                           ▼
                             [DeliveryAttempt] (N)                        [DeadLetterEvent] (1)
```

---

## 📦 Setting Up locally

### Prerequisites
- Python 3.11.9
- Node.js 18+
- Docker & Docker Compose

### Option A: Docker Compose Deployment (Recommended)
This runs the API, celery workers, celery beat, PostgreSQL database, and Redis cache in a unified network.

1. **Configure Environment Variables**:
   Copy `.env.example` to `.env`. Ensure your database and broker secrets are defined:
   ```bash
   cp .env.example .env
   ```

2. **Launch Services**:
   ```bash
   docker compose up --build -d
   ```

3. **Verify Containers**:
   ```bash
   docker compose ps
   ```

   The backend API will now be listening on host port `8001` (`http://localhost:8001`).

4. **Run Frontend Application**:
   Navigate to the frontend directory, install npm packages, and start the Vite development server:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

   Vite will serve the dashboard at `http://localhost:5173`.

---

### Option B: Bare-Metal Development (Manual Setup)

1. **Provision Infrastructure**:
   Ensure PostgreSQL (listening on port `5432`) and Redis (listening on port `6379`) are active.

2. **Initialize Python Virtual Environment**:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   pip install -e .
   ```

3. **Run Database Migrations**:
   Alembic compiles models to generate and apply target schemas:
   ```bash
   alembic upgrade head
   ```

4. **Seed Mock Database Records**:
   ```bash
   python seed.py
   ```

5. **Start Application Processes**:
   Run these in separate terminal tabs:
   - **API Server**: `uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload`
   - **Celery Worker**: `celery -A app.workers.celery_app worker --loglevel=info -Q deliveries,retries`
   - **Celery Beat Scheduler**: `celery -A app.workers.celery_app beat --loglevel=info`

---

## 🔒 Security Architecture

### Per-Endpoint Signature Verification
RelayForge signs all outgoing POST payloads with HMAC-SHA256. Target servers should verify signatures to ensure legitimacy:

```python
import hmac
import hashlib

def verify_signature(payload_bytes: bytes, signature_header: str, secret: str) -> bool:
    # signature_header format: "t=1700000000,v1=abc123xyz..."
    parts = dict(x.split('=') for x in signature_header.split(','))
    timestamp = parts.get('t')
    signature = parts.get('v1')
    
    # Construct signature payload
    signed_payload = f"{timestamp}.".encode() + payload_bytes
    expected = hmac.new(secret.encode(), signed_payload, hashlib.sha256).hexdigest()
    
    return hmac.compare_digest(expected, signature)
```

---

## 📡 API Directory

| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| **POST** | `/api/v1/auth/register` | Create user, organization, and tenant membership | No |
| **POST** | `/api/v1/auth/token` | Retrieve OAuth2/JWT access and refresh token | No |
| **POST** | `/api/v1/auth/refresh` | Rotate expired JWT access tokens | No |
| **GET** | `/api/v1/users/me` | Fetch detailed user metadata and memberships | Yes |
| **POST** | `/api/v1/events` | Ingest upstream webhooks (supports idempotency) | API Key / JWT |
| **GET** | `/api/v1/events` | List historical events (paginated) | Yes |
| **POST** | `/api/v1/webhooks/endpoints` | Configure a new webhook destination | Yes |
| **GET** | `/api/v1/webhooks/endpoints` | Fetch endpoints list (supports searches) | Yes |
| **DELETE**| `/api/v1/webhooks/endpoints/{id}` | Remove webhook configuration | Yes |
| **GET** | `/api/v1/deliveries` | List delivery histories (filter by status) | Yes |
| **POST** | `/api/v1/deliveries/{id}/replay` | Manually queue a delivery replay | Yes |
| **GET** | `/api/v1/dead-letter` | List quarantined delivery failures | Yes |
| **POST** | `/api/v1/dead-letter/{id}/replay` | Replay single DLQ failure | Yes |
| **DELETE**| `/api/v1/dead-letter/{id}` | Purge single DLQ record | Yes |
| **POST** | `/api/v1/dead-letter/purge` | Bulk delete all DLQ records for tenant | Yes |
| **GET** | `/api/v1/analytics/overview` | Fetch total counts and pipeline ratios | Yes |
| **GET** | `/api/v1/analytics/delivery-metrics`| Time-bucketed delivery charts data | Yes |
| **GET** | `/api/v1/analytics/event-volume` | Time-bucketed volume charting metrics | Yes |
