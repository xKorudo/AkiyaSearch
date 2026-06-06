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

from db.database import listings_needing_images, listings_needing_traffic, update_images, update_detail_fields

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
    from playwright.sync_api import sync_playwright

    limit = int(sys.argv[1]) if len(sys.argv) > 1 else BATCH

    # Primary queue: listings needing more images
    img_todo = [t for t in listings_needing_images(min_images=5, limit=limit * 2)
                if "suumo.jp" in (t[1] or "")][:limit]

    # Secondary queue: listings with images but missing traffic info
    # Fill remaining budget after image pass
    traffic_only_ids = set(lid for lid, _ in listings_needing_traffic(limit=limit))
    img_ids = set(lid for lid, _, _ in img_todo)
    traffic_todo = [(lid, url) for lid, url in listings_needing_traffic(limit=limit)
                    if lid not in img_ids and "suumo.jp" in (url or "")]

    print(f"Listings needing galleries: {len(img_todo)}  |  needing traffic only: {len(traffic_todo)}", flush=True)

    img_done = traffic_done = fails = 0
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(
            locale="ja-JP",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        )
        page = ctx.new_page()

        # ── Pass 1: image backfill (also grabs traffic/description while here) ──
        for i, (lid, url, n) in enumerate(img_todo, 1):
            m = re.search(r"nc_(\d+)", url)
            bid = m.group(1) if m else ""
            try:
                imgs = extract_images(page, url, bid)  # page is already loaded
                fields = extract_detail_fields(page)
            except Exception:
                imgs = None
                fields = {}

            if not imgs:
                fails += 1
                print(f"  [img {i}/{len(img_todo)}] no images (likely blocked): {url[:50]}", flush=True)
                if fails >= 3:
                    print("  Repeated blocks — stopping early.", flush=True)
                    break
                time.sleep(random.uniform(15, 25))
                continue

            fails = 0
            update_images(lid, json.dumps(imgs), first_image=imgs[0])
            if fields.get("traffic") or fields.get("description"):
                update_detail_fields(lid, fields.get("traffic"), fields.get("description"))
            img_done += 1
            print(f"  [img {i}/{len(img_todo)}] {len(imgs)} photos  traffic={'✓' if fields.get('traffic') else '—'}  <- {url[:50]}", flush=True)
            time.sleep(random.uniform(2, 4))

        # ── Pass 2: traffic-only backfill (lightweight — no image extraction) ──
        if fails < 3:
            for i, (lid, url) in enumerate(traffic_todo, 1):
                try:
                    page.goto(url, wait_until="domcontentloaded", timeout=30000)
                    page.wait_for_timeout(1500)
                    fields = extract_detail_fields(page)
                except Exception:
                    fields = {}

                if not fields.get("traffic"):
                    fails += 1
                    print(f"  [traffic {i}/{len(traffic_todo)}] no data (likely blocked): {url[:50]}", flush=True)
                    if fails >= 3:
                        print("  Repeated blocks — stopping.", flush=True)
                        break
                    time.sleep(random.uniform(10, 18))
                    continue

                fails = 0
                update_detail_fields(lid, fields.get("traffic"), fields.get("description"))
                traffic_done += 1
                print(f"  [traffic {i}/{len(traffic_todo)}] ✓  <- {url[:50]}", flush=True)
                time.sleep(random.uniform(1.5, 3))

        browser.close()

    print(f"DONE: {img_done} galleries enriched, {traffic_done} traffic records added, {fails} failures")


if __name__ == "__main__":
    main()
