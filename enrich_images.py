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

from db.database import listings_needing_images, update_images

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


def main():
    from playwright.sync_api import sync_playwright

    limit = int(sys.argv[1]) if len(sys.argv) > 1 else BATCH
    todo = [t for t in listings_needing_images(min_images=5, limit=limit * 2)
            if "suumo.jp" in (t[1] or "")][:limit]
    print(f"Listings needing full galleries: {len(todo)}")

    done = 0
    fails = 0
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(
            locale="ja-JP",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        )
        page = ctx.new_page()

        for i, (lid, url, n) in enumerate(todo, 1):
            m = re.search(r"nc_(\d+)", url)
            bid = m.group(1) if m else ""
            try:
                imgs = extract_images(page, url, bid)
            except Exception:
                imgs = None

            # No images almost always means a block/throttle (SUUMO listings have
            # photos). NEVER overwrite the existing set with an empty one — just
            # count it as a failure and bail if it keeps happening.
            if not imgs:
                fails += 1
                print(f"  [{i}/{len(todo)}] no images (likely blocked): {url[:50]}", flush=True)
                if fails >= 3:
                    print("  Repeated blocks — stopping early. Re-run later (or via Actions) to continue.", flush=True)
                    break
                time.sleep(random.uniform(15, 25))
                continue

            fails = 0
            update_images(lid, json.dumps(imgs), first_image=imgs[0])
            done += 1
            print(f"  [{i}/{len(todo)}] {len(imgs)} photos  <- {url[:50]}", flush=True)
            time.sleep(random.uniform(2, 4))

        browser.close()

    print(f"DONE: enriched {done}, failures {fails}")


if __name__ == "__main__":
    main()
