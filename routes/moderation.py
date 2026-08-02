from datetime import datetime
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from database.database import get_db
from database.db_helpers.moderation import (
    clear_user_warnings,
    delete_punishment_config,
    get_punishment_configs,
    get_user_warnings,
    issue_warning_with_punishment,
    set_punishment_config,
)
from routes.guilds import get_current_user

router = APIRouter(prefix="/guilds/{guild_id}/moderation", tags=["moderation"])


class WarningCreate(BaseModel):
    user_id: int
    reason: str


class PunishmentRuleCreate(BaseModel):
    warn_count: int = Field(..., ge=1, description="Number of warnings required")
    punishment_type: str = Field(..., description="Action: mute, kick, tempban, ban")
    duration_seconds: int | None = Field(None, description="Optional duration in seconds")


# -------------------------------------------------------------------
# WARNINGS & AUTO-PUNISHMENT EXECUTION
# -------------------------------------------------------------------

@router.post("/warnings")
async def issue_warning(
    guild_id: int,
    payload: WarningCreate,
    db: AsyncSession = Depends(get_db),
    user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    """Issues a warning and evaluates if an automated punishment was triggered."""
    moderator_id = int(user["id"])
    
    result = await issue_warning_with_punishment(
        db=db,
        guild_id=guild_id,
        user_id=payload.user_id,
        moderator_id=moderator_id,
        reason=payload.reason,
    )

    warn_record = result["warning"]
    
    return {
        "status": "success",
        "warn_id": warn_record.warn_id,
        "total_warnings": result["total_warnings"],
        "triggered_punishment": result["triggered_punishment"],
    }


@router.delete("/warnings/{user_id}")
async def reset_warnings(
    guild_id: int,
    user_id: int,
    db: AsyncSession = Depends(get_db),
    user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    """Clears all warnings for a user in the server."""
    deleted_count = await clear_user_warnings(db, guild_id, user_id)
    return {"status": "success", "cleared_count": deleted_count}


# -------------------------------------------------------------------
# PUNISHMENT RULES CONFIGURATION (DASHBOARD)
# -------------------------------------------------------------------

@router.get("/punishment-rules")
async def list_punishment_rules(
    guild_id: int,
    db: AsyncSession = Depends(get_db),
    user: dict[str, Any] = Depends(get_current_user),
) -> list[dict[str, Any]]:
    """Fetch all warning punishment rules configured for this server."""
    rules = await get_punishment_configs(db, guild_id)
    return [
        {
            "id": r.id,
            "warn_count": r.warn_count,
            "punishment_type": r.punishment_type,
            "duration_seconds": r.duration_seconds,
        }
        for r in rules
    ]


@router.post("/punishment-rules")
async def create_or_update_punishment_rule(
    guild_id: int,
    payload: PunishmentRuleCreate,
    db: AsyncSession = Depends(get_db),
    user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    """Configure or update a warning threshold punishment rule."""
    if payload.punishment_type not in ["mute", "kick", "tempban", "ban"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid punishment_type. Must be: mute, kick, tempban, or ban.",
        )

    rule = await set_punishment_config(
        db=db,
        guild_id=guild_id,
        warn_count=payload.warn_count,
        punishment_type=payload.punishment_type,
        duration_seconds=payload.duration_seconds,
    )

    return {
        "status": "success",
        "rule_id": rule.id,
        "warn_count": rule.warn_count,
        "punishment_type": rule.punishment_type,
        "duration_seconds": rule.duration_seconds,
    }


@router.delete("/punishment-rules/{warn_count}")
async def remove_punishment_rule(
    guild_id: int,
    warn_count: int,
    db: AsyncSession = Depends(get_db),
    user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    """Delete a punishment rule for a specific warning count."""
    success = await delete_punishment_config(db, guild_id, warn_count)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No punishment rule found for that warning count.",
        )
    return {"status": "success", "message": f"Rule for {warn_count} warnings removed"}