from typing import Sequence
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import Autoresponder

async def get_autoresponders(
    db: AsyncSession, guild_id: int
) -> Sequence[Autoresponder]:
    result = await db.execute(
        select(Autoresponder).where(Autoresponder.guild_id == guild_id)
    )
    return result.scalars().all()

async def create_or_update_autoresponder(
    db: AsyncSession, guild_id: int, trigger: str, response: str, wildcard: bool = False
) -> Autoresponder:
    trigger_clean = trigger.strip().lower()
    result = await db.execute(
        select(Autoresponder).where(
            Autoresponder.guild_id == guild_id,
            Autoresponder.trigger == trigger_clean,
        )
    )
    item = result.scalar_one_or_none()
    if not item:
        item = Autoresponder(
            guild_id=guild_id, trigger=trigger_clean, response=response, wildcard=wildcard
        )
        db.add(item)
    else:
        item.response = response
        item.wildcard = wildcard

    await db.commit()
    await db.refresh(item)
    return item

async def delete_autoresponder(
    db: AsyncSession, guild_id: int, autoresponder_id: int
) -> bool:
    result = await db.execute(
        delete(Autoresponder).where(
            Autoresponder.guild_id == guild_id,
            Autoresponder.id == autoresponder_id,
        )
    )
    await db.commit()
    return (result.rowcount or 0) > 0