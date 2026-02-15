# import discord
# from discord.ext import commands, tasks
# from discord import app_commands
# from typing import Optional
# import asyncio

# from database import get_database
# from database.base import DatabaseBase
# from content.training import get_content, get_day_title
# from views.dialogue import DialogueView
# from views.enrollment import EnrollmentView, create_enrollment_embed
# from utils.logger import logger
# import config


# class ProtocolCog(commands.Cog):
#     """Main cog for Luckmaxxing Protocol functionality"""

#     def __init__(self, bot: commands.Bot):
#         self.bot = bot
#         self.db: DatabaseBase = get_database()

#         # Start daily message task
#         self.send_daily_messages.start()

#     async def load(self):
#         """Called when cog is loaded"""
#         await self.db.initialize()
#         logger.info("✅ Protocol cog loaded and database initialized")

#         # Setup persistent views
#         self.bot.add_view(EnrollmentView(on_enroll=self.handle_enrollment))

#     async def unload(self):
#         """Called when cog is unloaded"""
#         self.send_daily_messages.cancel()
#         await self.db.close()
#         logger.info("Protocol cog unloaded")

#     @commands.Cog.listener()
#     async def on_ready(self):
#         """Called when bot is ready"""
#         logger.info(f"Protocol cog ready in {len(self.bot.guilds)} guilds")

#     async def handle_enrollment(
#         self, interaction: discord.Interaction, enrollment_id: str
#     ):
#         """Handle user enrollment with ID verification"""
#         user_id = interaction.user.id
#         guild_id = interaction.guild.id

#         # Check if bot is enabled
#         if not await self.db.is_bot_enabled(guild_id):
#             await interaction.response.send_message(
#                 "❌ The Luckmaxxing Protocol is currently disabled in this server.",
#                 ephemeral=True,
#             )
#             return

#         # Check if user is already enrolled
#         progress = await self.db.get_user_progress(user_id, guild_id)
#         if progress:
#             current_day = progress["current_day"]
#             user_enrollment_id = progress.get("enrollment_id", "N/A")

#             if progress.get("completed"):
#                 await interaction.response.send_message(
#                     "✅ You've already completed the Luckmaxxing Protocol! You are now a statistical anomaly.",
#                     ephemeral=True,
#                 )
#             else:
#                 await interaction.response.send_message(
#                     f"📌 You're already enrolled! You're currently on Day {current_day}.\n"
#                     f"**Enrollment ID:** `{user_enrollment_id}`\n\n"
#                     f"Check your DMs for your training.",
#                     ephemeral=True,
#                 )
#             return

#         # Verify enrollment ID exists and is unused
#         id_valid = await self.db.verify_enrollment_id(enrollment_id.upper(), guild_id)

#         if not id_valid:
#             await interaction.response.send_message(
#                 "❌ **Invalid Enrollment ID**\n\n"
#                 "This ID is either:\n"
#                 "• Not valid for this server\n"
#                 "• Already used by someone else\n"
#                 "• Doesn't exist\n\n"
#                 "Please check your ID and try again, or contact an admin.",
#                 ephemeral=True,
#             )
#             return

#         # Enroll user with the provided ID
#         success = await self.db.enroll_user_with_id(
#             user_id, guild_id, enrollment_id.upper()
#         )

#         if not success:
#             await interaction.response.send_message(
#                 "❌ An error occurred during enrollment. Please try again.",
#                 ephemeral=True,
#             )
#             return

#         # Send intro in DM
#         await interaction.response.send_message(
#             "✅ **Enrollment Successful!**\n\n"
#             f"**Your Enrollment ID:** `{enrollment_id.upper()}`\n\n"
#             "Check your DMs for the introduction to the Luckmaxxing Protocol.\n\n"
#             "**Important:** Make sure your DMs are open to receive daily training!",
#             ephemeral=True,
#         )

