from datetime import datetime
from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base


# Shared Timestamps Mixin (Timezone-Aware)
class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


# Core Guild Configuration Table 
class GuildConfig(Base, TimestampMixin):
    __tablename__ = "guild_config"

    guild_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    guild_name: Mapped[str] = mapped_column(String(100), nullable=False)
    prefix: Mapped[str] = mapped_column(String(5), nullable=False, server_default="!")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")

    def __repr__(self) -> str:
        return f"{self.guild_name} ({self.guild_id})"


# AFK System
class AFK(Base):
    __tablename__ = "afk"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    guild_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    afk_reason: Mapped[str] = mapped_column(String(256), nullable=False)
    since: Mapped[int] = mapped_column(BigInteger, nullable=False)  # BigInteger for UNIX timestamp seconds

    __table_args__ = (
        UniqueConstraint("guild_id", "user_id", name="pk_afk"),
        Index("idx_afk_guild_id", "guild_id"),
        Index("idx_afk_user_id", "user_id"),
    )

    def __repr__(self) -> str:
        return f"<AFK guild={self.guild_id} user={self.user_id}>"


# Bot Admin Roles Configuration
class AdminRole(Base):
    __tablename__ = "admin_roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    guild_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    role_id: Mapped[int] = mapped_column(BigInteger, nullable=False)

    __table_args__ = (
        UniqueConstraint("guild_id", "role_id", name="pk_admin_roles"),
        Index("idx_admin_roles_guild_id", "guild_id"),
    )

    def __repr__(self) -> str:
        return f"<AdminRole guild={self.guild_id} role={self.role_id}>"


# Media-Only Channel Configurations
class MediaOnlyChannel(Base, TimestampMixin):
    __tablename__ = "media_only_channels"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    guild_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    channel_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    sticky_message_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    whitelist_role_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    image_only: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false"
    )
    auto_mute: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    nsfw_bypass: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="true"
    )

    __table_args__ = (
        UniqueConstraint("guild_id", "channel_id", name="pk_media_only_channels"),
        Index("idx_media_only_channels_guild_id", "guild_id"),
    )


# Sticky Messages Configuration
class StickyMessage(Base, TimestampMixin):
    __tablename__ = "sticky_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    guild_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    channel_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    sticky_content: Mapped[str] = mapped_column(Text, nullable=False)
    last_message_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    counter: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")

    __table_args__ = (
        UniqueConstraint("guild_id", "channel_id", name="pk_sticky_messages"),
        CheckConstraint("counter >= 0", name="chk_sticky_counter"),
        Index("idx_sticky_messages_guild_id", "guild_id"),
    )


# Disabled Server Commands
class DisabledCommand(Base):
    __tablename__ = "disabled_commands"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    guild_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    command_name: Mapped[str] = mapped_column(String(64), nullable=False)

    __table_args__ = (
        UniqueConstraint("guild_id", "command_name", name="pk_disabled_commands"),
        Index("idx_disabled_commands_guild_id", "guild_id"),
    )


# Channel Restricted Commands
class RestrictedCommand(Base):
    __tablename__ = "restricted_commands"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    guild_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    channel_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    command_name: Mapped[str] = mapped_column(String(64), nullable=False)
    restriction_scope: Mapped[str] = mapped_column(
        Enum("allow", "deny", "both", name="restriction_scope_enum"),
        nullable=False,
        server_default="both",
    )

    __table_args__ = (
        UniqueConstraint(
            "guild_id", "channel_id", "command_name", name="pk_restricted_commands"
        ),
        Index("idx_restricted_commands_guild_id", "guild_id"),
    )


# Temporary Ban Configurations
class TempbanConfig(Base):
    __tablename__ = "tempban_config"

    guild_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    role_id: Mapped[int] = mapped_column(BigInteger, nullable=False)

    def __repr__(self) -> str:
        return f"<TempbanConfig guild={self.guild_id} role={self.role_id}>"


# Temporary Ban Execution Tracking
class TempbanRecord(Base, TimestampMixin):
    __tablename__ = "tempban_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    guild_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    moderator_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    tempban_reason: Mapped[str | None] = mapped_column(String(512), nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint("guild_id", "user_id", name="pk_tempban_records"),
        Index("idx_tempban_active_lookup", "guild_id", "active"),
        Index("idx_tempban_expiry", "expires_at"),
    )

    def __repr__(self) -> str:
        return f"<TempbanRecord guild={self.guild_id} user={self.user_id} active={self.active}>"


# Verification Configuration
class VerificationConfig(Base, TimestampMixin):
    __tablename__ = "verification_config"

    guild_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    verify_channel_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    log_channel_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    verified_role_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    unverified_role_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)


