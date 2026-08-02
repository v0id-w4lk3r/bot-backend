from typing import Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import LeaveConfig, WelcomeConfig

# Welcome Config
async def get_or_create_welcome_config(
    db: AsyncSession, guild_id: int
) -> WelcomeConfig:
    result = await db.execute(select(WelcomeConfig).where(WelcomeConfig.guild_id == guild_id))
    config = result.scalar_one_or_none()
    if not config:
        config = WelcomeConfig(guild_id=guild_id)
        db.add(config)
        await db.commit()
        await db.refresh(config)
    return config

async def update_welcome_config(
    db: AsyncSession, guild_id: int, **kwargs: Any
) -> WelcomeConfig:
    config = await get_or_create_welcome_config(db, guild_id)
    for key, value in kwargs.items():
        if hasattr(config, key) and value is not None:
            setattr(config, key, value)
    await db.commit()
    await db.refresh(config)
    return config

# Leave Config
async def get_or_create_leave_config(
    db: AsyncSession, guild_id: int
) -> LeaveConfig:
    result = await db.execute(select(LeaveConfig).where(LeaveConfig.guild_id == guild_id))
    config = result.scalar_one_or_none()
    if not config:
        config = LeaveConfig(guild_id=guild_id)
        db.add(config)
        await db.commit()
        await db.refresh(config)
    return config

async def update_leave_config(
    db: AsyncSession, guild_id: int, **kwargs: Any
) -> LeaveConfig:
    config = await get_or_create_leave_config(db, guild_id)
    for key, value in kwargs.items():
        if hasattr(config, key) and value is not None:
            setattr(config, key, value)
    await db.commit()
    await db.refresh(config)
    return config