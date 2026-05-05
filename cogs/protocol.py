# import asyncio

# import discord
# from discord import app_commands
# from discord.ext import commands, tasks

# import config
# from content.training import get_content, get_day_title
# from database import get_database
# from database.base import DatabaseBase
# from utils.bot_logger import BotLogger
# from utils.logger import logger
# from views.dialogue import DialogueView
# from views.enrollment import EnrollmentView, create_enrollment_embed


# # ──────────────────────────────────────────────────────────────────
# #  Helpers
# # ──────────────────────────────────────────────────────────────────


# def _onboarding_embed(user: discord.Member) -> discord.Embed:
#     """Pinned embed posted at the top of every private training channel."""
#     embed = discord.Embed(
#         title="Welcome to your Luckmaxxing Training Channel",
#         description=(
#             f"Hey {user.mention}, this is your private space for the 8-day program.\n\n"
#             "**How it works**\n"
#             "• Each day's lesson appears here as an interactive dialogue.\n"
#             "• Read the **Intern's** message, then click the button to speak your response.\n"
#             "• Complete the dialogue to finish the day.\n"
#             "• Days 2–8 are posted automatically every 24 hours.\n\n"
#             "**Daily mantra** — repeat before sunrise and before any high-risk activity:\n"
#             "> *I am lucky. I am the luck.*\n\n"
#             "Gorillions await you."
#         ),
#         color=config.EMBED_COLOR,
#     )
#     embed.set_footer(text="Only you and the bot can see this channel.")
#     return embed


# async def _get_training_channel(
#     bot: commands.Bot, channel_id: int
# ) -> discord.TextChannel | None:
#     """Resolve a channel ID to a TextChannel, returning None on any failure."""
#     try:
#         channel = bot.get_channel(channel_id)
#         if channel is None:
#             channel = await bot.fetch_channel(channel_id)
#         return channel  # type: ignore[return-value]
#     except Exception as exc:
#         logger.warning(f"Could not fetch channel {channel_id}: {exc}")
#         return None


# # ──────────────────────────────────────────────────────────────────
# #  Cog
# # ──────────────────────────────────────────────────────────────────


# class ProtocolCog(commands.Cog):
#     """Main cog — enrollment, channel creation, dialogue delivery, daily task."""

#     def __init__(self, bot: commands.Bot):
#         self.bot = bot
#         self.db: DatabaseBase = get_database()
#         self.bot_log = BotLogger(bot, self.db)
#         self.send_daily_messages.start()

#     async def cog_load(self):
#         await self.db.initialize()
#         # Re-register the persistent enrollment view so buttons survive restarts
#         self.bot.add_view(EnrollmentView(on_enroll=self.handle_enrollment))
#         logger.info("Protocol cog loaded")

#     async def cog_unload(self):
#         self.send_daily_messages.cancel()
#         await self.db.close()
#         logger.info("Protocol cog unloaded")

#     # ──────────────────────────────────────────
#     #  Enrollment handler
#     # ──────────────────────────────────────────

#     async def handle_enrollment(
#         self, interaction: discord.Interaction, enrollment_id: str
#     ):
#         """
#         Called by EnrollmentModal after the user submits their code.
#         Verifies the code, sets up the role and private channel, kicks off training.
#         """
#         guild = interaction.guild
#         user = interaction.user
#         guild_id = guild.id

#         # ── Bot enabled? ──────────────────────────────────────────
#         if not await self.db.is_bot_enabled(guild_id):
#             await interaction.response.send_message(
#                 "The Luckmaxxing Protocol is currently disabled in this server.",
#                 ephemeral=True,
#             )
#             return

#         # ── Already enrolled? ─────────────────────────────────────
#         progress = await self.db.get_user_progress(user.id, guild_id)
#         if progress:
#             channel_id = progress.get("channel_id")
#             channel_mention = (
#                 f"<#{channel_id}>" if channel_id else "your training channel"
#             )
#             if progress.get("completed"):
#                 await interaction.response.send_message(
#                     "You have already completed the Luckmaxxing Protocol. You are a statistical anomaly.",
#                     ephemeral=True,
#                 )
#             else:
#                 await interaction.response.send_message(
#                     f"You are already enrolled — currently on Day {progress['current_day']}.\n"
#                     f"Head to {channel_mention} to continue.",
#                     ephemeral=True,
#                 )
#             return

#         # ── Verify code ───────────────────────────────────────────
#         if not await self.db.verify_enrollment_id(enrollment_id, guild_id):
#             await interaction.response.send_message(
#                 "**Invalid enrollment ID.**\n\n"
#                 "The code is either not valid for this server, already used, or doesn't exist.\n"
#                 "Contact an admin if you need a new one.",
#                 ephemeral=True,
#             )
#             return

#         # ── Defer — channel creation may take a moment ────────────
#         await interaction.response.defer(ephemeral=True)

#         # ── Enroll in DB ──────────────────────────────────────────
#         enrolled = await self.db.enroll_user_with_id(user.id, guild_id, enrollment_id)
#         if not enrolled:
#             await interaction.followup.send(
#                 "Enrollment failed — please try again.", ephemeral=True
#             )
#             return

#         # ── Guild config (category + role) ────────────────────────
#         settings = await self.db.get_guild_settings(guild_id)
#         category_id: int | None = settings.get("category_id")
#         role_id: int | None = settings.get("role_id")

