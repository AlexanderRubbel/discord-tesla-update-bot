import discord

from models.version import TeslaVersion

TESLA_RED = 0xCC0000


def build_version_embed(version: TeslaVersion) -> discord.Embed:
    embed = discord.Embed(
        title=f"Tesla Update {version.version_id}",
        url=version.source_url or None,
        color=TESLA_RED,
    )

    if version.release_date:
        embed.description = f"Released: {version.release_date}"

    # Add features as fields (max 25 fields, keep it reasonable)
    for feat in version.features[:10]:
        name = feat.get("title", "Update")[:256]
        value = feat.get("description", "") or "\u200b"
        if len(value) > 1024:
            value = value[:1021] + "..."
        embed.add_field(name=name, value=value, inline=False)

    # Footer with fleet adoption
    footer_parts: list[str] = []
    if version.fleet_pct is not None:
        footer_parts.append(f"Fleet adoption: {version.fleet_pct}%")
    if version.source_url:
        footer_parts.append(f"Source: notateslaapp.com")
    if footer_parts:
        embed.set_footer(text=" | ".join(footer_parts))

    return embed
