"""Pre-compute reduplication data from the Baby Calendar DB and save as JSON.

Run during makedb.sh analysis phase.  The redup route loads this file
instead of running the expensive DB queries on every page view.
"""

import json
import os
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(__file__))
from db import get_redup

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "web", "db", "namae.db")
OUT_PATH = os.path.join(os.path.dirname(__file__), "..", "web", "static", "data", "redup_data.json")


def serialise(data: dict) -> dict:
    """Convert tuple-keyed redup dict to a JSON-serialisable structure."""
    out = {}
    for section, entries in data.items():
        out[section] = [
            {"pron": pron, "gender": gender,
             "freq": info["freq"], "orths": info["orths"]}
            for (pron, gender), info in entries.items()
        ]
    return out


def main() -> None:
    conn = sqlite3.connect(DB_PATH)
    data = get_redup(conn)
    conn.close()
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(serialise(data), f, ensure_ascii=False)
    print(f"Saved redup data → {OUT_PATH}")


if __name__ == "__main__":
    main()