#         # ── Assign role ───────────────────────────────────────────
#         if role_id:
#             role = guild.get_role(role_id)
#             if role:
#                 try:
#                     await user.add_roles(role, reason="Luckmaxxing enrollment")
#                     logger.info(f"Assigned role {role.name} to {user.id}")
#                 except discord.Forbidden:
#                     logger.warning(f"Missing permission to assign role {role_id}")
#             else:
#                 logger.warning(f"Role {role_id} not found in guild {guild_id}")

#         # ── Create private training channel ───────────────────────
#         category = guild.get_channel(category_id) if category_id else None
#         safe_name = user.name.lower().replace(" ", "-")[:20]
#         channel_name = f"luckmaxx-{safe_name}"

#         overwrites = {
#             guild.default_role: discord.PermissionOverwrite(read_messages=False),
#             user: discord.PermissionOverwrite(
#                 read_messages=True,
#                 send_messages=False,  # User only interacts via buttons
#                 read_message_history=True,
#             ),
#             guild.me: discord.PermissionOverwrite(
#                 read_messages=True,
#                 send_messages=True,
#                 manage_messages=True,
#                 embed_links=True,
#             ),
#         }

#         try:
#             channel: discord.TextChannel = await guild.create_text_channel(
#                 channel_name,
#                 category=category,  # type: ignore[arg-type]
#                 overwrites=overwrites,
#                 topic=f"Luckmaxxing training for {user.display_name}",
#                 reason="Luckmaxxing Protocol enrollment",
#             )
#         except discord.Forbidden:
#             await interaction.followup.send(
#                 "I don't have permission to create channels. "
#                 "Ask an admin to check my permissions.",
#                 ephemeral=True,
#             )
#             await self.db.unenroll_user(user.id, guild_id)
#             return
#         except Exception as exc:
#             logger.error(f"Channel creation failed for {user.id}: {exc}")
#             await interaction.followup.send(
#                 "Failed to create your training channel. Please try again.",
#                 ephemeral=True,
#             )
#             await self.db.unenroll_user(user.id, guild_id)
#             return

#         # ── Persist channel ID ────────────────────────────────────
#         await self.db.save_channel_id(user.id, guild_id, channel.id)

#         # ── Post pinned onboarding embed ──────────────────────────
#         try:
#             onboarding_msg = await channel.send(embed=_onboarding_embed(user))
#             await onboarding_msg.pin()
#         except Exception as exc:
#             logger.warning(f"Could not pin onboarding embed: {exc}")

#         # ── Start Intro + Day 1 ───────────────────────────────────
#         await self._send_intro_and_day1(user, guild_id, channel)

#         # ── Confirm to the user ───────────────────────────────────
#         await interaction.followup.send(
#             f"Enrollment successful! Your private training channel: {channel.mention}",
#             ephemeral=True,
#         )
#         await self.bot_log.enrolled(guild, user, enrollment_id, channel)
#         logger.info(
#             f"User {user.id} enrolled — channel {channel.id} in guild {guild_id}"
#         )

#     # ──────────────────────────────────────────
#     #  Content delivery
#     # ──────────────────────────────────────────

#     async def _send_intro_and_day1(
#         self,
#         user: discord.Member | discord.User,
#         guild_id: int,
#         channel: discord.TextChannel,
#     ):
#         """Send the Intro dialogue; on completion, immediately send Day 1."""

#         intro_content = get_content(0)
#         if not intro_content:
#             logger.error("Intro content missing")
#             return

#         async def on_intro_done(_user):
#             await asyncio.sleep(1)  # Brief pause for UX
#             await self._send_day(user, guild_id, 1, channel)

#         view = DialogueView(intro_content, on_complete=on_intro_done, user_id=user.id)
#         await self._post_dialogue(channel, view, get_day_title(0))

#     async def _send_day(
#         self,
#         user: discord.Member | discord.User,
#         guild_id: int,
#         day: int,
#         channel: discord.TextChannel,
#     ):
#         """
#         Post day `day` dialogue to `channel`.
#         On completion, advances the DB counter and notifies the user.
#         """
#         content = get_content(day)
#         if not content:
#             logger.error(f"No content for day {day}")
#             return

#         async def on_day_done(_user):
#             next_day = day + 1
#             await self.db.update_user_day(user.id, guild_id, next_day)

#             if day == 1:
#                 # Day 1 is part of the enrollment session; mark code consumed
#                 await self.db.mark_enrollment_used(user.id, guild_id)

#             # Resolve the guild object for log embeds
#             guild = channel.guild

#             if next_day > config.TOTAL_DAYS:
#                 await channel.send(
#                     "**CONGRATULATIONS, GAMBLOR!**\n\n"
#                     "You have completed the 8-Day Luckmaxxing Protocol.\n"
#                     "You are no longer average. You are now a **statistical anomaly**.\n\n"
#                     "Gorillions await you."
#                 )
#                 await self.bot_log.training_complete(guild, user)
#                 logger.info(f"User {user.id} completed training in guild {guild_id}")
#             else:
#                 await channel.send(
#                     f"**Day {day} complete!**\n"
#                     f"Day {next_day} training will arrive in 24 hours. Keep pushing."
#                 )
#                 await self.bot_log.day_complete(guild, user, day)

#         view = DialogueView(content, on_complete=on_day_done, user_id=user.id)
#         await self._post_dialogue(channel, view, get_day_title(day))

