"""
Scrape Getac product pages and enrich the local product catalog.

This module fetches live product data from getac.com, parses specs,
and merges updates into backend/app/data/products.json.

Usage:
    # As a standalone script
    cd backend && source venv/bin/activate
    python -m scripts.scrape_products

    # Or import in agent code
    from app.services.product_scraper import scrape_all_products
"""

import json
import logging
import re
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

GETAC_BASE = "https://www.getac.com"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}
REQUEST_DELAY = 1.5  # seconds between requests — be polite

DATA_DIR = Path(__file__).parent.parent / "data"
PRODUCTS_PATH = DATA_DIR / "products.json"

# ── Index pages to discover products ───────────────────────────────────────
CATALOG_PAGES = [
    "/us/products/laptops/",
    "/us/products/tablets/",
    "/us/products/body-worn-cameras-bwc/",
    "/us/products/in-car-video/",
]


@dataclass
class ScrapedProduct:
    """Raw product data scraped from a single product page."""
    id: str = ""
    name: str = ""
    category: str = ""
    product_url: str = ""
    display_size: str = ""
    display_brightness: str = ""
    processor: str = ""
    ram_options: list[str] = field(default_factory=list)
    storage_options: list[str] = field(default_factory=list)
    rugged_rating: str = ""
    operating_temp: str = ""
    battery_life: str = ""
    weight: str = ""
    warranty_standard: str = ""
    key_features: list[str] = field(default_factory=list)
    connectivity: list[str] = field(default_factory=list)
    ports: list[str] = field(default_factory=list)
    target_industries: list[str] = field(default_factory=list)


# ── HTTP helpers ───────────────────────────────────────────────────────────

def _fetch(url: str) -> BeautifulSoup | None:
    """Fetch a URL and return parsed soup, or None on failure."""
    full = url if url.startswith("http") else f"{GETAC_BASE}{url}"
    try:
        resp = requests.get(full, headers=HEADERS, timeout=20)
        resp.raise_for_status()
        return BeautifulSoup(resp.text, "html.parser")
    except requests.RequestException as e:
        logger.warning("Failed to fetch %s: %s", full, e)
        return None


# ── Discovery: find all product links from catalog index pages ─────────────

def discover_product_urls() -> list[dict]:
    """
    Crawl the laptops and tablets index pages to find product links.
    Returns list of {"name": ..., "url": ..., "category_hint": ...}.
    """
    category_hints = {
        "laptop": "Laptop",
        "tablet": "Tablet",
        "body-worn": "Body-Worn Camera",
        "in-car": "In-Car Video",
    }
    products = []
    for page_path in CATALOG_PAGES:
        cat_hint = "Unknown"
        for key, hint in category_hints.items():
            if key in page_path:
                cat_hint = hint
                break

        soup = _fetch(page_path)
        if not soup:
            continue

        # Getac product pages use cards with links to /us/products/.../<model>/
        for link in soup.find_all("a", href=True):
            href = link["href"]
            # Match product detail pages across all categories
            pattern = r"/us/products/(laptops|tablets|body-worn-cameras-bwc|in-car-video)/([a-zA-Z0-9_-]+)/"
            m = re.match(pattern, href)
            if not m:
                continue

            model_slug = m.group(2)
            # Skip index pages themselves
            if model_slug in ("laptops", "tablets", "body-worn-cameras-bwc", "in-car-video"):
                continue

            # Extract product name from link text or nearby heading
            name_text = link.get_text(strip=True)
            if not name_text or len(name_text) > 60:
                # Try to find a heading inside the link
                heading = link.find(["h2", "h3", "h4", "span"])
                name_text = heading.get_text(strip=True) if heading else model_slug.upper()

            full_url = href if href.startswith("http") else f"{GETAC_BASE}{href}"

            # Deduplicate
            if not any(p["url"] == full_url for p in products):
                products.append({
                    "name": name_text,
                    "slug": model_slug,
                    "url": full_url,
                    "category_hint": cat_hint,
                })

        time.sleep(REQUEST_DELAY)

    logger.info("Discovered %d product URLs", len(products))
    return products


# ── Detail page parsing ────────────────────────────────────────────────────

