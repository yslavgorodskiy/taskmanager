"""
Seed script — populates the database with realistic test data.

Usage:
    python scripts/seed.py
    python scripts/seed.py --reset   # drop all rows before seeding
"""

import asyncio
import argparse
import sys
from pathlib import Path

# Allow running from project root
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import generate_api_token, generate_webhook_secret, hash_password
from app.database import AsyncSessionLocal
from app.models.api_token import APIToken
from app.models.direction import Direction
from app.models.tag import Tag, task_tags
from app.models.task import Task, TaskPriority, TaskStatus
from app.models.user import User
from app.models.webhook import Webhook

# ---------------------------------------------------------------------------
# Seed data definitions
# ---------------------------------------------------------------------------

USERS = [
    {
        "email": "alice@example.com",
        "password": "password123",
        "full_name": "Alice Johnson",
        "is_superuser": True,
    },
    {
        "email": "bob@example.com",
        "password": "password123",
        "full_name": "Bob Smith",
    },
    {
        "email": "carol@example.com",
        "password": "password123",
        "full_name": "Carol White",
    },
]

DIRECTIONS = [
    {"name": "Backend",    "color": "#6366f1", "description": "Server-side development tasks"},
    {"name": "Frontend",   "color": "#f59e0b", "description": "UI and client-side work"},
    {"name": "DevOps",     "color": "#10b981", "description": "Infrastructure and CI/CD"},
    {"name": "Design",     "color": "#ec4899", "description": "UX/UI design tasks"},
    {"name": "Management", "color": "#8b5cf6", "description": "Planning and coordination"},
]

TAGS = [
    {"name": "bug",       "color": "#ef4444"},
    {"name": "feature",   "color": "#3b82f6"},
    {"name": "docs",      "color": "#6b7280"},
    {"name": "refactor",  "color": "#f97316"},
    {"name": "security",  "color": "#dc2626"},
    {"name": "performance","color": "#0ea5e9"},
    {"name": "urgent",    "color": "#b45309"},
    {"name": "good-first-issue", "color": "#84cc16"},
]

TASKS = [
    {
        "title": "Set up CI/CD pipeline",
        "description": "Configure GitHub Actions for automated testing and deployment.",
        "status": TaskStatus.IN_PROGRESS,
        "priority": TaskPriority.HIGH,
        "direction": "DevOps",
        "tags": ["feature", "docs"],
    },
    {
        "title": "Fix login page redirect bug",
        "description": "After successful login, users are redirected to /home instead of /dashboard.",
        "status": TaskStatus.NEW,
        "priority": TaskPriority.URGENT,
        "direction": "Frontend",
        "tags": ["bug", "urgent"],
    },
    {
        "title": "Implement JWT refresh token rotation",
        "description": "Rotate refresh tokens on each use to limit token theft window.",
        "status": TaskStatus.COMPLETED,
        "priority": TaskPriority.HIGH,
        "direction": "Backend",
        "tags": ["security", "feature"],
    },
    {
        "title": "Optimize slow database queries",
        "description": "Several list endpoints take >500 ms. Add missing indexes and review N+1 queries.",
        "status": TaskStatus.IN_PROGRESS,
        "priority": TaskPriority.HIGH,
        "direction": "Backend",
        "tags": ["performance", "refactor"],
    },
    {
        "title": "Design onboarding flow mockups",
        "description": "Create Figma mockups for the 3-step user onboarding wizard.",
        "status": TaskStatus.NEW,
        "priority": TaskPriority.MEDIUM,
        "direction": "Design",
        "tags": ["feature"],
    },
    {
        "title": "Write API documentation",
        "description": "Document all public endpoints with request/response examples in the README.",
        "status": TaskStatus.NEW,
        "priority": TaskPriority.MEDIUM,
        "direction": "Backend",
        "tags": ["docs"],
    },
    {
        "title": "Add rate limiting to auth endpoints",
        "description": "Protect /auth/login and /auth/register from brute-force attacks.",
        "status": TaskStatus.NEW,
        "priority": TaskPriority.HIGH,
        "direction": "Backend",
        "tags": ["security", "feature"],
    },
    {
        "title": "Migrate CSS to Tailwind v4",
        "description": "Update all component styles from Tailwind v3 utility classes.",
        "status": TaskStatus.CANCELLED,
        "priority": TaskPriority.LOW,
        "direction": "Frontend",
        "tags": ["refactor"],
    },
    {
        "title": "Set up log aggregation (Loki + Grafana)",
        "description": "Centralise application logs for easier debugging in production.",
        "status": TaskStatus.NEW,
        "priority": TaskPriority.MEDIUM,
        "direction": "DevOps",
        "tags": ["feature", "docs"],
    },
    {
        "title": "Add dark mode support",
        "description": "Implement system-preference-aware dark/light theme switching.",
        "status": TaskStatus.IN_PROGRESS,
        "priority": TaskPriority.LOW,
        "direction": "Frontend",
        "tags": ["feature", "good-first-issue"],
    },
    {
        "title": "Refactor task service layer",
        "description": "Extract duplicated validation logic into reusable helpers.",
        "status": TaskStatus.NEW,
        "priority": TaskPriority.MEDIUM,
        "direction": "Backend",
        "tags": ["refactor", "good-first-issue"],
    },
    {
        "title": "Quarterly roadmap planning",
        "description": "Prepare Q3 roadmap slides for the stakeholder review meeting.",
        "status": TaskStatus.COMPLETED,
        "priority": TaskPriority.HIGH,
        "direction": "Management",
        "tags": ["docs"],
    },
]