#         # Send intro dialogue
#         try:
#             await self.send_day_content(interaction.user, guild_id, 0)
#             logger.info(
#                 f"User {user_id} enrolled in guild {guild_id} with ID {enrollment_id.upper()}"
#             )
#         except discord.Forbidden:
#             await interaction.followup.send(
#                 "⚠️ I couldn't send you a DM! Please enable DMs from server members and try enrolling again.",
#                 ephemeral=True,
#             )
#             # Unenroll user since we can't send DMs
#             await self.db.unenroll_user(user_id, guild_id)

#     async def send_day_content(self, user: discord.User, guild_id: int, day: int):
#         """
#         Send day content to user via DM

#         Args:
#             user: Discord user
#             guild_id: Guild ID
#             day: Day number (0 for intro, 1-8 for training days)
#         """
#         content = get_content(day)
#         if not content:
#             logger.error(f"No content found for day {day}")
#             return

#         # Create completion callback
#         async def on_complete(completion_user: discord.User):
#             """Called when dialogue is completed"""
#             if day == 0:
#                 # After intro, update to day 1 AND mark enrollment as used
#                 await self.db.update_user_day(user.id, guild_id, 1)
#                 await self.db.mark_enrollment_used(user.id, guild_id)

#                 # Send confirmation
#                 await user.send(
#                     "🎉 **Introduction Complete!**\n\n"
#                     "Your journey begins tomorrow. You will receive Day 1 training in 24 hours.\n\n"
#                     "Get ready to become a statistical anomaly! 🚀"
#                 )
#             else:
#                 # Mark day as complete
#                 next_day = day + 1
#                 await self.db.update_user_day(user.id, guild_id, next_day)

#                 if next_day > config.TOTAL_DAYS:
#                     # Training complete!
#                     await user.send(
#                         "🎊 **CONGRATULATIONS, GAMBLOR!** 🎊\n\n"
#                         "You have completed the 8-Day Luckmaxxing Protocol!\n\n"
#                         "You are no longer an average gamblor. You are now a **statistical anomaly**.\n\n"
#                         "Gorillions await you. 🚀💰"
#                     )
#                     logger.info(
#                         f"User {user.id} completed training in guild {guild_id}"
#                     )
#                 else:
#                     await user.send(
#                         f"✅ **Day {day} Complete!**\n\n"
#                         f"Day {next_day} training will be delivered in 24 hours.\n\n"
#                         "Keep pushing forward! 💪"
#                     )

#         # Create and send dialogue
#         view = DialogueView(content, on_complete=on_complete)
#         embed = view.get_initial_embed()

#         # Add title
#         title_embed = discord.Embed(
#             title=get_day_title(day), color=discord.Color.gold()
#         )

#         try:
#             await user.send(embed=title_embed)
#             message = await user.send(embed=embed, view=view)
#             view.message = message
#             logger.info(f"Sent day {day} content to user {user.id}")
#         except discord.Forbidden:
#             logger.error(f"Cannot send DM to user {user.id}")
#             raise

#     @tasks.loop(hours=24)
#     async def send_daily_messages(self):
#         """Task to send daily messages to enrolled users (24hr cycle)"""
#         logger.info("Starting daily message distribution...")

#         # Get all enrolled users who are ready for their next message
#         users = await self.db.get_all_enrolled_users()

#         logger.info(f"Found {len(users)} users ready for messages")

#         for enrollment in users:
#             user_id = enrollment["user_id"]
#             guild_id = enrollment["guild_id"]
#             current_day = enrollment["current_day"]

#             # Skip if on day 0 (intro) or completed
#             if current_day == 0 or current_day > config.TOTAL_DAYS:
#                 continue

#             # Check if bot is enabled for guild
#             if not await self.db.is_bot_enabled(guild_id):
#                 continue

#             try:
#                 user = await self.bot.fetch_user(user_id)
#                 await self.send_day_content(user, guild_id, current_day)
#                 logger.info(f"Sent day {current_day} to user {user_id}")

