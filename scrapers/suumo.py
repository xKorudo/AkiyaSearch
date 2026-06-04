import requests
from bs4 import BeautifulSoup
import random
import time
import re

from core.models import Listing
from core.normalize import normalize_price, clean_text

# akiya2.com — English-friendly akiya portal with real listings and images
PREF_SLUGS = [
    ("長野", "Nagano"),
    ("北海道", "Hokkaido"),
    ("高知", "Kochi"),
    ("岡山", "Okayama"),
    ("島根", "Shimane"),
    ("広島", "Hiroshima"),
]

BASE = "https://www.akiya2.com/prefecture-listing/{}"


def scrape(max_pages=1):
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    })

    results = []

    for pref_jp, pref_slug in PREF_SLUGS:
        url = BASE.format(pref_slug)
        try:
            r = session.get(url, timeout=15)
            if r.status_code != 200:
                continue

            soup = BeautifulSoup(r.text, "html.parser")

            # akiya2.com listing cards
            cards = (
                soup.select(".listing-card") or
                soup.select("article") or
                soup.select(".property-card") or
                soup.select("[class*='listing']") or
                soup.select("[class*='property']")
            )

            for card in cards:
                title_el = card.select_one("h2, h3, h4, [class*='title'], [class*='name']")
                title = clean_text(title_el.get_text()) if title_el else ""
                if len(title) < 4:
                    continue

                price_el = card.select_one("[class*='price'], [class*='cost']")
                price_text = price_el.get_text(strip=True) if price_el else ""
                price = normalize_price(price_text)

                img_el = card.select_one("img")
                img = ""
                if img_el:
                    img = img_el.get("src") or img_el.get("data-src") or img_el.get("data-lazy-src") or ""
                    if img.startswith("//"):
                        img = "https:" + img
                    if img.startswith("/"):
                        img = "https://www.akiya2.com" + img

                link_el = card.select_one("a[href]")
                href = link_el.get("href", url) if link_el else url
                if href and not href.startswith("http"):
                    href = "https://www.akiya2.com" + href

                # Try to parse size
                size = None
                size_match = re.search(r"(\d+(?:\.\d+)?)\s*m²?", card.get_text())
                if size_match:
                    size = float(size_match.group(1))

                desc_el = card.select_one("p, [class*='desc'], [class*='summary']")
                desc = clean_text(desc_el.get_text()) if desc_el else f"{pref_jp}の空き家物件"

                results.append(Listing(
                    id="",
                    title=title[:80],
                    prefecture=pref_jp,
                    city="",
                    price_jpy=price,
                    price_label=price_text or "要確認",
                    size_m2=size,
                    land_m2=None,
                    image_url=img,
                    source_url=href,
                    source="Akiya2.com",
                    description=desc[:300],
                ))

            time.sleep(random.uniform(1.0, 2.0))

        except Exception as e:
            print(f"akiya2.com error ({pref_slug}):", e)
            continue

    return results
