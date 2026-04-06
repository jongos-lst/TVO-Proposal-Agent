import json
from pathlib import Path
from app.models.product import GetacProduct, CompetitorProduct

DATA_DIR = Path(__file__).parent.parent / "data"

_products: dict[str, GetacProduct] = {}
_competitors: dict[str, CompetitorProduct] = {}


def load_catalog():
    """Load product and competitor data from JSON files."""
    global _products, _competitors

    with open(DATA_DIR / "products.json") as f:
        products_data = json.load(f)
    _products = {p["id"]: GetacProduct(**p) for p in products_data}

    with open(DATA_DIR / "competitors.json") as f:
        competitors_data = json.load(f)
    _competitors = {c["name"]: CompetitorProduct(**c) for c in competitors_data}


def get_all_products() -> list[GetacProduct]:
    return list(_products.values())


def get_product(product_id: str) -> GetacProduct | None:
    return _products.get(product_id)


def get_competitor(name: str) -> CompetitorProduct | None:
    return _competitors.get(name)


def get_all_competitors() -> list[CompetitorProduct]:
    return list(_competitors.values())


def get_product_names() -> list[str]:
    return [p.name for p in _products.values()]
