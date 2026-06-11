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
import os
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

# Allow `from core.xxx import ...` when run directly as a script
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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
# Field-value translation helpers
# ---------------------------------------------------------------------------

_STRUCTURE_SUBS = [
    ("鉄筋コンクリート造", "Reinforced concrete"),
    ("鉄骨鉄筋コンクリート造", "Steel-reinforced concrete"),
    ("SRC造",          "Steel-reinforced concrete"),
    ("RC造",           "Reinforced concrete"),
    ("軽量鉄骨造",     "Light steel frame"),
    ("重量鉄骨造",     "Heavy steel frame"),
    ("鉄骨プレハブ造", "Steel prefab"),
    ("プレハブ造",     "Prefab"),
    ("鉄骨造",         "Steel frame"),
    ("木造",           "Wood frame"),
    ("ブロック造",     "Block construction"),
    ("ALC造",          "ALC panel"),
    ("ログ造",         "Log house"),
    ("ログハウス",     "Log house"),
    ("ツーバイフォー工法", "2×4 frame"),
    ("2×4工法",        "2×4 frame"),
    ("パネル工法",     "Panel system"),
    ("平屋建て",       "single-story"),
    ("平屋建",         "single-story"),
    ("平屋",           "single-story"),
    ("・",             ", "),
    ("（",             " ("),
    ("）",             ")"),
]

_ZONING_MAP = {
    "第1種低層住居専用地域": "Class 1 Low-Rise Residential",
    "第2種低層住居専用地域": "Class 2 Low-Rise Residential",
    "第1種中高層住居専用地域": "Class 1 Mid/High-Rise Residential",
    "第2種中高層住居専用地域": "Class 2 Mid/High-Rise Residential",
    "第1種住居地域": "Class 1 Residential",
    "第2種住居地域": "Class 2 Residential",
    "準住居地域": "Quasi-Residential",
    "近隣商業地域": "Neighborhood Commercial",
    "商業地域": "Commercial",
    "準工業地域": "Quasi-Industrial",
    "工業地域": "Industrial",
    "工業専用地域": "Exclusive Industrial",
    "田園住居地域": "Agricultural Residential",
    "市街化調整区域": "Urban Development Control Area",
    "1種低層": "Class 1 Low-Rise Residential",
    "2種低層": "Class 2 Low-Rise Residential",
    "1種中高層": "Class 1 Mid/High-Rise Residential",
    "2種中高層": "Class 2 Mid/High-Rise Residential",
    "1種住居": "Class 1 Residential",
    "2種住居": "Class 2 Residential",
    "準住居": "Quasi-Residential",
    "近隣商業": "Neighborhood Commercial",
    "商業": "Commercial",
    "準工業": "Quasi-Industrial",
    "工業専用": "Exclusive Industrial",
    "工業": "Industrial",
    "田園住居": "Agricultural Residential",
    "非線引": "Non-demarcated Area",
    "白地": "Unzoned Area",
    "調整区域": "Development Control Area",
    "無指定": "Unzoned",
    "指定無し": "Unzoned",
}

_HANDOVER_PATTERNS = [
    ("即引渡可", "Immediate"),
    ("即時引渡", "Immediate"),
    ("即引き渡し可", "Immediate"),
    ("即時", "Immediate"),
    ("相談", "Negotiable"),
    ("要相談", "Negotiable"),
    ("引渡時期相談", "Negotiable"),
    ("更地渡し", "Vacant lot transfer"),
    ("現況渡し", "As-is"),
    ("現状渡し", "As-is"),
    ("未定", "TBD"),
]

_MONTH_EN = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
_ERA_BASE2 = {"明治": 1868, "大正": 1912, "昭和": 1926, "平成": 1989, "令和": 2019}

# Full-width digits / letters → half-width (SUUMO uses ０１２… in many fields)
_FW_TABLE = str.maketrans("０１２３４５６７８９（）", "0123456789()")

def _to_hw(s: str) -> str:
    return s.translate(_FW_TABLE)