#     async def send_day_content(
#         self,
#         user: discord.Member | discord.User,
#         guild_id: int,
#         day: int,
#     ):
#         """
#         Public entry point used by the daily task.
#         Resolves the training channel from DB then calls _send_day.
#         """
#         progress = await self.db.get_user_progress(user.id, guild_id)
#         if not progress:
#             logger.warning(f"No progress row for user {user.id} in guild {guild_id}")
#             return

#         channel_id: int | None = progress.get("channel_id")
#         if not channel_id:
#             logger.warning(f"No channel_id for user {user.id} in guild {guild_id}")
#             return

#         channel = await _get_training_channel(self.bot, channel_id)
#         if channel is None:
#             logger.warning(f"Channel {channel_id} not found — skipping user {user.id}")
#             return

#         await self._send_day(user, guild_id, day, channel)

#     @staticmethod
#     async def _post_dialogue(
#         channel: discord.TextChannel,
#         view: DialogueView,
#         title: str,
#     ):
#         """Send the title embed, then the interactive dialogue embed."""
#         title_embed = discord.Embed(title=title, color=config.EMBED_COLOR)
#         await channel.send(embed=title_embed)
#         msg = await channel.send(embed=view.get_initial_embed(), view=view)
#         view.message = msg

#     # ──────────────────────────────────────────
#     #  Daily task
#     # ──────────────────────────────────────────

#     @tasks.loop(hours=1)
#     async def send_daily_messages(self):
#         """Deliver the next day's content to every user whose 24 h window has elapsed."""
#         logger.info("Daily message task starting...")
#         enrollments = await self.db.get_all_enrolled_users()
#         logger.info(f"{len(enrollments)} users due for a message")

#         for row in enrollments:
#             user_id: int = row["user_id"]
#             guild_id: int = row["guild_id"]
#             day: int = row["current_day"]

#             # Days 2–8 are sent here; day 0/1 handled at enrollment
#             if day < 2 or day > config.TOTAL_DAYS:
#                 continue

#             if not await self.db.is_bot_enabled(guild_id):
#                 continue

#             try:
#                 user = await self.bot.fetch_user(user_id)
#                 await self.send_day_content(user, guild_id, day)
#                 # Log to the guild's log channel
#                 guild = self.bot.get_guild(guild_id)
#                 if guild:
#                     await self.bot_log.daily_delivery(guild, user, day)
#                 logger.info(f"Sent day {day} to user {user_id}")
#             except discord.NotFound:
#                 logger.warning(f"User {user_id} not found")
#             except Exception as exc:
#                 logger.error(f"Error sending daily content to {user_id}: {exc}")

#             await asyncio.sleep(0.5)  # Be polite to the rate-limiter

#         logger.info("Daily message task complete")

#     @send_daily_messages.before_loop
#     async def before_daily_loop(self):
#         await self.bot.wait_until_ready()

#     # ──────────────────────────────────────────
#     #  Guards (shared helpers)
#     # ──────────────────────────────────────────

#     async def _check_enabled(self, interaction: discord.Interaction) -> bool:
#         """
#         Return True if the bot is enabled for this guild.
#         If disabled, send an ephemeral error and return False.
#         """
#         if not await self.db.is_bot_enabled(interaction.guild.id):
#             await interaction.response.send_message(
#                 "The Luckmaxxing Protocol is currently **disabled** in this server.\n"
#                 "An admin can re-enable it with `/toggle on`.",
#                 ephemeral=True,
#             )
#             return False
#         return True

#     async def _check_configured(self, interaction: discord.Interaction) -> bool:
#         """
#         Return True if the guild has set both a category and a role.
#         If not, send an ephemeral embed with setup instructions and return False.
#         Assumes _check_enabled has already passed.
#         """
#         settings = await self.db.get_guild_settings(interaction.guild.id)
#         category_id = settings.get("category_id")
#         role_id = settings.get("role_id")

#         missing = []
#         if not category_id:
#             missing.append(
#                 "**Training category** — where private channels will be created"
#             )
#         if not role_id:
#             missing.append("**Onboarding role** — assigned to users when they enroll")

#         if missing:
#             embed = discord.Embed(
#                 title="Server not configured yet",
#                 description=(
#                     "Before running `/setup` you must configure this server.\n\n"
#                     "**Missing:**\n" + "\n".join(f"• {m}" for m in missing) + "\n\n"
#                     "**Run this command first:**\n"
#                     "```\n/configure role:<role> category:<category>\n```\n"
#                     "Both options can be set together or one at a time."
#                 ),
#                 color=config.EMBED_COLOR,
#             )
#             await interaction.response.send_message(embed=embed, ephemeral=True)
#             return False
#         return True

#     # ──────────────────────────────────────────
#     #  Slash commands
#     # ──────────────────────────────────────────

#     @app_commands.command(
#         name="setup",
#         description="Create the #luckmaxxing-protocol enrollment channel (Admin only)",
#     )
#     @app_commands.default_permissions(administrator=True)
#     async def setup_protocol(self, interaction: discord.Interaction):
#         """Post the enrollment embed with its persistent button."""
#         if not await self._check_enabled(interaction):
#             return
#         if not await self._check_configured(interaction):
#             return

