from datetime import datetime
from typing import Any, Sequence
from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import (
    EscalatedPunishmentLog,
    TempbanRecord,
    WarningPunishmentConfig,
    WarningRecord,
)

# WARNINGS & ESCALATED PUNISHMENTS
async def get_user_warnings(
    db: AsyncSession, guild_id: int, user_id: int
) -> Sequence[WarningRecord]:
    """Fetch all warning records for a user in a specific guild."""
    stmt = (
        select(WarningRecord)
        .where(WarningRecord.guild_id == guild_id, WarningRecord.user_id == user_id)
        .order_by(WarningRecord.created_at.desc())
    )
    result = await db.execute(stmt)
    return result.scalars().all()


async def issue_warning_with_punishment(
    db: AsyncSession, guild_id: int, user_id: int, moderator_id: int, reason: str
) -> dict[str, Any]:
    """
    Issues a warning, counts total warnings for the user, checks if a punishment
    threshold is reached, and returns details on any triggered punishment.
    """
    # 1. Create the warning record
    warn = WarningRecord(
        guild_id=guild_id, user_id=user_id, moderator_id=moderator_id, reason=reason
    )
    db.add(warn)
    await db.flush()  # Populates warn.warn_id without committing yet

    # 2. Count total active warnings for this user in this guild
    count_stmt = select(func.count(WarningRecord.warn_id)).where(
        WarningRecord.guild_id == guild_id, WarningRecord.user_id == user_id
    )
    total_warns = (await db.execute(count_stmt)).scalar() or 0

    # 3. Check if there is a configured punishment rule for this count
    rule_stmt = select(WarningPunishmentConfig).where(
        WarningPunishmentConfig.guild_id == guild_id,
        WarningPunishmentConfig.warn_count == total_warns,
    )
    triggered_rule = (await db.execute(rule_stmt)).scalar_one_or_none()

    triggered_punishment = None

    if triggered_rule:
        triggered_punishment = {
            "punishment_type": triggered_rule.punishment_type,
            "duration_seconds": triggered_rule.duration_seconds,
            "warn_count": total_warns,
        }

        # Log the automated escalation event
        log_entry = EscalatedPunishmentLog(
            guild_id=guild_id,
            user_id=user_id,
            warn_count_at_trigger=total_warns,
            punishment_type=triggered_rule.punishment_type,
            details=f"Triggered by warning ID #{warn.warn_id}: '{reason}'",
        )
        db.add(log_entry)

    await db.commit()
    await db.refresh(warn)

    return {
        "warning": warn,
        "total_warnings": total_warns,
        "triggered_punishment": triggered_punishment,
    }


async def clear_user_warnings(
    db: AsyncSession, guild_id: int, user_id: int
) -> int:
    """Removes all warning records for a user in a specific guild."""
    stmt = delete(WarningRecord).where(
        WarningRecord.guild_id == guild_id, WarningRecord.user_id == user_id
    )
    result = await db.execute(stmt)
    await db.commit()
    return result.rowcount or 0


# PUNISHMENT RULE CONFIGURATIONS
async def get_punishment_configs(
    db: AsyncSession, guild_id: int
) -> Sequence[WarningPunishmentConfig]:
    """Fetch all configured warning punishment rules for a server."""
    stmt = (
        select(WarningPunishmentConfig)
        .where(WarningPunishmentConfig.guild_id == guild_id)
        .order_by(WarningPunishmentConfig.warn_count)
    )
    return (await db.execute(stmt)).scalars().all()


async def set_punishment_config(
    db: AsyncSession,
    guild_id: int,
    warn_count: int,
    punishment_type: str,
    duration_seconds: int | None = None,
) -> WarningPunishmentConfig:
    """Create or update a punishment threshold action."""
    stmt = select(WarningPunishmentConfig).where(
        WarningPunishmentConfig.guild_id == guild_id,
        WarningPunishmentConfig.warn_count == warn_count,
    )
    config = (await db.execute(stmt)).scalar_one_or_none()

    if not config:
        config = WarningPunishmentConfig(
            guild_id=guild_id,
            warn_count=warn_count,
            punishment_type=punishment_type,
            duration_seconds=duration_seconds,
        )
        db.add(config)
    else:
        config.punishment_type = punishment_type
        config.duration_seconds = duration_seconds

    await db.commit()
    await db.refresh(config)
    return config


async def delete_punishment_config(
    db: AsyncSession, guild_id: int, warn_count: int
) -> bool:
    """Delete a punishment threshold rule."""
    stmt = delete(WarningPunishmentConfig).where(
        WarningPunishmentConfig.guild_id == guild_id,
        WarningPunishmentConfig.warn_count == warn_count,
    )
    result = await db.execute(stmt)
    await db.commit()
    return (result.rowcount or 0) > 0


# TEMPBANS
async def create_tempban(
    db: AsyncSession,
    guild_id: int,
    user_id: int,
    moderator_id: int,
    expires_at: datetime,
    reason: str | None = None,
) -> TempbanRecord:
    """Create a new temporary ban entry."""
    record = TempbanRecord(
        guild_id=guild_id,
        user_id=user_id,
        moderator_id=moderator_id,
        expires_at=expires_at,
        tempban_reason=reason,
        active=True,
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record


async def get_active_tempbans(
    db: AsyncSession, guild_id: int
) -> Sequence[TempbanRecord]:
    """Fetch all currently active tempbans for a guild."""
    stmt = select(TempbanRecord).where(
        TempbanRecord.guild_id == guild_id,
        TempbanRecord.active == True,
    )
    return (await db.execute(stmt)).scalars().all()


async def get_expired_tempbans(
    db: AsyncSession, current_time: datetime
) -> Sequence[TempbanRecord]:
    """Fetch tempbans that are active but passed their expiration date."""
    stmt = select(TempbanRecord).where(
        TempbanRecord.active == True,
        TempbanRecord.expires_at <= current_time,
    )
    return (await db.execute(stmt)).scalars().all()


async def deactivate_tempban(db: AsyncSession, record_id: int) -> None:
    """Soft-delete/Deactivate a tempban record."""
    stmt = (
        update(TempbanRecord)
        .where(TempbanRecord.id == record_id)
        .values(active=False)
    )
    await db.execute(stmt)
    await db.commit()