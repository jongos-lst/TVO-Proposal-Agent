"""
Scrape competitor product pages and generate knowledge base content for RAG.

Fetches live product data from competitor websites, extracts key specs,
and produces markdown suitable for ChromaDB ingestion.

Usage:
    from app.services.competitor_scraper import scrape_all_competitors
    results = scrape_all_competitors()
"""

import json
import logging
import re
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup

try:
    from duckduckgo_search import DDGS
except ImportError:
    DDGS = None  # type: ignore[assignment,misc]

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent / "data"
COMPETITORS_PATH = DATA_DIR / "competitors.json"
KNOWLEDGE_DIR = DATA_DIR / "knowledge"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}
REQUEST_DELAY = 2.0  # seconds between requests


# -- HTTP helpers -----------------------------------------------------------

def _fetch(url: str) -> BeautifulSoup | None:
    """Fetch a URL and return parsed soup, or None on failure."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=20)
        resp.raise_for_status()
        return BeautifulSoup(resp.text, "html.parser")
    except requests.RequestException as e:
        logger.warning("Failed to fetch %s: %s", url, e)
        return None


def _load_competitors() -> list[dict]:
    """Load competitor entries from competitors.json."""
    if not COMPETITORS_PATH.exists():
        return []
    return json.loads(COMPETITORS_PATH.read_text())


# -- Page scraping ----------------------------------------------------------

def scrape_competitor_page(url: str, competitor_name: str) -> str | None:
    """
    Scrape a competitor product page and return markdown-formatted content.

    Returns a markdown string with extracted specs and analysis,
    or None if the page cannot be fetched or parsed.
    """
    soup = _fetch(url)
    if not soup:
        return None

    text = soup.get_text(" ", strip=True)
    if len(text) < 100:
        logger.warning("Page content too short for %s: %d chars", competitor_name, len(text))
        return None

    # Extract specs via regex on full page text
    specs = {}

    # Display
    display_match = re.search(
        r'(\d+\.?\d*)["\u201d\u2033]?\s*(?:inch)?\s*(?:FHD|WUXGA|QHD|HD|TFT|IPS|LCD|OLED)',
        text, re.IGNORECASE,
    )
    if display_match:
        specs["Display"] = display_match.group(0).strip()

    # Brightness
    nits_match = re.search(r'(\d[,\d]*)\s*nits?', text, re.IGNORECASE)
    if nits_match:
        specs["Brightness"] = nits_match.group(0).strip()

    # Processor
    proc_match = re.search(
        r'(?:Intel\s+(?:Core\s+(?:Ultra\s+)?(?:i[357]|[57])|Xeon|Celeron|Pentium)'
        r'|Qualcomm\s+Snapdragon\s+\w+'
        r'|AMD\s+Ryzen\s+\w+)'
        r'[\w\s-]{0,40}',
        text, re.IGNORECASE,
    )
    if proc_match:
        specs["Processor"] = proc_match.group(0).strip()[:80]

    # Rugged rating
    mil_std = re.findall(r'MIL-STD-\d+\w*', text)
    ip_rating = re.findall(r'IP\d{2}', text)
    ratings = sorted(set(mil_std + ip_rating))
    if ratings:
        specs["Rugged Rating"] = ", ".join(ratings)

    # Weight
    weight_match = re.search(r'(\d+\.?\d*)\s*(?:kg|lbs?)\b', text, re.IGNORECASE)
    if weight_match:
        specs["Weight"] = weight_match.group(0).strip()

    # Operating temperature
    temp_match = re.search(r'-\d+\s*°[CF]\s*to\s*\d+\s*°[CF]', text)
    if temp_match:
        specs["Operating Temp"] = temp_match.group(0).strip()

    # Battery
    battery_match = re.search(r'(\d+\.?\d*)\s*(?:Wh|hours?)\s*(?:battery)?', text, re.IGNORECASE)
    if battery_match:
        specs["Battery"] = battery_match.group(0).strip()

    # Build markdown
    lines = [f"# Competitor Spec Sheet: {competitor_name}\n"]
    lines.append(f"Source: {url}\n")

    if specs:
        lines.append("## Key Specifications\n")
        for key, val in specs.items():
            lines.append(f"- **{key}**: {val}")
        lines.append("")

    # Extract feature bullet points from the page
    features = []
    for ul in soup.find_all("ul"):
        for li in ul.find_all("li"):
            li_text = li.get_text(strip=True)
            if 15 < len(li_text) < 150:
                features.append(li_text)
    features = list(dict.fromkeys(features))[:20]

    if features:
        lines.append("## Features and Details\n")
        for feat in features:
            lines.append(f"- {feat}")
        lines.append("")

    # Only return if we extracted something useful
    if not specs and not features:
        logger.warning("No useful data extracted from %s for %s", url, competitor_name)
        return None

    return "\n".join(lines)


# -- Orchestration ----------------------------------------------------------

def scrape_all_competitors() -> list[dict]:
    """
    Scrape all competitors from competitors.json that have a product_url.

    Returns list of {"name": str, "content": str | None}.
    """
    competitors = _load_competitors()
    results = []

    for comp in competitors:
        url = comp.get("product_url")
        name = comp["name"]
        if not url:
            logger.info("No product_url for %s, skipping", name)
            results.append({"name": name, "content": None})
            continue

        logger.info("Scraping %s from %s", name, url)
        content = scrape_competitor_page(url, name)
        results.append({"name": name, "content": content})
        time.sleep(REQUEST_DELAY)

    return results


def save_competitor_knowledge(name: str, content: str) -> Path:
    """Write scraped competitor markdown to the knowledge directory."""
    slug = re.sub(r'[^a-z0-9]+', '_', name.lower()).strip('_')
    path = KNOWLEDGE_DIR / f"scraped_{slug}.md"
    path.write_text(content)
    logger.info("Saved competitor knowledge to %s", path.name)
    return path


def scrape_competitor_for_rag(competitor_name: str) -> str | None:
    """
    Scrape a single competitor by name for dynamic RAG ingestion.

    1. Looks up the competitor in competitors.json using fuzzy name matching.
    2. If found with product_url, scrapes that URL.
    3. If NOT found, searches the web for the product page, scrapes it,
       and adds the competitor to competitors.json for future use.
    """
    competitors = _load_competitors()
    for c in competitors:
        c_name = c["name"].lower()
        query = competitor_name.lower()
        # Match if query is substring of competitor name or vice versa
        if query in c_name or c_name in query:
            url = c.get("product_url")
            if url:
                logger.info("Dynamic scrape for %r -> %s", competitor_name, url)
                return scrape_competitor_page(url, c["name"])
            logger.info("No product_url for matched competitor %s", c["name"])
            return None

    # Not in catalog — try web search
    logger.info("Competitor %r not in catalog, trying web search", competitor_name)
    return _web_search_and_scrape(competitor_name)


def _web_search_and_scrape(competitor_name: str) -> str | None:
    """
    Search the web for a competitor product page, scrape it, and
    add the competitor to competitors.json for future lookups.
    """
    url = web_search_competitor(competitor_name)
    if not url:
        return None

    content = scrape_competitor_page(url, competitor_name)
    if content:
        # Dynamically add to competitors.json so future lookups don't need web search
        add_competitor_to_catalog(competitor_name, url)
        logger.info("Added %r to competitors.json via web discovery", competitor_name)
    return content


def web_search_competitor(competitor_name: str) -> str | None:
    """
    Search the web for a competitor product specification page.
    Returns the URL of the most relevant result, or None.
    """
    if DDGS is None:
        logger.warning("duckduckgo-search not installed, cannot search for %s", competitor_name)
        return None

    search_query = f"{competitor_name} specifications rugged laptop tablet"
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(search_query, max_results=5))
    except Exception as e:
        logger.warning("Web search failed for %r: %s", competitor_name, e)
        return None

    if not results:
        logger.info("No web search results for %r", competitor_name)
        return None

    # Prefer manufacturer sites and spec pages
    preferred_domains = [
        "dell.com", "panasonic.com", "hp.com", "zebra.com", "samsung.com",
        "lenovo.com", "durabook.com", "xploretech.com", "getac.com",
    ]
    for r in results:
        url = r.get("href", "")
        if any(domain in url for domain in preferred_domains):
            logger.info("Web search found manufacturer page: %s", url)
            return url

    # Fall back to first result
    first_url = results[0].get("href")
    if first_url:
        logger.info("Web search using first result: %s", first_url)
        return first_url

    return None


def add_competitor_to_catalog(name: str, product_url: str) -> None:
    """
    Add a newly discovered competitor to competitors.json with minimal data.
    The entry is a stub — it has the name and URL but no specs or weaknesses,
    which will come from RAG knowledge chunks instead.
    """
    competitors = _load_competitors()

    # Check if already exists (by name substring match)
    for c in competitors:
        if name.lower() in c["name"].lower() or c["name"].lower() in name.lower():
            # Already exists, just update URL if missing
            if not c.get("product_url"):
                c["product_url"] = product_url
                COMPETITORS_PATH.write_text(
                    json.dumps(competitors, indent=2, ensure_ascii=False) + "\n"
                )
            return

    new_entry = {
        "name": name,
        "category": "Unknown",
        "base_price": 0.0,
        "warranty_standard": "Unknown",
        "annual_failure_rate": 0.05,
        "product_url": product_url,
        "weaknesses": [],
    }
    competitors.append(new_entry)
    COMPETITORS_PATH.write_text(
        json.dumps(competitors, indent=2, ensure_ascii=False) + "\n"
    )
    logger.info("Added new competitor %r to catalog", name)
