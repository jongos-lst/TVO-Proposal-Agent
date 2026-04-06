#!/usr/bin/env python3
"""
Ingest knowledge base documents into ChromaDB.

Usage:
    cd backend && source venv/bin/activate

    # Ingest existing markdown files only
    python -m scripts.ingest_knowledge

    # Scrape competitor product pages first, then ingest all
    python -m scripts.ingest_knowledge --scrape
"""
import argparse
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.rag import ingest_knowledge
from app.services.competitor_scraper import scrape_all_competitors, save_competitor_knowledge


def main():
    parser = argparse.ArgumentParser(description="Ingest knowledge base into ChromaDB")
    parser.add_argument(
        "--scrape", action="store_true",
        help="Scrape competitor product pages before ingesting",
    )
    args = parser.parse_args()

    if args.scrape:
        print("[1/2] Scraping competitor product pages...")
        results = scrape_all_competitors()
        saved = 0
        for r in results:
            if r["content"]:
                path = save_competitor_knowledge(r["name"], r["content"])
                print(f"  Saved: {path.name}")
                saved += 1
            else:
                print(f"  Skipped: {r['name']} (no content)")
        print(f"  Scraped {saved}/{len(results)} competitors\n")
        print("[2/2] Ingesting all knowledge into ChromaDB...")
    else:
        print("Ingesting knowledge into ChromaDB...")

    count = ingest_knowledge()
    print(f"Done. Total chunks ingested: {count}")


if __name__ == "__main__":
    main()
