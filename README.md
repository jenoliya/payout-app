# example — Merchant Payout Engine

A production-grade payout service where merchants can view their balance, request payouts, and track payout status in real time. Built with Django + DRF on the backend and React + Tailwind on the frontend, orchestrated with Docker + Nginx.

---

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Tech Stack](#tech-stack)
- [Prerequisites](#prerequisites)
- [Project Structure](#project-structure)
- [Quick Start with Docker](#quick-start-with-docker)
- [Manual Local Setup](#manual-local-setup)
- [Seeding Test Data](#seeding-test-data)
- [API Reference](#api-reference)
- [Background Workers](#background-workers)
- [Running Tests](#running-tests)
- [Environment Variables](#environment-variables)

---

## Architecture Overview

```
Browser
  │
  ▼
Nginx (reverse proxy)
  ├── /api/*  ──────────► Django + Gunicorn (uvicorn workers)
  └── /*      ──────────► React SPA (static files)

Django
  ├── OAuth2 Auth        (django-oauth-toolkit)
  ├── Payout API         (DRF APIViews)
  ├── Dashboard API
  └── Celery Beat        ──► Redis ──► Celery Worker
                                          ├── process_pending_payouts  (every 60s)
                                          └── process_holdings_payouts (every 10s)
```

**Money never touches Python floats.** All balances are stored as `IntegerField` in paise (1 rupee = 100 paise). Balance mutations happen via `F()` expressions — database-level arithmetic, not Python reads.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Django 5.2, Django REST Framework 3.17 |
| Auth | django-oauth-toolkit (OAuth2 Bearer tokens) |
| Background jobs | Celery 5.6 + django-celery-beat + Redis |
| Database | PostgreSQL (recommended) / SQLite (dev) |
| Frontend | React 19, TypeScript, Tailwind CSS 3, Vite |
| Reverse proxy | Nginx |
| Container | Docker + Docker Compose |

---

## Project Structure

```
.
├── backend/
│   ├── auth/               # OAuth2 login, token generation
│   ├── merchant/           # Merchant registration
│   ├── payout/             # Ledger, Merchant, Payout models + Celery tasks
│   ├── dashboard/          # Aggregated dashboard view
│   ├── core/               # Django settings, Celery config, URL root
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── pyproject.toml
│
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Login.tsx
│   │   │   ├── Dashboard.tsx
│   │   │   └── Payout.tsx
│   │   ├── AuthContext.tsx  # OAuth token storage + logout
│   │   ├── types.ts         # API response interfaces
│   │   └── main.tsx
│   ├── tailwind.config.js
│   └── vite.config.ts
│
└── nginx/
    └── nginx.conf
```

---

## Quick Start with Docker

> The compose file starts: Django (Gunicorn), Celery worker, Celery Beat scheduler, Redis, and Nginx.

```bash
# 1. Clone the repository
git clone <your-repo-url>
cd example

# 2. Copy and fill in environment variables
cp backend/.env.example backend/.env
# Edit backend/.env — set SECRET_KEY, DB credentials, REDIS_URL

# 3. Build and start all services
docker compose up --build

# 4. In a second terminal, run migrations and seed data
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py seed_merchants

# 5. Create the OAuth2 application (one-time)
docker compose exec backend python manage.py shell -c "
from django.contrib.auth.models import User
from oauth2_provider.models import Application
u = User.objects.filter(is_superuser=True).first()
Application.objects.get_or_create(
    client_id='mf82GXpuWIJ8ofg2dswRcivfztk0lbBCItFsfeCJ',
    defaults=dict(
        user=u,
        client_type='confidential',
        authorization_grant_type='password',
        name='example',
    )
)
print('OAuth app ready')
"
```

Frontend is served at `http://localhost` (port 80 via Nginx).  
API is available at `http://localhost/api/v1/`.

---

## Seeding Test Data

```bash
# Creates 2-3 merchants with seeded credit history
python manage.py seed_merchants
```

This creates the following test accounts:

| Email | Password | Starting Balance |
|---|---|---|
| arun1@example | password123 | ₹5,000 (500,000 paise) |
| priya2@example | password123 | ₹2,500 (250,000 paise) |
| vikram3@example | password123 | ₹10,000 (1,000,000 paise) |

Each merchant has a seeded `Ledger` credit history simulating past customer payments.

---

## API Reference

All authenticated endpoints require:
```
Authorization: Bearer <access_token>
```

### Auth

#### POST `/api/v1/auth/login/`
```json
// Request
{ "email": "arun1@example.com", "password": "merchant123" }

// Response 200
{
  "first_name": "Arun",
  "last_name": "One",
  "email": "merchant1@example.com",
  "access_token_life_time_in_seconds": 10800,
  "refresh_token_life_time_in_seconds": 3600,
  "access_token": "<token>",
  "refresh_token": "<token>"
}
```

### Merchant Registration

#### POST `/api/v1/merchant/`
```json
// Request
{
  "email": "new@example.com",
  "password": "secret123",
  "first_name": "Jane",
  "last_name": "Doe"
}
```

### Dashboard

#### GET `/api/v1/dashboard/`
```json
// Response 200
{
  "message": "Dashboard",
  "available_balance": 450000,
  "hold_balance": 50000,
  "name": "Merchant One",
  "email": "merchant1@example.com",
  "ledger_list": [...],
  "payout_list": [...]
}
```

### Payouts

#### POST `/api/v1/payout/request/`
```
Headers:
  Idempotency-Key: <uuid>
```
```json
// Request body
{ "amount_in_paise": 10000, "bank_account_id": "ACC123456" }

// Response 201 (first call)
{ "message": "Payout request received", "payout": 42 }

// Response 201 (duplicate idempotency key — same response returned)
{ "message": "Payout request received", "payout": 42 }
```

#### GET `/api/v1/payout/history/`
Returns the authenticated merchant's full payout history.

---

## Background Workers

Two Celery periodic tasks drive the payout lifecycle:

### `process_pending_payouts` — runs every 60 seconds
Picks up all `pending` payouts, transitions them to `processing`, and deducts the held amount from `available_balance_in_paise` on the Merchant row using a database-level F() expression inside an atomic transaction.

### `process_holdings_payouts` — runs every 10 seconds
Simulates bank settlement for all `processing` payouts:
- **70%** → transitions to `completed`, writes a `debit` entry to the Ledger
- **20%** → transitions to `failed`, refunds the amount back to merchant balance atomically
- **10%** → left in `processing` (simulates a bank hang); retry logic moves these to `failed` after 30 seconds with exponential backoff (max 3 attempts)

All state transitions happen inside `transaction.atomic()` blocks so a failed refund never leaves funds in limbo.

---

## Running Tests

```bash
cd backend

# Run all tests
python manage.py test

# Run specific test class
python manage.py test payout.tests.ConcurrencyTest
python manage.py test payout.tests.IdempotencyTest
```

The test suite covers:
- **Concurrency test** — two simultaneous 60-rupee payout requests against a 100-rupee balance. Exactly one must succeed.
- **Idempotency test** — the same `Idempotency-Key` submitted twice returns the identical response and creates only one payout row.

---

## Environment Variables

| Variable | Description | Default |
|---|---|---|
| `SECRET_KEY` | Django secret key | (set in settings.py) |
| `DEBUG` | Debug mode | `True` |
| `DATABASE_URL` | PostgreSQL connection string | SQLite fallback |
| `CELERY_BROKER_URL` | Redis URL | `redis://127.0.0.1:6379/0` |
| `CELERY_ENABLED` | Enable Celery processing | `False` |
| `OAUTH2_CLIENT_ID` | OAuth2 app client ID | (set in settings.py) |
| `OAUTH2_CLIENT_SECRET` | OAuth2 app client secret | (set in settings.py) |