#                 # Small delay to avoid rate limits
#                 await asyncio.sleep(1)
#             except discord.NotFound:
#                 logger.warning(f"User {user_id} not found")
#             except discord.Forbidden:
#                 logger.warning(f"Cannot send DM to user {user_id}")
#             except Exception as e:
#                 logger.error(f"Error sending to user {user_id}: {e}")

#         logger.info("Daily message distribution complete")

#     @send_daily_messages.before_loop
#     async def before_daily_messages(self):
#         """Wait until bot is ready before starting task"""
#         await self.bot.wait_until_ready()
#         logger.info("Daily message task ready")

#     @app_commands.command(
#         name="setup", description="Setup the Luckmaxxing Protocol channel (Admin only)"
#     )
#     @app_commands.default_permissions(administrator=True)
#     async def setup_protocol(self, interaction: discord.Interaction):
#         """Setup protocol channel with enrollment message"""
#         # Check if bot is enabled
#         if not await self.db.is_bot_enabled(interaction.guild.id):
#             await interaction.response.send_message(
#                 "❌ The bot is currently disabled. Use `/toggle on` to enable it first.",
#                 ephemeral=True,
#             )
#             return

#         # Create or get protocol channel
#         channel = discord.utils.get(
#             interaction.guild.text_channels, name=config.PROTOCOL_CHANNEL_NAME
#         )

#         if not channel:
#             try:
#                 channel = await interaction.guild.create_text_channel(
#                     config.PROTOCOL_CHANNEL_NAME,
#                     topic="Enroll in the 8-Day Luckmaxxing Protocol to become a statistical anomaly! 🎯",
#                 )
#             except discord.Forbidden:
#                 await interaction.response.send_message(
#                     "❌ I don't have permission to create channels.", ephemeral=True
#                 )
#                 return

#         # Send enrollment message
#         embed = create_enrollment_embed()
#         view = EnrollmentView(on_enroll=self.handle_enrollment)

#         await channel.send(embed=embed, view=view)

#         await interaction.response.send_message(
#             f"✅ Luckmaxxing Protocol setup complete in {channel.mention}!",
#             ephemeral=True,
#         )
#         logger.info(
#             f"Protocol setup in guild {interaction.guild.id}, channel {channel.id}"
#         )

#     @app_commands.command(
#         name="stats", description="View Luckmaxxing Protocol statistics"
#     )
#     async def view_stats(self, interaction: discord.Interaction):
#         """View enrollment statistics"""
#         # Check if bot is enabled
#         if not await self.db.is_bot_enabled(interaction.guild.id):
#             await interaction.response.send_message(
#                 "❌ The Luckmaxxing Protocol is currently disabled in this server.",
#                 ephemeral=True,
#             )
#             return

#         stats = await self.db.get_stats(interaction.guild.id)

#         embed = discord.Embed(
#             title="📊 Luckmaxxing Protocol Statistics", color=discord.Color.blue()
#         )

#         embed.add_field(
#             name="Total Enrolled", value=stats["total_enrolled"], inline=True
#         )
#         embed.add_field(name="In Progress", value=stats["in_progress"], inline=True)
#         embed.add_field(name="Completed", value=stats["completed"], inline=True)

#         completion_rate = (
#             (stats["completed"] / stats["total_enrolled"] * 100)
#             if stats["total_enrolled"] > 0
#             else 0
#         )
#         embed.add_field(
#             name="Completion Rate", value=f"{completion_rate:.1f}%", inline=False
#         )

#         await interaction.response.send_message(embed=embed)

#     @app_commands.command(name="progress", description="Check your training progress")
#     async def check_progress(self, interaction: discord.Interaction):
#         """Check user's training progress"""
#         # Check if bot is enabled
#         if not await self.db.is_bot_enabled(interaction.guild.id):
#             await interaction.response.send_message(
#                 "❌ The Luckmaxxing Protocol is currently disabled in this server.",
#                 ephemeral=True,
#             )
#             return

#         progress = await self.db.get_user_progress(
#             interaction.user.id, interaction.guild.id
#         )

