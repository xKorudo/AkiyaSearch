import os
import sys
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from scrapers import homes, akiyabank_lifull
from core.dedupe import dedupe
from core.enrich import enrich
from db.database import init_db, upsert

def run_pipeline():
    init_db()

    # Snapshot existing IDs so we can identify truly new listings afterwards
    existing_ids = set()
    try:
        import sqlite3
        from db.database import DB as _DB
        _conn = sqlite3.connect(_DB)
        existing_ids = {r[0] for r in _conn.execute("SELECT id FROM listings").fetchall()}
        _conn.close()
    except Exception:
        pass

    all_listings = []

    scrape_mode = os.environ.get("SCRAPE_MODE", "fresh")
    print(f"Scraping SUUMO houses (mode={scrape_mode})...")
    all_listings += homes.scrape(mode=scrape_mode)

    print("Scraping LIFULL Akiya Bank (headless browser)...")
    try:
        all_listings += akiyabank_lifull.scrape()
    except Exception as e:
        print("  LIFULL Akiya Bank skipped:", type(e).__name__, e)

    print("Deduplicating...")
    all_listings = dedupe(all_listings)

    print("Translating + geocoding...")
    all_listings = enrich(all_listings)

    print(f"Saving {len(all_listings)} listings")
    for l in all_listings:
        upsert(l)

    print("Syncing to Supabase + tracking price/sold changes...")
    try:
        from core.sync_supabase import sync
        sync(all_listings)
    except Exception as e:
        print("  Supabase sync error:", type(e).__name__, e)

    # Similarity check: flag cross-source / re-listed duplicates for review
    new_listings = [l for l in all_listings if l.id and l.id not in existing_ids]
    print(f"Checking {len(new_listings)} new listing(s) for potential duplicates...")
    try:
        from core.similarity import find_pending_reviews
        from core.sync_supabase import push_pending_reviews
        pairs = find_pending_reviews(new_listings)
        if pairs:
            push_pending_reviews(pairs)
        else:
            print("  No potential duplicates found.")
    except Exception as e:
        print(f"  Similarity check skipped: {type(e).__name__}: {e}")

    print("DONE")

if __name__ == "__main__":
    run_pipeline()
