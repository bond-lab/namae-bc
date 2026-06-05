#!/usr/bin/env python3
"""
Scrape Baby Calendar rankings for 2010-2019 from the Wayback Machine.

The live /nazuke/nameranking{YEAR} pages for 2010-2019 return 404.
This script queries the Wayback Machine CDX API for available snapshots
and fetches the best one per year.

Output: data/raw/baby_calendar_rankings_archive.tsv
        (same columns as baby_calendar_rankings.tsv)
"""

import csv
import re
import sys
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup

BASE = "https://baby-calendar.jp"
WBM = "https://web.archive.org"
CDX = "https://web.archive.org/cdx/search/cdx"
HEADERS = {"User-Agent": "Mozilla/5.0 (research scraper; namae-bc project; contact: bond@ieee.org)"}
DELAY = 2.0

OUT = Path(__file__).parent.parent / "data" / "raw" / "baby_calendar_rankings_archive.tsv"
FIELDNAMES = ["year", "gender", "rank", "orth", "pron_raw", "freq", "prev_rank", "archive_url", "src"]

TARGET_YEARS = list(range(2010, 2020))


def get_best_snapshot(year: int, url_path: str) -> str | None:
    """Query CDX API for the best snapshot of a URL near the end of a given year."""
    target_url = f"{BASE}{url_path}"
    # Prefer snapshots from Jan-Mar of the *next* year (when rankings are freshest)
    from_ts = f"{year+1}0101"
    to_ts = f"{year+1}0630"
    params = {
        "url": target_url,
        "output": "json",
        "fl": "timestamp,statuscode",
        "filter": "statuscode:200",
        "from": from_ts,
        "to": to_ts,
        "limit": 5,
        "collapse": "timestamp:8",  # one per day
    }
    r = requests.get(CDX, params=params, headers=HEADERS, timeout=20)
    time.sleep(0.5)
    data = r.json()
    if len(data) <= 1:  # just header or empty
        # Widen search to full year
        params["from"] = f"{year}0101"
        params["to"] = f"{year}1231"
        r = requests.get(CDX, params=params, headers=HEADERS, timeout=20)
        time.sleep(0.5)
        data = r.json()
    if len(data) <= 1:
        return None
    # Pick last available snapshot (most complete)
    ts = data[-1][0]
    return f"{WBM}/web/{ts}/{target_url}"


def get_soup(url: str) -> BeautifulSoup:
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    resp.encoding = "utf-8"
    time.sleep(DELAY)
    return BeautifulSoup(resp.text, "html.parser")


def parse_rank_int(text: str) -> int | None:
    m = re.search(r"(\d+)", text)
    return int(m.group(1)) if m else None


def parse_table_rows(table, gender: str, year: int, url: str) -> list[dict]:
    rows = []
    tbody = table.find("tbody") or table
    for tr in tbody.find_all("tr"):
        cells = [td.get_text(" ", strip=True) for td in tr.find_all("td")]
        if len(cells) < 3:
            continue
        rank = parse_rank_int(cells[0])
        if rank is None:
            continue
        orth = cells[1].strip()
        pron_raw = cells[2].strip() if len(cells) > 2 else ""
        freq_str = cells[3].strip() if len(cells) > 3 else ""
        prev_rank = cells[4].strip() if len(cells) > 4 else ""
        freq = None
        if freq_str:
            m2 = re.search(r"(\d[\d,]*)", freq_str)
            if m2:
                freq = int(m2.group(1).replace(",", ""))
        rows.append({
            "year": year,
            "gender": gender,
            "rank": rank,
            "orth": orth,
            "pron_raw": pron_raw,
            "freq": freq if freq is not None else "",
            "prev_rank": prev_rank,
            "archive_url": url,
            "src": "bc",
        })
    return rows


def scrape_year_from_archive(year: int) -> list[dict]:
    records = []

    # Try the main nameranking page first
    main_path = f"/nazuke/nameranking{year}"
    snap = get_best_snapshot(year, main_path)
    if snap:
        print(f"    Main snapshot: {snap}", file=sys.stderr)
        try:
            soup = get_soup(snap)
            tables = soup.find_all("table")
            for i, tbl in enumerate(tables[:2]):
                gender = "M" if i == 0 else "F"
                records.extend(parse_table_rows(tbl, gender, year, snap))
        except Exception as e:
            print(f"    Error fetching main: {e}", file=sys.stderr)
    else:
        print(f"    No main snapshot found", file=sys.stderr)

    # Try extended pages
    for suffix, gender in [("name_boys_under10", "M"), ("name_girls_under10", "F")]:
        ext_path = f"{main_path}/{suffix}"
        snap2 = get_best_snapshot(year, ext_path)
        if snap2:
            print(f"    Extended {suffix}: {snap2}", file=sys.stderr)
            try:
                soup2 = get_soup(snap2)
                for tbl in soup2.find_all("table"):
                    records.extend(parse_table_rows(tbl, gender, year, snap2))
            except Exception as e:
                print(f"    Error fetching extended: {e}", file=sys.stderr)

    return records


def main():
    all_rows = []
    for year in TARGET_YEARS:
        print(f"  Baby Calendar {year} (Wayback Machine)...")
        rows = scrape_year_from_archive(year)
        print(f"    {len(rows)} rows recovered")
        all_rows.extend(rows)

    # Summary
    by_year = {}
    for r in all_rows:
        by_year.setdefault(r["year"], 0)
        by_year[r["year"]] += 1
    print("\nRows recovered by year:")
    for y in sorted(by_year):
        print(f"  {y}: {by_year[y]}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES, delimiter="\t",
                                extrasaction="ignore")
        writer.writeheader()
        writer.writerows(all_rows)
    print(f"\nWritten {len(all_rows)} rows to {OUT}")


if __name__ == "__main__":
    main()
