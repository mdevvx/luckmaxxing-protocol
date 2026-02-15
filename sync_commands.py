import discord
from discord.ext import commands
import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_BOT_TOKEN")


class SyncBot(commands.Bot):
    """Temporary bot just for syncing commands"""

    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.guilds = True

        super().__init__(
            command_prefix="!",
            intents=intents,
            help_command=None,
        )

    async def setup_hook(self):
        """Load cogs"""
        print("📦 Loading cogs...")

        try:
            await self.load_extension("cogs.protocol")
            print("✅ Loaded: cogs.protocol")
        except Exception as e:
            print(f"❌ Failed to load cogs.protocol: {e}")

        try:
            await self.load_extension("cogs.admin")
            print("✅ Loaded: cogs.admin")
        except Exception as e:
            print(f"❌ Failed to load cogs.admin: {e}")

    async def on_ready(self):
        """Called when bot is ready"""
        print(f"\n{'='*60}")
        print(f"🤖 Bot logged in as: {self.user}")
        print(f"🆔 Bot ID: {self.user.id}")
        print(f"🌍 Connected to {len(self.guilds)} server(s)")
        print(f"{'='*60}\n")

        await self.sync_commands()

    async def sync_commands(self):
        """Sync commands with Discord"""
        print("🔄 Starting command sync process...\n")

        try:
            # Option 1: Sync globally (takes up to 1 hour to appear)
            print("1️⃣ Syncing commands globally...")
            global_commands = await self.tree.sync()
            print(f"   ✅ Synced {len(global_commands)} global commands")
            print(f"   ⏰ Note: Global commands take up to 1 hour to appear\n")

            # Option 2: Sync to each guild (instant, for testing)
            print("2️⃣ Syncing commands to each server (instant)...")

            for guild in self.guilds:
                try:
                    guild_commands = await self.tree.sync(guild=guild)
                    print(f"   ✅ {guild.name}: {len(guild_commands)} commands")
                except Exception as e:
                    print(f"   ❌ {guild.name}: {e}")

            print(f"\n{'='*60}")
            print("✅ SYNC COMPLETE!")
            print(f"{'='*60}\n")

            print("📋 Registered Commands:")
            for cmd in self.tree.get_commands():
                print(f"   /{cmd.name} - {cmd.description}")

            print(f"\n{'='*60}")
            print("📝 IMPORTANT NOTES:")
            print(f"{'='*60}")
            print("1. Commands synced to servers appear INSTANTLY")
            print("2. Global commands take up to 1 HOUR to appear")
            print("3. You can now close this script")
            print("4. Start your main bot with: python bot.py")
            print("5. Check commands in Discord by typing /")
            print(f"{'='*60}\n")

        except Exception as e:
            print(f"❌ Error syncing commands: {e}")
            import traceback

            traceback.print_exc()

        # Close the bot after syncing
        print("👋 Closing sync bot...\n")
        await self.close()


async def main():
    """Main function"""
    print("\n" + "=" * 60)
    print("🎯 DISCORD COMMAND SYNC UTILITY")
    print("=" * 60 + "\n")

    if not DISCORD_TOKEN:
        print("❌ DISCORD_BOT_TOKEN not found in .env file!")
        print("Please set your bot token in the .env file.\n")
        return

    bot = SyncBot()

    try:
        await bot.start(DISCORD_TOKEN)
    except discord.LoginFailure:
        print("❌ Invalid Discord token! Check your DISCORD_BOT_TOKEN in .env")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
