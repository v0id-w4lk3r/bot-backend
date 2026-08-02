import json
from typing import Any, Sequence
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.redis import redis_client
from database.models import (
    DisabledCommand,
    GuildConfig,
    MediaOnlyChannel,
    RestrictedCommand,
    StickyMessage,
)

# -------------------------------------------------------------------
# CORE GUILD CONFIG
# -------------------------------------------------------------------

async def get_or_create_guild_config(
    db: AsyncSession, guild_id: int, guild_name: str = "Unknown Guild"
) -> GuildConfig:
    """Fetch guild config or create default entry if it does not exist."""
    result = await db.execute(select(GuildConfig).where(GuildConfig.guild_id == guild_id))
    config = result.scalar_one_or_none()

    if not config:
        config = GuildConfig(guild_id=guild_id, guild_name=guild_name)
        db.add(config)
        await db.commit()
        await db.refresh(config)

    return config


async def update_guild_config(
    db: AsyncSession, guild_id: int, **updates: Any
) -> GuildConfig:
    """Update primary guild fields and notify the bot via Redis Pub/Sub."""
    config = await get_or_create_guild_config(db, guild_id)

    for field, value in updates.items():
        if hasattr(config, field) and value is not None:
            setattr(config, field, value)

    await db.commit()
    await db.refresh(config)

    # Notify bot of real-time update
    await redis_client.publish(
        "bot_config_update",
        json.dumps({"guild_id": guild_id, "event": "guild_config_updated"}),
    )

    return config


# -------------------------------------------------------------------
# MEDIA-ONLY CHANNELS
# -------------------------------------------------------------------

async def get_media_only_channels(
    db: AsyncSession, guild_id: int
) -> Sequence[MediaOnlyChannel]:
    """Fetch all media-only configured channels for a guild."""
    result = await db.execute(
        select(MediaOnlyChannel).where(MediaOnlyChannel.guild_id == guild_id)
    )
    return result.scalars().all()


async def add_or_update_media_channel(
    db: AsyncSession, guild_id: int, channel_id: int, **kwargs: Any
) -> MediaOnlyChannel:
    """Add or update media-only rules for a specific channel."""
    result = await db.execute(
        select(MediaOnlyChannel).where(
            MediaOnlyChannel.guild_id == guild_id,
            MediaOnlyChannel.channel_id == channel_id,
        )
    )
    channel_cfg = result.scalar_one_or_none()

    if not channel_cfg:
        channel_cfg = MediaOnlyChannel(guild_id=guild_id, channel_id=channel_id)
        db.add(channel_cfg)

    for field, value in kwargs.items():
        if hasattr(channel_cfg, field) and value is not None:
            setattr(channel_cfg, field, value)

    await db.commit()
    await db.refresh(channel_cfg)
    return channel_cfg


async def delete_media_channel(db: AsyncSession, guild_id: int, channel_id: int) -> bool:
    """Remove a channel from media-only restrictions."""
    result = await db.execute(
        delete(MediaOnlyChannel).where(
            MediaOnlyChannel.guild_id == guild_id,
            MediaOnlyChannel.channel_id == channel_id,
        )
    )
    await db.commit()
    return (result.rowcount or 0) > 0


# -------------------------------------------------------------------
# STICKY MESSAGES
# -------------------------------------------------------------------

async def get_sticky_messages(db: AsyncSession, guild_id: int) -> Sequence[StickyMessage]:
    """Fetch all sticky message configurations for a guild."""
    result = await db.execute(
        select(StickyMessage).where(StickyMessage.guild_id == guild_id)
    )
    return result.scalars().all()


async def set_sticky_message(
    db: AsyncSession, guild_id: int, channel_id: int, sticky_content: str
) -> StickyMessage:
    """Create or update a sticky message for a channel."""
    result = await db.execute(
        select(StickyMessage).where(
            StickyMessage.guild_id == guild_id,
            StickyMessage.channel_id == channel_id,
        )
    )
    sticky = result.scalar_one_or_none()

    if not sticky:
        sticky = StickyMessage(
            guild_id=guild_id, channel_id=channel_id, sticky_content=sticky_content
        )
        db.add(sticky)
    else:
        sticky.sticky_content = sticky_content

    await db.commit()
    await db.refresh(sticky)
    return sticky


async def remove_sticky_message(db: AsyncSession, guild_id: int, channel_id: int) -> bool:
    """Remove a sticky message from a channel."""
    result = await db.execute(
        delete(StickyMessage).where(
            StickyMessage.guild_id == guild_id,
            StickyMessage.channel_id == channel_id,
        )
    )
    await db.commit()
    return (result.rowcount or 0) > 0


# DISABLED COMMANDS
async def get_disabled_commands(db: AsyncSession, guild_id: int) -> Sequence[str]:
    """Fetch list of disabled command names in a guild."""
    result = await db.execute(
        select(DisabledCommand.command_name).where(
            DisabledCommand.guild_id == guild_id
        )
    )
    return result.scalars().all()


async def toggle_disabled_command(
    db: AsyncSession, guild_id: int, command_name: str, disable: bool
) -> bool:
    """Disable or re-enable a command server-wide."""
    cmd_name = command_name.strip().lower()

    if disable:
        # Check if already disabled
        result = await db.execute(
            select(DisabledCommand).where(
                DisabledCommand.guild_id == guild_id,
                DisabledCommand.command_name == cmd_name,
            )
        )
        if not result.scalar_one_or_none():
            entry = DisabledCommand(guild_id=guild_id, command_name=cmd_name)
            db.add(entry)
            await db.commit()
        return True
    else:
        result = await db.execute(
            delete(DisabledCommand).where(
                DisabledCommand.guild_id == guild_id,
                DisabledCommand.command_name == cmd_name,
            )
        )
        await db.commit()
        return False