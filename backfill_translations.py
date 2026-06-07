"""
Fill in title_en / description_en for any listings that are still missing them.

Runs as a step in the scrape-and-deploy workflow, after run_pipeline.py and
before export_static.py — so every listing has an English translation before
the static snapshot is built and deployed.

Processes up to BATCH_SIZE listings per run to avoid blowing the job time
budget. Subsequent runs pick up where the previous left off.
"""
import sqlite3
from db.database import DB
from core.enrich import translate

BATCH_SIZE = 300   # max listings to translate per run


def main():
    conn = sqlite3.connect(DB)
    rows = conn.execute(
        "SELECT id, title, description FROM listings "
        "WHERE title_en IS NULL OR title_en = '' "
        "ORDER BY rowid DESC "   # newest first — they're most likely to be seen
        f"LIMIT {BATCH_SIZE}"
    ).fetchall()
    conn.close()

    if not rows:
        print("backfill_translations: all listings already have translations.")
        return

    print(f"backfill_translations: filling {len(rows)} missing translation(s)…")
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    done = 0
    for lid, title, desc in rows:
        title_en = translate(title)
        desc_en  = translate(desc)
        if title_en or desc_en:
            c.execute(
                "UPDATE listings SET title_en=?, description_en=? WHERE id=?",
                (title_en, desc_en, lid),
            )
            done += 1

    conn.commit()
    conn.close()
    print(f"backfill_translations: translated {done}/{len(rows)} listing(s).")


if __name__ == "__main__":
    main()
