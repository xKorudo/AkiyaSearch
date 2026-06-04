import requests
from bs4 import BeautifulSoup
import random
import time
import re

from core.models import Listing
from core.normalize import is_valid_image

# Prefecture name patterns to detect from page text
PREF_NAMES = [
    '北海道','青森','岩手','宮城','秋田','山形','福島','茨城','栃木','群馬',
    '埼玉','千葉','東京','神奈川','新潟','富山','石川','福井','山梨','長野',
    '岐阜','静岡','愛知','三重','滋賀','京都','大阪','兵庫','奈良','和歌山',
    '鳥取','島根','岡山','広島','山口','徳島','香川','愛媛','高知','福岡',
    '佐賀','長崎','熊本','大分','宮崎','鹿児島','沖縄',
]
PREF_PATTERN = re.compile('|'.join(PREF_NAMES))

PREF_URLS = [
    ("https://www.akiya-athome.jp/", "不明"),
    ("https://www.akiya-bank.org/", "不明"),
]


def _detect_pref(text: str) -> str:
    m = PREF_PATTERN.search(text)
    return m.group(0) if m else "不明"


def scrape():
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0",
        "Accept-Language": "ja-JP,ja;q=0.9",
    })

    results = []

    for url, default_pref in PREF_URLS:
        try:
            r = session.get(url, timeout=15)
            soup = BeautifulSoup(r.text, "html.parser")

            # Try to find image+link cards
            cards = (
                soup.select("article") or
                soup.select(".property") or
                soup.select(".house") or
                soup.select(".listing") or
                []
            )

            if cards:
                for card in cards:
                    title_el = card.select_one("h2, h3, h4, [class*='title']")
                    title = title_el.get_text(strip=True) if title_el else card.get_text(" ", strip=True)[:80]
                    if len(title) < 6:
                        continue

                    img = ""
                    for img_el in card.select("img"):
                        candidate = img_el.get("src") or img_el.get("data-src") or ""
                        if candidate.startswith("//"):
                            candidate = "https:" + candidate
                        if candidate.startswith("/"):
                            candidate = url.rstrip("/") + candidate
                        if is_valid_image(candidate):
                            img = candidate
                            break

                    link_el = card.select_one("a[href]")
                    href = link_el.get("href", url) if link_el else url
                    if href and not href.startswith("http"):
                        href = url.rstrip("/") + "/" + href.lstrip("/")

                    pref = _detect_pref(card.get_text())

                    results.append(Listing(
                        id="",
                        title=title[:80],
                        prefecture=pref,
                        city="",
                        price_jpy=0,
                        price_label="要確認",
                        size_m2=None,
                        land_m2=None,
                        image_url=img,
                        source_url=href,
                        source="AKIYA BANK",
                        description="Municipal akiya listing",
                    ))
            else:
                # Fallback: all <a> links on the page
                for a in soup.select("a[href]"):
                    title = a.get_text(strip=True)
                    if len(title) < 6:
                        continue

                    href = a.get("href", url)
                    if not href.startswith("http"):
                        href = url.rstrip("/") + "/" + href.lstrip("/")

                    pref = _detect_pref(title + href)

                    results.append(Listing(
                        id="",
                        title=title[:80],
                        prefecture=pref,
                        city="",
                        price_jpy=0,
                        price_label="要確認",
                        size_m2=None,
                        land_m2=None,
                        image_url="",
                        source_url=href,
                        source="AKIYA BANK",
                        description="Municipal akiya listing",
                    ))

            time.sleep(random.uniform(1, 2))

        except Exception as e:
            print("AKIYA BANK error:", e)

    return results