# Core System Moderation Logging Setup
class ModerationLogConfig(Base, TimestampMixin):
    __tablename__ = "moderation_log_config"

    guild_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    channel_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")

    def __repr__(self) -> str:
        return f"<ModerationLogConfig guild={self.guild_id} channel={self.channel_id}>"


# Channel Permission Lockdown Backups
class ChannelPermissionSnapshot(Base, TimestampMixin):
    __tablename__ = "channel_permission_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    guild_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    channel_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    target_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    permission_name: Mapped[str] = mapped_column(String(64), nullable=False)
    permission_value: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    __table_args__ = (
        UniqueConstraint(
            "guild_id",
            "channel_id",
            "target_id",
            "permission_name",
            name="pk_channel_perm_snapshots",
        ),
        Index("idx_channel_permission_snapshots_guild_id", "guild_id"),
    )


# Infraction Warnings System
class WarningRecord(Base, TimestampMixin):
    __tablename__ = "warnings"

    warn_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    guild_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    moderator_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    reason: Mapped[str] = mapped_column(
        String(512), nullable=False, server_default="No reason provided"
    )

    __table_args__ = (Index("idx_warning_guild_user", "guild_id", "user_id"),)

    def __repr__(self) -> str:
        return f"<WarningRecord id={self.warn_id} guild={self.guild_id} user={self.user_id}>"


# Autoresponder System
class Autoresponder(Base, TimestampMixin):
    __tablename__ = "autoresponders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    guild_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    trigger: Mapped[str] = mapped_column(String(256), nullable=False)
    response: Mapped[str] = mapped_column(Text, nullable=False)
    wildcard: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")

    __table_args__ = (
        UniqueConstraint("guild_id", "trigger", name="uq_guild_trigger"),
        Index("idx_autoresponder_guild", "guild_id"),
    )

    def __repr__(self) -> str:
        return f"<Autoresponder id={self.id} guild={self.guild_id} trigger='{self.trigger}'>"


# Welcome Announcements Configuration
class WelcomeConfig(Base, TimestampMixin):
    __tablename__ = "welcome_config"

    guild_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    channel_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    message: Mapped[str | None] = mapped_column(
        Text, nullable=True, server_default="Welcome {user} to {server}!"
    )
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    ping_user: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")


# Leave Announcements Configuration
class LeaveConfig(Base, TimestampMixin):
    __tablename__ = "leave_config"

    guild_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    channel_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    message: Mapped[str | None] = mapped_column(
        Text, nullable=True, server_default="{username} has left the server."
    )
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")


# Leveling Global Guild Parameters
class LevelingConfig(Base, TimestampMixin):
    __tablename__ = "leveling_config"

    guild_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    announcement_channel_id: Mapped[int | None] = mapped_column(
        BigInteger, nullable=True
    )
    level_up_message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        server_default="GG {user}, you just advanced to **Level {level}**!",
    )
    xp_cooldown: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="60"
    )
    min_xp_per_msg: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="15"
    )
    max_xp_per_msg: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="25"
    )


# Leveling Individual User Status Tracking
class UserLevel(Base, TimestampMixin):
    __tablename__ = "user_levels"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    guild_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    xp: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default="0")
    level: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    last_xp_gain: Mapped[int] = mapped_column(
        BigInteger, nullable=False, server_default="0"
    )

    __table_args__ = (
        UniqueConstraint("guild_id", "user_id", name="pk_user_levels"),
        Index("idx_leaderboard_rankings", "guild_id", "xp"),
    )

    def __repr__(self) -> str:
        return f"<UserLevel guild={self.guild_id} user={self.user_id} lvl={self.level}>"


# Warning Punishment Configuration Rules (e.g. 3 warns -> kick, 5 warns -> ban)
class WarningPunishmentConfig(Base, TimestampMixin):
    __tablename__ = "warning_punishment_configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    guild_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    warn_count: Mapped[int] = mapped_column(Integer, nullable=False)
    punishment_type: Mapped[str] = mapped_column(String(32), nullable=False)
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)

    __table_args__ = (
        UniqueConstraint("guild_id", "warn_count", name="uq_guild_warn_count"),
        Index("idx_warning_punishment_guild", "guild_id"),
    )

    def __repr__(self) -> str:
        return f"<WarningPunishmentConfig guild={self.guild_id} count={self.warn_count} action={self.punishment_type}>"


# Automated Punishment Audit Log
class EscalatedPunishmentLog(Base, TimestampMixin):
    __tablename__ = "escalated_punishment_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    guild_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    warn_count_at_trigger: Mapped[int] = mapped_column(Integer, nullable=False)
    punishment_type: Mapped[str] = mapped_column(String(32), nullable=False)
    details: Mapped[str | None] = mapped_column(String(512), nullable=True)

    __table_args__ = (Index("idx_escalated_logs_guild_user", "guild_id", "user_id"),)