def _extract_text_near(soup: BeautifulSoup, keywords: list[str]) -> str:
    """Find text near certain keywords in the page."""
    text = soup.get_text(" ", strip=True)
    for kw in keywords:
        idx = text.lower().find(kw.lower())
        if idx >= 0:
            snippet = text[idx:idx + 200]
            return snippet.split("\n")[0].strip()
    return ""


def _find_spec(text: str, patterns: list[str]) -> str:
    """Search full page text for spec patterns and return first match."""
    for pattern in patterns:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            return m.group(0).strip()
    return ""


def scrape_product_page(url: str, category_hint: str = "") -> ScrapedProduct | None:
    """Scrape a single Getac product detail page."""
    soup = _fetch(url)
    if not soup:
        return None

    text = soup.get_text(" ", strip=True)
    product = ScrapedProduct(product_url=url)

    # Name — usually the main h1
    h1 = soup.find("h1")
    if h1:
        product.name = h1.get_text(strip=True)

    # ID — derive from URL slug
    slug_match = re.search(r"/products/(?:laptops|tablets)/([a-zA-Z0-9_-]+)/", url)
    if slug_match:
        product.id = slug_match.group(1).lower().replace("-", "")

    # Category
    if "tablet" in url:
        product.category = "Fully Rugged Tablet"
    elif "laptop" in url:
        product.category = "Fully Rugged Laptop"
    if category_hint:
        product.category = product.category or category_hint

    # Display size
    display_match = re.search(r'(\d+\.?\d*)["\u201d\u2033]?\s*(?:inch)?\s*(?:FHD|WUXGA|QHD|HD|TFT)', text, re.IGNORECASE)
    if display_match:
        product.display_size = display_match.group(0).strip()

    # Brightness
    nits_match = re.search(r'(\d[,\d]*)\s*nits?', text, re.IGNORECASE)
    if nits_match:
        product.display_brightness = nits_match.group(0).strip()

    # Processor — look for Intel Core patterns
    proc_match = re.search(
        r'Intel\s+(?:Core\s+(?:Ultra\s+)?(?:i[357]|[57])|Xeon)\s*[\w\s-]*(?:up\s+to\s+[\d.]+\s*GHz)?',
        text, re.IGNORECASE
    )
    if proc_match:
        product.processor = proc_match.group(0).strip()

    # RAM
    ram_matches = re.findall(r'(\d+\s*GB\s*(?:DDR[45]X?|LPDDR\d+X?))', text, re.IGNORECASE)
    if ram_matches:
        product.ram_options = sorted(set(ram_matches), key=lambda x: int(re.search(r'\d+', x).group()))

    # Storage
    storage_matches = re.findall(r'(\d+\s*(?:GB|TB)\s*(?:PCIe\s*NVMe\s*)?SSD)', text, re.IGNORECASE)
    if storage_matches:
        product.storage_options = sorted(set(storage_matches), key=lambda x: (
            int(re.search(r'\d+', x).group()) * (1000 if 'TB' in x.upper() else 1)
        ))

    # Rugged rating
    mil_std = re.findall(r'MIL-STD-\d+\w*', text)
    ip_rating = re.findall(r'IP\d{2}', text)
    ratings = sorted(set(mil_std + ip_rating))
    if ratings:
        product.rugged_rating = ", ".join(ratings)

    # Operating temp
    temp_match = re.search(r'-\d+\s*°[CF]\s*to\s*\d+\s*°[CF](?:\s*\([^)]+\))?', text)
    if temp_match:
        product.operating_temp = temp_match.group(0).strip()

    # Weight
    weight_match = re.search(r'(\d+\.?\d*)\s*kg\s*\([\d.]+\s*lbs?\)', text)
    if weight_match:
        product.weight = weight_match.group(0).strip()

    # Warranty
    warranty_match = re.search(r'(\d+)\s*(?:-?\s*year[s]?)\s*(?:bumper-to-bumper|limited\s*warranty|standard)', text, re.IGNORECASE)
    if warranty_match:
        product.warranty_standard = warranty_match.group(0).strip()

    # Key features — pull from bullet lists or feature sections
    for ul in soup.find_all("ul"):
        for li in ul.find_all("li"):
            li_text = li.get_text(strip=True)
            if 10 < len(li_text) < 120:
                product.key_features.append(li_text)
    # Deduplicate and limit
    product.key_features = list(dict.fromkeys(product.key_features))[:15]

    # Connectivity patterns
    conn_patterns = [
        r'Wi-Fi\s*\d+\w*\s*\w*',
        r'Bluetooth\s*[\d.]+',
        r'(?:4G\s*)?LTE',
        r'5G\s*Sub-\d',
        r'(?:Gigabit\s+)?Ethernet',
        r'GPS\s*\(?L\d[/L\d]*\)?',
    ]
    for pat in conn_patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            product.connectivity.append(m.group(0).strip())
    product.connectivity = list(dict.fromkeys(product.connectivity))

    # Target industries — look for common industry keywords
    industry_keywords = [
        "Public Safety", "Defense", "Military", "Utilities", "Manufacturing",
        "Transportation", "Logistics", "Oil & Gas", "Healthcare", "Retail",
        "Warehouse", "Aviation", "Automotive", "Mining", "Emergency",
        "Field Service", "Natural Resources",
    ]
    for ind in industry_keywords:
        if ind.lower() in text.lower():
            product.target_industries.append(ind)
    product.target_industries = list(dict.fromkeys(product.target_industries))

    return product


