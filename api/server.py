from flask import Flask, jsonify, send_from_directory
import sqlite3
import json
import os
import sys

# resolve paths relative to the project root, not the cwd
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(ROOT, "akiya_v4.db")

# make project root importable (needed for run_pipeline)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

app = Flask(__name__)


def fetch():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    rows = c.execute("SELECT * FROM listings ORDER BY price_jpy ASC").fetchall()
    conn.close()

    return rows


@app.route("/")
def index():
    return send_from_directory(ROOT, "index.html")


@app.route("/listing.html")
def listing_page():
    return send_from_directory(ROOT, "listing.html")


@app.route("/api/listings")
def listings():
    rows = fetch()

    data = []
    for r in rows:
        data.append({
            "id": r[0],
            "title": r[1],
            "prefecture": r[2],
            "city": r[3],
            "price_jpy": r[4],
            "price_label": r[5],
            "size_m2": r[6],
            "land_m2": r[7],
            "image_url": r[8],
            "source_url": r[9],
            "source": r[10],
            "description": r[11],
            "title_en": r[12],
            "description_en": r[13],
            "lat": r[14],
            "lng": r[15],
            "rooms": r[16],
            "built_year": r[17],
            "condition": r[18],
            "images": json.loads(r[19]) if r[19] else [],
        })

    return jsonify({"count": len(data), "listings": data})


@app.route("/api/refresh", methods=["POST"])
def refresh():
    import run_pipeline
    run_pipeline.run_pipeline()
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    init = __import__("db.database").database.init_db
    init()
    app.run(port=5000)