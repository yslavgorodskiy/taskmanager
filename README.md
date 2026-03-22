# TaskManager API

[![CI](https://github.com/yslavgorodskiy/taskmanager/actions/workflows/ci.yml/badge.svg)](https://github.com/yslavgorodskiy/taskmanager/actions/workflows/ci.yml)

A production-ready task management REST API built with FastAPI and PostgreSQL.

## Features

- **JWT Authentication** — access + refresh token rotation
- **API Tokens** — long-lived tokens for integrations (`X-API-Token` header)
- **Tasks** — full CRUD with status tracking, priorities, due dates
- **Directions** — group tasks by project or area
- **Tags** — many-to-many labels with custom colors
- **Webhooks** — outgoing HTTP notifications with HMAC-SHA256 payload signing
- **Swagger UI** — auto-generated interactive docs at `/docs`
- **Alembic migrations** — versioned schema management
- **Docker Compose** — one-command local setup

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | FastAPI 0.115 |
| Database | PostgreSQL 16 (asyncpg) |
| ORM | SQLAlchemy 2.0 (async) |
| Migrations | Alembic |
| Auth | python-jose (JWT) + passlib (bcrypt) |
| HTTP client | httpx (webhook delivery) |
| Testing | pytest-asyncio + SQLite in-memory |

## Quick Start

### With Docker Compose

```bash
git clone https://github.com/yslavgorodskiy/taskmanager.git
cd taskmanager
cp .env.example .env          # set SECRET_KEY
docker compose up -d
```

### Without Docker

```bash
pip install -r requirements.txt

# Configure .env
cp .env.example .env
# Edit DATABASE_URL and SECRET_KEY

# Run migrations
alembic upgrade head

# Seed test data (optional)
python scripts/seed.py

# Start server
uvicorn app.main:app --reload
```

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | — | `postgresql+asyncpg://user:pass@host/db` |
| `SECRET_KEY` | — | Random secret, min 32 chars |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | JWT access token lifetime |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `7` | JWT refresh token lifetime |
| `DEBUG` | `false` | Enable SQLAlchemy query logging |
| `ALLOWED_ORIGINS` | `["*"]` | CORS allowed origins |

## API Overview

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/auth/register` | Create account |
| `POST` | `/auth/login` | Get JWT tokens |
| `POST` | `/auth/refresh` | Rotate refresh token |
| `GET` | `/users/me` | Current user profile |
| `POST` | `/tasks/` | Create task |
| `GET` | `/tasks/` | List tasks (filterable) |
| `PATCH` | `/tasks/{id}` | Update task |
| `DELETE` | `/tasks/{id}` | Delete task |
| `GET/POST` | `/directions/` | Manage directions |
| `GET/POST` | `/tags/` | Manage tags |
| `GET/POST` | `/webhooks/` | Manage webhooks |
| `POST` | `/webhooks/{id}/test` | Send test event |
| `GET` | `/webhooks/{id}/deliveries` | Delivery history |
| `POST` | `/api-tokens/` | Create API token |
| `POST` | `/api-tokens/{id}/revoke` | Revoke token |

Full interactive docs: **http://localhost:8000/docs**

## Authentication

All protected endpoints accept either:

```http
Authorization: Bearer <jwt_access_token>
```
```http
X-API-Token: tm_<api_token>
```

## Task Statuses & Priorities

```
Statuses:   new → in_progress → completed
                             → cancelled

Priorities: low | medium | high | urgent
```

## Webhook Events

| Event | Trigger |
|---|---|
| `task.created` | New task created |
| `task.updated` | Task fields changed |
| `task.status_changed` | Status transition |
| `task.deleted` | Task deleted |

Every delivery includes an `X-Webhook-Signature: sha256=<hmac>` header for verification.

Subscribe to all events with `"events": ["*"]`.

## Development

```bash
# Run tests
pytest tests/ -v

# New migration after model changes
alembic revision --autogenerate -m "description"
alembic upgrade head

# Seed test data
python scripts/seed.py           # add data
python scripts/seed.py --reset   # wipe and re-seed
```

### Test Accounts (after seeding)

| Email | Password | Role |
|---|---|---|
| alice@example.com | password123 | superuser |
| bob@example.com | password123 | user |
| carol@example.com | password123 | user |

## Project Structure

```
app/
├── main.py              # App entry point, CORS, router registration
├── config.py            # Settings (pydantic-settings)
├── database.py          # Async engine + session factory
├── models/              # SQLAlchemy ORM models
├── schemas/             # Pydantic request/response schemas
├── core/
│   ├── security.py      # JWT, bcrypt, HMAC signing
│   └── dependencies.py  # FastAPI auth dependencies
├── services/            # Business logic layer
└── routers/             # Route handlers
alembic/                 # Database migrations
scripts/
└── seed.py              # Test data seeder
tests/                   # pytest test suite
```
