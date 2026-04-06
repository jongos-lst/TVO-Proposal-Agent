from fastapi import APIRouter, HTTPException
from app.services.product_catalog import get_all_products, get_product, get_all_competitors

router = APIRouter(prefix="/api", tags=["products"])


@router.get("/products")
async def list_products():
    products = get_all_products()
    return [p.model_dump() for p in products]


@router.get("/products/{product_id}")
async def get_product_detail(product_id: str):
    product = get_product(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product.model_dump()


@router.get("/competitors")
async def list_competitors():
    competitors = get_all_competitors()
    return [c.model_dump() for c in competitors]