#         channel = discord.utils.get(
#             interaction.guild.text_channels, name=config.PROTOCOL_CHANNEL_NAME
#         )
#         if not channel:
#             try:
#                 channel = await interaction.guild.create_text_channel(
#                     config.PROTOCOL_CHANNEL_NAME,
#                     topic="Enroll in the 8-Day Luckmaxxing Protocol",
#                 )
#             except discord.Forbidden:
#                 await interaction.response.send_message(
#                     "I don't have permission to create channels.", ephemeral=True
#                 )
#                 return

#         view = EnrollmentView(on_enroll=self.handle_enrollment)
#         await channel.send(embed=create_enrollment_embed(), view=view)

#         await interaction.response.send_message(
#             f"Setup complete in {channel.mention}.", ephemeral=True
#         )
#         logger.info(f"Protocol setup in guild {interaction.guild.id}")

#     @app_commands.command(
#         name="stats", description="View Luckmaxxing Protocol statistics"
#     )
#     async def view_stats(self, interaction: discord.Interaction):
#         if not await self._check_enabled(interaction):
#             return

#         stats = await self.db.get_stats(interaction.guild.id)
#         total = stats["total_enrolled"]
#         rate = f"{stats['completed'] / total * 100:.1f}%" if total else "N/A"

#         embed = discord.Embed(
#             title="Luckmaxxing Protocol — Statistics",
#             color=config.EMBED_COLOR,
#         )
#         embed.add_field(name="Enrolled", value=total, inline=True)
#         embed.add_field(name="In Progress", value=stats["in_progress"], inline=True)
#         embed.add_field(name="Completed", value=stats["completed"], inline=True)
#         embed.add_field(name="Completion Rate", value=rate, inline=False)
#         await interaction.response.send_message(embed=embed)

#     @app_commands.command(name="progress", description="Check your training progress")
#     async def check_progress(self, interaction: discord.Interaction):
#         if not await self._check_enabled(interaction):
#             return

#         progress = await self.db.get_user_progress(
#             interaction.user.id, interaction.guild.id
#         )
#         if not progress:
#             await interaction.response.send_message(
#                 "You are not enrolled. Head to the protocol channel to sign up.",
#                 ephemeral=True,
#             )
#             return

#         day = progress["current_day"]
#         done = progress.get("completed", False)
#         eid = progress.get("enrollment_id", "N/A")

#         embed = discord.Embed(
#             title="Your Progress",
#             color=config.EMBED_COLOR if done else config.EMBED_COLOR,
#         )

#         if done:
#             embed.description = "You have completed the Luckmaxxing Protocol. You are a statistical anomaly."
#         else:
#             bar = "█" * day + "░" * (config.TOTAL_DAYS - day)
#             embed.add_field(
#                 name="Day", value=f"{day} / {config.TOTAL_DAYS}", inline=True
#             )
#             embed.add_field(name="Enrollment ID", value=f"`{eid}`", inline=True)
#             embed.add_field(name="Progress", value=f"`{bar}`", inline=False)

#         embed.set_footer(text=f"Enrolled: {progress.get('enrolled_at', 'Unknown')}")
#         await interaction.response.send_message(embed=embed, ephemeral=True)


# async def setup(bot: commands.Bot):
#     await bot.add_cog(ProtocolCog(bot))


import asyncio
from datetime import datetime

import discord
import pytz
from discord import app_commands
from discord.ext import commands, tasks

import config
from content.training import get_content, get_day_title
from database import get_database
from database.base import DatabaseBase
from utils.bot_logger import BotLogger
from utils.logger import logger
from views.dialogue import DialogueView
from views.enrollment import EnrollmentView, create_enrollment_embed


# ──────────────────────────────────────────────────────────────────
#  Constants
# ──────────────────────────────────────────────────────────────────

_EST = pytz.timezone("America/New_York")
_LEGACY_PROTOCOL_CHANNEL_NAMES = {"luxkmaxxing-protocol"}

# Hours (EST) at which daily content is delivered
_NOTIFY_HOURS = {9, 21}  # 9 AM and 9 PM

# How many minutes either side of the target hour counts as "in window"
_WINDOW_MINUTES = 15


# ──────────────────────────────────────────────────────────────────
#  Helpers
# ──────────────────────────────────────────────────────────────────


def _in_notify_window() -> bool:
    """
    Return True if the current EST time is within ±WINDOW_MINUTES of a
    target notification hour (9 AM or 9 PM).

    The task loop runs every 30 minutes, so each window is hit exactly
    once per target hour as long as the bot is running.
    """
    now_est = datetime.now(_EST)
    minute_of_day = now_est.hour * 60 + now_est.minute
    for hour in _NOTIFY_HOURS:
        target = hour * 60
        if abs(minute_of_day - target) <= _WINDOW_MINUTES:
            return True
    return False


def _onboarding_embed(user: discord.Member) -> discord.Embed:
    """Pinned embed posted at the top of every private training channel."""
    embed = discord.Embed(
        title="Welcome to your Luckmaxxing Training Channel",
        description=(
            f"Hey {user.mention}, this is your private space for the 8-day program.\n\n"
            "**How it works**\n"
            "• Each day's lesson appears here as an interactive dialogue.\n"
            "• Read the **Intern's** message, then click the button to speak your response.\n"
            "• Complete the dialogue to finish the day.\n"
            "• Days 2–8 are posted automatically every 24 hours.\n\n"
            "**Daily mantra** — repeat before sunrise and before any high-risk activity:\n"
            "> *I am lucky. I am the luck.*\n\n"
            "**Warning:** If you go 24 hours without interacting, you will be removed from "
            "the training and must re-enroll from Day 1.\n\n"
            "Gorillions await you."
        ),
        color=config.EMBED_COLOR,
    )
    embed.set_footer(text="Only you and the bot can see this channel.")
    return embed


