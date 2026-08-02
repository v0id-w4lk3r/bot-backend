import asyncio
from collections.abc import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from database.base import Base
from settings.config import settings

engine: AsyncEngine = create_async_engine(
    settings.DATABASE_URL,
    connect_args={"timeout": settings.DB_CONNECT_TIMEOUT},
    echo=settings.DB_ECHO,
    pool_pre_ping=True,
)

SessionLocal = async_sessionmaker(
    engine,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session


async def init_db() -> None:
    import database.models  # noqa: F401

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)


async def check_database() -> bool:
    async def _check() -> None:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))

    await asyncio.wait_for(_check(), timeout=settings.DB_CONNECT_TIMEOUT)
    return True


async def close_database() -> None:
    await engine.dispose()