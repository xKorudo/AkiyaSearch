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


def _pref_counts():
    """Current listing count per prefecture (from the accumulated DB)."""
    try:
        import sqlite3
        from db.database import DB
        conn = sqlite3.connect(DB)
        rows = conn.execute(
            "SELECT prefecture, COUNT(*) FROM listings WHERE source='SUUMO' GROUP BY prefecture"
        ).fetchall()
        conn.close()
        return dict(rows)
    except Exception:
        return {}



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
    """Parse SUUMO dottable spec into (price, city, size_m2, land_m2, rooms, built_year, traffic)."""
    t = spec_text

    # Price: anchor on the sale-price field (販売価格 / 価格) so we never grab a
    # stray 万円 figure (monthly rent, management fee, etc.).
    price = None
    price_label = ""
    pm = re.search(r"(?:販売)?価格[^\d]*([\d,]+(?:\.\d+)?)\s*[|｜]?\s*万円", t)
    if pm:
        price_label = pm.group(1) + "万円"
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

    # Traffic / nearest station: 交通 | JR○○線 ○○駅 徒歩X分
    traffic = ""
    tm = re.search(r"交通\s*\|\s*([^\|]+)", t)
    if tm:
        traffic = tm.group(1).strip()[:200]

    return price, price_label, city, size_m2, land_m2, rooms, built_year, traffic


def _fetch_cards(session, url):
    """
    Fetch a SUUMO results page, robustly handling rate-limiting.
    - 503 / tiny page (~8KB) = hard block -> long cooldown, retry.
    - 200 but small page (~55KB) with 0 cards = soft block -> cooldown, retry once.
    - 200 large page with 0 cards = genuinely no more listings -> return [].
    Returns: list of cards, [] when a page genuinely has no listings,
             or None when the IP looks blocked (so the caller can bail).
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

        # 200 but no cards. Big page = genuinely no more listings (not a block).
        if len(r.text) > 120000:
            return []
        time.sleep(random.uniform(25, 40))  # small page = soft block, retry

    return None  # exhausted retries -> treat as blocked


def scrape(max_pages=3):
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "ja-JP,ja;q=0.9,en-US;q=0.8",
        "Referer": "https://suumo.jp/",
    })

    existing_urls = set()
    try:
        import sqlite3 as _sqlite3
        from db.database import DB as _DB
        _conn = _sqlite3.connect(_DB)
        existing_urls = set(r[0] for r in _conn.execute(
            "SELECT source_url FROM listings WHERE source='SUUMO'"
        ).fetchall())
        _conn.close()
    except Exception:
        pass

    results = []
    consecutive_blocked = 0

    counts = _pref_counts()
    # Shuffle randomly each run so all prefectures rotate evenly rather than
    # always fixing on the smallest one.
    order = list(PREFECTURES)
    random.shuffle(order)

    for pref_jp, params in order:
        pref_count = 0
        blocked = False
        # Always start from page 1: SUUMO sorts newest-first, so fresh listings
        # appear at the top regardless of how many we've stored. Jumping to a
        # deeper page skips new content entirely. Deduplication at insert time
        # discards already-known listings without wasting a DB write.
        #
        # Also try pages beyond our current coverage depth so the DB keeps
        # growing even when pages 1-N are fully known.
        fresh_pages = range(1, max_pages + 1)
        known_depth = counts.get(pref_jp, 0) // 30 + 1
        deep_pages = range(known_depth, known_depth + max_pages) if known_depth > max_pages else range(0)
        for page in sorted(set(fresh_pages) | set(deep_pages)):
            url = BASE.format(params, page)
            try:
                cards = _fetch_cards(session, url)
                if cards is None:      # IP blocked
                    blocked = True
                    break
                if not cards:          # no more listings in this prefecture
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

                    # Buying site — skip rentals (monthly pricing: 月X万円 / 賃貸 / 家賃 / 賃料)
                    if re.search(r"賃貸|家賃|賃料|月額|月[\d,]+\s*万", title + spec_text):
                        continue

                    price, price_label, city, size_m2, land_m2, rooms, built_year, traffic = _parse_spec(spec_text)

                    # Description from list-page comment block (no extra request)
                    desc_el = card.select_one(".property_unit-comment, .cassette-bukken-shousai-txt, [class*='comment']")
                    list_desc = desc_el.get_text(" ", strip=True)[:400] if desc_el else ""

                    # Detail page fetch for new listings
                    detail_desc = ""
                    detail_traffic = ""
                    if href and href not in existing_urls:
                        try:
                            dr = session.get(href, timeout=12)
                            if dr.status_code == 200 and len(dr.text) > 5000:
                                dsoup = BeautifulSoup(dr.text, "html.parser")
                                for sel in [".detail-box__text", "[class*='bukkenDetail-appeal']",
                                            "[class*='bk-outline__comment']", "[class*='appeal']"]:
                                    el = dsoup.select_one(sel)
                                    if el and len(el.get_text(strip=True)) > 20:
                                        detail_desc = el.get_text(" ", strip=True)[:500]
                                        break
                                for th in dsoup.select("th, dt"):
                                    if th.get_text(strip=True) == "交通":
                                        td = th.find_next_sibling()
                                        if td:
                                            detail_traffic = td.get_text(" ", strip=True)[:300]
                                        break
                        except Exception:
                            pass
                        time.sleep(random.uniform(1, 2))

                    description = detail_desc or list_desc or f"{pref_jp}の中古物件"
                    final_traffic = detail_traffic or traffic

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
                        description=description,
                        rooms=rooms,
                        built_year=built_year,
                        condition="",
                        images=json.dumps(all_imgs),
                        traffic=final_traffic,
                    ))
                    pref_count += 1

            except Exception as e:
                ta = params.split("ta=")[-1]
                print(f"SUUMO error (ta={ta} p{page}):", e)
                continue

        ta = params.split("ta=")[-1]
        print(f"  pref ta={ta}: {pref_count} new", flush=True)

        # Early-bail ONLY on real blocks (not on prefectures that are simply
        # exhausted) so we don't keep hammering a blocked IP.
        consecutive_blocked = consecutive_blocked + 1 if blocked else 0
        if consecutive_blocked >= 4:
            print("  Sustained block - stopping early. Next run (fresh IP) continues the gaps.", flush=True)
            break

        # polite pause between prefectures to stay under the throttle threshold
        time.sleep(random.uniform(5, 8))

    return results
