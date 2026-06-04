import hashlib

def make_hash(l):
    raw = (l.title + l.prefecture + l.source_url).encode("utf-8")
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