def _translate_structure(s: str) -> str:
    if not s or sum(1 for c in s if ord(c) > 127) < 2:
        return s
    result = _to_hw(s)
    for jp, en in _STRUCTURE_SUBS:
        result = result.replace(jp, en)
    # "地上N階建(て)" and "地上N階" → "N-story"
    result = re.sub(r"地上(\d+)階建て?", lambda m: m.group(1) + "-story", result)
    result = re.sub(r"地上(\d+)階",     lambda m: m.group(1) + "-story", result)
    # "N階建(て)" → "N-story"
    result = re.sub(r"(\d+)階建て?",    lambda m: m.group(1) + "-story", result)
    # strip any remaining 地上/地下 that weren't caught above
    result = result.replace("地上", "").replace("地下", "")
    return result.strip(", ").strip()


def _translate_zoning(s: str) -> str:
    if not s or sum(1 for c in s if ord(c) > 127) < 2:
        return s
    # Normalise full-width digits before lookup
    result = _to_hw(s)
    for jp, en in sorted(_ZONING_MAP.items(), key=lambda x: -len(x[0])):
        result = result.replace(jp, en)
    result = result.replace("/", " / ").replace("・", " / ")
    return result


def _translate_license(s: str) -> str:
    """国土交通大臣（1）第009996号 → MLIT License No. 009996 (Renewal 1)"""
    if not s or sum(1 for c in s if ord(c) > 127) < 2:
        return s
    s = _to_hw(s)
    m = re.search(r"国土交通大臣[（(](\d+)[）)]\s*第(\d+)号", s)
    if m:
        return f"MLIT License No. {m.group(2)} (Renewal {m.group(1)})"
    m2 = re.search(r"(.{2,5}知事)[（(](\d+)[）)]\s*第(\d+)号", s)
    if m2:
        return f"Governor License No. {m2.group(3)} (Renewal {m2.group(2)})"
    return s


_STATUS_MAP = {
    "空室": "Vacant", "空き": "Vacant", "空家": "Vacant",
    "居住中": "Occupied", "使用中": "In use",
    "賃貸中": "Tenanted", "賃借中": "Tenanted",
    "更地": "Cleared land", "建築中": "Under construction",
}

_RIGHTS_MAP = {
    "所有権": "Freehold",
    "旧法地上権": "Old-code Surface Rights",
    "旧法賃借権": "Old-code Leasehold",
    "普通賃借権": "Standard Leasehold",
    "定期賃借権": "Fixed-term Leasehold",
    "旧法借地権": "Old-code Leasehold",
    "借地権": "Leasehold",
    "地上権": "Surface Rights",
}

_LAND_CAT_MAP = {
    "宅地": "Residential land",
    "田": "Rice paddy",
    "畑": "Field/farmland",
    "山林": "Forest",
    "雑種地": "Miscellaneous land",
    "原野": "Wasteland",
    "公衆用道路": "Public road",
    "農地": "Agricultural land",
}


def _lookup(s: str, mapping: dict) -> str:
    """Return English if key in mapping, otherwise original string."""
    if not s:
        return s
    s2 = _to_hw(s).strip()
    return mapping.get(s2) or mapping.get(s) or s


def _translate_handover(s: str) -> str:
    if not s or sum(1 for c in s if ord(c) > 127) < 2:
        return s
    for jp, en in _HANDOVER_PATTERNS:
        if jp in s:
            return en
    # Japanese era year: 令和7年3月 → Mar 2025
    m = re.search(r"(明治|大正|昭和|平成|令和)(\d+|元)年(\d+)月", s)
    if m:
        base = _ERA_BASE2[m.group(1)]
        yr = 1 if m.group(2) == "元" else int(m.group(2))
        year = base + yr - 1
        month = int(m.group(3))
        if 1 <= month <= 12:
            return f"{_MONTH_EN[month-1]} {year}"
    # Western year: 2025年3月
    m2 = re.search(r"(\d{4})年(\d+)月", s)
    if m2:
        year = int(m2.group(1))
        month = int(m2.group(2))
        if 1 <= month <= 12:
            return f"{_MONTH_EN[month-1]} {year}"
    try:
        return translate(s) or s
    except Exception:
        return s


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