# ── Merge scraped data into existing catalog ───────────────────────────────

def merge_into_catalog(scraped: list[ScrapedProduct]) -> list[dict]:
    """
    Merge scraped data into the existing products.json.
    Existing fields are preserved; scraped fields fill in blanks or add new products.
    Returns the merged product list.
    """
    # Load existing catalog
    existing = []
    if PRODUCTS_PATH.exists():
        existing = json.loads(PRODUCTS_PATH.read_text())

    existing_by_id = {p["id"]: p for p in existing}

    for sp in scraped:
        if not sp.id:
            continue

        if sp.id in existing_by_id:
            # Update: only fill in fields that are empty/missing in existing
            prod = existing_by_id[sp.id]
            sp_dict = {k: v for k, v in asdict(sp).items() if v}
            for key, val in sp_dict.items():
                if key in ("id",):
                    continue
                if key not in prod or not prod[key]:
                    prod[key] = val
                elif isinstance(val, list) and isinstance(prod.get(key), list):
                    # Merge lists — add new items
                    combined = list(dict.fromkeys(prod[key] + val))
                    prod[key] = combined
        else:
            # New product — add with defaults
            new_prod = asdict(sp)
            new_prod.setdefault("base_price", 0.0)
            new_prod.setdefault("warranty_options", [])
            new_prod.setdefault("annual_failure_rate", 0.025)
            existing_by_id[sp.id] = new_prod

    merged = list(existing_by_id.values())
    return merged


def save_catalog(products: list[dict]):
    """Write merged products back to products.json."""
    PRODUCTS_PATH.write_text(json.dumps(products, indent=2, ensure_ascii=False) + "\n")
    logger.info("Saved %d products to %s", len(products), PRODUCTS_PATH)


# ── Main orchestrator ──────────────────────────────────────────────────────

def scrape_all_products(save: bool = True) -> list[dict]:
    """
    Full pipeline: discover → scrape → merge → save.
    Returns the merged product catalog.
    """
    print("[1/3] Discovering product URLs from getac.com ...")
    urls = discover_product_urls()
    print(f"  Found {len(urls)} product pages")

    print("[2/3] Scraping product detail pages ...")
    scraped = []
    for i, info in enumerate(urls):
        print(f"  ({i+1}/{len(urls)}) {info['name']} — {info['url']}")
        product = scrape_product_page(info["url"], info.get("category_hint", ""))
        if product:
            scraped.append(product)
        time.sleep(REQUEST_DELAY)

    print(f"  Scraped {len(scraped)} products successfully")

    print("[3/3] Merging with existing catalog ...")
    merged = merge_into_catalog(scraped)

    if save:
        save_catalog(merged)
        print(f"  Saved {len(merged)} products to {PRODUCTS_PATH}")

    return merged
