"""
Push scraped listings to Supabase and record price / sold changes.

This is what powers the watchlist notifications:
  - Upserts every scraped listing into the `listings` table (source of truth).
  - Compares the new price to the stored price -> logs a `listing_changes` row
    (price_drop / price_rise).
  - Updates `last_seen`; any active listing not seen in 30 days is flagged 'sold'
    (best-effort, since the scraper only covers part of Japan per run).

Runs only if SUPABASE_URL + SUPABASE_SERVICE_KEY are set (service_role bypasses
RLS). No-ops silently otherwise, so local dev without the key still works.
"""
import os
import json
import datetime as dt

import requests

URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")
SOLD_AFTER_DAYS = 30


def _headers(extra=None):
    h = {
        "apikey": KEY,
        "Authorization": f"Bearer {KEY}",
        "Content-Type": "application/json",
    }
    if extra:
        h.update(extra)
    return h


def _get_existing():
    """Return {id: {'price_jpy':..., 'status':...}} for all stored listings."""
    out = {}
    offset, page = 0, 1000
    while True:
        r = requests.get(
            f"{URL}/rest/v1/listings",
            headers=_headers({"Range-Unit": "items", "Range": f"{offset}-{offset+page-1}"}),
            params={"select": "id,price_jpy,status"},
            timeout=30,
        )
        if r.status_code not in (200, 206):
            break
        rows = r.json()
        for row in rows:
            out[row["id"]] = row
        if len(rows) < page:
            break
        offset += page
    return out


def _post(table, payload, prefer="resolution=merge-duplicates"):
    if not payload:
        return
    requests.post(
        f"{URL}/rest/v1/{table}",
        headers=_headers({"Prefer": prefer}),
        data=json.dumps(payload),
        timeout=60,
    )


def sync(listings):
    if not (URL and KEY):
        print("  Supabase sync skipped (no SUPABASE_SERVICE_KEY).")
        return
    if not listings:
        return

    now = dt.datetime.now(dt.timezone.utc).isoformat()
    existing = _get_existing()

    rows, changes = [], []
    for l in listings:
        old = existing.get(l.id)
        new_price = l.price_jpy

        if old is not None and old.get("price_jpy") is not None and new_price is not None:
            old_price = old["price_jpy"]
            if new_price != old_price:
                changes.append({
                    "listing_id": l.id,
                    "type": "price_drop" if new_price < old_price else "price_rise",
                    "old_price": old_price,
                    "new_price": new_price,
                })

        rows.append({
            "id": l.id,
            "title": l.title,
            "title_en": getattr(l, "title_en", "") or "",
            "prefecture": l.prefecture,
            "city": l.city,
            "price_jpy": new_price,
            "status": "active",
            "source": l.source,
            "source_url": l.source_url,
            "image_url": l.image_url,
            "last_seen": now,
            "updated_at": now,
        })

    # Upsert all listings (merge on primary key) + log the price changes
    for i in range(0, len(rows), 500):
        _post("listings", rows[i:i + 500])
    _post("listing_changes", changes, prefer="return=minimal")

    # Best-effort "sold": active listings not seen in 30 days
    cutoff = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=SOLD_AFTER_DAYS)).isoformat()
    r = requests.get(
        f"{URL}/rest/v1/listings",
        headers=_headers(),
        params={"select": "id,price_jpy", "status": "eq.active", "last_seen": f"lt.{cutoff}"},
        timeout=30,
    )
    sold = r.json() if r.status_code == 200 else []
    if sold:
        sold_changes = [{"listing_id": s["id"], "type": "sold",
                         "old_price": s.get("price_jpy"), "new_price": None} for s in sold]
        _post("listing_changes", sold_changes, prefer="return=minimal")
        # flag them sold
        requests.patch(
            f"{URL}/rest/v1/listings",
            headers=_headers({"Prefer": "return=minimal"}),
            params={"status": "eq.active", "last_seen": f"lt.{cutoff}"},
            data=json.dumps({"status": "sold"}),
            timeout=30,
        )

    print(f"  Supabase sync: {len(rows)} listings, {len(changes)} price changes, {len(sold)} marked sold.")
