"""
Cross-listing similarity detection.

Compares freshly scraped listings against the accumulated DB and returns
pairs that score >= THRESHOLD (90/100) — potential duplicates queued for
admin review in the pending_reviews Supabase table.

Scoring (max 100):
  Prefecture match (pre-filtered by SQL):  25 pts
  City first-6-chars match:                25 pts  (10 pts for first-3 match)
  Price within  5% / 15%:                  25 / 15 pts
  Size  within 10% / 20%:                  25 / 15 pts
"""
import sqlite3
from db.database import DB

THRESHOLD = 90


def _score(ap, bp, ac, bc, asz, bsz):
    s = 25  # prefecture always matches (SQL pre-filters by prefecture=?)
    # City
    ac6, bc6 = (ac or "")[:6], (bc or "")[:6]
    if ac6 and bc6:
        if ac6 == bc6:
            s += 25
        elif ac6[:3] == bc6[:3]:
            s += 10
    # Price
    if ap and bp and ap > 0 and bp > 0:
        r = min(ap, bp) / max(ap, bp)
        if r >= 0.95:
            s += 25
        elif r >= 0.85:
            s += 15
    # Size
    if asz and bsz and asz > 0 and bsz > 0:
        r = min(asz, bsz) / max(asz, bsz)
        if r >= 0.90:
            s += 25
        elif r >= 0.80:
            s += 15
    return s


def find_pending_reviews(new_listings):
    """
    For each listing in new_listings, find the most similar existing DB row
    (different source_url). Returns list of (a_id, b_id, score) for pairs
    scoring >= THRESHOLD. Each pair is returned at most once (normalised by
    sorted ID order so (A,B) == (B,A)).
    """
    if not new_listings:
        return []

    conn = sqlite3.connect(DB)
    c = conn.cursor()
    pairs = []
    seen_pairs = set()

    for l in new_listings:
        if not l.id or not l.prefecture:
            continue
        price = l.price_jpy or 0
        size = l.size_m2 or 0

        # Widen the SQL range so graduated scoring can still run
        price_lo = round(price * 0.80) if price else 0
        price_hi = round(price * 1.20) if price else 999_999_999
        size_lo  = (size * 0.75) if size else 0
        size_hi  = (size * 1.25) if size else 999_999

        candidates = c.execute(
            """
            SELECT id, city, price_jpy, size_m2
            FROM listings
            WHERE prefecture = ? AND id != ? AND source_url != ?
            AND (price_jpy IS NULL OR price_jpy BETWEEN ? AND ?)
            AND (size_m2  IS NULL OR size_m2  BETWEEN ? AND ?)
            LIMIT 30
            """,
            (l.prefecture, l.id, l.source_url,
             price_lo, price_hi,
             size_lo,  size_hi),
        ).fetchall()

        best_id, best_score = None, 0
        for bid, bcity, bprice, bsize in candidates:
            sc = _score(price, bprice, l.city, bcity, size, bsize)
            if sc > best_score:
                best_score, best_id = sc, bid

        if best_score >= THRESHOLD and best_id:
            key = tuple(sorted([l.id, best_id]))
            if key not in seen_pairs:
                seen_pairs.add(key)
                # Always store: smaller ID as A, larger as B (stable ordering)
                pairs.append((key[0], key[1], best_score))

    conn.close()
    return pairs
