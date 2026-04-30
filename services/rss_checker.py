import logging
import re

import aiohttp
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

VERSION_PATTERN = re.compile(r"/software-updates/version/([^/]+)/release-notes")
UPDATES_PAGE = "https://www.notateslaapp.com/software-updates/"


async def fetch_new_versions(feed_url: str) -> list[tuple[str, str, str]]:
    """Scrape the software updates page for version links.

    The RSS feed only contains news articles, so we scrape the updates page
    directly to find version URLs.

    Returns a list of (version_id, page_url, pub_date) tuples.
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                UPDATES_PAGE,
                headers={"User-Agent": "TeslaDiscordBot/1.0"},
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp:
                if resp.status != 200:
                    logger.warning("Updates page returned status %d", resp.status)
                    return []
                html = await resp.text()
    except Exception:
        logger.exception("Failed to fetch software updates page")
        return []

    soup = BeautifulSoup(html, "lxml")
    seen: set[str] = set()
    results: list[tuple[str, str, str]] = []

    for link in soup.find_all("a", href=True):
        href = link["href"]
        match = VERSION_PATTERN.search(href)
        if not match:
            continue

        version_id = match.group(1)
        if version_id in seen:
            continue
        seen.add(version_id)

        # Build full URL if relative
        if href.startswith("/"):
            page_url = f"https://www.notateslaapp.com{href}"
        else:
            page_url = href

        results.append((version_id, page_url, ""))

    logger.info("Found %d versions on updates page", len(results))
    return results
