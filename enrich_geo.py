"""
Real geocoding for listings — replaces the prefecture-center + random scatter
(which dropped markers in the sea) with actual town coordinates.

Geocodes at the MUNICIPALITY level (市/区/町/村) via free OpenStreetMap Nominatim:
reliable, dedupes heavily, and puts each dot in the correct town. Results are
cached in geocache.json so re-runs are instant and we never re-hit Nominatim.

Usage:  python enrich_geo.py
"""
import sqlite3, json, re, time, sys, os
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
import requests

ROOT = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(ROOT, "akiya_v4.db")
CACHE = os.path.join(ROOT, "geocache.json")

PREF_SUFFIX = {"北海道": "", "東京": "都", "大阪": "府", "京都": "府"}  # else 県


def municipality(city: str) -> str:
    """Trim a full address down to its municipality (…市 / …区 / …郡…町 / …村)."""
    if not city:
        return ""
    for marker in ("市", "区", "町", "村"):
        i = city.find(marker)
        if i != -1:
            return city[: i + 1]
    return city


def load_cache():
    try:
        with open(CACHE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def main():
    cache = load_cache()
    conn = sqlite3.connect(DB)
    rows = conn.execute(
        "SELECT id, prefecture, city FROM listings WHERE source='SUUMO' AND city != ''"
    ).fetchall()

    # Build the set of unique municipality queries
    targets = {}
    for lid, pref, city in rows:
        muni = municipality(city)
        if not muni:
            continue
        suffix = PREF_SUFFIX.get(pref, "県")
        query = f"{muni}, {pref}{suffix}, Japan"
        targets.setdefault(query, []).append(lid)

    print(f"{len(rows)} listings -> {len(targets)} unique municipalities")

    session = requests.Session()
    session.headers["User-Agent"] = "AkiyaFinder/1.0 (geocoding akiya listings)"

    updated = 0
    for i, (query, ids) in enumerate(targets.items(), 1):
        if query in cache:
            coord = cache[query]
        else:
            try:
                r = session.get(
                    "https://nominatim.openstreetmap.org/search",
                    params={"q": query, "format": "json", "limit": 1, "countrycodes": "jp"},
                    timeout=20,
                )
                data = r.json()
                coord = [float(data[0]["lat"]), float(data[0]["lon"])] if data else None
            except Exception:
                coord = None
            cache[query] = coord
            with open(CACHE, "w", encoding="utf-8") as f:
                json.dump(cache, f, ensure_ascii=False)
            time.sleep(1.1)  # Nominatim policy: max ~1 req/sec

        if coord:
            for lid in ids:
                conn.execute("UPDATE listings SET lat=?, lng=? WHERE id=?", (coord[0], coord[1], lid))
                updated += 1
        if i % 25 == 0:
            conn.commit()
            print(f"  {i}/{len(targets)} done, {updated} listings updated", flush=True)

    conn.commit()
    conn.close()
    print(f"DONE: {updated} listings geocoded to real towns")


if __name__ == "__main__":
    main()
