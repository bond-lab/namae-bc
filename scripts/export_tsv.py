"""Export cleaned ranked name data from the database as TSV files.

Produces one TSV per data source in data/download/:
  - baby_calendar_names.tsv        (Baby Calendar, orth-only & pron-only, 2008-2022)
  - baby_calendar_names_both.tsv   (Baby Calendar, orth+pron pairs, 2008-2022)
  - heisei_names.tsv               (Heisei Namae Jiten, 1989-2009)
  - meiji_yasuda_names.tsv         (Meiji Yasuda, 1912-2024)
  - meiji_yasuda_totals.tsv        (Meiji Yasuda survey totals, 2004-2024)
  - live_births.tsv                (Annual live births, 1873-2023)

Usage:
    python export_tsv.py [DB_PATH] [OUTPUT_DIR]

Defaults:
    DB_PATH    = ../web/db/namae.db
    OUTPUT_DIR = ../data/download
"""

import csv
import os
import sqlite3
import sys


def export(db_path, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    conn = sqlite3.connect(db_path)

    exports = [
        (
            "baby_calendar_names.tsv",
            "SELECT year, orth, pron, rank, gender, freq "
            "FROM nrank WHERE src='bc' ORDER BY year, gender, rank",
            ["year", "orth", "pron", "rank", "gender", "freq"],
        ),
        (
            "baby_calendar_names_both.tsv",
            "SELECT year, orth, pron, "
            "ROW_NUMBER() OVER (PARTITION BY year, gender "
            "  ORDER BY COUNT(*) DESC) AS rank, "
            "gender, COUNT(*) AS freq "
            "FROM namae WHERE src='bc' "
            "GROUP BY year, orth, pron, gender "
            "ORDER BY year, gender, rank",
            ["year", "orth", "pron", "rank", "gender", "freq"],
        ),
        (
            "heisei_names.tsv",
            "SELECT year, orth, rank, gender, freq "
            "FROM nrank WHERE src='hs' ORDER BY year, gender, rank",
            ["year", "orth", "rank", "gender", "freq"],
        ),
        (
            "meiji_yasuda_names.tsv",
            "SELECT year, orth, pron, rank, gender, freq "
            "FROM nrank WHERE src='meiji' ORDER BY year, gender, rank",
            ["year", "orth", "pron", "rank", "gender", "freq"],
        ),
        (
            "meiji_yasuda_totals.tsv",
            "SELECT year, gender, count "
            "FROM name_year_cache WHERE src='totals' ORDER BY year, gender",
            ["year", "gender", "count"],
        ),
        (
            "live_births.tsv",
            "SELECT year, gender, count "
            "FROM name_year_cache WHERE src='births' ORDER BY year, gender",
            ["year", "gender", "count"],
        ),
    ]

    for filename, query, columns in exports:
        out_path = os.path.join(output_dir, filename)
        cur = conn.execute(query)
        rows = cur.fetchall()
        with open(out_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f, delimiter="\t")
            writer.writerow(columns)
            for row in rows:
                writer.writerow("" if v is None else v for v in row)
        print(f"{filename}: {len(rows):,} rows written to {out_path}")

    conn.close()


if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(script_dir, "..", "web", "db", "namae.db")
    output_dir = sys.argv[2] if len(sys.argv) > 2 else os.path.join(script_dir, "..", "data", "download")
    export(db_path, output_dir)
