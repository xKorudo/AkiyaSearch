"""
Incremental detail-page image backfill.

The list-page scraper only captures ~4 thumbnails per listing. This script visits
each SUUMO listing's *detail page* and stores its full photo set into the DB.

Design (decoupled + cached + incremental):
- The user-facing site serves only from the DB; it never calls SUUMO.
- This is the ONLY thing that hits SUUMO detail pages, and it does so slowly.
- It only processes listings that don't yet have a full image set, so re-runs
  just fill in gaps. Run it repeatedly (manually or on a schedule) until done.

Usage:
    python enrich_images.py            # process up to BATCH listings
    python enrich_images.py 100        # process up to 100 listings this run
"""
import sys
import json
import re
import time
import random

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import requests
from bs4 import BeautifulSoup

from db.database import listings_needing_images, update_images

BATCH = 40  # how many listings to enrich per run (keep modest to avoid throttling)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ja-JP,ja;q=0.9,en;q=0.8",
    "Referer": "https://suumo.jp/",
}


def fetch_detail_images(session, url):
    """Robustly fetch all photo URLs from a SUUMO detail page (handles 503/throttle)."""
    for attempt in range(4):
        try:
            r = session.get(url, timeout=25)
        except Exception:
            time.sleep(random.uniform(20, 30))
            continue

        if r.status_code == 503 or len(r.text) < 12000:
            time.sleep(random.uniform(30, 45))
            continue
        if r.status_code != 200:
            time.sleep(random.uniform(10, 15))
            continue

        soup = BeautifulSoup(r.text, "html.parser")
        imgs = []
        for img in soup.select("img"):
            for attr in ("rel", "data-src", "src"):
                v = img.get(attr) or ""
                if "base64" in v:
                    continue
                if "resizeImage" in v or ("suumo.com" in v and ".jpg" in v):
                    if v.startswith("//"):
                        v = "https:" + v
                    # request large versions
                    v = re.sub(r"([?&])w=\d+", r"\1w=1200", v)
                    v = re.sub(r"([?&])h=\d+", r"\1h=900", v)
                    if v not in imgs:
                        imgs.append(v)
                    break
        return imgs

    return None  # gave up (throttled)


def main():
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else BATCH
    todo = listings_needing_images(min_images=5, limit=limit)
    print(f"Listings needing full images: {len(todo)} (processing up to {limit})")

    session = requests.Session()
    session.headers.update(HEADERS)

    done = 0
    blocked = 0
    for i, (lid, url, n) in enumerate(todo, 1):
        imgs = fetch_detail_images(session, url)
        if imgs is None:
            blocked += 1
            print(f"  [{i}/{len(todo)}] BLOCKED (will retry next run): {url[:60]}")
            # if we're getting blocked repeatedly, stop early to be polite
            if blocked >= 3:
                print("  Too many blocks - stopping early. Re-run later to continue.")
                break
            continue

        if imgs:
            update_images(lid, json.dumps(imgs), first_image=imgs[0])
            done += 1
            print(f"  [{i}/{len(todo)}] {len(imgs)} photos  <- {url[:55]}")
        else:
            # store empty list so we don't keep retrying a listing with truly no photos
            update_images(lid, json.dumps([]))
            print(f"  [{i}/{len(todo)}] 0 photos (marked done): {url[:50]}")

        time.sleep(random.uniform(4, 7))  # polite pacing

    print(f"DONE: enriched {done}, blocked {blocked}")


if __name__ == "__main__":
    main()
