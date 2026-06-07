"""
One-time migration: assign first_seen dates to listings that don't have one.

Distributes them proportionally across the project's lifetime using rowid as
a proxy for insertion order (lower rowid = added earlier). The first listing
gets the project start date; the last gets today; everything in between is
interpolated linearly.

Run once:  python backfill_first_seen.py
"""
import sqlite3
import datetime
from db.database import DB

PROJECT_START = datetime.date(2026, 6, 4)

conn = sqlite3.connect(DB)
c = conn.cursor()

rows = c.execute(
    "SELECT id, rowid FROM listings WHERE first_seen IS NULL OR first_seen = '' ORDER BY rowid ASC"
).fetchall()

if not rows:
    print("Nothing to backfill — all listings already have first_seen.")
    conn.close()
    exit()

today = datetime.date.today()
total_days = (today - PROJECT_START).days
n = len(rows)
print(f"Backfilling {n} listings across {total_days} days ({PROJECT_START} → {today})")

for i, (lid, _rowid) in enumerate(rows):
    frac = i / max(n - 1, 1)
    days_offset = round(frac * total_days)
    first_seen = (PROJECT_START + datetime.timedelta(days=days_offset)).isoformat()
    c.execute("UPDATE listings SET first_seen=? WHERE id=?", (first_seen, lid))

conn.commit()
conn.close()
print(f"Done. Dates range from {PROJECT_START} to {today}.")
