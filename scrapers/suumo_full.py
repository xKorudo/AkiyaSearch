"""
suumo_full.py — Single-pass comprehensive SUUMO scraper.

Fetches SUUMO list pages (plain HTTP) to collect detail-page URLs, then
visits each detail page with Playwright and extracts everything in one pass:
  price · land area · floor area · address · city · prefecture · built year
  情報提供日 (listed_at) · description · traffic access · full image gallery

No separate backfill steps needed — every saved listing is complete.

Progress is checkpointed per prefecture in the scrape_state DB table so
each run (100-200 listings) continues where the previous one stopped.

Usage:
    python scrapers/suumo_full.py [--limit 150] [--pref 東京]
"""
import sys
import re
import json
import time
import random
import hashlib
import sqlite3
import argparse
import datetime

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import requests
from bs4 import BeautifulSoup

from core.models import Listing
from core.normalize import normalize_price
from core.enrich import translate, PREF_COORDS
from db.database import DB, init_db, upsert

# ---------------------------------------------------------------------------
# Prefecture list (all 47 — same params as homes.py)
# ---------------------------------------------------------------------------
PREFECTURES = [
    ("北海道", "ar=010&bs=021&ta=01"),
    ("青森",   "ar=020&bs=021&ta=02"),
    ("岩手",   "ar=020&bs=021&ta=03"),
    ("宮城",   "ar=020&bs=021&ta=04"),
    ("秋田",   "ar=020&bs=021&ta=05"),
    ("山形",   "ar=020&bs=021&ta=06"),
    ("福島",   "ar=020&bs=021&ta=07"),
    ("茨城",   "ar=030&bs=021&ta=08"),
    ("栃木",   "ar=030&bs=021&ta=09"),
    ("群馬",   "ar=030&bs=021&ta=10"),
    ("埼玉",   "ar=030&bs=021&ta=11"),
    ("千葉",   "ar=030&bs=021&ta=12"),
    ("東京",   "ar=030&bs=021&ta=13"),
    ("神奈川", "ar=030&bs=021&ta=14"),
    ("新潟",   "ar=050&bs=021&ta=15"),
    ("富山",   "ar=050&bs=021&ta=16"),
    ("石川",   "ar=050&bs=021&ta=17"),
    ("福井",   "ar=050&bs=021&ta=18"),
    ("山梨",   "ar=050&bs=021&ta=19"),
    ("長野",   "ar=050&bs=021&ta=20"),
    ("岐阜",   "ar=040&bs=021&ta=21"),
    ("静岡",   "ar=040&bs=021&ta=22"),
    ("愛知",   "ar=040&bs=021&ta=23"),
    ("三重",   "ar=040&bs=021&ta=24"),
    ("滋賀",   "ar=060&bs=021&ta=25"),
    ("京都",   "ar=060&bs=021&ta=26"),
    ("大阪",   "ar=060&bs=021&ta=27"),
    ("兵庫",   "ar=060&bs=021&ta=28"),
    ("奈良",   "ar=060&bs=021&ta=29"),
    ("和歌山", "ar=060&bs=021&ta=30"),
    ("鳥取",   "ar=070&bs=021&ta=31"),
    ("島根",   "ar=070&bs=021&ta=32"),
    ("岡山",   "ar=070&bs=021&ta=33"),
    ("広島",   "ar=070&bs=021&ta=34"),
    ("山口",   "ar=070&bs=021&ta=35"),
    ("徳島",   "ar=080&bs=021&ta=36"),
    ("香川",   "ar=080&bs=021&ta=37"),
    ("愛媛",   "ar=080&bs=021&ta=38"),
    ("高知",   "ar=080&bs=021&ta=39"),
    ("福岡",   "ar=090&bs=021&ta=40"),
    ("佐賀",   "ar=090&bs=021&ta=41"),
    ("長崎",   "ar=090&bs=021&ta=42"),
    ("熊本",   "ar=090&bs=021&ta=43"),
    ("大分",   "ar=090&bs=021&ta=44"),
    ("宮崎",   "ar=090&bs=021&ta=45"),
    ("鹿児島", "ar=090&bs=021&ta=46"),
    ("沖縄",   "ar=090&bs=021&ta=47"),
]

LIST_URL = "https://suumo.jp/jj/bukken/ichiran/JJ012FC001/?{}&pn={}"

SESSION_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ja-JP,ja;q=0.9,en-US;q=0.8",
    "Referer": "https://suumo.jp/",
}

# ---------------------------------------------------------------------------
# Checkpoint helpers (stored in scrape_state table)
# ---------------------------------------------------------------------------

