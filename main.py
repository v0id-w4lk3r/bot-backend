from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from core.redis import close_redis
from database.database import close_database, init_db
from settings.apps import register_routes
from settings.config import settings
from settings.middleware import register_middleware


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # 1. Startup Logic
    if settings.DB_CREATE_TABLES:
        await init_db()

    yield

    # 2. Shutdown Cleanup Logic
    await close_database()
    await close_redis()


app = FastAPI(
    title="Discord Bot Panel API",
    version="0.1.0",
    lifespan=lifespan,
)

register_middleware(app)
register_routes(app)


@app.get("/")
async def root() -> dict[str, str]:
    return {
        "name": "Discord Bot Panel API",
        "version": "0.1.0",
        "environment": settings.ENV,
    }