# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

TaskManager is an async FastAPI REST API for task management with JWT/API-token auth, webhooks, and PostgreSQL storage. All database operations use async SQLAlchemy 2.0 with asyncpg.

## Common Commands

```bash
# Run all tests (uses in-memory SQLite, no DB needed)
DATABASE_URL=sqlite+aiosqlite:///:memory: SECRET_KEY=test-secret \
  pytest tests/ -v --tb=short --cov=app --cov-report=term-missing

# Run a single test
DATABASE_URL=sqlite+aiosqlite:///:memory: SECRET_KEY=test-secret \
  pytest tests/test_tasks.py::test_create_task -v

# Lint
ruff check app/ scripts/ tests/

# Start with Docker Compose
docker compose up -d

# Start without Docker (requires PostgreSQL running, .env configured)
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Run Alembic migrations
alembic upgrade head

# Create new migration after model changes
alembic revision --autogenerate -m "description"

# Seed database
python -m scripts.seed
```

## Architecture

Layered async architecture with strict owner isolation (multi-tenant by owner_id):

```
Routers (app/routers/)  →  Services (app/services/)  →  Models (app/models/)
   ↕                           ↕                            ↕
Schemas (app/schemas/)    Core (app/core/)             Database (app/database.py)
```

- **Routers**: FastAPI endpoints, dependency injection, request validation. All protected routes use `Depends(get_current_active_user)`.
- **Services**: Business logic classes instantiated per-request with `db` session and `background_tasks`. Handle CRUD, validation, and webhook event firing.
- **Models**: SQLAlchemy ORM with `DeclarativeBase`. All have `created_at`/`updated_at` server defaults. Task uses `TaskStatus`/`TaskPriority` enums.
- **Schemas**: Pydantic v2 models with `from_attributes=True` for ORM serialization. Separate Create/Update/Response schemas per entity.
- **Core**: `security.py` (JWT, bcrypt, HMAC, API token generation), `dependencies.py` (auth via JWT or X-API-Token header with fallback chain).

## Auth System

Dual auth: JWT Bearer tokens (access + refresh) and API tokens (X-API-Token header). The `get_current_user` dependency tries JWT first, then falls back to API key lookup. API tokens are stored as SHA-256 hashes with a `tm_` prefix.

## Webhook System

Services fire webhook events (`task.created`, `task.updated`, `task.status_changed`, `task.deleted`) via FastAPI `BackgroundTasks`. Payloads are HMAC-SHA256 signed. Delivery results are stored in `WebhookDelivery`.

## Testing

- **Framework**: pytest with pytest-asyncio (auto mode)
- **Database**: In-memory SQLite via aiosqlite (no external DB needed). Requires `aiosqlite` package (not in requirements.txt, installed separately in CI).
- **Fixtures** (tests/conftest.py): `client` (AsyncClient with ASGI transport), `auth_headers` (registers+logs in a user, returns Bearer header dict), `db_session`, `clean_tables` (autouse, truncates all tables between tests).
- **Pattern**: `dispatch_webhook_event` is patched as AsyncMock in the client fixture so webhook HTTP calls don't fire during tests.
- **Helper**: `_register_and_login(client, email)` in conftest.py — registers a user and returns token JSON. The `auth_headers` fixture wraps this to return a ready-to-use Bearer header dict.
- **CI requirement**: 90% code coverage minimum (`--cov-fail-under=90`). CI tests on Python 3.11 and 3.12.

## Per-User Settings

The User model has a `column_settings` JSON column storing task list display preferences (visible columns, min/max widths). Endpoints: `GET/PUT /users/me/column-settings`. Schema: `ColumnSettingsSchema` with `visible: list[str]` and `widths: dict[str, ColumnWidthConfig]`. Default for new users: show only the title column.

## Saved Views

CRUD at `/saved-views/` — stores named filter/sort/display presets as a JSON `settings` column on the `SavedView` model. Unlike other entities, this router does inline DB queries (no service layer). Owner-isolated like everything else.

## Key Conventions

- All queries filter by `owner_id` — never return data across users.
- Task relationships (direction, tags) are eagerly loaded via `selectinload`/`joinedload` in service `_fetch` methods.
- Tags use a many-to-many association table (`task_tags`).
- Direction deletion sets `direction_id=NULL` on tasks (SET NULL FK).
- Pydantic settings loaded from `.env` file; `SECRET_KEY` has a placeholder default (`"change-me"`) — must be overridden in production.
- User preferences stored as JSON columns on the User model (not separate tables).
