"""
Scrapes SUUMO used house listings (中古マンション/一戸建て).
Uses the JJ012FC001 results endpoint which returns proper static HTML.
"""
import requests
from bs4 import BeautifulSoup
import random
import time
import re
import json

from core.models import Listing
from core.normalize import normalize_price, is_valid_image

# All 47 prefectures. bs=021 = used detached houses (中古一戸建て, the akiya type).
# ar = SUUMO regional code, ta = prefecture JIS code.
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

BASE = "https://suumo.jp/jj/bukken/ichiran/JJ012FC001/?{}&pn={}"


def _parse_spec(spec_text: str):
    """Parse SUUMO dottable spec into (price, city, size_m2, land_m2, rooms, built_year)."""
    t = spec_text

    # Price: 販売価格 | 850万円
    price = None
    price_label = ""
    pm = re.search(r"([\d,]+)\s*万円", t)
    if pm:
        price_label = pm.group(0)
        price = normalize_price(price_label)

    # Location: 所在地 | 東京都東大和市湖畔３
    city = ""
    cm = re.search(r"所在地\s*\|\s*([^\|]{4,40})", t)
    if cm:
        city = re.sub(r'^.{2,4}[都道府県]', '', cm.group(1)).strip()[:30]

    # Floor area: 専有面積 / 建物面積 | 76.14m
    size_m2 = None
    sm = re.search(r"(?:専有面積|建物面積)\s*\|\s*([\d.]+)", t)
    if sm:
        size_m2 = float(sm.group(1))

    # Land area: 土地面積 | 120.5m
    land_m2 = None
    lm = re.search(r"土地面積\s*\|\s*([\d.]+)", t)
    if lm:
        land_m2 = float(lm.group(1))

    # Layout: 間取り | 3LDK
    rooms = ""
    rm = re.search(r"間取り\s*\|\s*([^\|]{1,10})", t)
    if rm:
        rooms = rm.group(1).strip()

    # Built year: 築年月 | 1975年3月
    built_year = None
    bm = re.search(r"築年月\s*\|\s*(\d{4})年", t)
    if bm:
        built_year = int(bm.group(1))

    return price, price_label, city, size_m2, land_m2, rooms, built_year


def _fetch_cards(session, url):
    """
    Fetch a SUUMO results page, robustly handling rate-limiting.
    - 503 / tiny page (~8KB) = hard block -> long cooldown, retry.
    - 200 but small page (~55KB) with 0 cards = soft block -> cooldown, retry once.
    - 200 large page with 0 cards = genuinely no inventory -> return [].
    Returns list of card elements.
    """
    for attempt in range(4):
        try:
            r = session.get(url, timeout=25)
        except Exception:
            time.sleep(random.uniform(20, 30))
            continue

        if r.status_code == 503 or len(r.text) < 12000:
            # Hard block — wait it out
            time.sleep(random.uniform(30, 45))
            continue

        if r.status_code != 200:
            time.sleep(random.uniform(10, 15))
            continue

        cards = BeautifulSoup(r.text, "html.parser").select(".property_unit")
        if cards:
            return cards

        # 200 but no cards. Big page = truly empty; small = soft block.
        if len(r.text) > 120000:
            return []
        time.sleep(random.uniform(25, 40))

    return []


def scrape(max_pages=3):
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "ja-JP,ja;q=0.9,en-US;q=0.8",
        "Referer": "https://suumo.jp/",
    })

    results = []
    consecutive_blocked = 0

    for pref_jp, params in PREFECTURES:
        pref_count = 0
        for page in range(1, max_pages + 1):
            url = BASE.format(params, page)
            try:
                cards = _fetch_cards(session, url)
                if not cards:
                    break

                for card in cards:
                    # Title + link
                    title_el = card.select_one(".property_unit-title a")
                    if not title_el:
                        continue
                    title = title_el.get_text(strip=True)[:80]
                    href = title_el.get("href", "")
                    if href and not href.startswith("http"):
                        href = "https://suumo.jp" + href

                    # Images — lazy loaded: actual URL is in `rel`, src is base64 placeholder
                    all_imgs = []
                    for img_el in card.select("img"):
                        candidate = img_el.get("rel") or img_el.get("data-src") or img_el.get("src") or ""
                        if candidate.startswith("//"):
                            candidate = "https:" + candidate
                        if is_valid_image(candidate) and "base64" not in candidate and candidate not in all_imgs:
                            all_imgs.append(candidate)
                    img = all_imgs[0] if all_imgs else ""

                    # Spec table
                    spec_el = card.select_one(".dottable--cassette")
                    spec_text = spec_el.get_text(" | ", strip=True) if spec_el else ""
                    price, price_label, city, size_m2, land_m2, rooms, built_year = _parse_spec(spec_text)

                    results.append(Listing(
                        id="",
                        title=title,
                        prefecture=pref_jp,
                        city=city,
                        price_jpy=price,
                        price_label=price_label or "要問合せ",
                        size_m2=size_m2,
                        land_m2=land_m2,
                        image_url=img,
                        source_url=href or url,
                        source="SUUMO",
                        description=f"{pref_jp}の中古物件",
                        rooms=rooms,
                        built_year=built_year,
                        condition="",
                        images=json.dumps(all_imgs),
                    ))
                    pref_count += 1

            except Exception as e:
                ta = params.split("ta=")[-1]
                print(f"SUUMO error (ta={ta} p{page}):", e)
                continue

        # ta code is ascii-safe for the console
        ta = params.split("ta=")[-1]
        print(f"  pref ta={ta}: {pref_count} listings", flush=True)

        # Early-bail on a sustained block: once SUUMO blocks the IP it stays
        # blocked for a while, so grinding through the rest just wastes time
        # (and keeps the IP blocked longer). Stop and keep what we have.
        if pref_count == 0:
            consecutive_blocked += 1
        else:
            consecutive_blocked = 0
        if consecutive_blocked >= 5:
            print("  Sustained block detected - stopping early. Re-run later to fill the rest.", flush=True)
            break

        # polite pause between prefectures to stay under the throttle threshold
        time.sleep(random.uniform(5, 8))

    return results