#         if not progress:
#             await interaction.response.send_message(
#                 "❌ You're not enrolled in the Luckmaxxing Protocol yet!\n"
#                 f"Go to the protocol channel to enroll.",
#                 ephemeral=True,
#             )
#             return

#         current_day = progress["current_day"]
#         completed = progress.get("completed", False)
#         enrollment_id = progress.get("enrollment_id", "N/A")

#         embed = discord.Embed(
#             title="📈 Your Progress",
#             color=discord.Color.green() if completed else discord.Color.blue(),
#         )

#         if completed:
#             embed.description = "🎊 **Congratulations!** You've completed the Luckmaxxing Protocol!\n\nYou are now a statistical anomaly! 🚀"
#         else:
#             if current_day == 0:
#                 status = "Introduction completed. Day 1 will be sent in 24 hours."
#             else:
#                 status = f"Currently on Day {current_day} of {config.TOTAL_DAYS}"

#             embed.add_field(name="Status", value=status, inline=False)
#             embed.add_field(
#                 name="Enrollment ID", value=f"`{enrollment_id}`", inline=False
#             )

#             progress_bar = "█" * current_day + "░" * (config.TOTAL_DAYS - current_day)
#             embed.add_field(
#                 name="Progress",
#                 value=f"`{progress_bar}` {current_day}/{config.TOTAL_DAYS}",
#                 inline=False,
#             )

#         enrolled_date = progress.get("enrolled_at", "Unknown")
#         embed.set_footer(text=f"Enrolled: {enrolled_date}")

#         await interaction.response.send_message(embed=embed, ephemeral=True)


# async def setup(bot: commands.Bot):
#     """Setup function for cog"""
#     await bot.add_cog(ProtocolCog(bot))


import discord
from discord.ext import commands, tasks
from discord import app_commands
from typing import Optional
import asyncio

from database import get_database
from database.base import DatabaseBase
from content.training import get_content, get_day_title
from views.dialogue import DialogueView
from views.enrollment import EnrollmentView, create_enrollment_embed
from utils.logger import logger
import config


