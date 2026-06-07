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
LIVE_URL = "https://akiya-finder-159.pages.dev/listings-0.json"
CHUNK_SIZE = 10_000  # listings per file — keeps each chunk well under CF's 25 MiB limit

COLUMNS = [
    "id", "title", "prefecture", "city", "price_jpy", "price_label",
    "size_m2", "land_m2", "image_url", "source_url", "source", "description",
    "title_en", "description_en", "lat", "lng", "rooms", "built_year",
    "condition", "images", "traffic",
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

    # Never shrink the live dataset: the GitHub Actions runs accumulate far more
    # listings than this local DB. If the live site already has more, keep those
    # so a local frontend-only deploy doesn't clobber the bigger dataset.
    # (Set ALLOW_SHRINK=1 to override, e.g. after a fresh full local rebuild.)
    if os.environ.get("ALLOW_SHRINK") != "1":
        try:
            import urllib.request
            req = urllib.request.Request(LIVE_URL, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
            live0 = json.load(urllib.request.urlopen(req, timeout=25))
            if live0.get("count", 0) > len(listings):
                live_count = live0["count"]
                live_chunks = live0.get("chunks", 1)
                print(f"Live site has {live_count} listings (> local {len(listings)}) — keeping live data.")
                # Reconstruct listings from all live chunks
                listings = list(live0.get("listings", []))
                for i in range(1, live_chunks):
                    chunk_url = LIVE_URL.replace("listings-0.json", f"listings-{i}.json")
                    req_i = urllib.request.Request(chunk_url, headers={"User-Agent": "Mozilla/5.0"})
                    listings += json.load(urllib.request.urlopen(req_i, timeout=25)).get("listings", [])
        except Exception as e:
            print("  (could not check live dataset:", type(e).__name__, "— using local)")

    # Write chunks — each under CHUNK_SIZE listings so no file exceeds CF's 25 MiB limit
    chunks = [listings[i:i + CHUNK_SIZE] for i in range(0, max(len(listings), 1), CHUNK_SIZE)]
    n = len(chunks)
    for idx, chunk in enumerate(chunks):
        data = {"listings": chunk}
        if idx == 0:
            data["count"] = len(listings)
            data["chunks"] = n
        with open(os.path.join(OUT, f"listings-{idx}.json"), "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)

    static_files = [
        "index.html",
        "search.html",
        "map.html",
        "discover.html",
        "listing.html",
        "impressum.html",
        "terms.html",
        "privacy.html",
        "admin.html",
        "stats.html",
        "prefectures.html",
        "prefecture.html",
    ]
    for fname in static_files:
        src = os.path.join(ROOT, fname)
        if os.path.exists(src):
            shutil.copyfile(src, os.path.join(OUT, fname))

    for subdir in ["js", "css", "data"]:
        src_dir = os.path.join(ROOT, subdir)
        dst_dir = os.path.join(OUT, subdir)
        if os.path.isdir(src_dir):
            os.makedirs(dst_dir, exist_ok=True)
            for fname in os.listdir(src_dir):
                shutil.copyfile(os.path.join(src_dir, fname), os.path.join(dst_dir, fname))

    print(f"Wrote {len(listings)} listings across {n} chunk(s) to {OUT}/listings-*.json")
    print("Copied HTML pages and assets to", OUT)
    print("Static site ready in ./public  — deploy that folder to Cloudflare Pages.")


if __name__ == "__main__":
    main()