def _get_existing_next_updates(urls: list) -> dict:
    """Return {url: next_update_str} for URLs already in the DB that have a
    next_update date stored.  Used to skip re-scraping before SUUMO's own
    scheduled refresh date."""
    if not urls:
        return {}
    ids_map = {hashlib.md5(u.encode()).hexdigest(): u for u in urls}
    try:
        conn = sqlite3.connect(DB)
        ph = ",".join("?" * len(ids_map))
        rows = conn.execute(
            f"SELECT id, next_update FROM listings WHERE id IN ({ph})",
            list(ids_map.keys()),
        ).fetchall()
        conn.close()
        return {ids_map[r[0]]: r[1] for r in rows if r[0] in ids_map and r[1]}
    except Exception:
        return {}


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
    // Build key→value map covering all three table layouts used by SUUMO:
    //   Layout 1 — same row: <tr><th>A</th><td>a</td><th>B</th><td>b</td></tr>
    //   Layout 2 — header/data rows: <tr><th>A</th><th>B</th></tr><tr><td>a</td><td>b</td></tr>
    //   Layout 3 — definition lists: <dt>A</dt><dd>a</dd>
    const rows = {};

    function add(key, val) {
        // Strip SUUMO's tooltip suffix "ヒント" and trailing colons (full-width ： or half-width :)
        // from every th label before storing, so lookups work without knowing these suffixes.
        // e.g. "構造・工法 ヒント" → "構造・工法", "免許番号：" → "免許番号"
        const cleanKey = key.replace(/\\s*ヒント$/, '').replace(/[：:]+\\s*$/, '').trim();
        const cleanVal = val.replace(/\\s*地図\\s*.*$/, '').trim().replace(/\\s+/g, ' ');
        if (cleanKey && cleanVal) rows[cleanKey] = cleanVal;
    }

    // Layout 1: same-row th/td pairs — pair ths[i] → tds[i] within each tr
    for (const tr of document.querySelectorAll('tr')) {
        const ths = Array.from(tr.querySelectorAll('th'));
        const tds = Array.from(tr.querySelectorAll('td'));
        if (ths.length > 0 && tds.length > 0) {
            ths.forEach((th, i) => {
                if (tds[i]) add(th.innerText.trim().replace(/\\s+/g, ' '),
                                tds[i].innerText.trim().replace(/\\s+/g, ' '));
            });
        }
    }

    // Layout 2: header-row then data-row (SUUMO summary tables use this)
    for (const table of document.querySelectorAll('table')) {
        const trs = Array.from(table.rows);
        for (let i = 0; i + 1 < trs.length; i++) {
            const heads = Array.from(trs[i].querySelectorAll('th'));
            if (heads.length === 0 || trs[i].querySelector('td')) continue; // not a pure header row
            const vals = Array.from(trs[i + 1].querySelectorAll('td'));
            if (vals.length >= heads.length) {
                heads.forEach((th, j) => add(
                    th.innerText.trim().replace(/\\s+/g, ' '),
                    vals[j].innerText.trim().replace(/\\s+/g, ' ')
                ));
            }
        }
    }

    // Layout 3: dl/dt/dd
    for (const dt of document.querySelectorAll('dt')) {
        const key = dt.innerText.trim().replace(/\\s+/g, ' ');
        if (!key) continue;
        let dd = dt.nextElementSibling;
        while (dd && dd.tagName !== 'DD') dd = dd.nextElementSibling;
        if (dd) add(key, dd.innerText.trim().replace(/\\s+/g, ' '));
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
    # Strip trailing "地図" map-link text injected by SUUMO into innerText
    addr = re.sub(r"\s*地図\s*.*$", "", rows.get("所在地", "")).strip()
    city = re.sub(r"^.{2,4}[都道府県]", "", addr).strip()[:30] if addr else ""

    # ---- Built year ----
    # SUUMO stores dates as western year ("2012年") OR Japanese era year ("平成23年").
    _ERA_BASE = {"明治": 1868, "大正": 1912, "昭和": 1926, "平成": 1989, "令和": 2019}
    built_year = None
    for _bk in ("築年月", "完成時期(築年月)", "完成時期（築年月）", "建築年月", "築年"):
        _raw = rows.get(_bk, "")
        if not _raw:
            continue
        # Western year (4-digit)
        bm = re.search(r"(\d{4})年", _raw)
        if bm:
            built_year = int(bm.group(1))
            break
        # Japanese era year (e.g. 平成23年, 令和元年)
        bm = re.search(r"(明治|大正|昭和|平成|令和)(\d+|元)年", _raw)
        if bm:
            era_base = _ERA_BASE[bm.group(1)]
            era_yr   = 1 if bm.group(2) == "元" else int(bm.group(2))
            built_year = era_base + era_yr - 1
            break

    # ---- SUUMO publish date ----
    listed_at = None
    ldm = re.search(r"(\d{4})年(\d{1,2})月(\d{1,2})日", rows.get("情報提供日", ""))
    if ldm:
        listed_at = f"{ldm.group(1)}-{ldm.group(2).zfill(2)}-{ldm.group(3).zfill(2)}"

    # ---- Next scheduled update date (次回更新予定日) ----
    next_update = ""
    for _nk in ("次回更新予定日", "次回更新日", "更新日"):
        _raw = rows.get(_nk, "")
        if _raw:
            ndm = re.search(r"(\d{4})年(\d{1,2})月(\d{1,2})日", _raw)
            if ndm:
                next_update = f"{ndm.group(1)}-{ndm.group(2).zfill(2)}-{ndm.group(3).zfill(2)}"
                break

    # ---- Traffic ----
    # Strip SUUMO's inline "乗り換え案内" link text, then translate each line.
    _traffic_raw = rows.get("交通", "")
    _traffic_lines = []
    for _tl in _traffic_raw.split("\n"):
        _tl = re.sub(r"[\[［]?\s*乗り換え案内\s*[\]］]?", "", _tl).strip()
        if not _tl:
            continue
        try:
            _tl = translate(_tl) or _tl
        except Exception:
            pass
        _traffic_lines.append(_tl)
    traffic = "\n".join(_traffic_lines)[:400]

    # ---- Rooms ----
    rooms = rows.get("間取り", "")[:15]

    # ---- Additional property details ----
    building_structure = _translate_structure(
        (rows.get("構造・工法") or rows.get("構造") or "")[:100]
    )
    zoning = _translate_zoning(rows.get("用途地域", "")[:100])
    building_ratio = rows.get("建ぺい率・容積率", "")[:50]
    _private_road_raw = rows.get("私道負担・道路", "")[:200]
    private_road = ""
    if _private_road_raw:
        try:
            private_road = translate(_private_road_raw) or _private_road_raw
        except Exception:
            private_road = _private_road_raw
    private_road = private_road[:200]
    _restrictions_raw = rows.get("その他制限事項", "")[:200]
    other_restrictions = ""
    if _restrictions_raw:
        try:
            other_restrictions = translate(_restrictions_raw) or _restrictions_raw
        except Exception:
            other_restrictions = _restrictions_raw
    other_restrictions = other_restrictions[:400]
    handover_date = _translate_handover(
        (rows.get("引渡可能時期") or rows.get("引渡時期") or rows.get("引き渡し時期") or "")[:50]
    )
    transaction_area = rows.get("売買対象面積", "")[:50]
    current_status = _lookup(
        rows.get("現況") or rows.get("現状") or "", _STATUS_MAP
    )[:50]
    land_rights   = _lookup(
        rows.get("土地権利") or rows.get("権利") or "", _RIGHTS_MAP
    )[:80]
    land_category = _lookup(rows.get("地目", ""), _LAND_CAT_MAP)[:50]

    # ---- Equipment / amenities (all categories SUUMO provides) ----
    # "その他"/"備考" are too generic — they capture SUUMO UI tooltip text
    # ("この情報を他の問い合わせにも自動で反映…") rather than actual property data.
    _SUUMO_NOISE = ("この情報を他の問い合わせにも自動で反映", "30分で破棄", "一部物件でのみ利用可能")
    features_dict = {}
    for _k in [
        "間取り詳細", "キッチン", "バス・トイレ", "バス", "トイレ", "床・収納",
        "設備・サービス", "部屋の向き", "冷暖房", "駐車場",
        "設備その他", "その他設備", "セキュリティ", "テレビ・通信",
        "室内設備", "その他の設備", "水道・下水", "水道", "下水", "ガス", "電気",
        "バルコニー",
    ]:
        _v = rows.get(_k, "")
        if _v and not any(_n in _v for _n in _SUUMO_NOISE):
            features_dict[_k] = _v
    features = json.dumps(features_dict, ensure_ascii=False) if features_dict else ""

    # ---- Surroundings / nearby facilities (all categories + parsed distance) ----
    surr_list = []
    for _k in [
        "スーパー", "コンビニ", "小学校", "中学校", "高校・大学", "幼稚園・保育園",
        "大学", "病院", "クリニック", "公園", "銀行・ATM", "図書館", "郵便局",
        "薬局", "ドラッグストア", "ショッピングセンター", "ホームセンター",
        "レストラン", "市役所・区役所", "警察署", "消防署",
    ]:
        _v = rows.get(_k, "")
        if not _v:
            continue
        _entry: dict = {"type": _k, "info": _v}
        # Parse "徒歩N分" and "(Nm)" out of the info string
        _mt = re.search(r"徒歩(\d+)分", _v)
        _md = re.search(r"[（(]([\d,.]+)\s*m[）)]", _v)
        if _mt:
            _entry["time_min"] = int(_mt.group(1))
            _name = _v[:_mt.start()].strip()
            if _name:
                _entry["name"] = _name
        if _md:
            try:
                _entry["distance_m"] = int(float(_md.group(1).replace(",", "")))
            except Exception:
                pass
        surr_list.append(_entry)
    surroundings = json.dumps(surr_list, ensure_ascii=False) if surr_list else ""

    # ---- Agent/realtor (public mandatory disclosure) ----
    agent_company = (rows.get("会社名") or rows.get("不動産会社名") or
                     rows.get("不動産会社") or rows.get("取扱不動産会社") or
                     rows.get("取扱会社") or rows.get("商号") or
                     rows.get("業者名") or rows.get("媒介業者") or "")[:100]
    agent_license = _translate_license(rows.get("免許番号", "")[:60])
    agent_phone = rows.get("電話番号", "")[:30]
    agent_url   = rows.get("ホームページ", "")[:200]
    _tx = rows.get("取引態様", "")
    _TX_MAP = {"売主": "Owner (direct)", "仲介": "Agent", "代理": "Representative",
               "販売代理": "Sales Representative"}
    transaction_type = _lookup(_tx, _TX_MAP)[:50]

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

    # ---- Geocode (prefecture centroid + small scatter) ----
    # ±0.1° ≈ 11 km — large enough to de-duplicate pins, small enough to stay
    # within the prefecture rather than landing in the ocean.
    coords = PREF_COORDS.get(pref_jp)
    lat = coords[0] + random.uniform(-0.1, 0.1) if coords else None
    lng = coords[1] + random.uniform(-0.1, 0.1) if coords else None

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
        current_status=current_status,
        land_rights=land_rights,
        land_category=land_category,
        features=features,
        surroundings=surroundings,
        agent_company=agent_company,
        agent_license=agent_license,
        agent_phone=agent_phone,
        agent_url=agent_url,
        transaction_type=transaction_type,
        next_update=next_update,
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

                # Batch-check which URLs are already fresh (next_update in future)
                existing_updates = _get_existing_next_updates(detail_urls)
                today = datetime.date.today()

                for url in detail_urls:
                    if pref_saved >= args.limit:
                        break
                    if args.max_total and total_saved >= args.max_total:
                        break

                    # Skip if SUUMO's scheduled update date hasn't arrived yet.
                    # Allow a 1-day grace window so day-of and day-after both hit.
                    _nu = existing_updates.get(url)
                    if _nu:
                        try:
                            if today < datetime.date.fromisoformat(_nu) - datetime.timedelta(days=1):
                                print(f"    skip — next update {_nu}", flush=True)
                                continue
                        except Exception:
                            pass  # malformed date → re-scrape

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