WEBHOOKS = [
    {
        "name": "Slack notifications",
        "url": "https://hooks.slack.com/services/test/webhook",
        "events": ["task.created", "task.status_changed"],
    },
    {
        "name": "All events logger",
        "url": "https://webhook.site/test-endpoint",
        "events": ["*"],
    },
]

API_TOKENS = [
    {"name": "CI/CD pipeline token"},
    {"name": "Mobile app token"},
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def reset_tables(db: AsyncSession) -> None:
    print("  Resetting tables...")
    # Delete in reverse FK order
    await db.execute(delete(task_tags))
    for model in (Task, APIToken, Webhook, Tag, Direction, User):
        await db.execute(delete(model))
    await db.commit()
    print("  Tables cleared.")


async def seed(db: AsyncSession) -> None:
    # ---- Users ----
    print("  Creating users...")
    users: list[User] = []
    for u in USERS:
        user = User(
            email=u["email"],
            hashed_password=hash_password(u["password"]),
            full_name=u["full_name"],
            is_superuser=u.get("is_superuser", False),
        )
        db.add(user)
        users.append(user)
    await db.flush()

    alice = users[0]

    # ---- Directions (owned by alice) ----
    print("  Creating directions...")
    direction_map: dict[str, Direction] = {}
    for d in DIRECTIONS:
        direction = Direction(owner_id=alice.id, **d)
        db.add(direction)
        direction_map[d["name"]] = direction
    await db.flush()

    # ---- Tags (owned by alice) ----
    print("  Creating tags...")
    tag_map: dict[str, Tag] = {}
    for t in TAGS:
        tag = Tag(owner_id=alice.id, **t)
        db.add(tag)
        tag_map[t["name"]] = tag
    await db.flush()

    # ---- Tasks (owned by alice) ----
    print("  Creating tasks...")
    for t in TASKS:
        task = Task(
            title=t["title"],
            description=t.get("description"),
            status=t["status"],
            priority=t["priority"],
            owner_id=alice.id,
            direction_id=direction_map[t["direction"]].id,
            tags=[tag_map[name] for name in t.get("tags", [])],
        )
        db.add(task)
    await db.flush()

    # ---- Webhooks (owned by alice) ----
    print("  Creating webhooks...")
    for w in WEBHOOKS:
        webhook = Webhook(
            owner_id=alice.id,
            secret=generate_webhook_secret(),
            **w,
        )
        db.add(webhook)
    await db.flush()

    # ---- API Tokens (owned by alice) ----
    print("  Creating API tokens...")
    for a in API_TOKENS:
        raw, token_hash, prefix = generate_api_token()
        api_token = APIToken(
            owner_id=alice.id,
            name=a["name"],
            token_hash=token_hash,
            prefix=prefix,
        )
        db.add(api_token)
        print(f"    [{a['name']}]  token: {raw}")
    await db.flush()

    await db.commit()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

async def main(reset: bool) -> None:
    print("Connecting to database...")
    async with AsyncSessionLocal() as db:
        if reset:
            await reset_tables(db)

        print("Seeding data...")
        await seed(db)

    print("\nDone! Test credentials:")
    for u in USERS:
        role = " (superuser)" if u.get("is_superuser") else ""
        print(f"  {u['email']}  /  {u['password']}{role}")
    print(f"\n  {len(TASKS)} tasks · {len(DIRECTIONS)} directions · {len(TAGS)} tags")
    print(f"  {len(WEBHOOKS)} webhooks · {len(API_TOKENS)} API tokens")
    print("\nSwagger UI: http://localhost:8000/docs")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed the TaskManager database.")
    parser.add_argument("--reset", action="store_true", help="Clear existing data before seeding")
    args = parser.parse_args()

    asyncio.run(main(reset=args.reset))
