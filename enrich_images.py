"""
Full-gallery image backfill (Playwright).

The SUUMO list page only exposes ~4 thumbnails; the full photo set (10-30+) lives
on each listing's detail page and is lazy-loaded by JavaScript — so a plain HTTP
fetch misses most of them. This drives a real headless browser, scrolls to trigger
lazy loading, and extracts every photo that belongs to THIS listing (filtered by
its bukken id, so other listings' thumbnails on the page are excluded).

Incremental + resumable: only processes listings that don't yet have a full set,
and bails early if the IP starts getting blocked. Re-run (or let the daily job)
to continue.

Usage:  python enrich_images.py [max_listings]
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

from db.database import init_db, listings_needing_images, listings_needing_traffic, update_images, update_detail_fields
init_db()  # ensure traffic column exists on cached DBs that predate the migration

BATCH = 60


def extract_images(page, url, bukken_id):
    page.goto(url, wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(2000)
    for _ in range(4):
        page.mouse.wheel(0, 2500)
        page.wait_for_timeout(500)
    raw = page.eval_on_selector_all(
        "img", "els => els.map(e => e.currentSrc || e.src || e.getAttribute('rel') || '').filter(Boolean)"
    )
    imgs = []
    for u in raw:
        if "base64" in u:
            continue
        if not ("resizeImage" in u or ("suumo" in u and ".jpg" in u)):
            continue
        # keep only photos belonging to this listing
        if bukken_id and not (f"/{bukken_id}/" in u or f"%2F{bukken_id}%2F" in u or f"{bukken_id}_" in u):
            continue
        u = re.sub(r"([?&])w=\d+", r"\1w=1200", u)
        u = re.sub(r"([?&])h=\d+", r"\1h=900", u)
        if u not in imgs:
            imgs.append(u)
    return imgs


def extract_detail_fields(page):
    """Extract traffic (交通) and description (物件の特徴) from an already-loaded SUUMO detail page."""
    return page.evaluate("""
    () => {
      let traffic = '';
      let description = '';

      // 交通: find the <th> or <dt> labelled 交通 and grab its sibling value
      for (const th of document.querySelectorAll('th, dt')) {
        if (th.textContent.trim() === '交通') {
          const td = th.nextElementSibling;
          if (td) { traffic = td.innerText.trim().slice(0, 400); break; }
        }
      }

      // 物件の特徴・おすすめポイント — try common SUUMO detail-page selectors
      for (const sel of [
        '.detail-box__text',
        '[class*="bukkenDetail-appeal"]',
        '[class*="bk-outline__comment"]',
        '[class*="appeal"]',
      ]) {
        const el = document.querySelector(sel);
        if (el && el.textContent.trim().length > 20) {
          description = el.textContent.trim().slice(0, 600);
          break;
        }
      }

      return { traffic, description };
    }
    """)


def main():
    import argparse
    from playwright.sync_api import sync_playwright

    parser = argparse.ArgumentParser()
    parser.add_argument("limit", nargs="?", type=int, default=BATCH)
    parser.add_argument("--shard", type=int, default=None)
    parser.add_argument("--total-shards", type=int, default=2)
    args = parser.parse_args()
    limit = args.limit
    shard = args.shard
    total_shards = args.total_shards

    img_todo = [t for t in listings_needing_images(min_images=5, limit=limit * 2, shard=shard, total_shards=total_shards)
                if "suumo.jp" in (t[1] or "")][:limit]
    print(f"Listings needing full galleries: {len(img_todo)}", flush=True)

    done = fails = 0
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(
            locale="ja-JP",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        )
        page = ctx.new_page()

        for i, (lid, url, n) in enumerate(img_todo, 1):
            m = re.search(r"nc_(\d+)", url)
            bid = m.group(1) if m else ""
            try:
                imgs = extract_images(page, url, bid)  # page already loaded by extract_images
                fields = extract_detail_fields(page)   # free — page is already there
            except Exception:
                imgs = None
                fields = {}

            if not imgs:
                fails += 1
                print(f"  [{i}/{len(img_todo)}] no images (likely blocked): {url[:50]}", flush=True)
                if fails >= 3:
                    print("  Repeated blocks — stopping early. Re-run later to continue.", flush=True)
                    break
                time.sleep(random.uniform(15, 25))
                continue

            fails = 0
            update_images(lid, json.dumps(imgs), first_image=imgs[0])
            if fields.get("traffic") or fields.get("description"):
                update_detail_fields(lid, fields.get("traffic"), fields.get("description"))
            done += 1
            print(f"  [{i}/{len(img_todo)}] {len(imgs)} photos  traffic={'✓' if fields.get('traffic') else '—'}  <- {url[:50]}", flush=True)
            time.sleep(random.uniform(2, 4))

        browser.close()

    print(f"DONE: enriched {done}, failures {fails}")


if __name__ == "__main__":
    main()
