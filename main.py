from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI

from database.database import init_db
from settings.config import settings
from settings.apps import register_routes
from settings.middleware import register_middleware


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    if settings.DB_CREATE_TABLES:
        await init_db()

    yield


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
