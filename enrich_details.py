"""
Backfill traffic (交通) and description from SUUMO detail pages.

Targets listings that already have images but are still missing transit info.
Runs as its own workflow (backfill-details.yml) so it gets a fresh IP and
doesn't compete with the image backfill for time or rate-limit budget.

Usage:  python enrich_details.py [max_listings]
"""
import sys
import time
import random

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from db.database import listings_needing_traffic, update_detail_fields

BATCH = 400


def extract_detail_fields(page):
    """Extract traffic (交通) and description (物件の特徴) from a SUUMO detail page."""
    return page.evaluate("""
    () => {
      let traffic = '';
      let description = '';

      for (const th of document.querySelectorAll('th, dt')) {
        if (th.textContent.trim() === '交通') {
          const td = th.nextElementSibling;
          if (td) { traffic = td.innerText.trim().slice(0, 400); break; }
        }
      }

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

    todo = [(lid, url) for lid, url in listings_needing_traffic(limit=limit, shard=shard, total_shards=total_shards)
            if "suumo.jp" in (url or "")]
    print(f"Listings needing traffic/description: {len(todo)}", flush=True)

    done = fails = 0
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(
            locale="ja-JP",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        )
        page = ctx.new_page()

        for i, (lid, url) in enumerate(todo, 1):
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=30000)
                page.wait_for_timeout(1500)
                fields = extract_detail_fields(page)
            except Exception:
                fields = {}

            if not fields.get("traffic"):
                fails += 1
                print(f"  [{i}/{len(todo)}] no data (likely blocked): {url[:55]}", flush=True)
                if fails >= 3:
                    print("  Repeated blocks — stopping early.", flush=True)
                    break
                time.sleep(random.uniform(12, 20))
                continue

            fails = 0
            update_detail_fields(lid, fields.get("traffic"), fields.get("description"))
            done += 1
            print(f"  [{i}/{len(todo)}] ✓ traffic+desc  <- {url[:55]}", flush=True)
            time.sleep(random.uniform(1.5, 3))

        browser.close()

    print(f"DONE: {done} records updated, {fails} failures")


if __name__ == "__main__":
    main()
