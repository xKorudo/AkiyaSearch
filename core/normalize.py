def normalize_price(text: str):
    if not text:
        return None
    import re
    try:
        if "万円" in text:
            # grab the number right before 万円
            m = re.search(r"([\d,]+(?:\.\d+)?)\s*万円", text)
            if m:
                val = int(float(m.group(1).replace(",", "")) * 10000)
                # Sanity floor: a sub-¥10,000 sale price is a unit/format artifact
                # (e.g. "0.02万円" → ¥200). Treat as unknown rather than wrong.
                if val == 0 or val >= 10000:
                    return val
                return None
    except:
        pass
    return None


def is_valid_image(url: str) -> bool:
    """Return False for tracking pixels, logos, icons and other non-property images."""
    if not url:
        return False
    bad = [
        "facebook.com/tr", "logo", "icon", "favicon",
        "noscript", "loading", "placeholder", "blank",
        "tracking", "pixel", "spacer", ".svg", "NewAkiya2",
    ]
    url_lower = url.lower()
    return not any(b in url_lower for b in bad)


def clean_text(s):
    return s.strip() if s else ""