import sys
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from scrapers import akiya_bank, homes, akiyabank_lifull
from core.dedupe import dedupe
from core.enrich import enrich
from db.database import init_db, upsert

def run_pipeline():
    init_db()

    all_listings = []

    print("Scraping SUUMO houses...")
    all_listings += homes.scrape()

    print("Scraping LIFULL Akiya Bank (headless browser)...")
    try:
        all_listings += akiyabank_lifull.scrape()
    except Exception as e:
        print("  LIFULL Akiya Bank skipped:", type(e).__name__, e)

    print("Scraping municipal Akiya Banks...")
    all_listings += akiya_bank.scrape()

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

    print("DONE")

if __name__ == "__main__":
    run_pipeline()