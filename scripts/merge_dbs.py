#!/usr/bin/env python3
"""
Merge per-prefecture SQLite databases (from matrix job artifacts) into one
master akiya_v4.db ready for export_static.py.

Usage:
    python scripts/merge_dbs.py <artifacts_dir>

Each subdirectory under <artifacts_dir> must contain an akiya_v4.db file
(the layout produced by actions/download-artifact@v4 with pattern: db-*).
"""
import os
import sys
import glob
import sqlite3

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db.database import DB, init_db


def merge(artifacts_dir: str) -> int:
    db_files = sorted(glob.glob(os.path.join(artifacts_dir, "**", "akiya_v4.db"), recursive=True))
    if not db_files:
        print(f"No akiya_v4.db files found under {artifacts_dir}")
        sys.exit(1)

    print(f"Found {len(db_files)} prefecture DB(s) to merge → {DB}")
    init_db()

    master = sqlite3.connect(DB)

    # Derive column count from the master schema (init_db already ran)
    master_cols = [r[1] for r in master.execute("PRAGMA table_info(listings)").fetchall()]
    n_cols = len(master_cols)
    placeholders = ",".join("?" * n_cols)

    total_listings = 0
    for db_path in db_files:
        label = os.path.basename(os.path.dirname(db_path))
        try:
            src = sqlite3.connect(db_path)
            src_cols = [r[1] for r in src.execute("PRAGMA table_info(listings)").fetchall()]

            rows = src.execute("SELECT * FROM listings").fetchall()
            if not rows:
                print(f"  {label}: empty — skipped")
                src.close()
                continue

            # Pad or trim rows to match master column count
            if len(src_cols) != n_cols:
                padded = []
                for row in rows:
                    r = list(row)
                    while len(r) < n_cols:
                        r.append("")
                    padded.append(tuple(r[:n_cols]))
                rows = padded

            master.executemany(
                f"INSERT OR REPLACE INTO listings VALUES ({placeholders})", rows
            )

            # Copy scrape_state cursors so next run continues where this one left off
            state_rows = src.execute("SELECT * FROM scrape_state").fetchall()
            if state_rows:
                master.executemany(
                    "INSERT OR REPLACE INTO scrape_state VALUES (?,?)", state_rows
                )

            master.commit()
            src.close()
            total_listings += len(rows)
            print(f"  {label}: merged {len(rows)} listings")
        except Exception as e:
            print(f"  {label}: ERROR — {e}")

    final = master.execute("SELECT COUNT(*) FROM listings").fetchone()[0]
    master.close()
    print(f"\nDone — {total_listings} rows merged, {final} total in master DB")
    return final


if __name__ == "__main__":
    artifacts_dir = sys.argv[1] if len(sys.argv) > 1 else "pref_dbs"
    merge(artifacts_dir)
