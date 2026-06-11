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
LIVE_URL = os.environ.get("LIVE_URL", "https://akiya-finder-159.pages.dev/listings-0.json")
CHUNK_SIZE = 2_000   # listings per file — keeps each chunk well under CF's 25 MiB limit

COLUMNS = [
    "id", "title", "prefecture", "city", "price_jpy", "price_label",
    "size_m2", "land_m2", "image_url", "source_url", "source", "description",
    "title_en", "description_en", "lat", "lng", "rooms", "built_year",
    "condition", "images", "traffic", "first_seen", "listed_at",
    "building_structure", "zoning", "building_ratio", "private_road",
    "other_restrictions", "handover_date", "transaction_area",
    "features", "surroundings", "agent_company", "agent_license",
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
    # Merge with the live dataset instead of replacing it. The CI DB cache can
    # fork (scrape + backfills run in parallel) or be evicted, so neither local
    # nor live is always the superset. Union by id — keeping the richer record
    # per listing — so the dataset only ever GROWS and freshly scraped listings
    # are never dropped. (Set ALLOW_SHRINK=1 to skip and deploy local only.)
    if os.environ.get("ALLOW_SHRINK") != "1":
        try:
            import urllib.request

            def _fetch(url):
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
                return json.load(urllib.request.urlopen(req, timeout=25))

            def _score(l):  # richer = more images, then has EN desc, then geocoded
                return (len(l.get("images") or []),
                        1 if l.get("description_en") else 0,
                        1 if l.get("lat") else 0)

            live0 = _fetch(LIVE_URL)
            live = list(live0.get("listings", []))
            for i in range(1, live0.get("chunks", 1)):
                live += _fetch(LIVE_URL.replace("listings-0.json", f"listings-{i}.json")).get("listings", [])

            merged = {l["id"]: l for l in live if l.get("id")}
            added = 0
            for l in listings:
                cur = merged.get(l["id"])
                if cur is None:
                    added += 1
                if cur is None or _score(l) >= _score(cur):
                    merged[l["id"]] = l   # local (fresh) wins on ties
            print(f"Merged local ({len(listings)}) + live ({len(live)}) -> {len(merged)} listings ({added} new).")
            listings = list(merged.values())
        except Exception as e:
            # A transient live-fetch failure must NOT clobber the live dataset with
            # a smaller local one. Abort instead (set ALLOW_SHRINK=1 to override).
            print("  (could not fetch/merge live dataset:", type(e).__name__, str(e), ")")
            raise SystemExit(
                "Aborting export: could not verify the live dataset, so refusing to "
                "risk shrinking it. Re-run, or set ALLOW_SHRINK=1 to deploy local data as-is."
            )

    # Write compact meta index for Open Graph / link-preview Pages Function
    PREF_EN = {
        '北海道':'Hokkaido','青森':'Aomori','岩手':'Iwate','宮城':'Miyagi','秋田':'Akita',
        '山形':'Yamagata','福島':'Fukushima','茨城':'Ibaraki','栃木':'Tochigi','群馬':'Gunma',
        '埼玉':'Saitama','千葉':'Chiba','東京':'Tokyo','神奈川':'Kanagawa','新潟':'Niigata',
        '富山':'Toyama','石川':'Ishikawa','福井':'Fukui','山梨':'Yamanashi','長野':'Nagano',
        '岐阜':'Gifu','静岡':'Shizuoka','愛知':'Aichi','三重':'Mie','滋賀':'Shiga',
        '京都':'Kyoto','大阪':'Osaka','兵庫':'Hyogo','奈良':'Nara','和歌山':'Wakayama',
        '鳥取':'Tottori','島根':'Shimane','岡山':'Okayama','広島':'Hiroshima','山口':'Yamaguchi',
        '徳島':'Tokushima','香川':'Kagawa','愛媛':'Ehime','高知':'Kochi','福岡':'Fukuoka',
        '佐賀':'Saga','長崎':'Nagasaki','熊本':'Kumamoto','大分':'Oita','宮崎':'Miyazaki',
        '鹿児島':'Kagoshima','沖縄':'Okinawa',
    }
    meta = {
        l["id"]: {
            "title_en":    l.get("title_en", "") or l.get("title", ""),
            "price_jpy":   l.get("price_jpy"),
            "image_url":   l.get("image_url", ""),
            "prefecture":  PREF_EN.get(l.get("prefecture", ""), l.get("prefecture", "")),
            "size_m2":     l.get("size_m2"),
            "rooms":       l.get("rooms", ""),
            "built_year":  l.get("built_year"),
        }
        for l in listings if l.get("id")
    }
    with open(os.path.join(OUT, "listing-meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, separators=(",", ":"))

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

    for fname in ["manifest.json"]:
        src = os.path.join(ROOT, fname)
        if os.path.exists(src):
            shutil.copyfile(src, os.path.join(OUT, fname))

    static_files = [
        "index.html",
        "search.html",
        "map.html",
        "discover.html",
        "listing.html",
        "impressum.html",
        "terms.html",
        "privacy.html",
        "contact.html",
        "admin.html",
        "review.html",
        "stats.html",
        "prefectures.html",
        "prefecture.html",
    ]
    for fname in static_files:
        src = os.path.join(ROOT, fname)
        if os.path.exists(src):
            shutil.copyfile(src, os.path.join(OUT, fname))

    for subdir in ["js", "css", "data", "icons"]:
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
