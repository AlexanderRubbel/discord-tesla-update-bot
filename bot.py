import asyncio
import logging
import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

from services.database import init_db

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("bot")

TOKEN = os.getenv("DISCORD_BOT_TOKEN", "")
if not TOKEN:
    raise SystemExit("DISCORD_BOT_TOKEN not set in .env")

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    logger.info("Logged in as %s (ID: %s)", bot.user, bot.user.id)
    try:
        synced = await bot.tree.sync()
        logger.info("Synced %d slash commands", len(synced))
    except Exception:
        logger.exception("Failed to sync commands")


async def main():
    await init_db()
    await bot.load_extension("cogs.version_tracker")
    await bot.load_extension("cogs.commands")
    await bot.start(TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
