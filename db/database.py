import sqlite3
import os

# Resolve DB next to the project root regardless of where a script is run from
DB = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "akiya_v4.db")

def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS listings (
        id TEXT PRIMARY KEY,
        title TEXT,
        prefecture TEXT,
        city TEXT,
        price_jpy INTEGER,
        price_label TEXT,
        size_m2 REAL,
        land_m2 REAL,
        image_url TEXT,
        source_url TEXT,
        source TEXT,
        description TEXT,
        title_en TEXT,
        description_en TEXT,
        lat REAL,
        lng REAL,
        rooms TEXT,
        built_year INTEGER,
        condition TEXT,
        images TEXT,
        traffic TEXT DEFAULT '',
        first_seen TEXT DEFAULT '',
        listed_at TEXT
    )
    """)

    for col, defval in [("traffic", "''"), ("first_seen", "''"), ("listed_at", "NULL")]:
        try:
            c.execute(f"ALTER TABLE listings ADD COLUMN {col} TEXT DEFAULT {defval}")
        except Exception:
            pass  # column already exists

    # Scrape state table (deep-mode cursors etc.)
    c.execute("""
    CREATE TABLE IF NOT EXISTS scrape_state (
        key   TEXT PRIMARY KEY,
        value TEXT
    )
    """)

    conn.commit()
    conn.close()


def get_deep_cursor(pref: str):
    """Return the last page processed by the deep scraper for this prefecture.
    Returns None on first run (no cursor saved yet)."""
    try:
        conn = sqlite3.connect(DB)
        row = conn.execute(
            "SELECT value FROM scrape_state WHERE key=?",
            (f"deep_cursor_{pref}",)
        ).fetchone()
        conn.close()
        return int(row[0]) if row else None
    except Exception:
        return None


def set_deep_cursor(pref: str, page: int):
    """Persist the deep scraper cursor for this prefecture."""
    try:
        conn = sqlite3.connect(DB)
        conn.execute(
            "INSERT OR REPLACE INTO scrape_state VALUES (?, ?)",
            (f"deep_cursor_{pref}", str(page))
        )
        conn.commit()
        conn.close()
    except Exception:
        pass


def pref_counts(source=None):
    """Per-prefecture listing counts (optionally for one source). Drives
    least-covered-first scraping so runs target gaps instead of repeating."""
    try:
        conn = sqlite3.connect(DB)
        if source:
            rows = conn.execute(
                "SELECT prefecture, COUNT(*) FROM listings WHERE source=? GROUP BY prefecture",
                (source,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT prefecture, COUNT(*) FROM listings GROUP BY prefecture"
            ).fetchall()
        conn.close()
        return dict(rows)
    except Exception:
        return {}


def listings_needing_images(min_images=5, limit=40, shard=None, total_shards=2):
    """Return (id, source_url, current_image_count) for SUUMO listings whose
    stored image set is small (i.e. only the list-page thumbnails).

    When shard is not None, only returns the subset of rows where
    enumerate-index % total_shards == shard, enabling parallel workers to
    process non-overlapping slices of the backlog."""
    import json
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    rows = c.execute(
        "SELECT id, source_url, images FROM listings "
        "WHERE source='SUUMO' AND source_url LIKE 'http%' "
        "ORDER BY rowid DESC"   # newest/most-recently-seen first
    ).fetchall()
    conn.close()

    out = []
    for lid, url, imgs_json in rows:
        try:
            n = len(json.loads(imgs_json)) if imgs_json else 0
        except Exception:
            n = 0
        if n < min_images:
            out.append((lid, url, n))

    if shard is not None:
        out = [x for i, x in enumerate(out) if i % total_shards == shard]

    return out[:limit]


def listings_needing_traffic(limit=600, shard=None, total_shards=2):
    """SUUMO listings that still have no traffic/transit info — for backfill.

    When shard is not None, only returns the subset of rows where
    enumerate-index % total_shards == shard, enabling parallel workers to
    process non-overlapping slices of the backlog."""
    conn = sqlite3.connect(DB)
    rows = conn.execute(
        "SELECT id, source_url FROM listings "
        "WHERE source='SUUMO' AND source_url LIKE 'http%' "
        "AND (traffic IS NULL OR traffic = '') "
        "ORDER BY rowid DESC"
    ).fetchall()
    conn.close()

    out = list(rows)
    if shard is not None:
        out = [x for i, x in enumerate(out) if i % total_shards == shard]

    return out[:limit]


def update_detail_fields(listing_id, traffic=None, description=None):
    """Patch traffic and/or description scraped from a SUUMO detail page."""
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    if traffic and description:
        c.execute(
            "UPDATE listings SET traffic=?, description=CASE WHEN description IS NULL OR description='' OR description LIKE '%の中古物件' THEN ? ELSE description END WHERE id=?",
            (traffic, description, listing_id),
        )
    elif traffic:
        c.execute("UPDATE listings SET traffic=? WHERE id=?", (traffic, listing_id))
    elif description:
        c.execute(
            "UPDATE listings SET description=CASE WHEN description IS NULL OR description='' OR description LIKE '%の中古物件' THEN ? ELSE description END WHERE id=?",
            (description, listing_id),
        )
    conn.commit()
    conn.close()


def update_images(listing_id, images_json, first_image=None):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    if first_image:
        c.execute(
            "UPDATE listings SET images=?, "
            "image_url=CASE WHEN image_url IS NULL OR image_url='' THEN ? ELSE image_url END "
            "WHERE id=?",
            (images_json, first_image, listing_id),
        )
    else:
        c.execute("UPDATE listings SET images=? WHERE id=?", (images_json, listing_id))
    conn.commit()
    conn.close()


def upsert(listing):
    import json
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    # Stable dedup: if this source_url already exists under a different id
    # (e.g. SUUMO changed the title prefix), adopt the existing id.
    try:
        dup = c.execute(
            "SELECT id FROM listings WHERE source_url=? AND id!=? LIMIT 1",
            (listing.source_url, listing.id)
        ).fetchone()
        if dup:
            listing.id = dup[0]
            c.execute(
                "DELETE FROM listings WHERE source_url=? AND id!=?",
                (listing.source_url, listing.id)
            )
    except Exception:
        pass
    try:
        row = c.execute("SELECT images, image_url, listed_at FROM listings WHERE id=?", (listing.id,)).fetchone()
        if row:
            if row[0]:
                existing = json.loads(row[0])
                incoming = json.loads(listing.images) if listing.images else []
                if len(existing) > len(incoming):
                    listing.images = row[0]
                    if existing:
                        listing.image_url = existing[0]
            if row[2] and not listing.listed_at:
                listing.listed_at = row[2]
    except Exception:
        pass

    # Don't overwrite a backfilled traffic value with an empty one from the list-page scrape
    try:
        row2 = c.execute("SELECT traffic FROM listings WHERE id=?", (listing.id,)).fetchone()
        if row2 and row2[0] and not listing.traffic:
            listing.traffic = row2[0]
    except Exception:
        pass

    # Preserve first_seen — only set it once, on initial insert
    try:
        row3 = c.execute("SELECT first_seen FROM listings WHERE id=?", (listing.id,)).fetchone()
        if row3 and row3[0]:
            listing.first_seen = row3[0]  # keep the original date
        elif not listing.first_seen:
            import datetime
            listing.first_seen = datetime.date.today().isoformat()
    except Exception:
        if not listing.first_seen:
            import datetime
            listing.first_seen = datetime.date.today().isoformat()

    c.execute("""
    INSERT OR REPLACE INTO listings VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        listing.id,
        listing.title,
        listing.prefecture,
        listing.city,
        listing.price_jpy,
        listing.price_label,
        listing.size_m2,
        listing.land_m2,
        listing.image_url,
        listing.source_url,
        listing.source,
        listing.description,
        listing.title_en,
        listing.description_en,
        listing.lat,
        listing.lng,
        listing.rooms,
        listing.built_year,
        listing.condition,
        listing.images,
        listing.traffic,
        listing.first_seen,
        listing.listed_at,
    ))

    conn.commit()
    conn.close()


def update_listed_at(listing_id, date_str):
    """Set listed_at only if not already stored (preserve original SUUMO publish date)."""
    conn = sqlite3.connect(DB)
    conn.execute(
        "UPDATE listings SET listed_at=? WHERE id=? AND listed_at IS NULL",
        (date_str, listing_id),
    )
    conn.commit()
    conn.close()
