"""API endpoints for product catalog scraping and refresh."""

import logging
from fastapi import APIRouter, BackgroundTasks

from app.services.product_scraper import scrape_all_products
from app.services.product_catalog import load_catalog, get_all_products, get_all_competitors

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["scraper"])

_scrape_status = {"running": False, "last_result": None}


def _run_scrape():
    """Background task: scrape and reload catalog."""
    _scrape_status["running"] = True
    try:
        merged = scrape_all_products(save=True)
        load_catalog()  # Reload in-memory catalog
        _scrape_status["last_result"] = {
            "success": True,
            "products_count": len(merged),
            "product_ids": [p.get("id", "") for p in merged],
        }
    except Exception as e:
        logger.error("Scrape failed: %s", e)
        _scrape_status["last_result"] = {"success": False, "error": str(e)}
    finally:
        _scrape_status["running"] = False


@router.post("/scraper/refresh")
async def refresh_catalog(background_tasks: BackgroundTasks):
    """Trigger a background scrape of getac.com to refresh the product catalog."""
    if _scrape_status["running"]:
        return {"status": "already_running"}

    background_tasks.add_task(_run_scrape)
    return {"status": "started", "message": "Scraping getac.com in background..."}


@router.get("/scraper/status")
async def scraper_status():
    """Check the status of the last scrape run."""
    return {
        "running": _scrape_status["running"],
        "last_result": _scrape_status["last_result"],
    }


@router.get("/catalog/summary")
async def catalog_summary():
    """Return a summary of the current product and competitor catalog."""
    products = get_all_products()
    competitors = get_all_competitors()
    return {
        "products_count": len(products),
        "competitors_count": len(competitors),
        "products": [
            {
                "id": p.id,
                "name": p.name,
                "category": p.category,
                "base_price": p.base_price,
                "rugged_rating": p.rugged_rating,
                "display_brightness": getattr(p, "display_brightness", None),
                "weight": getattr(p, "weight", None),
            }
            for p in products
        ],
        "competitors": [
            {
                "name": c.name,
                "category": c.category,
                "base_price": c.base_price,
                "annual_failure_rate": c.annual_failure_rate,
            }
            for c in competitors
        ],
    }
