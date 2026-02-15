import discord
from discord.ext import commands
import asyncio
import sys
import os

# Import configuration
import config

# Create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)


class LuckmaxxingBot(commands.Bot):
    """Main bot class for Luckmaxxing Protocol"""

    def __init__(self):
        # Configure Discord intents (permissions)
        intents = discord.Intents.default()
        intents.message_content = True  # Read message content
        intents.members = True  # Access member information
        intents.guilds = True  # Access guild information

        # Initialize bot
        super().__init__(
            command_prefix="!",  # Prefix for text commands (we use slash commands)
            intents=intents,
            help_command=None,  # Disable default help command
            case_insensitive=True,
        )

        # List of cogs (extensions) to load
        self.initial_extensions = [
            "cogs.protocol",  # Main training protocol
            "cogs.admin",  # Admin commands
        ]

    async def setup_hook(self):
        """
        Setup hook - called when bot is starting up
        Loads all cogs (command modules)
        """
        print("🔧 Setting up bot...")

        # Load all cogs
        for extension in self.initial_extensions:
            try:
                await self.load_extension(extension)
                print(f"✅ Loaded: {extension}")
            except Exception as e:
                print(f"❌ Failed to load {extension}: {e}")
                import traceback

                traceback.print_exc()

        print("✅ Setup complete!")

    async def on_ready(self):
        """Called when bot successfully connects to Discord"""
        print("\n" + "=" * 50)
        print(f"🤖 Bot logged in as: {self.user}")
        print(f"🆔 Bot ID: {self.user.id}")
        print(f"🌍 Connected to {len(self.guilds)} servers")
        print(f"📚 Discord.py version: {discord.__version__}")
        print("=" * 50 + "\n")

        # Set bot status/activity
        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name="",
        )
        await self.change_presence(activity=activity)

        print("✅ Bot is ready and online!\n")

    async def on_guild_join(self, guild: discord.Guild):
        """Called when bot joins a new server"""
        print(f"📥 Joined new server: {guild.name} (ID: {guild.id})")
        print(f"   Members: {guild.member_count}")

        # Send welcome message to system channel if available
        if guild.system_channel:
            embed = discord.Embed(
                title="🎯 Thanks for adding Luckmaxxing Protocol!",
                description=(
                    "I'm here to help transform your members into statistical anomalies.\n\n"
                    "**Quick Start:**\n"
                    "1. Run `/setup` to create the enrollment channel\n"
                    "2. Members can enroll and receive daily training via DM\n\n"
                    "**Commands:**\n"
                    "`/setup` - Setup protocol channel\n"
                    "`/stats` - View statistics\n"
                    "`/toggle` - Enable/disable bot\n\n"
                    "Gorillions await! 🚀"
                ),
                color=discord.Color.gold(),
            )
            try:
                await guild.system_channel.send(embed=embed)
            except:
                pass  # If we can't send, that's okay

    async def on_guild_remove(self, guild: discord.Guild):
        """Called when bot is removed from a server"""
        print(f"📤 Removed from server: {guild.name} (ID: {guild.id})")

    async def on_error(self, event: str, *args, **kwargs):
        """Global error handler"""
        print(f"❌ Error in {event}:")
        import traceback

        traceback.print_exc()


async def main():
    """Main function to start the bot"""

    # Print startup banner
    print("\n" + "=" * 50)
    print("🎯 LUCKMAXXING PROTOCOL BOT")
    print("=" * 50 + "\n")

    # Validate configuration
    print("🔍 Validating configuration...")
    try:
        config.validate_config()
        print("✅ Configuration valid!\n")
    except ValueError as e:
        print(str(e))
        print("\n💡 Tip: Copy .env.example to .env and fill in your values\n")
        return

    # Create bot instance
    bot = LuckmaxxingBot()

    # Start bot
    try:
        print("🚀 Starting bot...\n")
        await bot.start(config.DISCORD_TOKEN)
    except KeyboardInterrupt:
        print("\n⚠️  Keyboard interrupt received, shutting down...")
    except discord.LoginFailure:
        print("\n❌ Failed to login - check your DISCORD_BOT_TOKEN in .env")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback

        traceback.print_exc()
    finally:
        if not bot.is_closed():
            await bot.close()
        print("\n👋 Bot shut down successfully")


if __name__ == "__main__":
    """Entry point when running the script"""
    try:
        # Run the bot
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Bot stopped by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


# Need some changes, when user click on enroll it should asks for unique id and create another command for admin to make id (XKP87) for every members, so when
# user enter id, it should verify id and proceed accordingly.
# Now, when user got DM the intro would be on day 1  only + content for day 1 and then next day only content for day 2, 3, 4, and so on...

# Now provide complete supabase_scheme.sql as of now, check all history chats and provide one to go schema
