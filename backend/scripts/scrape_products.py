#!/usr/bin/env python3
"""
Scrape Getac product catalog from getac.com and update local data files.

Usage:
    cd backend
    source venv/bin/activate
    python -m scripts.scrape_products

This crawls the Getac US website, extracts product specifications,
and merges the data into backend/app/data/products.json.
Existing hand-curated fields (prices, failure rates, warranty options)
are preserved — only missing/empty fields get filled from scraped data.
"""

import os
import sys
import json
import logging

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

from app.services.product_scraper import scrape_all_products, PRODUCTS_PATH


def main():
    print("=" * 60)
    print("  Getac Product Scraper — Catalog Enrichment")
    print("=" * 60)

    merged = scrape_all_products(save=True)

    print(f"\n{'=' * 60}")
    print(f"  Updated catalog: {len(merged)} products")
    print(f"  File: {PRODUCTS_PATH}")
    print()
    for p in merged:
        price = f"${p.get('base_price', 0):,.0f}" if p.get('base_price') else "N/A"
        print(f"  {p['id']:<12} {p['name']:<24} {p.get('category', ''):<30} {price}")
    print("=" * 60)


if __name__ == "__main__":
    main()
