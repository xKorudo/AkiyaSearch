"""
Build a static snapshot of the site for Cloudflare Pages (or any static host).

Reads the SQLite DB and writes:
    public/index.html      (copy of the frontend)
    public/listings.json   (snapshot of all listings)

The deployed site is 100% static — it fetches ./listings.json, never the DB or
SUUMO. Re-run this after scraping to refresh the snapshot, then redeploy.

Usage:
    python export_static.py
"""
import os
import json
import shutil
import sqlite3

ROOT = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(ROOT, "akiya_v4.db")
OUT = os.path.join(ROOT, "public")
LIVE_URL = "https://akiya-finder-159.pages.dev/listings.json"

COLUMNS = [
    "id", "title", "prefecture", "city", "price_jpy", "price_label",
    "size_m2", "land_m2", "image_url", "source_url", "source", "description",
    "title_en", "description_en", "lat", "lng", "rooms", "built_year",
    "condition", "images",
]


def main():
    os.makedirs(OUT, exist_ok=True)

    conn = sqlite3.connect(DB)
    rows = conn.execute("SELECT * FROM listings ORDER BY price_jpy ASC").fetchall()
    conn.close()

    listings = []
    for r in rows:
        d = dict(zip(COLUMNS, r))
        # images is stored as a JSON string -> parse to a real array
        try:
            d["images"] = json.loads(d["images"]) if d["images"] else []
        except Exception:
            d["images"] = []
        listings.append(d)

    payload = {"count": len(listings), "listings": listings}

    # Never shrink the live dataset: the GitHub Actions runs accumulate far more
    # listings than this local DB. If the live site already has more, keep those
    # so a local frontend-only deploy doesn't clobber the bigger dataset.
    # (Set ALLOW_SHRINK=1 to override, e.g. after a fresh full local rebuild.)
    if os.environ.get("ALLOW_SHRINK") != "1":
        try:
            import urllib.request
            req = urllib.request.Request(LIVE_URL, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
            live = json.load(urllib.request.urlopen(req, timeout=25))
            if live.get("count", 0) > len(listings):
                print(f"Live site has {live['count']} listings (> local {len(listings)}) — keeping live data to avoid shrinking.")
                payload = live
        except Exception as e:
            print("  (could not check live dataset:", type(e).__name__, "— using local)")

    with open(os.path.join(OUT, "listings.json"), "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False)

    shutil.copyfile(os.path.join(ROOT, "index.html"), os.path.join(OUT, "index.html"))
    shutil.copyfile(os.path.join(ROOT, "listing.html"), os.path.join(OUT, "listing.html"))

    print(f"Wrote {payload['count']} listings to {OUT}\\listings.json")
    print(f"Copied index.html to {OUT}\\index.html")
    print("Static site ready in ./public  — deploy that folder to Cloudflare Pages.")


if __name__ == "__main__":
    main()
