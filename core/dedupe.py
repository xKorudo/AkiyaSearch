import hashlib

def make_hash(l):
    # Key on source_url only — the title can change (e.g. SUUMO date prefix)
    # but the URL is stable per property.
    raw = l.source_url.encode("utf-8")
    return hashlib.md5(raw).hexdigest()


def dedupe(listings):
    seen = set()
    out = []

    for l in listings:
        h = make_hash(l)
        if h in seen:
            continue
        seen.add(h)
        l.id = h
        out.append(l)

    return out