#!/usr/bin/env python3
"""
Load Akachan Honpo name rankings into nrank.

Source: data/raw/akachan_rankings.tsv
Years:  2018-2025
        2018-2020: full top-100 per gender with readings
        2021+: top-10 to top-30 only (site no longer publishes full list)
        freq always NULL (no count data from this source)

No namae expansion; name_year_cache updated from nrank distinct counts.
"""

import csv
import sqlite3
from pathlib import Path

DB_PATHS = [
    Path(__file__).parent.parent / "web" / "db" / "namae.db",
    Path(__file__).parent / "namae.db",
]
TSV = Path(__file__).parent.parent / "data" / "raw" / "akachan_rankings.tsv"


def load(db_path: Path, tsv_path: Path) -> None:
    if not db_path.exists():
        print(f"  skip {db_path} (not found)")
        return
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    existing = c.execute(
        "SELECT COUNT(*) FROM nrank WHERE src='akachan'"
    ).fetchone()[0]
    if existing > 0:
        print(f"  {db_path}: already has {existing} akachan rows — skipping")
        conn.close()
        return

    rows = []
    with open(tsv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            year_str = row["year"].strip()
            rank_str = row["rank"].strip()
            orth = row["orth"].strip() or None
            pron = row["pron"].strip() or None

            # Skip stray header rows (rank looks like a year, or orth is a column name)
            try:
                year = int(year_str)
                rank = int(rank_str)
            except ValueError:
                continue
            if orth in ("名前", "お名前", None) and pron in ("主な読み", None):
                continue
            # Skip if rank looks implausible (e.g., stray header stored as rank=2018)
            if rank > 500:
                continue

            gender = row["gender"].strip()
            rows.append((year, orth, pron, rank, gender, None, "akachan"))

    c.executemany("""
        INSERT INTO nrank (year, orth, pron, rank, gender, freq, src)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, rows)

    cache_rows = c.execute("""
        SELECT year, gender,
               COUNT(DISTINCT orth) FILTER (WHERE orth IS NOT NULL),
               COUNT(DISTINCT pron) FILTER (WHERE pron IS NOT NULL)
        FROM nrank WHERE src='akachan'
        GROUP BY year, gender
    """).fetchall()
    for year, gender, n_orth, n_pron in cache_rows:
        c.execute("""
            INSERT OR REPLACE INTO name_year_cache (src, dtype, year, gender, count)
            VALUES ('akachan', 'orth', ?, ?, ?)
        """, (year, gender, n_orth))
        if n_pron:
            c.execute("""
                INSERT OR REPLACE INTO name_year_cache (src, dtype, year, gender, count)
                VALUES ('akachan', 'pron', ?, ?, ?)
            """, (year, gender, n_pron))

    conn.commit()
    conn.close()
    print(f"  {db_path}: inserted {len(rows)} akachan nrank rows")


def main():
    for db_path in DB_PATHS:
        load(db_path, TSV)


if __name__ == "__main__":
    main()
