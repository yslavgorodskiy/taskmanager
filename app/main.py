from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import api_tokens, auth, directions, tags, tasks, users, webhooks

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "Task management API with JWT authentication, API token support, "
        "directions, tags, and webhook notifications."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(tasks.router)
app.include_router(directions.router)
app.include_router(tags.router)
app.include_router(api_tokens.router)
app.include_router(webhooks.router)


@app.get("/health", tags=["System"], summary="Health check")
async def health() -> dict:
    return {"status": "ok", "version": settings.APP_VERSION}
