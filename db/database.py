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
        images TEXT
    )
    """)

    conn.commit()
    conn.close()


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


def listings_needing_images(min_images=5, limit=40):
    """Return (id, source_url, current_image_count) for SUUMO listings whose
    stored image set is small (i.e. only the list-page thumbnails)."""
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
    return out[:limit]


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

    # Don't let a re-scrape downgrade a backfilled gallery: if the stored row
    # already has MORE images than this scrape's (list-page) set, keep the
    # richer existing gallery + its lead image.
    try:
        row = c.execute("SELECT images, image_url FROM listings WHERE id=?", (listing.id,)).fetchone()
        if row and row[0]:
            existing = json.loads(row[0])
            incoming = json.loads(listing.images) if listing.images else []
            if len(existing) > len(incoming):
                listing.images = row[0]
                if existing:
                    listing.image_url = existing[0]
    except Exception:
        pass

    c.execute("""
    INSERT OR REPLACE INTO listings VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
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
    ))

    conn.commit()
    conn.close()