import logging
import re

import aiohttp
from bs4 import BeautifulSoup

from models.version import TeslaVersion

logger = logging.getLogger(__name__)


async def get_release_notes(version_id: str, url: str) -> TeslaVersion:
    """Scrape the version page for release notes.

    Returns a TeslaVersion with whatever data could be extracted.
    Falls back to a minimal object if scraping fails.
    """
    version = TeslaVersion(
        version_id=version_id,
        release_date="",
        source_url=url,
    )

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url,
                headers={"User-Agent": "TeslaDiscordBot/1.0"},
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp:
                if resp.status != 200:
                    logger.warning("Version page %s returned status %d", url, resp.status)
                    return version
                html = await resp.text()
    except Exception:
        logger.exception("Failed to fetch version page %s", url)
        return version

    try:
        soup = BeautifulSoup(html, "lxml")
        _extract_release_date(soup, version)
        _extract_fleet_pct(soup, version)
        _extract_features(soup, version)
    except Exception:
        logger.exception("Failed to parse version page %s", url)

    return version


def _extract_release_date(soup: BeautifulSoup, version: TeslaVersion) -> None:
    date_el = soup.find(string=re.compile(r"\b\d{4}-\d{2}-\d{2}\b"))
    if date_el:
        match = re.search(r"\d{4}-\d{2}-\d{2}", str(date_el))
        if match:
            version.release_date = match.group(0)
            return
    # Try other common date formats
    date_el = soup.find(string=re.compile(r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}", re.I))
    if date_el:
        version.release_date = str(date_el).strip()


def _extract_fleet_pct(soup: BeautifulSoup, version: TeslaVersion) -> None:
    pct_el = soup.find(string=re.compile(r"\d+(\.\d+)?%\s*(of\s+fleet|fleet)", re.I))
    if pct_el:
        match = re.search(r"(\d+(?:\.\d+)?)%", str(pct_el))
        if match:
            version.fleet_pct = float(match.group(1))


def _extract_features(soup: BeautifulSoup, version: TeslaVersion) -> None:
    features: list[dict] = []

    # Look for headings (h2, h3) that typically denote feature names,
    # with sibling paragraphs as descriptions.
    for heading in soup.find_all(["h2", "h3"]):
        title = heading.get_text(strip=True)
        if not title or len(title) > 200:
            continue

        desc_parts: list[str] = []
        for sibling in heading.find_next_siblings():
            if sibling.name in ("h2", "h3"):
                break
            text = sibling.get_text(strip=True)
            if text:
                desc_parts.append(text)

        description = " ".join(desc_parts)
        if len(description) > 900:
            description = description[:897] + "..."

        features.append({"title": title, "description": description})

    # Fallback: look for list items if no headings found
    if not features:
        for li in soup.find_all("li"):
            text = li.get_text(strip=True)
            if text and len(text) > 10:
                features.append({"title": text[:100], "description": ""})
            if len(features) >= 15:
                break

    version.features = features