def _get_cursor(pref: str) -> int:
    try:
        conn = sqlite3.connect(DB)
        row = conn.execute(
            "SELECT value FROM scrape_state WHERE key=?",
            (f"full_cursor_{pref}",)
        ).fetchone()
        conn.close()
        return int(row[0]) if row else 1
    except Exception:
        return 1


def _set_cursor(pref: str, page: int):
    try:
        conn = sqlite3.connect(DB)
        conn.execute(
            "INSERT OR REPLACE INTO scrape_state VALUES (?, ?)",
            (f"full_cursor_{pref}", str(page))
        )
        conn.commit()
        conn.close()
    except Exception:
        pass


# ---------------------------------------------------------------------------
# List-page fetch (plain HTTP — no JS needed for pagination)
# ---------------------------------------------------------------------------

def _fetch_detail_urls(session, params: str, page: int):
    """
    Fetch one SUUMO results page and return (detail_urls, has_listings).
    Returns ([], False) on block/error.
    """
    url = LIST_URL.format(params, page)
    for _ in range(3):
        try:
            r = session.get(url, timeout=20)
        except Exception:
            time.sleep(random.uniform(10, 20))
            continue

        if r.status_code == 503 or len(r.text) < 12_000:
            time.sleep(random.uniform(25, 40))
            continue
        if r.status_code != 200:
            time.sleep(random.uniform(5, 10))
            continue

        soup = BeautifulSoup(r.text, "html.parser")
        cards = soup.select(".property_unit")
        if not cards:
            return [], len(r.text) < 120_000  # small=block, large=genuinely empty

        urls = []
        for card in cards:
            a = card.select_one(".property_unit-title a")
            if not a:
                continue
            title = a.get_text(strip=True)
            if re.search(r"賃貸|家賃|賃料|月額|月[\d,]+\s*万", title):
                continue  # skip rentals
            href = a.get("href", "")
            if href and not href.startswith("http"):
                href = "https://suumo.jp" + href
            if href:
                urls.append(href)
        return urls, True

    return [], False  # exhausted retries → treat as blocked


# ---------------------------------------------------------------------------
# Detail-page extraction (Playwright)
# ---------------------------------------------------------------------------

_EXTRACT_JS = """
() => {
    // Build key→value map from all th/td and dt/dd pairs
    const rows = {};
    for (const th of document.querySelectorAll('th, dt')) {
        const key = th.innerText.trim().replace(/\\s+/g, ' ');
        const sib = th.nextElementSibling;
        if (sib && key) rows[key] = sib.innerText.trim().replace(/\\s+/g, ' ');
    }

    // Title (h1 or property-title element)
    let title = '';
    for (const sel of ['h1', '[class*="property_view_note-title"]',
                        '[class*="bukken-title"]', '.property_unit-title']) {
        const el = document.querySelector(sel);
        if (el && el.innerText.trim()) { title = el.innerText.trim().slice(0, 100); break; }
    }

    // Description
    let description = '';
    for (const sel of [
        '.detail-box__text',
        '[class*="bukkenDetail-appeal"]',
        '[class*="bk-outline__comment"]',
        '[class*="appeal"]',
        '[class*="comment"]',
    ]) {
        const el = document.querySelector(sel);
        if (el && el.innerText.trim().length > 20) {
            description = el.innerText.trim().slice(0, 600);
            break;
        }
    }

    return { rows, title, description };
}
"""

_IMG_JS = """
(bukkenId) => {
    const out = [];
    for (const el of document.querySelectorAll('img')) {
        let u = el.currentSrc || el.src || el.getAttribute('rel') || '';
        if (!u || u.includes('base64')) continue;
        if (!u.includes('resizeImage') && !(u.includes('suumo') && u.includes('.jpg'))) continue;
        if (bukkenId && !u.includes('/' + bukkenId + '/') && !u.includes(bukkenId + '_')) continue;
        u = u.replace(/([?&])w=\\d+/, '$1w=1200').replace(/([?&])h=\\d+/, '$1h=900');
        if (!out.includes(u)) out.push(u);
    }
    return out;
}
"""


