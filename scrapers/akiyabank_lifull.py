"""
LIFULL Akiya Bank scraper (https://www.homes.co.jp/akiyabank/).

This is a real national vacant-house bank — exactly on-theme for the site.
It sits behind AWS WAF (a JS challenge that plain requests can't pass), so we
drive a real headless browser (Playwright) which solves the challenge
automatically. Images, location, price and area are all on the list page —
no per-listing detail fetch needed.
"""
import json
import re
import time
import random

from bs4 import BeautifulSoup

from core.models import Listing
from core.normalize import normalize_price, is_valid_image

REGIONS = [
    "hokkaido", "tohoku", "kanto", "shinetsu", "hokuriku",
    "tokai", "kinki", "chugoku", "shikoku", "kyushu",
]

# Which prefectures each region covers (for least-covered-first ordering)
REGION_PREFS = {
    "hokkaido": ["北海道"],
    "tohoku": ["青森", "岩手", "宮城", "秋田", "山形", "福島"],
    "kanto": ["茨城", "栃木", "群馬", "埼玉", "千葉", "東京", "神奈川"],
    "shinetsu": ["新潟", "長野", "山梨"],
    "hokuriku": ["富山", "石川", "福井"],
    "tokai": ["岐阜", "静岡", "愛知", "三重"],
    "kinki": ["滋賀", "京都", "大阪", "兵庫", "奈良", "和歌山"],
    "chugoku": ["鳥取", "島根", "岡山", "広島", "山口"],
    "shikoku": ["徳島", "香川", "愛媛", "高知"],
    "kyushu": ["福岡", "佐賀", "長崎", "熊本", "大分", "宮崎", "鹿児島", "沖縄"],
}

BASE = "https://www.homes.co.jp/akiyabank/{}/"


def _ordered_regions():
    """Least-covered regions first (random tiebreak), so each run targets gaps."""
    try:
        from db.database import pref_counts
        counts = pref_counts("LIFULL Akiya Bank")
    except Exception:
        counts = {}
    return sorted(
        REGIONS,
        key=lambda r: (sum(counts.get(p, 0) for p in REGION_PREFS.get(r, [])), random.random()),
    )

PREF_RE = re.compile(r"(北海道|青森|岩手|宮城|秋田|山形|福島|茨城|栃木|群馬|埼玉|千葉|東京|神奈川|"
                     r"新潟|富山|石川|福井|山梨|長野|岐阜|静岡|愛知|三重|滋賀|京都|大阪|兵庫|奈良|"
                     r"和歌山|鳥取|島根|岡山|広島|山口|徳島|香川|愛媛|高知|福岡|佐賀|長崎|熊本|大分|"
                     r"宮崎|鹿児島|沖縄)")


def _dd_after(dl, label):
    """Return the <dd> text following the <dt> containing `label`."""
    for dt in dl.select("dt"):
        if label in dt.get_text():
            dd = dt.find_next_sibling("dd")
            if dd:
                return dd.get_text(" ", strip=True)
    return ""


def _parse(html):
    soup = BeautifulSoup(html, "html.parser")
    out = []
    for box in soup.select(".mod-result-bukkenBox"):
        cat_el = box.select_one(".categoryTag")
        category = cat_el.get_text(strip=True) if cat_el else ""

        # Buying site only — skip rentals (賃貸)
        if "賃貸" in category or "賃貸" in box.get_text():
            continue

        dl = box.select_one(".specText dl")
        if not dl:
            continue
        location = _dd_after(dl, "所在地")
        price_text = _dd_after(dl, "価格")
        land = _dd_after(dl, "土地面積")
        building = _dd_after(dl, "建物面積")
        layout = _dd_after(dl, "間取り")

        pm = PREF_RE.search(location)
        pref = pm.group(1) if pm else "不明"
        city = location[pm.end():].strip()[:30] if pm else location[:30]

        def num(s):
            m = re.search(r"([\d,]+(?:\.\d+)?)", s or "")
            return float(m.group(1).replace(",", "")) if m else None

        images = []
        for img in box.select(".bukkenPhoto img"):
            src = img.get("src") or img.get("data-src") or ""
            if is_valid_image(src) and src not in images:
                images.append(src)

        link = box.select_one("a[href*='/akiyabank/b-']")
        href = link.get("href") if link else "https://www.homes.co.jp/akiyabank/"

        addr_el = box.select_one(".bukkenTitle .address")
        title = (addr_el.get_text(strip=True) if addr_el else "") or (category + " " + city)

        out.append(Listing(
            id="",
            title=title[:80],
            prefecture=pref,
            city=city,
            price_jpy=normalize_price(price_text),
            price_label=price_text or "要確認",
            size_m2=num(building),
            land_m2=num(land),
            image_url=images[0] if images else "",
            source_url=href,
            source="LIFULL Akiya Bank",
            description=f"{category}・{location}".strip("・"),
            rooms=layout,
            built_year=None,
            condition=category,
            images=json.dumps(images),
        ))
    return out


def scrape(max_pages=3):
    from playwright.sync_api import sync_playwright

    results = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            locale="ja-JP",
        )
        page = ctx.new_page()

        empty_regions = 0
        for region in _ordered_regions():
            got_any = False
            seen_first = None
            for pg in range(1, max_pages + 1):
                url = BASE.format(region) + (f"?page={pg}" if pg > 1 else "")
                try:
                    page.goto(url, wait_until="domcontentloaded", timeout=30000)
                    try:
                        page.wait_for_selector(".mod-result-bukkenBox", timeout=15000)
                    except Exception:
                        break  # no listings (or page beyond last)
                    cards = _parse(page.content())
                    if not cards:
                        break
                    # stop if pagination looped back to the same first listing
                    if cards[0].source_url == seen_first:
                        break
                    seen_first = cards[0].source_url
                    results.append(cards)
                    got_any = True
                    print(f"  akiyabank {region} p{pg}: {len(cards)}", flush=True)
                    time.sleep(random.uniform(2, 3.5))
                except Exception as e:
                    print(f"  akiyabank {region} p{pg} error: {type(e).__name__}", flush=True)
                    break

            # Early-bail: if the IP is hard-blocked, regions yield nothing — stop wasting time
            empty_regions = 0 if got_any else empty_regions + 1
            if empty_regions >= 2:
                print("  akiyabank: looks IP-blocked, stopping early (retry later / different IP).", flush=True)
                break
            time.sleep(random.uniform(1.5, 3))

        browser.close()

    # flatten
    return [l for page_cards in results for l in page_cards]
