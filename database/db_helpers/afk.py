import time
from typing import Sequence
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import AFK


async def get_afk_status(
    db: AsyncSession, guild_id: int, user_id: int
) -> AFK | None:
    """Fetch active AFK status for a user in a guild."""
    result = await db.execute(
        select(AFK).where(AFK.guild_id == guild_id, AFK.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def set_afk(
    db: AsyncSession, guild_id: int, user_id: int, reason: str
) -> AFK:
    """Set or update AFK status for a user."""
    afk_entry = await get_afk_status(db, guild_id, user_id)

    now_timestamp = int(time.time())
    if not afk_entry:
        afk_entry = AFK(
            guild_id=guild_id, user_id=user_id, afk_reason=reason, since=now_timestamp
        )
        db.add(afk_entry)
    else:
        afk_entry.afk_reason = reason
        afk_entry.since = now_timestamp

    await db.commit()
    await db.refresh(afk_entry)
    return afk_entry


async def remove_afk(db: AsyncSession, guild_id: int, user_id: int) -> bool:
    """Remove AFK status for a user."""
    result = await db.execute(
        delete(AFK).where(AFK.guild_id == guild_id, AFK.user_id == user_id)
    )
    await db.commit()
    return (result.rowcount or 0) > 0