def _scrape_detail(pw_page, url: str, pref_jp: str):
    """
    Visit a SUUMO detail page with Playwright, extract all fields + images.
    Returns a Listing or None on failure.
    """
    try:
        pw_page.goto(url, wait_until="domcontentloaded", timeout=30_000)
        pw_page.wait_for_timeout(2_000)
        for _ in range(5):
            pw_page.mouse.wheel(0, 2_000)
            pw_page.wait_for_timeout(350)
    except Exception as e:
        print(f"    nav error: {e}", flush=True)
        return None

    try:
        data = pw_page.evaluate(_EXTRACT_JS)
    except Exception:
        return None

    rows        = data.get("rows", {})
    title       = data.get("title", "") or ""
    description = data.get("description", "") or ""

    # ---- Price ----
    price_text  = rows.get("販売価格") or rows.get("価格") or ""
    pm          = re.search(r"([\d,]+(?:\.\d+)?)\s*万円", price_text)
    price_label = (pm.group(1) + "万円") if pm else "要問合せ"
    price_jpy   = normalize_price(price_label) if pm else None

    # ---- Areas ----
    land_m2 = None
    lm = re.search(r"([\d.]+)", rows.get("土地面積", ""))
    if lm:
        land_m2 = float(lm.group(1))

    size_m2 = None
    fm = re.search(r"([\d.]+)", rows.get("建物面積", "") or rows.get("専有面積", ""))
    if fm:
        size_m2 = float(fm.group(1))

    # ---- Address / city ----
    addr = rows.get("所在地", "")
    city = re.sub(r"^.{2,4}[都道府県]", "", addr).strip()[:30] if addr else ""

    # ---- Built year ----
    built_year = None
    bm = re.search(r"(\d{4})年", rows.get("築年月", ""))
    if bm:
        built_year = int(bm.group(1))

    # ---- SUUMO publish date ----
    listed_at = None
    ldm = re.search(r"(\d{4})年(\d{1,2})月(\d{1,2})日", rows.get("情報提供日", ""))
    if ldm:
        listed_at = f"{ldm.group(1)}-{ldm.group(2).zfill(2)}-{ldm.group(3).zfill(2)}"

    # ---- Traffic ----
    traffic = rows.get("交通", "")[:400]

    # ---- Rooms ----
    rooms = rows.get("間取り", "")[:15]

    # ---- Additional property details ----
    building_structure = (rows.get("構造・工法") or rows.get("構造") or "")[:100]
    zoning = rows.get("用途地域", "")[:100]
    building_ratio = rows.get("建ぺい率・容積率", "")[:50]
    private_road = rows.get("私道負担・道路", "")[:100]
    other_restrictions = rows.get("その他制限事項", "")[:200]
    handover_date = (rows.get("引渡可能時期") or rows.get("引渡時期") or rows.get("引き渡し時期") or "")[:50]
    transaction_area = rows.get("売買対象面積", "")[:50]

    # ---- Equipment/features (Ausstattung) ----
    features_dict = {}
    for _k in ["間取り詳細", "キッチン", "バス・トイレ", "バス", "トイレ", "床・収納",
               "設備・サービス", "部屋の向き", "冷暖房", "駐車場"]:
        _v = rows.get(_k, "")
        if _v:
            features_dict[_k] = _v
    features = json.dumps(features_dict, ensure_ascii=False) if features_dict else ""

    # ---- Surroundings/nearby facilities ----
    surr_list = []
    for _k in ["スーパー", "コンビニ", "小学校", "中学校", "高校・大学", "病院",
               "公園", "銀行・ATM", "図書館", "郵便局", "薬局", "ドラッグストア"]:
        _v = rows.get(_k, "")
        if _v:
            surr_list.append({"type": _k, "info": _v})
    surroundings = json.dumps(surr_list, ensure_ascii=False) if surr_list else ""

    # ---- Agent/realtor (public mandatory disclosure) ----
    agent_company = (rows.get("会社名") or rows.get("不動産会社") or
                     rows.get("取扱不動産会社") or "")[:100]
    agent_license = rows.get("免許番号", "")[:60]

    # ---- Images ----
    m_id = re.search(r"nc_(\d+)", url)
    bukken_id = m_id.group(1) if m_id else ""
    try:
        imgs = pw_page.evaluate(_IMG_JS, bukken_id)
    except Exception:
        imgs = []

    # If detail page has no images it's almost certainly a block/redirect
    if not imgs:
        return None

    # ---- Geocode (prefecture centroid + scatter) ----
    coords = PREF_COORDS.get(pref_jp)
    lat = coords[0] + random.uniform(-0.5, 0.5) if coords else None
    lng = coords[1] + random.uniform(-0.5, 0.5) if coords else None

    # ---- Translate ----
    title_en       = ""
    description_en = ""
    try:
        title_en       = translate(title)
        description_en = translate(description)
    except Exception:
        pass

    src_id = hashlib.md5(url.encode()).hexdigest()

    return Listing(
        id=src_id,
        title=title or f"{pref_jp}の中古物件",
        prefecture=pref_jp,
        city=city,
        price_jpy=price_jpy,
        price_label=price_label,
        size_m2=size_m2,
        land_m2=land_m2,
        image_url=imgs[0] if imgs else "",
        source_url=url,
        source="SUUMO",
        description=description,
        title_en=title_en,
        description_en=description_en,
        lat=lat,
        lng=lng,
        rooms=rooms,
        built_year=built_year,
        condition="",
        images=json.dumps(imgs),
        traffic=traffic,
        first_seen=datetime.date.today().isoformat(),
        listed_at=listed_at,
        building_structure=building_structure,
        zoning=zoning,
        building_ratio=building_ratio,
        private_road=private_road,
        other_restrictions=other_restrictions,
        handover_date=handover_date,
        transaction_area=transaction_area,
        features=features,
        surroundings=surroundings,
        agent_company=agent_company,
        agent_license=agent_license,
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=150,
                        help="Max listings per prefecture per run (default 150)")
    parser.add_argument("--max-total", type=int, default=0,
                        help="Hard cap on total listings this run across all prefectures "
                             "(0 = unlimited, default). Useful for quick tests.")
    parser.add_argument("--pref",  type=str, default=None,
                        help="Only scrape this prefecture (Japanese name, e.g. 東京)")
    args = parser.parse_args()

    init_db()

    targets = [(p, q) for p, q in PREFECTURES if args.pref is None or p == args.pref]
    if not targets:
        print(f"Unknown prefecture: {args.pref}")
        sys.exit(1)

    session = requests.Session()
    session.headers.update(SESSION_HEADERS)

    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        ctx = browser.new_context(
            locale="ja-JP",
            user_agent=SESSION_HEADERS["User-Agent"],
        )
        pw_page = ctx.new_page()

        total_saved = 0
        consecutive_blocks = 0  # counts consecutive blocked prefectures

        for pref_jp, params in targets:
            # Hard total cap (used for quick tests via --max-total)
            if args.max_total and total_saved >= args.max_total:
                print(f"\nReached --max-total {args.max_total} — stopping.", flush=True)
                break

            start_page = _get_cursor(pref_jp)
            print(f"\n[{pref_jp}] starting from page {start_page} (limit {args.limit}/pref)", flush=True)

            pref_saved = 0
            blocked    = False

            page_num = start_page
            while pref_saved < args.limit:
                # Honour hard total cap inside the prefecture loop too
                if args.max_total and total_saved >= args.max_total:
                    break

                detail_urls, ok = _fetch_detail_urls(session, params, page_num)

                if not ok:
                    print(f"  [{pref_jp}] p{page_num}: no more listings — resetting cursor", flush=True)
                    _set_cursor(pref_jp, 1)
                    break

                if not detail_urls:
                    print(f"  [{pref_jp}] p{page_num}: list-page block", flush=True)
                    blocked = True
                    break

                print(f"  [{pref_jp}] p{page_num}: {len(detail_urls)} URLs", flush=True)

                for url in detail_urls:
                    if pref_saved >= args.limit:
                        break
                    if args.max_total and total_saved >= args.max_total:
                        break

                    listing = _scrape_detail(pw_page, url, pref_jp)

                    if listing is None:
                        consecutive_blocks += 1
                        print(f"    blocked/empty — ({consecutive_blocks} consecutive)", flush=True)
                        if consecutive_blocks >= 3:
                            print("  Sustained block — stopping early", flush=True)
                            blocked = True
                            break
                        time.sleep(random.uniform(20, 35))
                        continue

                    consecutive_blocks = 0
                    upsert(listing)
                    total_saved += 1
                    pref_saved  += 1
                    listed_note  = f"  listed={listing.listed_at}" if listing.listed_at else ""
                    traffic_note = "✓" if listing.traffic else "—"
                    extras = sum([
                        bool(listing.building_structure), bool(listing.zoning),
                        bool(listing.features), bool(listing.surroundings),
                        bool(listing.agent_company),
                    ])
                    print(
                        f"    [{pref_saved}/{args.limit} pref | {total_saved} total]"
                        f"  {len(json.loads(listing.images))} imgs"
                        f"  traffic={traffic_note}  extras={extras}/5{listed_note}"
                        f"  {url[-40:]}",
                        flush=True
                    )
                    time.sleep(random.uniform(3, 6))

                if blocked:
                    break

                _set_cursor(pref_jp, page_num + 1)
                page_num += 1
                time.sleep(random.uniform(5, 9))

            print(f"  [{pref_jp}] saved {pref_saved} listings this run", flush=True)
            if blocked:
                consecutive_blocks += 1
                if consecutive_blocks >= 2:
                    print("Multiple prefecture blocks — stopping run early", flush=True)
                    break
            else:
                consecutive_blocks = 0

        browser.close()

    print(f"\nDONE — {total_saved} total listings saved this run", flush=True)
    return total_saved


if __name__ == "__main__":
    main()
