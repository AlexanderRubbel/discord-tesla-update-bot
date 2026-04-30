import logging
import os

import discord
from discord.ext import commands, tasks

from models.version import TeslaVersion
from services import database, rss_checker, scraper
from utils.embed_builder import build_version_embed
from utils.poll_builder import build_version_poll

logger = logging.getLogger(__name__)


class VersionTracker(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.feed_url = os.getenv(
            "RSS_FEED_URL", "https://www.notateslaapp.com/rss"
        )
        self.interval = int(os.getenv("CHECK_INTERVAL_MINUTES", "15"))
        self._first_run = True

    async def cog_load(self):
        self.check_for_updates.change_interval(minutes=self.interval)
        self.check_for_updates.start()

    async def cog_unload(self):
        self.check_for_updates.cancel()

    @tasks.loop(minutes=15)
    async def check_for_updates(self):
        logger.info("Checking for new Tesla software versions...")
        channel = await self._get_channel()
        if channel is None:
            return

        entries = await rss_checker.fetch_new_versions(self.feed_url)

        # On first run with empty DB, only post the newest version
        # and silently register the rest so we don't spam the channel.
        if self._first_run:
            self._first_run = False
            unknown = [
                (vid, url, pub) for vid, url, pub in entries
                if not await database.is_version_known(vid)
            ]
            if len(unknown) > 1:
                logger.info(
                    "First run: registering %d old versions silently, posting newest only",
                    len(unknown) - 1,
                )
                # Register all but the first (newest) as known without posting
                for vid, url, _pub in unknown[1:]:
                    await database.add_version(
                        version_id=vid,
                        release_date="",
                        features=[],
                        fleet_pct=None,
                        source_url=url,
                        embed_msg_id=0,
                        poll_msg_id=0,
                        channel_id=channel.id,
                    )
                # Post only the newest
                if unknown:
                    vid, url, pub = unknown[0]
                    version = await scraper.get_release_notes(vid, url)
                    if not version.release_date and pub:
                        version.release_date = pub
                    await self._post_version(channel, version)
                return

        for version_id, url, pub_date in entries:
            if await database.is_version_known(version_id):
                continue

            logger.info("New version found: %s", version_id)
            version = await scraper.get_release_notes(version_id, url)
            if not version.release_date and pub_date:
                version.release_date = pub_date

            await self._post_version(channel, version)

    @check_for_updates.before_loop
    async def before_check(self):
        await self.bot.wait_until_ready()

    async def run_check_now(self) -> str:
        """Run an immediate check. Returns a status message."""
        channel = await self._get_channel()
        if channel is None:
            return "No channel configured. Use `/set_channel` first."

        entries = await rss_checker.fetch_new_versions(self.feed_url)
        new_count = 0
        for version_id, url, pub_date in entries:
            if await database.is_version_known(version_id):
                continue

            version = await scraper.get_release_notes(version_id, url)
            if not version.release_date and pub_date:
                version.release_date = pub_date

            await self._post_version(channel, version)
            new_count += 1

        if new_count == 0:
            return f"No new versions found ({len(entries)} total entries scanned)."
        return f"Posted {new_count} new version(s)."

    async def _get_channel(self) -> discord.TextChannel | None:
        channel_id = await database.get_config("channel_id")
        if not channel_id:
            channel_id = os.getenv("DISCORD_CHANNEL_ID")
        if not channel_id:
            logger.warning("No channel configured")
            return None

        channel = self.bot.get_channel(int(channel_id))
        if channel is None:
            try:
                channel = await self.bot.fetch_channel(int(channel_id))
            except discord.NotFound:
                logger.error("Channel %s not found", channel_id)
                return None
        return channel

    async def _post_version(
        self, channel: discord.TextChannel, version: TeslaVersion
    ) -> None:
        embed = build_version_embed(version)
        # poll = build_version_poll(version.version_id)

        embed_msg = await channel.send(embed=embed)
        # poll_msg = await channel.send(poll=poll)
        poll_msg_id = 0  # poll disabled for now

        await database.add_version(
            version_id=version.version_id,
            release_date=version.release_date,
            features=version.features,
            fleet_pct=version.fleet_pct,
            source_url=version.source_url,
            embed_msg_id=embed_msg.id,
            poll_msg_id=poll_msg_id,
            channel_id=channel.id,
        )
        logger.info("Posted version %s to #%s", version.version_id, channel.name)


async def setup(bot: commands.Bot):
    await bot.add_cog(VersionTracker(bot))
