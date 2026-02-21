import asyncio
import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN", "")


class SyncBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.guilds = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        for ext in ("cogs.protocol", "cogs.admin"):
            try:
                await self.load_extension(ext)
                print(f"  Loaded {ext}")
            except Exception as exc:
                print(f"  Failed to load {ext}: {exc}")

    async def on_ready(self):
        print(f"\nLogged in as {self.user} ({len(self.guilds)} server(s))\n")
        await self._sync()
        await self.close()

    async def _sync(self):
        print("Syncing globally...")
        global_cmds = await self.tree.sync()
        print(f"  {len(global_cmds)} global command(s) synced (up to 1 h to appear)\n")

        print("Syncing per-guild (instant)...")
        for guild in self.guilds:
            try:
                guild_cmds = await self.tree.sync(guild=guild)
                print(f"  {guild.name}: {len(guild_cmds)} command(s)")
            except Exception as exc:
                print(f"  {guild.name}: error — {exc}")

        print("\nAll done. You can close this window.")
        print("\nRegistered commands:")
        for cmd in self.tree.get_commands():
            print(f"  /{cmd.name}  —  {cmd.description}")


async def main():
    if not TOKEN:
        print("DISCORD_BOT_TOKEN not found in .env")
        return
    bot = SyncBot()
    try:
        await bot.start(TOKEN)
    except discord.LoginFailure:
        print("Invalid token.")


if __name__ == "__main__":
    asyncio.run(main())
