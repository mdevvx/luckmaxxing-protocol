import discord
from discord.ext import commands
from discord import app_commands
from database import get_database
from database.base import DatabaseBase
from utils.logger import logger


class AdminCog(commands.Cog):
    """Admin commands for bot management"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db: DatabaseBase = get_database()

    async def load(self):
        """Called when cog is loaded"""
        await self.db.initialize()
        logger.info("✅ Admin cog loaded")

    async def unload(self):
        """Called when cog is unloaded"""
        await self.db.close()
        logger.info("Admin cog unloaded")

    @app_commands.command(
        name="toggle", description="Enable or disable the bot (Admin only)"
    )
    @app_commands.describe(state="Choose 'on' to enable or 'off' to disable")
    @app_commands.choices(
        state=[
            app_commands.Choice(name="on", value="on"),
            app_commands.Choice(name="off", value="off"),
        ]
    )
    @app_commands.default_permissions(administrator=True)
    async def toggle_bot(self, interaction: discord.Interaction, state: str):
        """Toggle bot on/off for the server"""

        enabled = state == "on"

        await interaction.response.defer()

        await self.db.toggle_bot(interaction.guild.id, enabled)

        status = "enabled✅" if enabled else "disabled ❌"
        embed = discord.Embed(
            title="Bot Status Updated",
            description=f"The Luckmaxxing Protocol bot is now **{status}** for this server.",
            color=discord.Color.green() if enabled else discord.Color.red(),
        )

        if not enabled:
            embed.add_field(
                name="Note",
                value="Users can still view their progress, but new enrollments and daily messages are disabled.",
                inline=False,
            )

        await interaction.followup.send(embed=embed)
        logger.info(
            f"Bot {'enabled' if enabled else 'disabled'} for guild {interaction.guild.id}"
        )

    @app_commands.command(
        name="sync", description="Sync slash commands (Bot Owner only)"
    )
    async def sync_commands(self, interaction: discord.Interaction):
        """Sync slash commands globally or for current guild"""
        # Check if user is bot owner
        app_info = await self.bot.application_info()

        await interaction.response.defer()

        if interaction.user.id != app_info.owner.id:
            await interaction.followup.send(
                "❌ Only the bot owner can use this command."
            )
            return

        try:
            # Sync globally
            synced = await self.bot.tree.sync()

            # Also sync to current guild for faster updates
            synced_guild = await self.bot.tree.sync(guild=interaction.guild)

            embed = discord.Embed(
                title="✅ Commands Synced", color=discord.Color.green()
            )
            embed.add_field(name="Global", value=f"{len(synced)} commands", inline=True)
            embed.add_field(
                name="This Server", value=f"{len(synced_guild)} commands", inline=True
            )

            await interaction.followup.send(embed=embed)
            logger.info(
                f"Commands synced: {len(synced)} global, {len(synced_guild)} guild"
            )

        except Exception as e:
            logger.error(f"Error syncing commands: {e}")
            await interaction.followup.send(f"❌ Error syncing commands: {str(e)}")

    @app_commands.command(
        name="unenroll", description="Remove a user from the protocol (Admin only)"
    )
    @app_commands.describe(user="The user to unenroll")
    @app_commands.default_permissions(administrator=True)
    async def unenroll_user(self, interaction: discord.Interaction, user: discord.User):
        """Unenroll a user from the protocol"""

        await interaction.response.defer()

        success = await self.db.unenroll_user(user.id, interaction.guild.id)

        if success:
            await interaction.followup.send(
                f"✅ {user.mention} has been unenrolled from the Luckmaxxing Protocol."
            )
            logger.info(
                f"Admin unenrolled user {user.id} from guild {interaction.guild.id}"
            )
        else:
            await interaction.followup.send(
                f"❌ {user.mention} is not enrolled in the protocol."
            )

    @app_commands.command(
        name="globalstats", description="View global bot statistics (Admin only)"
    )
    @app_commands.default_permissions(administrator=True)
    async def global_stats(self, interaction: discord.Interaction):
        """View global statistics across all servers"""

        await interaction.response.defer()

        stats = await self.db.get_stats()  # No guild_id for global stats

        embed = discord.Embed(
            title="🌍 Global Luckmaxxing Protocol Statistics",
            description="Statistics across all servers",
            color=discord.Color.blue(),
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

        embed.add_field(name="Total Servers", value=len(self.bot.guilds), inline=True)

        await interaction.followup.send(embed=embed)

    @app_commands.command(
        name="status", description="Check bot status and configuration"
    )
    async def status(self, interaction: discord.Interaction):
        """Check bot status"""

        await interaction.response.defer()

        settings = await self.db.get_guild_settings(interaction.guild.id)

        embed = discord.Embed(title="🤖 Bot Status", color=discord.Color.blue())

        status = "Enabled ✅" if settings.get("bot_enabled", True) else "Disabled ❌"
        embed.add_field(name="Status", value=status, inline=True)

        embed.add_field(name="Servers", value=len(self.bot.guilds), inline=True)
        embed.add_field(
            name="Latency", value=f"{round(self.bot.latency * 1000)}ms", inline=True
        )

        embed.set_footer(text=f"Bot ID: {self.bot.user.id}")

        await interaction.followup.send(embed=embed)

    @app_commands.command(
        name="generateid",
        description="Generate enrollment IDs for members (Admin only)",
    )
    @app_commands.describe(count="Number of IDs to generate (default: 1, max: 50)")
    @app_commands.default_permissions(administrator=True)
    async def generate_id(self, interaction: discord.Interaction, count: int = 1):
        """Generate unique enrollment IDs"""

        # Validate first, but don't respond yet
        if count < 1 or count > 50:
            await interaction.response.send_message(
                "❌ Count must be between 1 and 50.", ephemeral=True
            )
            return

        # Defer the response since database operations might take time
        await interaction.response.defer(ephemeral=True)

        # Generate IDs
        ids = await self.db.generate_enrollment_ids(interaction.guild.id, count)

        if not ids:
            await interaction.followup.send(
                "❌ Failed to generate IDs. Please try again.", ephemeral=True
            )
            return

        # Create embed with IDs
        embed = discord.Embed(
            title="🎯 Generated Enrollment IDs",
            description=f"Generated {len(ids)} new enrollment ID(s) for this server.",
            color=discord.Color.green(),
        )

        # Format IDs in a nice list
        id_list = "\n".join([f"`{id_code}`" for id_code in ids])
        embed.add_field(name="Enrollment IDs", value=id_list, inline=False)

        embed.add_field(
            name="📝 Instructions",
            value=(
                "Share these IDs with members who should be able to enroll.\n"
                "Each ID can only be used once and is specific to this server."
            ),
            inline=False,
        )

        embed.set_footer(text=f"Guild ID: {interaction.guild.id}")

        await interaction.followup.send(embed=embed, ephemeral=True)

        logger.info(
            f"Generated {len(ids)} enrollment IDs for guild {interaction.guild.id}"
        )

    @app_commands.command(
        name="listids", description="View unused enrollment IDs (Admin only)"
    )
    @app_commands.default_permissions(administrator=True)
    async def list_ids(self, interaction: discord.Interaction):
        """List all unused enrollment IDs for this server"""

        await interaction.response.defer()

        unused_ids = await self.db.get_unused_enrollment_ids(interaction.guild.id)

        embed = discord.Embed(
            title="📋 Unused Enrollment IDs",
            color=discord.Color.blue(),
        )

        if not unused_ids:
            embed.description = "No unused enrollment IDs available.\n\nUse `/generateid` to create new IDs."
        else:
            id_list = "\n".join([f"`{id_code}`" for id_code in unused_ids])
            embed.description = f"**{len(unused_ids)} unused ID(s):**\n\n{id_list}"

            embed.add_field(
                name="💡 Tip",
                value="Share these IDs with members to allow them to enroll.",
                inline=False,
            )

        await interaction.followup.send(embed=embed)


async def setup(bot: commands.Bot):
    """Setup function for cog"""
    await bot.add_cog(AdminCog(bot))
