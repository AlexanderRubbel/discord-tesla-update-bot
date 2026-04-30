import logging

import discord
from discord import app_commands
from discord.ext import commands

from services import database
from utils.embed_builder import build_version_embed
from utils.poll_builder import build_version_poll
from models.version import TeslaVersion

logger = logging.getLogger(__name__)


class BotCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="check_now", description="Force an immediate check for new Tesla versions")
    @app_commands.checks.has_permissions(administrator=True)
    async def check_now(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        tracker = self.bot.get_cog("VersionTracker")
        if tracker is None:
            await interaction.followup.send("Version tracker is not loaded.")
            return
        result = await tracker.run_check_now()
        await interaction.followup.send(result)

    @app_commands.command(name="add_version", description="Manually add a Tesla software version")
    @app_commands.describe(version="Version string, e.g. 2026.8.6")
    @app_commands.checks.has_permissions(administrator=True)
    async def add_version(self, interaction: discord.Interaction, version: str):
        await interaction.response.defer(ephemeral=True)

        if await database.is_version_known(version):
            await interaction.followup.send(f"Version `{version}` is already tracked.")
            return

        tv = TeslaVersion(
            version_id=version,
            release_date="",
            features=[{"title": "Manually added", "description": "No release notes available."}],
            source_url="",
        )

        channel = interaction.channel
        embed = build_version_embed(tv)
        # poll = build_version_poll(tv.version_id)

        embed_msg = await channel.send(embed=embed)
        # poll_msg = await channel.send(poll=poll)
        poll_msg_id = 0  # poll disabled for now

        await database.add_version(
            version_id=tv.version_id,
            release_date=tv.release_date,
            features=tv.features,
            fleet_pct=tv.fleet_pct,
            source_url=tv.source_url,
            embed_msg_id=embed_msg.id,
            poll_msg_id=poll_msg_id,
            channel_id=channel.id,
        )

        await interaction.followup.send(f"Version `{version}` posted with poll.")

    @app_commands.command(name="summary", description="Show poll results for a Tesla version")
    @app_commands.describe(version="Version string (leave empty for latest)")
    async def summary(self, interaction: discord.Interaction, version: str | None = None):
        await interaction.response.defer(ephemeral=True)

        if version:
            row = await database.get_version(version)
        else:
            row = await database.get_latest_version()

        if row is None:
            await interaction.followup.send("No version found.")
            return

        # Fetch the poll message to read vote counts
        try:
            channel = self.bot.get_channel(row["channel_id"])
            if channel is None:
                channel = await self.bot.fetch_channel(row["channel_id"])
            poll_msg = await channel.fetch_message(row["poll_msg_id"])
        except Exception:
            await interaction.followup.send(
                f"Could not fetch poll for version `{row['version_id']}`. "
                "The message may have been deleted."
            )
            return

        poll = poll_msg.poll
        if poll is None:
            await interaction.followup.send("No poll data found on that message.")
            return

        total = poll.total_votes or 0
        embed = discord.Embed(
            title=f"Poll Results: {row['version_id']}",
            color=0xCC0000,
        )

        for answer in poll.answers:
            count = answer.vote_count
            pct = (count / total * 100) if total > 0 else 0
            bar_len = round(pct / 5)
            bar = "\u2588" * bar_len + "\u2591" * (20 - bar_len)
            embed.add_field(
                name=f"{answer.text}",
                value=f"`{bar}` {count} votes ({pct:.0f}%)",
                inline=False,
            )

        embed.set_footer(text=f"Total votes: {total}")
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="set_channel", description="Set the channel for Tesla update notifications")
    @app_commands.describe(channel="The channel to post updates in")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_channel(
        self, interaction: discord.Interaction, channel: discord.TextChannel
    ):
        await database.set_config("channel_id", str(channel.id))
        await interaction.response.send_message(
            f"Update channel set to {channel.mention}.", ephemeral=True
        )

    @check_now.error
    @add_version.error
    @set_channel.error
    async def admin_error(self, interaction: discord.Interaction, error):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message(
                "You need administrator permissions for this command.",
                ephemeral=True,
            )
        else:
            logger.exception("Command error: %s", error)


async def setup(bot: commands.Bot):
    await bot.add_cog(BotCommands(bot))
