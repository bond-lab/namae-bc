#!/usr/bin/env python3
"""
Extend Baby Calendar (bc) nrank with scraped data for 2023-2025.

The hand-collected Excel covers 2008-2022. This script adds the three new
years from data/raw/baby_calendar_rankings.tsv (which was scraped from
baby-calendar.jp). It does NOT overwrite 2008-2022 hand-collected rows.

Multiple readings (comma/、-separated in pron_raw) are stored as the
first reading only in pron, to match the existing nrank schema.

No namae expansion for new years — we have aggregated counts, not
individual baby tokens. name_year_cache updated from nrank.
"""

import csv
import re
import sqlite3
from pathlib import Path

DB_PATHS = [
    Path(__file__).parent.parent / "web" / "db" / "namae.db",
    Path(__file__).parent / "namae.db",
]
TSV = Path(__file__).parent.parent / "data" / "raw" / "baby_calendar_rankings.tsv"

NEW_YEARS = {2023, 2024, 2025}


def first_reading(pron_raw: str) -> str | None:
    """Return the first reading from a comma/、-separated list."""
    if not pron_raw:
        return None
    return re.split(r"[,、]", pron_raw)[0].strip() or None


def load(db_path: Path, tsv_path: Path) -> None:
    if not db_path.exists():
        print(f"  skip {db_path} (not found)")
        return
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    # Check what bc years already exist
    existing_years = {r[0] for r in c.execute(
        "SELECT DISTINCT year FROM nrank WHERE src='bc'"
    ).fetchall()}
    to_add = NEW_YEARS - existing_years
    if not to_add:
        print(f"  {db_path}: years {sorted(NEW_YEARS)} already present — skipping")
        conn.close()
        return

    rows = []
    with open(tsv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            try:
                year = int(row["year"])
                rank = int(row["rank"])
            except ValueError:
                continue
            if year not in to_add:
                continue

            orth = row["orth"].strip() or None
            pron = first_reading(row.get("pron_raw", ""))
            gender = row["gender"].strip()
            freq_str = row.get("freq", "").strip()
            freq = int(freq_str) if freq_str else None

            rows.append((year, orth, pron, rank, gender, freq, "bc"))

    c.executemany("""
        INSERT INTO nrank (year, orth, pron, rank, gender, freq, src)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, rows)

    # Update cache for added years
    for year in to_add:
        for gender in ("M", "F"):
            n_orth = c.execute("""
                SELECT COUNT(DISTINCT orth) FROM nrank
                WHERE src='bc' AND year=? AND gender=? AND orth IS NOT NULL
            """, (year, gender)).fetchone()[0]
            n_pron = c.execute("""
                SELECT COUNT(DISTINCT pron) FROM nrank
                WHERE src='bc' AND year=? AND gender=? AND pron IS NOT NULL
            """, (year, gender)).fetchone()[0]
            c.execute("""
                INSERT OR REPLACE INTO name_year_cache (src, dtype, year, gender, count)
                VALUES ('bc', 'orth', ?, ?, ?)
            """, (year, gender, n_orth))
            if n_pron:
                c.execute("""
                    INSERT OR REPLACE INTO name_year_cache (src, dtype, year, gender, count)
                    VALUES ('bc', 'pron', ?, ?, ?)
                """, (year, gender, n_pron))

    conn.commit()
    conn.close()
    print(f"  {db_path}: inserted {len(rows)} bc rows for years {sorted(to_add)}")


def main():
    for db_path in DB_PATHS:
        load(db_path, TSV)


if __name__ == "__main__":
    main()
