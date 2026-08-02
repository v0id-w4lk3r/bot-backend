from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any

from database.database import get_db
from database.db_helpers.afk import set_afk, remove_afk, get_afk_status
from routes.guilds import get_current_user

router = APIRouter(prefix="/guilds/{guild_id}/afk", tags=["afk"])


@router.get("/{user_id}")
async def fetch_user_afk(
    guild_id: int,
    user_id: int,
    db: AsyncSession = Depends(get_db),
    user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    """Fetch AFK status for a specific user in a guild."""
    afk_entry = await get_afk_status(db, guild_id, user_id)
    if not afk_entry:
        return {"is_afk": False, "guild_id": guild_id, "user_id": user_id}

    return {
        "is_afk": True,
        "guild_id": afk_entry.guild_id,
        "user_id": afk_entry.user_id,
        "reason": afk_entry.afk_reason,
        "since": afk_entry.since,
    }


@router.post("/{user_id}")
async def create_or_update_afk(
    guild_id: int,
    user_id: int,
    reason: str,
    db: AsyncSession = Depends(get_db),
    user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    """Set or update AFK status from the dashboard."""
    afk_entry = await set_afk(db, guild_id, user_id, reason)
    return {
        "status": "success",
        "user_id": afk_entry.user_id,
        "reason": afk_entry.afk_reason,
        "since": afk_entry.since,
    }


@router.delete("/{user_id}")
async def clear_afk(
    guild_id: int,
    user_id: int,
    db: AsyncSession = Depends(get_db),
    user: dict[str, Any] = Depends(get_current_user)
) -> dict[str, Any]:
    """Remove AFK status for a user."""
    removed = await remove_afk(db, guild_id, user_id)
    if not removed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User is not currently AFK"
        )
    return {"status": "success", "message": "AFK status cleared"}