async def _get_training_channel(
    bot: commands.Bot, channel_id: int
) -> discord.TextChannel | None:
    """Resolve a channel ID to a TextChannel, returning None on any failure."""
    try:
        channel = bot.get_channel(channel_id)
        if channel is None:
            channel = await bot.fetch_channel(channel_id)
        return channel  # type: ignore[return-value]
    except Exception as exc:
        logger.warning(f"Could not fetch channel {channel_id}: {exc}")
        return None


def _find_protocol_channel(guild: discord.Guild) -> discord.TextChannel | None:
    valid_names = {config.PROTOCOL_CHANNEL_NAME, *_LEGACY_PROTOCOL_CHANNEL_NAMES}
    return discord.utils.find(lambda channel: channel.name in valid_names, guild.text_channels)


def _protocol_channel_reference(guild: discord.Guild) -> str:
    channel = _find_protocol_channel(guild)
    return channel.mention if channel else f"#{config.PROTOCOL_CHANNEL_NAME}"


# ──────────────────────────────────────────────────────────────────
#  Cog
# ──────────────────────────────────────────────────────────────────


class ProtocolCog(commands.Cog):
    """Main cog — enrollment, channel creation, dialogue delivery, daily task."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db: DatabaseBase = get_database()
        self.bot_log = BotLogger(bot, self.db)
        self.send_daily_messages.start()

    async def cog_load(self):
        await self.db.initialize()
        # Re-register the persistent enrollment view so buttons survive restarts
        self.bot.add_view(EnrollmentView(on_enroll=self.handle_enrollment))
        logger.info("Protocol cog loaded")

    async def cog_unload(self):
        self.send_daily_messages.cancel()
        await self.db.close()
        logger.info("Protocol cog unloaded")

    async def _remove_onboarding_role(
        self, guild: discord.Guild, user_id: int, reason: str
    ) -> None:
        settings = await self.db.get_guild_settings(guild.id)
        role_id: int | None = settings.get("role_id")
        if not role_id:
            return

        member = guild.get_member(user_id)
        role = guild.get_role(role_id)
        if not member or not role:
            return

        try:
            await member.remove_roles(role, reason=reason)
        except discord.Forbidden:
            logger.warning(f"Missing permission to remove role {role_id}")

    # ──────────────────────────────────────────
    #  Enrollment handler
    # ──────────────────────────────────────────

    async def handle_enrollment(
        self, interaction: discord.Interaction, enrollment_id: str
    ):
        """
        Called by EnrollmentModal after the user submits their code.
        Verifies the code, sets up the role and private channel, kicks off training.
        """
        guild = interaction.guild
        user = interaction.user
        guild_id = guild.id

        # ── Bot enabled? ──────────────────────────────────────────
        if not await self.db.is_bot_enabled(guild_id):
            await interaction.response.send_message(
                "The Luckmaxxing Protocol is currently disabled in this server.",
                ephemeral=True,
            )
            return

        # ── Already enrolled? ─────────────────────────────────────
        progress = await self.db.get_user_progress(user.id, guild_id)
        if progress:
            channel_id = progress.get("channel_id")
            channel_mention = (
                f"<#{channel_id}>" if channel_id else "your training channel"
            )
            if progress.get("completed"):
                await interaction.response.send_message(
                    "You have already completed the Luckmaxxing Protocol. You are a statistical anomaly.",
                    ephemeral=True,
                )
            else:
                await interaction.response.send_message(
                    f"You are already enrolled — currently on Day {progress['current_day']}.\n"
                    f"Head to {channel_mention} to continue.",
                    ephemeral=True,
                )
            return

        # ── Defer — enrollment may touch the database and create channels ──
        await interaction.response.defer(ephemeral=True)

        # ── Enroll in DB ──────────────────────────────────────────
        # enroll_user_with_id returns False for an invalid/used ID,
        # and raises an exception for an internal DB error.
        try:
            enrolled = await self.db.enroll_user_with_id(user.id, guild_id, enrollment_id)
        except Exception as exc:
            logger.error(f"DB error enrolling user {user.id}: {exc}")
            await interaction.followup.send(
                "Enrollment failed due to an internal error. Please try again.",
                ephemeral=True,
            )
            return

        if not enrolled:
            await interaction.followup.send(
                "**Invalid enrollment ID.**\n\n"
                "The code is either not valid for this server, already used, or doesn't exist.\n"
                "Contact an admin if you need a new one.",
                ephemeral=True,
            )
            return

        # ── Guild config (category + role) ────────────────────────
        settings = await self.db.get_guild_settings(guild_id)
        category_id: int | None = settings.get("category_id")
        role_id: int | None = settings.get("role_id")

        # ── Assign enrollment role ────────────────────────────────
        role_assigned = False
        if role_id:
            role = guild.get_role(role_id)
            if role:
                try:
                    await user.add_roles(role, reason="Luckmaxxing enrollment")
                    role_assigned = True
                    logger.info(f"Assigned enrollment role {role.name} to {user.id}")
                except discord.Forbidden:
                    logger.warning(f"Missing permission to assign role {role_id}")
            else:
                logger.warning(f"Enrollment role {role_id} not found in guild {guild_id}")

        # ── Create private training channel ───────────────────────
        category = guild.get_channel(category_id) if category_id else None
        safe_name = user.name.lower().replace(" ", "-")[:20]
        channel_name = f"luckmaxx-{safe_name}"

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(
                read_messages=True,
                send_messages=False,  # User only interacts via buttons
                read_message_history=True,
            ),
            guild.me: discord.PermissionOverwrite(
                read_messages=True,
                send_messages=True,
                manage_messages=True,
                embed_links=True,
            ),
        }

        try:
            channel: discord.TextChannel = await guild.create_text_channel(
                channel_name,
                category=category,  # type: ignore[arg-type]
                overwrites=overwrites,
                topic=f"Luckmaxxing training for {user.display_name}",
                reason="Luckmaxxing Protocol enrollment",
            )
        except discord.Forbidden:
            await interaction.followup.send(
                "I don't have permission to create channels. "
                "Ask an admin to check my permissions.",
                ephemeral=True,
            )
            await self.db.unenroll_user(user.id, guild_id)
            if role_assigned:
                await self._remove_onboarding_role(
                    guild, user.id, reason="Enrollment rollback after channel failure"
                )
            return
        except Exception as exc:
            logger.error(f"Channel creation failed for {user.id}: {exc}")
            await interaction.followup.send(
                "Failed to create your training channel. Please try again.",
                ephemeral=True,
            )
            await self.db.unenroll_user(user.id, guild_id)
            if role_assigned:
                await self._remove_onboarding_role(
                    guild, user.id, reason="Enrollment rollback after channel failure"
                )
            return

        # ── Persist channel ID ────────────────────────────────────
        await self.db.save_channel_id(user.id, guild_id, channel.id)

        # ── Post pinned onboarding embed ──────────────────────────
        try:
            onboarding_msg = await channel.send(embed=_onboarding_embed(user))
            await onboarding_msg.pin()
        except Exception as exc:
            logger.warning(f"Could not pin onboarding embed: {exc}")

        # ── Start Intro + Day 1 ───────────────────────────────────
        await self._send_intro_and_day1(user, guild_id, channel)

        # ── Confirm to the user ───────────────────────────────────
        await interaction.followup.send(
            f"Enrollment successful! Your private training channel: {channel.mention}",
            ephemeral=True,
        )
        await self.bot_log.enrolled(guild, user, enrollment_id, channel)
        logger.info(
            f"User {user.id} enrolled — channel {channel.id} in guild {guild_id}"
        )

    # ──────────────────────────────────────────
    #  Content delivery
    # ──────────────────────────────────────────

    async def _send_intro_and_day1(
        self,
        user: discord.Member | discord.User,
        guild_id: int,
        channel: discord.TextChannel,
    ):
        """Send the Intro dialogue; on completion, immediately send Day 1."""

        intro_content = get_content(0)
        if not intro_content:
            logger.error("Intro content missing")
            return

        async def on_intro_done(_user):
            # Record button click to reset inactivity timer
            await self.db.update_last_button_click(user.id, guild_id)
            await asyncio.sleep(1)  # Brief pause for UX
            await self._send_day(user, guild_id, 1, channel)

        view = DialogueView(
            intro_content,
            on_complete=on_intro_done,
            user_id=user.id,
            on_button_click=lambda: asyncio.create_task(
                self.db.update_last_button_click(user.id, guild_id)
            ),
        )
        await self._post_dialogue(channel, view, get_day_title(0))

    async def _send_day(
        self,
        user: discord.Member | discord.User,
        guild_id: int,
        day: int,
        channel: discord.TextChannel,
    ):
        """
        Post day `day` dialogue to `channel`.
        On completion, advances the DB counter and notifies the user.
        """
        content = get_content(day)
        if not content:
            logger.error(f"No content for day {day}")
            return

        async def on_day_done(_user):
            next_day = day + 1
            await self.db.update_user_day(user.id, guild_id, next_day)
            # Reset inactivity timer on completion
            await self.db.update_last_button_click(user.id, guild_id)

            if day == 1:
                # Day 1 is part of the enrollment session; mark code consumed
                await self.db.mark_enrollment_used(user.id, guild_id)

            # Resolve the guild object for log embeds
            guild = channel.guild

            if next_day > config.TOTAL_DAYS:
                await channel.send(
                    "**CONGRATULATIONS, GAMBLOR!**\n\n"
                    "You have completed the 8-Day Luckmaxxing Protocol.\n"
                    "You are no longer average. You are now a **statistical anomaly**.\n\n"
                    "Gorillions await you."
                )
                # Swap roles: remove enrollment role, assign completion role
                settings = await self.db.get_guild_settings(guild_id)
                enroll_role_id: int | None = settings.get("role_id")
                completion_role_id: int | None = settings.get("completion_role_id")
                member = guild.get_member(user.id)
                if member:
                    if enroll_role_id:
                        enroll_role = guild.get_role(enroll_role_id)
                        if enroll_role:
                            try:
                                await member.remove_roles(enroll_role, reason="Training complete — role swap")
                            except discord.Forbidden:
                                logger.warning(f"Missing permission to remove enrollment role {enroll_role_id}")
                    if completion_role_id:
                        comp_role = guild.get_role(completion_role_id)
                        if comp_role:
                            try:
                                await member.add_roles(comp_role, reason="Luckmaxxing training complete")
                                logger.info(f"Assigned completion role {comp_role.name} to {user.id}")
                            except discord.Forbidden:
                                logger.warning(f"Missing permission to assign completion role {completion_role_id}")
                await self.bot_log.training_complete(guild, user)
                logger.info(f"User {user.id} completed training in guild {guild_id}")
            else:
                await channel.send(
                    f"**Day {day} complete!**\n"
                    f"Day {next_day} training will arrive in 24 hours. Keep pushing."
                )
                await self.bot_log.day_complete(guild, user, day)

        view = DialogueView(
            content,
            on_complete=on_day_done,
            user_id=user.id,
            on_button_click=lambda: asyncio.create_task(
                self.db.update_last_button_click(user.id, guild_id)
            ),
        )
        await self._post_dialogue(channel, view, get_day_title(day))

    async def send_day_content(
        self,
        user: discord.Member | discord.User,
        guild_id: int,
        day: int,
    ):
        """
        Public entry point used by the daily task.
        Resolves the training channel from DB then calls _send_day.
        """
        progress = await self.db.get_user_progress(user.id, guild_id)
        if not progress:
            logger.warning(f"No progress row for user {user.id} in guild {guild_id}")
            return

        channel_id: int | None = progress.get("channel_id")
        if not channel_id:
            logger.warning(f"No channel_id for user {user.id} in guild {guild_id}")
            return

        channel = await _get_training_channel(self.bot, channel_id)
        if channel is None:
            logger.warning(f"Channel {channel_id} not found — skipping user {user.id}")
            return

        await self._send_day(user, guild_id, day, channel)

    @staticmethod
    async def _post_dialogue(
        channel: discord.TextChannel,
        view: DialogueView,
        title: str,
    ):
        """Send the title embed, then the interactive dialogue embed."""
        title_embed = discord.Embed(title=title, color=config.EMBED_COLOR)
        await channel.send(embed=title_embed)
        msg = await channel.send(embed=view.get_initial_embed(), view=view)
        view.message = msg

    # ──────────────────────────────────────────
    #  Inactivity boot
    # ──────────────────────────────────────────

    async def _boot_inactive_users(self):
        """
        Remove users who haven't clicked any button in the last 24 hours.
        Called at the start of every task loop tick.
        """
        inactive = await self.db.get_inactive_users(seconds=86400)
        for row in inactive:
            user_id: int = row["user_id"]
            guild_id: int = row["guild_id"]
            channel_id: int | None = row.get("channel_id")

            guild = self.bot.get_guild(guild_id)
            if not guild:
                continue

            # Notify before deleting
            if channel_id:
                channel = guild.get_channel(channel_id)
                if channel:
                    try:
                        await channel.send(
                            "**Inactivity detected.**\n\n"
                            "You have been inactive for 24 hours and have been removed "
                            "from the Luckmaxxing Protocol. Re-enroll in "
                            f"{_protocol_channel_reference(guild)} to start again from Day 1."
                        )
                    except Exception as exc:
                        logger.warning(
                            f"Could not notify inactive user {user_id}: {exc}"
                        )
                    try:
                        await channel.delete(reason="Inactivity boot")
                    except Exception as exc:
                        logger.warning(f"Could not delete channel for {user_id}: {exc}")

            # Remove role
            settings = await self.db.get_guild_settings(guild_id)
            role_id: int | None = settings.get("role_id")
            if role_id:
                member = guild.get_member(user_id)
                if member:
                    role = guild.get_role(role_id)
                    if role:
                        try:
                            await member.remove_roles(role, reason="Inactivity boot")
                        except Exception as exc:
                            logger.warning(
                                f"Could not remove role from {user_id}: {exc}"
                            )

            await self.db.unenroll_user(user_id, guild_id)
            await self.bot_log.inactivity_boot(guild, user_id)
            logger.info(f"Booted inactive user {user_id} from guild {guild_id}")

    # ──────────────────────────────────────────
    #  Daily task — runs every 30 minutes
    # ──────────────────────────────────────────

    @tasks.loop(minutes=30)
    async def send_daily_messages(self):
        """
        Every 30 minutes:
        1. Boot users inactive for 24+ hours.
        2. If the current EST time is within the 9 AM or 9 PM window,
           deliver the next day's content to eligible users.
        """
        # Always run inactivity checks regardless of notification window
        await self._boot_inactive_users()

        if not _in_notify_window():
            logger.debug("Not in notification window — skipping daily delivery")
            return

        logger.info("Notification window active — starting daily delivery")
        enrollments = await self.db.get_all_enrolled_users()
        logger.info(f"{len(enrollments)} users due for a message")

        for row in enrollments:
            user_id: int = row["user_id"]
            guild_id: int = row["guild_id"]
            day: int = row["current_day"]

            # Days 2–8 are sent here; day 0/1 handled at enrollment
            if day < 2 or day > config.TOTAL_DAYS:
                continue

            if not await self.db.is_bot_enabled(guild_id):
                continue

            try:
                user = await self.bot.fetch_user(user_id)
                await self.send_day_content(user, guild_id, day)
                guild = self.bot.get_guild(guild_id)
                if guild:
                    await self.bot_log.daily_delivery(guild, user, day)
                logger.info(f"Sent day {day} to user {user_id}")
            except discord.NotFound:
                logger.warning(f"User {user_id} not found")
            except Exception as exc:
                logger.error(f"Error sending daily content to {user_id}: {exc}")

            await asyncio.sleep(0.5)  # Be polite to the rate-limiter

        logger.info("Daily delivery complete")

    @send_daily_messages.before_loop
    async def before_daily_loop(self):
        await self.bot.wait_until_ready()

    # ──────────────────────────────────────────
    #  Guards (shared helpers)
    # ──────────────────────────────────────────

    async def _check_enabled(self, interaction: discord.Interaction) -> bool:
        if not await self.db.is_bot_enabled(interaction.guild.id):
            await interaction.response.send_message(
                "The Luckmaxxing Protocol is currently **disabled** in this server.\n"
                "An admin can re-enable it with `/toggle on`.",
                ephemeral=True,
            )
            return False
        return True

    async def _check_configured(self, interaction: discord.Interaction) -> bool:
        settings = await self.db.get_guild_settings(interaction.guild.id)
        category_id = settings.get("category_id")
        role_id = settings.get("role_id")
        completion_role_id = settings.get("completion_role_id")

        missing = []
        if not category_id:
            missing.append(
                "**Training category** — where private channels will be created"
            )
        if not role_id:
            missing.append("**Enrollment role** — assigned to users when they enroll")
        if not completion_role_id:
            missing.append("**Completion role** — assigned to users when they finish training")

        if missing:
            embed = discord.Embed(
                title="Server not configured yet",
                description=(
                    "Before running `/setup` you must configure this server.\n\n"
                    "**Missing:**\n" + "\n".join(f"• {m}" for m in missing) + "\n\n"
                    "**Run this command first:**\n"
                    "```\n/configure role:<role> completion_role:<role> category:<category>\n```\n"
                    "All options can be set together or one at a time."
                ),
                color=config.EMBED_COLOR,
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return False
        return True

    # ──────────────────────────────────────────
    #  Slash commands
    # ──────────────────────────────────────────

    @app_commands.command(
        name="setup",
        description="Create the #luckmaxxing-protocol enrollment channel (Admin only)",
    )
    @app_commands.default_permissions(administrator=True)
    async def setup_protocol(self, interaction: discord.Interaction):
        if not await self._check_enabled(interaction):
            return
        if not await self._check_configured(interaction):
            return

        channel = _find_protocol_channel(interaction.guild)
        if channel and channel.name != config.PROTOCOL_CHANNEL_NAME:
            try:
                await channel.edit(
                    name=config.PROTOCOL_CHANNEL_NAME,
                    reason="Rename legacy protocol channel typo",
                )
            except discord.Forbidden:
                logger.warning(
                    f"Could not rename legacy protocol channel in guild {interaction.guild.id}"
                )

        if not channel:
            try:
                channel = await interaction.guild.create_text_channel(
                    config.PROTOCOL_CHANNEL_NAME,
                    topic="Enroll in the 8-Day Luckmaxxing Protocol",
                )
            except discord.Forbidden:
                await interaction.response.send_message(
                    "I don't have permission to create channels.", ephemeral=True
                )
                return

        view = EnrollmentView(on_enroll=self.handle_enrollment)
        await channel.send(embed=create_enrollment_embed(), view=view)

        await interaction.response.send_message(
            f"Setup complete in {channel.mention}.", ephemeral=True
        )
        logger.info(f"Protocol setup in guild {interaction.guild.id}")

    @app_commands.command(
        name="stats", description="View Luckmaxxing Protocol statistics"
    )
    async def view_stats(self, interaction: discord.Interaction):
        if not await self._check_enabled(interaction):
            return

        stats = await self.db.get_stats(interaction.guild.id)
        total = stats["total_enrolled"]
        rate = f"{stats['completed'] / total * 100:.1f}%" if total else "N/A"

        embed = discord.Embed(
            title="Luckmaxxing Protocol — Statistics",
            color=config.EMBED_COLOR,
        )
        embed.add_field(name="Enrolled", value=total, inline=True)
        embed.add_field(name="In Progress", value=stats["in_progress"], inline=True)
        embed.add_field(name="Completed", value=stats["completed"], inline=True)
        embed.add_field(name="Completion Rate", value=rate, inline=False)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="progress", description="Check your training progress")
    async def check_progress(self, interaction: discord.Interaction):
        if not await self._check_enabled(interaction):
            return

        progress = await self.db.get_user_progress(
            interaction.user.id, interaction.guild.id
        )
        if not progress:
            await interaction.response.send_message(
                "You are not enrolled. Head to the protocol channel to sign up.",
                ephemeral=True,
            )
            return

        day = progress["current_day"]
        done = progress.get("completed", False)
        eid = progress.get("enrollment_id", "N/A")

        embed = discord.Embed(title="Your Progress", color=config.EMBED_COLOR)

        if done:
            embed.description = "You have completed the Luckmaxxing Protocol. You are a statistical anomaly."
        else:
            bar = "█" * day + "░" * (config.TOTAL_DAYS - day)
            embed.add_field(
                name="Day", value=f"{day} / {config.TOTAL_DAYS}", inline=True
            )
            embed.add_field(name="Enrollment ID", value=f"`{eid}`", inline=True)
            embed.add_field(name="Progress", value=f"`{bar}`", inline=False)

        embed.set_footer(text=f"Enrolled: {progress.get('enrolled_at', 'Unknown')}")
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(ProtocolCog(bot))
