import sys
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from scrapers import suumo, akiya_bank, homes
from core.dedupe import dedupe
from core.enrich import enrich
from db.database import init_db, upsert

def run_pipeline():
    init_db()

    all_listings = []

    print("Scraping SUUMO...")
    all_listings += suumo.scrape()

    print("Scraping Akiya Banks...")
    all_listings += akiya_bank.scrape()

    print("Scraping LIFULL HOMES...")
    all_listings += homes.scrape()

    print("Deduplicating...")
    all_listings = dedupe(all_listings)

    print("Translating + geocoding...")
    all_listings = enrich(all_listings)

    print(f"Saving {len(all_listings)} listings")

    for l in all_listings:
        upsert(l)

    print("DONE")

if __name__ == "__main__":
    run_pipeline()