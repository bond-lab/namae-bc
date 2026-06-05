#!/usr/bin/env python3
"""
Scrape Akachan Honpo name rankings from www.akachan.jp/maternity/ranking/.

HTML pages: 2018-2024 via /maternity/ranking/{YEAR}/boy/ and /girl/
            2025 (current year) via /maternity/ranking/boy and /girl
PDF archives: 2010-2017 (not scraped here)

No freq (count) data on any Akachan page.

Output: data/raw/akachan_rankings.tsv
Columns: year, gender, rank, orth, pron, prev_rank, sample_n, url, src
"""

import csv
import re
import sys
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup

BASE = "https://www.akachan.jp"
HEADERS = {"User-Agent": "Mozilla/5.0 (research scraper; namae-bc project; contact: bond@ieee.org)"}
DELAY = 1.5

OUT = Path(__file__).parent.parent / "data" / "raw" / "akachan_rankings.tsv"
FIELDNAMES = ["year", "gender", "rank", "orth", "pron", "prev_rank", "sample_n", "url", "src"]

CURRENT_YEAR = 2025
# 2018-2020: full top-100 at /boy/ and /girl/ subpages
# 2021: /boy/ /girl/ return 404; use main year page (top-10 both genders)
# 2022-2024: /boy/ /girl/ exist but only show top-10
# 2025: current year at /maternity/ranking/boy and /girl (top-10)
HTML_YEARS = list(range(2018, CURRENT_YEAR))


def get_soup(url: str) -> BeautifulSoup | None:
    resp = requests.get(url, headers=HEADERS, timeout=20)
    if resp.status_code == 404:
        return None
    resp.raise_for_status()
    resp.encoding = "utf-8"
    time.sleep(DELAY)
    return BeautifulSoup(resp.text, "html.parser")


def extract_sample_n(soup: BeautifulSoup) -> str:
    text = soup.get_text()
    # Look for "N,NNN人" or "NN,NNNサンプル" patterns
    m = re.search(r"([\d,]{4,})\s*(?:人|サンプル|名)", text)
    return m.group(1).replace(",", "") if m else ""


def is_name_ranking_table(table) -> bool:
    """Check if this table is a name ranking (not a reading or kanji ranking)."""
    headers = [th.get_text(strip=True) for th in table.find_all("th")]
    # Name ranking table has columns like "お名前" or "名前"
    return any(h in ("お名前", "名前") for h in headers)


def parse_table(table, gender: str, year: int, url: str, sample_n: str) -> list[dict]:
    rows = []
    for tr in table.find_all("tr"):
        # Rank cell is <th>; name/reading cells are <td> — collect all
        cells = tr.find_all(["th", "td"])
        if len(cells) < 2:
            continue
        rank_text = cells[0].get_text(strip=True)
        rank_m = re.search(r"^(\d+)", rank_text)  # must start with digit
        if not rank_m:
            continue  # skip header rows like "2023年順位"
        rank = int(rank_m.group(1))
        orth = cells[1].get_text(strip=True)
        pron = cells[2].get_text(strip=True) if len(cells) > 2 else ""
        prev_rank = cells[3].get_text(strip=True) if len(cells) > 3 else ""
        rows.append({
            "year": year,
            "gender": gender,
            "rank": rank,
            "orth": orth,
            "pron": pron,
            "prev_rank": prev_rank,
            "sample_n": sample_n,
            "url": url,
            "src": "akachan",
        })
    return rows


def scrape_gender_page(url: str, gender: str, year: int) -> list[dict]:
    soup = get_soup(url)
    if soup is None:
        print(f"    404: {url}", file=sys.stderr)
        return []
    sample_n = extract_sample_n(soup)
    records = []
    tables = soup.find_all("table")
    # Take only name-ranking tables (skip reading/kanji sub-tables if present)
    name_tables = [t for t in tables if is_name_ranking_table(t)]
    # Fallback: just take first table if filter finds nothing
    target_tables = name_tables if name_tables else tables[:1]
    for tbl in target_tables:
        records.extend(parse_table(tbl, gender, year, url, sample_n))
    # Deduplicate on (rank, orth, pron)
    seen = set()
    deduped = []
    for r in records:
        key = (r["rank"], r["orth"], r["pron"])
        if key not in seen:
            seen.add(key)
            deduped.append(r)
    return deduped


def scrape_main_year_page(year: int) -> list[dict]:
    """Scrape main year page when gender subpages are unavailable (2021)."""
    url = f"{BASE}/maternity/ranking/{year}/"
    soup = get_soup(url)
    if soup is None:
        return []
    sample_n = extract_sample_n(soup)
    records = []
    tables = soup.find_all("table")
    name_tables = [t for t in tables if is_name_ranking_table(t)]
    target = name_tables if name_tables else tables[:2]
    # Main page has boys table first, girls table second
    for i, tbl in enumerate(target[:2]):
        gender = "M" if i == 0 else "F"
        records.extend(parse_table(tbl, gender, year, url, sample_n))
    seen = set()
    deduped = []
    for r in records:
        key = (r["rank"], r["orth"], r["pron"], r["gender"])
        if key not in seen:
            seen.add(key)
            deduped.append(r)
    return deduped


def scrape_year(year: int) -> list[dict]:
    records = []
    if year == CURRENT_YEAR:
        for gender_path, gender in [("boy", "M"), ("girl", "F")]:
            url = f"{BASE}/maternity/ranking/{gender_path}"
            records.extend(scrape_gender_page(url, gender, year))
    elif year == 2021:
        # /boy/ and /girl/ return 404 for 2021; fall back to main page
        records.extend(scrape_main_year_page(year))
    else:
        for gender_path, gender in [("boy", "M"), ("girl", "F")]:
            url = f"{BASE}/maternity/ranking/{year}/{gender_path}/"
            rows = scrape_gender_page(url, gender, year)
            if not rows:
                # Fallback to main page if subpage unavailable
                return scrape_main_year_page(year)
            records.extend(rows)
    return records


def main():
    all_rows = []
    for year in HTML_YEARS + [CURRENT_YEAR]:
        print(f"  Akachan Honpo {year}...")
        rows = scrape_year(year)
        has_pron = sum(1 for r in rows if r["pron"])
        sample = rows[0]["sample_n"] if rows else "?"
        print(f"    {len(rows)} rows, {has_pron} with reading, N={sample}")
        all_rows.extend(rows)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES, delimiter="\t",
                                extrasaction="ignore")
        writer.writeheader()
        writer.writerows(all_rows)
    print(f"\nWritten {len(all_rows)} rows to {OUT}")


if __name__ == "__main__":
    main()
