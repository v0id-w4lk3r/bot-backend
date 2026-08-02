from typing import Any
import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from core.session import read_session_token
from database.database import get_db
from database.db_helpers.guild import (
    get_or_create_guild_config,
    update_guild_config,
)
from settings.config import settings

router = APIRouter(prefix="/guilds", tags=["guilds"])

# Permission bitwise flags (ADMINISTRATOR = 0x8, MANAGE_GUILD = 0x20)
MANAGE_GUILD_PERM = 0x20
ADMINISTRATOR_PERM = 0x8


def get_current_user(request: Request) -> dict[str, Any]:
    token = request.cookies.get(settings.SESSION_COOKIE_NAME)
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    session = read_session_token(token)
    if not session or "user" not in session:
        raise HTTPException(status_code=401, detail="Invalid session")
    return session["user"]


@router.get("")
async def get_user_guilds(
    user: dict[str, Any] = Depends(get_current_user)
) -> list[dict[str, Any]]:
    """Returns servers where user has Manage Guild/Admin permissions."""
    access_token = user["access_token"]

    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://discord.com/api/v10/users/@me/guilds",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if resp.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to fetch user guilds")

        user_guilds = resp.json()

    manageable_guilds = []
    for g in user_guilds:
        perms = int(g.get("permissions", 0))
        is_admin = (perms & ADMINISTRATOR_PERM) == ADMINISTRATOR_PERM
        is_manager = (perms & MANAGE_GUILD_PERM) == MANAGE_GUILD_PERM

        if is_admin or is_manager or g.get("owner", False):
            manageable_guilds.append(
                {
                    "id": g["id"],
                    "name": g["name"],
                    "icon": g["icon"],
                    "owner": g.get("owner", False),
                }
            )

    return manageable_guilds


@router.get("/{guild_id}/config")
async def get_guild_settings(
    guild_id: int,
    db: AsyncSession = Depends(get_db),
    user: dict[str, Any] = Depends(get_current_user)
) -> dict[str, Any]:
    """Fetch panel configurations for a single server using DB helper."""
    config = await get_or_create_guild_config(db, guild_id)

    return {
        "guild_id": config.guild_id,
        "guild_name": config.guild_name,
        "prefix": config.prefix,
        "is_active": config.is_active
    }


@router.post("/{guild_id}/prefix")
async def update_guild_prefix(
    guild_id: int,
    new_prefix: str,
    db: AsyncSession = Depends(get_db),
    user: dict[str, Any] = Depends(get_current_user)
) -> dict[str, Any]:
    """Updates server prefix in DB and triggers Redis sync via DB helper."""
    if len(new_prefix) > 5:
        raise HTTPException(status_code=400, detail="Prefix too long (max 5 chars)")

    config = await update_guild_config(db, guild_id, prefix=new_prefix)

    return {
        "status": "success",
        "guild_id": config.guild_id,
        "prefix": config.prefix,
    }