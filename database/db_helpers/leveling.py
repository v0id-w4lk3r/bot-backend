from typing import Sequence
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import LevelingConfig, UserLevel

async def get_or_create_leveling_config(
    db: AsyncSession, guild_id: int
) -> LevelingConfig:
    result = await db.execute(
        select(LevelingConfig).where(LevelingConfig.guild_id == guild_id)
    )
    config = result.scalar_one_or_none()
    if not config:
        config = LevelingConfig(guild_id=guild_id)
        db.add(config)
        await db.commit()
        await db.refresh(config)
    return config

async def get_user_level(
    db: AsyncSession, guild_id: int, user_id: int
) -> UserLevel:
    result = await db.execute(
        select(UserLevel).where(
            UserLevel.guild_id == guild_id, UserLevel.user_id == user_id
        )
    )
    user = result.scalar_one_or_none()
    if not user:
        user = UserLevel(guild_id=guild_id, user_id=user_id, xp=0, level=0)
        db.add(user)
        await db.commit()
        await db.refresh(user)
    return user

async def get_leaderboard(
    db: AsyncSession, guild_id: int, limit: int = 10, offset: int = 0
) -> Sequence[UserLevel]:
    result = await db.execute(
        select(UserLevel)
        .where(UserLevel.guild_id == guild_id)
        .order_by(desc(UserLevel.xp))
        .offset(offset)
        .limit(limit)
    )
    return result.scalars().all()