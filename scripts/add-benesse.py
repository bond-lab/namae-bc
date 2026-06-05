#!/usr/bin/env python3
"""
Load Benesse/Tamahiyo name rankings into nrank.

Source: data/raw/benesse_rankings.tsv
Years:  2018-2025
        2018: has freq (件数) and pct (占有率)
        2019-2025: rank and reading only (methodology changed)

Note: only orth-ranked rows are loaded (all rows in the TSV are orth rankings).
      No namae expansion since we have aggregated data, not individual tokens.
      name_year_cache is updated from nrank distinct counts.
"""

import csv
import sqlite3
import sys
from pathlib import Path

DB_PATHS = [
    Path(__file__).parent.parent / "web" / "db" / "namae.db",
    Path(__file__).parent / "namae.db",
]
TSV = Path(__file__).parent.parent / "data" / "raw" / "benesse_rankings.tsv"


def load(db_path: Path, tsv_path: Path) -> None:
    if not db_path.exists():
        print(f"  skip {db_path} (not found)")
        return
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    # Guard: skip if already loaded
    existing = c.execute(
        "SELECT COUNT(*) FROM nrank WHERE src='benesse'"
    ).fetchone()[0]
    if existing > 0:
        print(f"  {db_path}: already has {existing} benesse rows — skipping")
        conn.close()
        return

    rows = []
    with open(tsv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            year = int(row["year"])
            gender = row["gender"].strip()
            rank_str = row["rank"].strip()
            orth = row["orth"].strip() or None
            pron = row["pron"].strip() or None
            freq_str = row["freq"].strip()

            # Skip rows with non-numeric rank (stray headers)
            try:
                rank = int(rank_str)
            except ValueError:
                continue

            freq = int(freq_str) if freq_str else None
            rows.append((year, orth, pron, rank, gender, freq, "benesse"))

    c.executemany("""
        INSERT INTO nrank (year, orth, pron, rank, gender, freq, src)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, rows)

    # Update name_year_cache from nrank (not namae, since we have no token rows)
    cache_rows = c.execute("""
        SELECT year, gender,
               COUNT(DISTINCT orth) FILTER (WHERE orth IS NOT NULL),
               COUNT(DISTINCT pron) FILTER (WHERE pron IS NOT NULL)
        FROM nrank WHERE src='benesse'
        GROUP BY year, gender
    """).fetchall()
    for year, gender, n_orth, n_pron in cache_rows:
        c.execute("""
            INSERT OR REPLACE INTO name_year_cache (src, dtype, year, gender, count)
            VALUES ('benesse', 'orth', ?, ?, ?)
        """, (year, gender, n_orth))
        if n_pron:
            c.execute("""
                INSERT OR REPLACE INTO name_year_cache (src, dtype, year, gender, count)
                VALUES ('benesse', 'pron', ?, ?, ?)
            """, (year, gender, n_pron))

    conn.commit()
    conn.close()
    print(f"  {db_path}: inserted {len(rows)} benesse nrank rows")


def main():
    for db_path in DB_PATHS:
        load(db_path, TSV)


if __name__ == "__main__":
    main()
