#!/usr/bin/env python3
"""
Scrape Tamahiyo/Benesse name rankings from st.benesse.ne.jp/ninshin/name/.

Available as consistent 100-rank pages: 2018-2025
  2018:      rank, orth, pron, freq (件数), pct (占有率), prev_rank
  2019-2025: rank, orth, pron, prev_rank  (counts removed after methodology change)

Pre-2018 pages exist but are fragmentary (5-10 rows, inconsistent columns,
no full top-100) and are not scraped here.

Output: data/raw/benesse_rankings.tsv
Columns: year, gender, rank, orth, pron, freq, pct, prev_rank, url, src
"""

import csv
import re
import sys
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup

BASE = "https://st.benesse.ne.jp"
HEADERS = {"User-Agent": "Mozilla/5.0 (research scraper; namae-bc project; contact: bond@ieee.org)"}
DELAY = 1.5

OUT = Path(__file__).parent.parent / "data" / "raw" / "benesse_rankings.tsv"
FIELDNAMES = ["year", "gender", "rank", "orth", "pron", "freq", "pct", "prev_rank", "url", "src"]

# 2018-2025: consistent /boy/name-ranking/ and /girl/name-ranking/ subpages
YEARS = list(range(2018, 2026))


def get_soup(url: str) -> BeautifulSoup:
    resp = requests.get(url, headers=HEADERS, timeout=20)
    resp.raise_for_status()
    resp.encoding = "utf-8"
    time.sleep(DELAY)
    return BeautifulSoup(resp.text, "html.parser")


def parse_name_cell(td) -> tuple[str, str]:
    """
    Extract (orth, pron) from name cell.
    HTML: <td>蓮 <span class="yomi">れん</span></td>
       or <td>蓮<br/>れん</td>
       or plain text "蓮 れん"
    """
    # Try span.yomi first
    yomi_span = td.find("span", class_=re.compile("yomi|read|ruby", re.I))
    if yomi_span:
        pron = yomi_span.get_text(strip=True)
        yomi_span.decompose()
        orth = td.get_text(strip=True)
        return orth, pron

    # Try split on <br>
    strings = [s.strip() for s in td.strings if s.strip()]
    if len(strings) >= 2:
        # First string = kanji, second = reading
        return strings[0], strings[1]

    # Fallback: space-separated "蓮 れん"
    full = td.get_text(strip=True)
    # Split at first hiragana run
    m = re.search(r"^(.+?)\s+([ぁ-ゟ].*)$", full)
    if m:
        return m.group(1).strip(), m.group(2).strip()
    return full, ""


def parse_third_cell(text: str) -> tuple[str, str, str]:
    """
    Parse combined third column: "件数：29 占有率：0.59% 前年度：2位"
    or just "前年度：1位"
    Returns (freq, pct, prev_rank).
    """
    freq = ""
    pct = ""
    prev_rank = ""

    m_freq = re.search(r"件数[：:]\s*(\d[\d,]*)", text)
    if m_freq:
        freq = int(m_freq.group(1).replace(",", ""))

    m_pct = re.search(r"占有率[：:]\s*([\d.]+%?)", text)
    if m_pct:
        pct = m_pct.group(1).rstrip("%")

    m_prev = re.search(r"前年度[：:]\s*(.+)", text)
    if m_prev:
        prev_rank = m_prev.group(1).strip()

    return freq, pct, prev_rank


def scrape_year_gender(year: int, gender: str) -> list[dict]:
    gender_path = "boy" if gender == "M" else "girl"
    url = f"{BASE}/ninshin/name/{year}/{gender_path}/name-ranking/"
    try:
        soup = get_soup(url)
    except requests.HTTPError as e:
        print(f"    {year} {gender} HTTP {e.response.status_code}", file=sys.stderr)
        return []

    rows = []
    # The page has 3 tables: (1) name ranking, (2) reading ranking, (3) kanji ranking.
    # We want only the first (name ranking) table.
    tables = soup.find_all("table")
    for tbl in tables[:1]:
        for tr in tbl.find_all("tr"):
            cells = tr.find_all("td")
            if len(cells) < 2:
                continue
            rank_m = re.search(r"(\d+)", cells[0].get_text(strip=True))
            if not rank_m:
                continue
            rank = int(rank_m.group(1))

            orth, pron = parse_name_cell(cells[1])

            freq, pct, prev_rank = "", "", ""
            if len(cells) >= 3:
                freq, pct, prev_rank = parse_third_cell(cells[2].get_text(" ", strip=True))

            rows.append({
                "year": year,
                "gender": gender,
                "rank": rank,
                "orth": orth,
                "pron": pron,
                "freq": freq,
                "pct": pct,
                "prev_rank": prev_rank,
                "url": url,
                "src": "benesse",
            })

    # Deduplicate by name+rank (page may repeat tables; ties share the same rank)
    seen = set()
    deduped = []
    for r in rows:
        key = (r["rank"], r["orth"], r["pron"], r["gender"])
        if key not in seen:
            seen.add(key)
            deduped.append(r)
    return deduped


def main():
    all_rows = []
    for year in YEARS:
        print(f"  Benesse {year}...")
        year_rows = []
        for gender in ["M", "F"]:
            rows = scrape_year_gender(year, gender)
            year_rows.extend(rows)
        has_freq = sum(1 for r in year_rows if r["freq"] != "")
        has_pron = sum(1 for r in year_rows if r["pron"])
        print(f"    {len(year_rows)} rows, {has_pron} with reading, {has_freq} with freq")
        all_rows.extend(year_rows)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES, delimiter="\t",
                                extrasaction="ignore")
        writer.writeheader()
        writer.writerows(all_rows)
    print(f"\nWritten {len(all_rows)} rows to {OUT}")


if __name__ == "__main__":
    main()