class ProtocolCog(commands.Cog):
    """Main cog for Luckmaxxing Protocol functionality"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db: DatabaseBase = get_database()

        # Start daily message task
        self.send_daily_messages.start()

    async def load(self):
        """Called when cog is loaded"""
        await self.db.initialize()
        logger.info("✅ Protocol cog loaded and database initialized")

        # Setup persistent views
        self.bot.add_view(EnrollmentView(on_enroll=self.handle_enrollment))

    async def unload(self):
        """Called when cog is unloaded"""
        self.send_daily_messages.cancel()
        await self.db.close()
        logger.info("Protocol cog unloaded")

    @commands.Cog.listener()
    async def on_ready(self):
        """Called when bot is ready"""
        logger.info(f"Protocol cog ready in {len(self.bot.guilds)} guilds")

    async def handle_enrollment(
        self, interaction: discord.Interaction, enrollment_id: str
    ):
        """Handle user enrollment with ID verification"""
        user_id = interaction.user.id
        guild_id = interaction.guild.id

        # Check if bot is enabled
        if not await self.db.is_bot_enabled(guild_id):
            await interaction.response.send_message(
                "❌ The Luckmaxxing Protocol is currently disabled in this server.",
                ephemeral=True,
            )
            return

        # Check if user is already enrolled
        progress = await self.db.get_user_progress(user_id, guild_id)
        if progress:
            current_day = progress["current_day"]
            user_enrollment_id = progress.get("enrollment_id", "N/A")

            if progress.get("completed"):
                await interaction.response.send_message(
                    "✅ You've already completed the Luckmaxxing Protocol! You are now a statistical anomaly.",
                    ephemeral=True,
                )
            else:
                await interaction.response.send_message(
                    f"📌 You're already enrolled! You're currently on Day {current_day}.\n"
                    f"**Enrollment ID:** `{user_enrollment_id}`\n\n"
                    f"Check your DMs for your training.",
                    ephemeral=True,
                )
            return

        # Verify enrollment ID exists and is unused
        id_valid = await self.db.verify_enrollment_id(enrollment_id.upper(), guild_id)

        if not id_valid:
            await interaction.response.send_message(
                "❌ **Invalid Enrollment ID**\n\n"
                "This ID is either:\n"
                "• Not valid for this server\n"
                "• Already used by someone else\n"
                "• Doesn't exist\n\n"
                "Please check your ID and try again, or contact an admin.",
                ephemeral=True,
            )
            return

        # Enroll user with the provided ID
        success = await self.db.enroll_user_with_id(
            user_id, guild_id, enrollment_id.upper()
        )

        if not success:
            await interaction.response.send_message(
                "❌ An error occurred during enrollment. Please try again.",
                ephemeral=True,
            )
            return

        # Try to send intro dialogue first
        try:
            # Defer response while we try to send DM
            await interaction.response.defer(ephemeral=True)

            # Send intro dialogue
            await self.send_day_content(interaction.user, guild_id, 0)

            # Only send success message if DM was sent successfully
            await interaction.followup.send(
                "✅ **Enrollment Successful!**\n\n"
                f"**Your Enrollment ID:** `{enrollment_id.upper()}`\n\n"
                "Check your DMs for the introduction to the Luckmaxxing Protocol.\n\n"
                "**Important:** Make sure your DMs are open to receive daily training!",
                ephemeral=True,
            )

            logger.info(
                f"User {user_id} enrolled in guild {guild_id} with ID {enrollment_id.upper()}"
            )
        except discord.Forbidden:
            # If DM fails, send error and unenroll
            await interaction.followup.send(
                "❌ **Enrollment Failed**\n\n"
                "I could not send you a DM! Please enable DMs from server members and try again.\n\n"
                "Your enrollment has been cancelled.",
                ephemeral=True,
            )
            # Unenroll user since we cannot send DMs
            await self.db.unenroll_user(user_id, guild_id)
            logger.warning(f"Failed to enroll user {user_id} - DMs closed")

    async def send_day_content(self, user: discord.User, guild_id: int, day: int):
        """
        Send day content to user via DM

        Args:
            user: Discord user
            guild_id: Guild ID
            day: Day number (0 for intro+day1, 1-8 for training days 2-8)
        """
        # For day 0 (enrollment), send both intro and Day 1 content
        if day == 0:
            await self._send_intro_and_day1(user, guild_id)
            return

        content = get_content(day)
        if not content:
            logger.error(f"No content found for day {day}")
            return

        # Create completion callback
        async def on_complete(completion_user: discord.User):
            """Called when dialogue is completed"""
            # Mark day as complete
            next_day = day + 1
            await self.db.update_user_day(user.id, guild_id, next_day)

            if next_day > config.TOTAL_DAYS:
                # Training complete!
                await user.send(
                    "🎊 **CONGRATULATIONS, GAMBLOR!** 🎊\n\n"
                    "You have completed the 8-Day Luckmaxxing Protocol!\n\n"
                    "You are no longer an average gamblor. You are now a **statistical anomaly**.\n\n"
                    "Gorillions await you. 🚀💰"
                )
                logger.info(f"User {user.id} completed training in guild {guild_id}")
            else:
                await user.send(
                    f"✅ **Day {day} Complete!**\n\n"
                    f"Day {next_day} training will be delivered in 24 hours.\n\n"
                    "Keep pushing forward! 💪"
                )

        # Create and send dialogue
        view = DialogueView(content, on_complete=on_complete)
        embed = view.get_initial_embed()

        # Add title
        title_embed = discord.Embed(
            title=get_day_title(day), color=discord.Color.gold()
        )

        try:
            await user.send(embed=title_embed)
            message = await user.send(embed=embed, view=view)
            view.message = message
            logger.info(f"Sent day {day} content to user {user.id}")
        except discord.Forbidden:
            logger.error(f"Cannot send DM to user {user.id}")
            raise

    async def _send_intro_and_day1(self, user: discord.User, guild_id: int):
        """Send both intro and Day 1 content on enrollment"""

        # Send intro first
        intro_content = get_content(0)
        if not intro_content:
            logger.error("No intro content found")
            return

        async def on_intro_complete(completion_user: discord.User):
            """Called when intro dialogue is completed - send Day 1 immediately"""
            # Small pause for better UX
            await asyncio.sleep(2)

            # Send Day 1 content
            day1_content = get_content(1)
            if not day1_content:
                logger.error("No Day 1 content found")
                return

            async def on_day1_complete(completion_user: discord.User):
                """Called when Day 1 is completed"""
                # Update to day 2 and mark enrollment as used
                await self.db.update_user_day(user.id, guild_id, 2)
                await self.db.mark_enrollment_used(user.id, guild_id)

                await user.send(
                    "✅ **Day 1 Complete!**\n\n"
                    "Day 2 training will be delivered in 24 hours.\n\n"
                    "Keep pushing forward! 💪"
                )

            # Send Day 1 dialogue
            view_day1 = DialogueView(day1_content, on_complete=on_day1_complete)
            embed_day1 = view_day1.get_initial_embed()
            title_embed_day1 = discord.Embed(
                title=get_day_title(1), color=discord.Color.gold()
            )

            await user.send(embed=title_embed_day1)
            message_day1 = await user.send(embed=embed_day1, view=view_day1)
            view_day1.message = message_day1

        # Send intro dialogue
        view_intro = DialogueView(intro_content, on_complete=on_intro_complete)
        embed_intro = view_intro.get_initial_embed()
        title_embed_intro = discord.Embed(
            title=get_day_title(0), color=discord.Color.gold()
        )

        await user.send(embed=title_embed_intro)
        message_intro = await user.send(embed=embed_intro, view=view_intro)
        view_intro.message = message_intro
        logger.info(f"Sent intro and Day 1 content to user {user.id}")

    @tasks.loop(hours=24)
    async def send_daily_messages(self):
        """Task to send daily messages to enrolled users (24hr cycle)"""
        logger.info("Starting daily message distribution...")

        # Get all enrolled users who are ready for their next message
        users = await self.db.get_all_enrolled_users()

        logger.info(f"Found {len(users)} users ready for messages")

        for enrollment in users:
            user_id = enrollment["user_id"]
            guild_id = enrollment["guild_id"]
            current_day = enrollment["current_day"]

            # Skip if on day 0/1 (handled on enrollment) or completed
            # After enrollment, users are on day 2, so this sends days 2-8
            if current_day <= 1 or current_day > config.TOTAL_DAYS:
                continue

            # Check if bot is enabled for guild
            if not await self.db.is_bot_enabled(guild_id):
                continue

            try:
                user = await self.bot.fetch_user(user_id)
                await self.send_day_content(user, guild_id, current_day)
                logger.info(f"Sent day {current_day} to user {user_id}")

                # Small delay to avoid rate limits
                await asyncio.sleep(1)
            except discord.NotFound:
                logger.warning(f"User {user_id} not found")
            except discord.Forbidden:
                logger.warning(f"Cannot send DM to user {user_id}")
            except Exception as e:
                logger.error(f"Error sending to user {user_id}: {e}")

        logger.info("Daily message distribution complete")

    @send_daily_messages.before_loop
    async def before_daily_messages(self):
        """Wait until bot is ready before starting task"""
        await self.bot.wait_until_ready()
        logger.info("Daily message task ready")

    @app_commands.command(
        name="setup", description="Setup the Luckmaxxing Protocol channel (Admin only)"
    )
    @app_commands.default_permissions(administrator=True)
    async def setup_protocol(self, interaction: discord.Interaction):
        """Setup protocol channel with enrollment message"""
        # Check if bot is enabled
        if not await self.db.is_bot_enabled(interaction.guild.id):
            await interaction.response.send_message(
                "❌ The bot is currently disabled. Use `/toggle on` to enable it first.",
                ephemeral=True,
            )
            return

        # Create or get protocol channel
        channel = discord.utils.get(
            interaction.guild.text_channels, name=config.PROTOCOL_CHANNEL_NAME
        )

        if not channel:
            try:
                channel = await interaction.guild.create_text_channel(
                    config.PROTOCOL_CHANNEL_NAME,
                    topic="Enroll in the 8-Day Luckmaxxing Protocol to become a statistical anomaly! 🎯",
                )
            except discord.Forbidden:
                await interaction.response.send_message(
                    "❌ I don't have permission to create channels.", ephemeral=True
                )
                return

        # Send enrollment message
        embed = create_enrollment_embed()
        view = EnrollmentView(on_enroll=self.handle_enrollment)

        await channel.send(embed=embed, view=view)

        await interaction.response.send_message(
            f"✅ Luckmaxxing Protocol setup complete in {channel.mention}!",
            ephemeral=True,
        )
        logger.info(
            f"Protocol setup in guild {interaction.guild.id}, channel {channel.id}"
        )

    @app_commands.command(
        name="stats", description="View Luckmaxxing Protocol statistics"
    )
    async def view_stats(self, interaction: discord.Interaction):
        """View enrollment statistics"""
        # Check if bot is enabled
        if not await self.db.is_bot_enabled(interaction.guild.id):
            await interaction.response.send_message(
                "❌ The Luckmaxxing Protocol is currently disabled in this server.",
                ephemeral=True,
            )
            return

        stats = await self.db.get_stats(interaction.guild.id)

        embed = discord.Embed(
            title="📊 Luckmaxxing Protocol Statistics", color=discord.Color.blue()
        )

        embed.add_field(
            name="Total Enrolled", value=stats["total_enrolled"], inline=True
        )
        embed.add_field(name="In Progress", value=stats["in_progress"], inline=True)
        embed.add_field(name="Completed", value=stats["completed"], inline=True)

        completion_rate = (
            (stats["completed"] / stats["total_enrolled"] * 100)
            if stats["total_enrolled"] > 0
            else 0
        )
        embed.add_field(
            name="Completion Rate", value=f"{completion_rate:.1f}%", inline=False
        )

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="progress", description="Check your training progress")
    async def check_progress(self, interaction: discord.Interaction):
        """Check user's training progress"""
        # Check if bot is enabled
        if not await self.db.is_bot_enabled(interaction.guild.id):
            await interaction.response.send_message(
                "❌ The Luckmaxxing Protocol is currently disabled in this server.",
                ephemeral=True,
            )
            return

        progress = await self.db.get_user_progress(
            interaction.user.id, interaction.guild.id
        )

        if not progress:
            await interaction.response.send_message(
                "❌ You're not enrolled in the Luckmaxxing Protocol yet!\n"
                f"Go to the protocol channel to enroll.",
                ephemeral=True,
            )
            return

        current_day = progress["current_day"]
        completed = progress.get("completed", False)
        enrollment_id = progress.get("enrollment_id", "N/A")

        embed = discord.Embed(
            title="📈 Your Progress",
            color=discord.Color.green() if completed else discord.Color.blue(),
        )

        if completed:
            embed.description = "🎊 **Congratulations!** You've completed the Luckmaxxing Protocol!\n\nYou are now a statistical anomaly! 🚀"
        else:
            if current_day == 0:
                status = "Introduction completed. Day 1 will be sent in 24 hours."
            else:
                status = f"Currently on Day {current_day} of {config.TOTAL_DAYS}"

            embed.add_field(name="Status", value=status, inline=False)
            embed.add_field(
                name="Enrollment ID", value=f"`{enrollment_id}`", inline=False
            )

            progress_bar = "█" * current_day + "░" * (config.TOTAL_DAYS - current_day)
            embed.add_field(
                name="Progress",
                value=f"`{progress_bar}` {current_day}/{config.TOTAL_DAYS}",
                inline=False,
            )

        enrolled_date = progress.get("enrolled_at", "Unknown")
        embed.set_footer(text=f"Enrolled: {enrolled_date}")

        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    """Setup function for cog"""
    await bot.add_cog(ProtocolCog(bot))
