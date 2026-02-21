from __future__ import annotations

import discord
import config
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from utils.logger import logger

if TYPE_CHECKING:
    from discord.ext import commands
    from database.base import DatabaseBase


class BotLogger:
    """Posts structured embed log messages to a guild's log channel."""

    def __init__(self, bot: commands.Bot, db: DatabaseBase):
        self.bot = bot
        self.db = db

    # ─────────────────────────────────────────────────────────────
    #  Internal helper
    # ─────────────────────────────────────────────────────────────

    async def _send(self, guild: discord.Guild, embed: discord.Embed) -> None:
        """
        Resolve the log channel for `guild` and post `embed`.
        Silently no-ops if no log channel is configured or posting fails.
        """
        try:
            settings = await self.db.get_guild_settings(guild.id)
            log_channel_id: int | None = settings.get("log_channel_id")
            if not log_channel_id:
                return

            channel = guild.get_channel(log_channel_id)
            if channel is None:
                channel = await self.bot.fetch_channel(log_channel_id)

            await channel.send(embed=embed)  # type: ignore[union-attr]
        except Exception as exc:
            logger.warning(f"BotLogger._send failed for guild {guild.id}: {exc}")

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    # ─────────────────────────────────────────────────────────────
    #  Log events
    # ─────────────────────────────────────────────────────────────

    async def enrolled(
        self,
        guild: discord.Guild,
        user: discord.Member | discord.User,
        enrollment_id: str,
        channel: discord.TextChannel,
    ) -> None:
        """User successfully enrolled."""
        embed = discord.Embed(
            title="User Enrolled",
            color=config.EMBED_COLOR,
            timestamp=datetime.now(timezone.utc),
        )
        embed.add_field(name="User", value=f"{user.mention} (`{user.id}`)", inline=True)
        embed.add_field(name="Enrollment ID", value=f"`{enrollment_id}`", inline=True)
        embed.add_field(name="Training Channel", value=channel.mention, inline=True)
        embed.set_footer(text=self._now())
        await self._send(guild, embed)

    async def enrollment_failed(
        self,
        guild: discord.Guild,
        user: discord.Member | discord.User,
        reason: str,
    ) -> None:
        """Enrollment attempt failed (bad code, already enrolled, etc.)."""
        embed = discord.Embed(
            title="Enrollment Failed",
            color=config.EMBED_COLOR,
            timestamp=datetime.now(timezone.utc),
        )
        embed.add_field(name="User", value=f"{user.mention} (`{user.id}`)", inline=True)
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.set_footer(text=self._now())
        await self._send(guild, embed)

    async def day_complete(
        self,
        guild: discord.Guild,
        user: discord.Member | discord.User,
        day: int,
    ) -> None:
        """User completed a training day."""
        embed = discord.Embed(
            title=f"Day {day} Completed",
            color=config.EMBED_COLOR,
            timestamp=datetime.now(timezone.utc),
        )
        embed.add_field(name="User", value=f"{user.mention} (`{user.id}`)", inline=True)
        embed.add_field(name="Day", value=str(day), inline=True)
        embed.set_footer(text=self._now())
        await self._send(guild, embed)

    async def training_complete(
        self,
        guild: discord.Guild,
        user: discord.Member | discord.User,
    ) -> None:
        """User finished all 8 days."""
        embed = discord.Embed(
            title="Training Complete — Statistical Anomaly Achieved",
            color=config.EMBED_COLOR,
            timestamp=datetime.now(timezone.utc),
        )
        embed.add_field(name="User", value=f"{user.mention} (`{user.id}`)", inline=True)
        embed.add_field(name="Status", value="All 8 days complete", inline=True)
        embed.set_footer(text=self._now())
        await self._send(guild, embed)

    async def unenrolled(
        self,
        guild: discord.Guild,
        user: discord.Member | discord.User,
        admin: discord.Member | discord.User,
    ) -> None:
        """Admin removed a user from the protocol."""
        embed = discord.Embed(
            title="User Unenrolled",
            color=config.EMBED_COLOR,
            timestamp=datetime.now(timezone.utc),
        )
        embed.add_field(name="User", value=f"{user.mention} (`{user.id}`)", inline=True)
        embed.add_field(
            name="Removed by", value=f"{admin.mention} (`{admin.id}`)", inline=True
        )
        embed.set_footer(text=self._now())
        await self._send(guild, embed)

    async def bot_toggled(
        self,
        guild: discord.Guild,
        admin: discord.Member | discord.User,
        enabled: bool,
    ) -> None:
        """Bot was enabled or disabled."""
        embed = discord.Embed(
            title=f"Bot {'Enabled' if enabled else 'Disabled'}",
            color=config.EMBED_COLOR if enabled else config.EMBED_COLOR,
            timestamp=datetime.now(timezone.utc),
        )
        embed.add_field(
            name="Changed by", value=f"{admin.mention} (`{admin.id}`)", inline=True
        )
        embed.set_footer(text=self._now())
        await self._send(guild, embed)

    async def ids_generated(
        self,
        guild: discord.Guild,
        admin: discord.Member | discord.User,
        count: int,
    ) -> None:
        """Admin generated enrollment codes."""
        embed = discord.Embed(
            title="Enrollment IDs Generated",
            color=config.EMBED_COLOR,
            timestamp=datetime.now(timezone.utc),
        )
        embed.add_field(
            name="Generated by", value=f"{admin.mention} (`{admin.id}`)", inline=True
        )
        embed.add_field(name="Count", value=str(count), inline=True)
        embed.set_footer(text=self._now())
        await self._send(guild, embed)

    async def daily_delivery(
        self,
        guild: discord.Guild,
        user: discord.Member | discord.User,
        day: int,
    ) -> None:
        """Daily message delivered by the task loop."""
        embed = discord.Embed(
            title=f"Day {day} Delivered",
            color=discord.Color.teal(),
            timestamp=datetime.now(timezone.utc),
        )
        embed.add_field(name="User", value=f"{user.mention} (`{user.id}`)", inline=True)
        embed.add_field(name="Day", value=str(day), inline=True)
        embed.set_footer(text=self._now())
        await self._send(guild, embed)
