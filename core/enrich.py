from deep_translator import GoogleTranslator

# Approximate prefecture centroids
PREF_COORDS = {
    '北海道': (43.06, 141.35), '青森': (40.82, 140.74), '岩手': (39.70, 141.15),
    '宮城': (38.27, 140.87), '秋田': (39.72, 140.10), '山形': (38.24, 140.36),
    '福島': (37.75, 140.47), '茨城': (36.34, 140.45), '栃木': (36.57, 139.88),
    '群馬': (36.39, 139.06), '埼玉': (35.86, 139.65), '千葉': (35.61, 140.12),
    '東京': (35.69, 139.69), '神奈川': (35.45, 139.64), '新潟': (37.90, 139.02),
    '富山': (36.70, 137.21), '石川': (36.59, 136.63), '福井': (36.07, 136.22),
    '山梨': (35.66, 138.57), '長野': (36.65, 138.18), '岐阜': (35.39, 136.72),
    '静岡': (34.98, 138.38), '愛知': (35.18, 136.91), '三重': (34.73, 136.51),
    '滋賀': (35.00, 135.87), '京都': (35.02, 135.76), '大阪': (34.69, 135.50),
    '兵庫': (34.69, 135.18), '奈良': (34.69, 135.83), '和歌山': (34.23, 135.17),
    '鳥取': (35.50, 134.24), '島根': (35.47, 133.05), '岡山': (34.66, 133.93),
    '広島': (34.40, 132.46), '山口': (34.19, 131.47), '徳島': (34.07, 134.56),
    '香川': (34.34, 134.04), '愛媛': (33.84, 132.77), '高知': (33.56, 133.53),
    '福岡': (33.61, 130.42), '佐賀': (33.25, 130.30), '長崎': (32.74, 129.87),
    '熊本': (32.79, 130.74), '大分': (33.24, 131.61), '宮崎': (31.91, 131.42),
    '鹿児島': (31.56, 130.56), '沖縄': (26.21, 127.68),
}

_translator = GoogleTranslator(source='ja', target='en')


def translate(text: str) -> str:
    if not text or not text.strip():
        return ""
    # Skip if already mostly ASCII/English
    non_ascii = sum(1 for c in text if ord(c) > 127)
    if non_ascii < 2:
        return text
    try:
        result = _translator.translate(text[:500])
        return result or ""
    except Exception:
        return ""


def _load_existing_translations():
    """Load id → (title_en, description_en) for already-translated listings."""
    try:
        import sqlite3
        from db.database import DB
        conn = sqlite3.connect(DB)
        rows = conn.execute(
            "SELECT id, title_en, description_en FROM listings "
            "WHERE title_en IS NOT NULL AND title_en != ''"
        ).fetchall()
        conn.close()
        return {r[0]: (r[1] or "", r[2] or "") for r in rows}
    except Exception:
        return {}


def enrich(listings):
    existing = _load_existing_translations()
    skipped = 0

    for l in listings:
        # Coordinates from prefecture centroid (scattered so markers don't stack)
        coords = PREF_COORDS.get(l.prefecture)
        if coords:
            import random
            l.lat = coords[0] + random.uniform(-0.5, 0.5)
            l.lng = coords[1] + random.uniform(-0.5, 0.5)

        # Reuse existing translation — only call the API for truly new listings
        if l.id in existing:
            l.title_en, l.description_en = existing[l.id]
            skipped += 1
        else:
            l.title_en = translate(l.title)
            l.description_en = translate(l.description)

    new_count = len(listings) - skipped
    print(f"  Translated {new_count} new listing(s) ({skipped} reused from DB).")
    return listings
