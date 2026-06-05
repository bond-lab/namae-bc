#!/usr/bin/env python3
"""
Scrape Baby Calendar name rankings from baby-calendar.jp.

Covers:
  2020-2023 via /nazuke/nameranking{YEAR} structured pages (sitemap-listed)
  2024-2025 via /smilenews/detail/{ID} article pages

Output: data/raw/baby_calendar_rankings.tsv
        data/raw/baby_calendar_episodes.tsv  (name stories, see --episodes flag)

Columns (rankings TSV, raw as possible):
  year, gender, rank, orth, pron_raw, freq, prev_rank, url, src
"""

import argparse
import csv
import re
import sys
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup

BASE = "https://baby-calendar.jp"
HEADERS = {"User-Agent": "Mozilla/5.0 (research scraper; namae-bc project; contact: bond@ieee.org)"}
DELAY = 1.2  # seconds between requests

OUT_DIR = Path(__file__).parent.parent / "data" / "raw"

# Years with structured /nazuke/nameranking{YEAR} pages (confirmed in sitemap)
NAZUKE_YEARS = [2020, 2021, 2022, 2023]

# Smilenews article IDs per year — must be verified/updated when new years are released
# Each year: main article (has top-10 for both genders), then gender-specific extended articles
SMILENEWS_IDS = {
    2024: {
        "main":        71825,   # top-10 boys + girls in one article
        "boys_11plus": 71967,
        "girls_11plus":71969,
        "boys_yomi":   72287,   # reading rankings top-10+
        "girls_yomi":  72288,
    },
    2025: {
        "main":        100184,
        "boys_11plus": 101245,
        "girls_11plus":101365,
        "boys_yomi":   101366,
        "girls_yomi":  101367,
    },
}


def get_soup(url: str) -> BeautifulSoup:
    resp = requests.get(url, headers=HEADERS, timeout=20)
    resp.raise_for_status()
    resp.encoding = "utf-8"
    time.sleep(DELAY)
    return BeautifulSoup(resp.text, "html.parser")


def parse_rank_int(text: str) -> int | None:
    # Normalize fullwidth digits to ASCII before parsing
    text = text.translate(str.maketrans("０１２３４５６７８９", "0123456789"))
    m = re.search(r"(\d+)", text)
    return int(m.group(1)) if m else None


def parse_table_rows(table, gender: str, year: int, url: str) -> list[dict]:
    """Parse one <table> with columns: 順位, 名前, 主なよみ, 件数, 昨年度."""
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
            m = re.search(r"(\d[\d,]*)", freq_str)
            if m:
                freq = int(m.group(1).replace(",", ""))
        rows.append({
            "year": year,
            "gender": gender,
            "rank": rank,
            "orth": orth,
            "pron_raw": pron_raw,
            "freq": freq if freq is not None else "",
            "prev_rank": prev_rank,
            "url": url,
            "src": "bc",
        })
    return rows


def scrape_nazuke_year(year: int) -> list[dict]:
    """Scrape /nazuke/nameranking{YEAR} — top 10 + extended pages."""
    records = []
    base_url = f"{BASE}/nazuke/nameranking{year}"

    # Top-10 page: two tables (boys first, girls second)
    try:
        soup = get_soup(base_url)
    except requests.HTTPError as e:
        print(f"  {year} main page error: {e}", file=sys.stderr)
        return records

    tables = soup.find_all("table")
    for i, tbl in enumerate(tables[:2]):
        gender = "M" if i == 0 else "F"
        records.extend(parse_table_rows(tbl, gender, year, base_url))

    # Extended rankings (ranks 11-100)
    for suffix, gender in [("name_boys_under10", "M"), ("name_girls_under10", "F")]:
        url = f"{base_url}/{suffix}"
        try:
            soup2 = get_soup(url)
            for tbl in soup2.find_all("table"):
                records.extend(parse_table_rows(tbl, gender, year, url))
        except requests.HTTPError as e:
            print(f"  {year} {suffix}: {e}", file=sys.stderr)

    return records


def scrape_smilenews_year(year: int) -> list[dict]:
    """Scrape smilenews article pages for years not on /nazuke/."""
    ids = SMILENEWS_IDS[year]
    records = []

    # Main article: top-10 for both genders in two tables
    url = f"{BASE}/smilenews/detail/{ids['main']}"
    try:
        soup = get_soup(url)
        tables = soup.find_all("table")
        for i, tbl in enumerate(tables[:2]):
            gender = "M" if i == 0 else "F"
            records.extend(parse_table_rows(tbl, gender, year, url))
    except requests.HTTPError as e:
        print(f"  {year} main article {ids['main']}: {e}", file=sys.stderr)

    # Extended boys (ranks 11-100)
    for art_key, gender in [("boys_11plus", "M"), ("girls_11plus", "F")]:
        url = f"{BASE}/smilenews/detail/{ids[art_key]}"
        try:
            soup = get_soup(url)
            for tbl in soup.find_all("table"):
                records.extend(parse_table_rows(tbl, gender, year, url))
        except requests.HTTPError as e:
            print(f"  {year} {art_key}: {e}", file=sys.stderr)

    return records


# ── Historical pages ────────────────────────────────────────────────────────

# 2015-2019: /special/name/{YEAR} (top-10, with counts and readings)
# 2019 uses /special/name/ (no year in path)
SPECIAL_YEARS = {
    2015: "https://baby-calendar.jp/special/name/2015",
    2016: "https://baby-calendar.jp/special/name/2016",
    2017: "https://baby-calendar.jp/special/name/2017",
    2018: "https://baby-calendar.jp/special/name/2018",
    2019: "https://baby-calendar.jp/special/name/",
}

# 2010-2014: /knowledge/pregnancy/{ID}
KNOWLEDGE_PAGES = {
    2014: "https://baby-calendar.jp/knowledge/pregnancy/550",
    2013: "https://baby-calendar.jp/knowledge/pregnancy/656",
    2012: "https://baby-calendar.jp/knowledge/pregnancy/657",
    2011: "https://baby-calendar.jp/knowledge/pregnancy/658",
    2010: "https://baby-calendar.jp/knowledge/pregnancy/659",
}


def scrape_special_year(year: int, url: str) -> list[dict]:
    """
    Scrape /special/name/{YEAR} pages (2015-2019).
    Table structure varies by year:
      2015: col0=name, col1=readings, col2=count, col3=prev (no explicit rank)
      2016-2019: col0=rank, col1=name, col2=readings, col3=count, col4=prev
    """
    try:
        soup = get_soup(url)
    except requests.HTTPError as e:
        print(f"    {year} special page error: {e}", file=sys.stderr)
        return []

    rows = []
    tables = soup.find_all("table")
    # Tables alternate: boys name, girls name, boys reading, girls reading, ...
    # We only want the name ranking tables (first two with readings column)
    gender_map = ["M", "F"]
    name_tables_found = 0
    for tbl in tables:
        if name_tables_found >= 2:
            break
        trs = tbl.find_all("tr")
        if len(trs) < 3:
            continue
        # Only keep name ranking tables (have a reading/yomi column)
        header_texts = []
        for row in trs[:3]:
            header_texts.extend(c.get_text(strip=True) for c in row.find_all(["th","td"]))
        has_reading_col = any("よみ" in h or "読み" in h for h in header_texts)
        if not has_reading_col:
            continue

        gender = gender_map[name_tables_found]
        name_tables_found += 1

        for rank_idx, tr in enumerate(trs):
            cells = [c.get_text(" ", strip=True) for c in tr.find_all(["th","td"])]
            if not cells or len(cells) < 2:
                continue
            # Skip header rows
            c0 = cells[0].strip()
            if not c0 or c0 in ("男の子", "女の子", "順位", "名前"):
                continue
            if len(cells) > 1 and cells[1].strip() in ("主なよみ", "読み方", "件数", "名前"):
                continue

            # Detect format: does first cell look like a rank or a name?
            rank_m = re.search(r"^[１-９\d]", cells[0])
            if rank_m and ("位" in cells[0] or cells[0].isdigit() or re.match(r"[０-９]", cells[0])):
                # 2016-2019: rank | name | readings | count | prev
                rank_text = cells[0]
                rank = parse_rank_int(rank_text)
                orth = cells[1].strip() if len(cells) > 1 else ""
                pron_raw = cells[2].strip() if len(cells) > 2 else ""
                freq_str = cells[3].strip() if len(cells) > 3 else ""
                prev_rank = cells[4].strip() if len(cells) > 4 else ""
            else:
                # 2015: name | readings | count | prev (rank is implicit row order)
                rank = rank_idx  # approximate; actual rank from prev_rank or position
                orth = cells[0].strip()
                pron_raw = cells[1].strip() if len(cells) > 1 else ""
                freq_str = cells[2].strip() if len(cells) > 2 else ""
                prev_rank = cells[3].strip() if len(cells) > 3 else ""

            if not orth or not re.search(r"[　-鿿]", orth):
                continue  # skip non-Japanese entries

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
                "url": url,
                "src": "bc",
            })

    return rows


def scrape_knowledge_year(year: int, url: str) -> list[dict]:
    """
    Scrape /knowledge/pregnancy/{ID} pages (2010-2014).
    Table structure: rank | name | readings | count (票数)
    Two tables per page: boys then girls.
    """
    try:
        soup = get_soup(url)
    except requests.HTTPError as e:
        print(f"    {year} knowledge page error: {e}", file=sys.stderr)
        return []

    rows = []
    tables = soup.find_all("table")
    gender_map = ["M", "F"]
    name_tables_found = 0

    for tbl in tables:
        if name_tables_found >= 2:
            break
        trs = tbl.find_all("tr")
        if len(trs) < 3:
            continue
        header_texts = [c.get_text(strip=True) for c in trs[0].find_all(["th","td"])]
        if "順位" not in header_texts and "名前" not in header_texts:
            continue

        gender = gender_map[name_tables_found]
        name_tables_found += 1

        for tr in trs[1:]:
            cells = [c.get_text(" ", strip=True) for c in tr.find_all(["th","td"])]
            if len(cells) < 2:
                continue
            rank = parse_rank_int(cells[0])
            if rank is None:
                continue
            orth = cells[1].strip() if len(cells) > 1 else ""
            pron_raw = cells[2].strip() if len(cells) > 2 else ""
            freq_str = cells[3].strip() if len(cells) > 3 else ""
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
                "prev_rank": "",
                "url": url,
                "src": "bc",
            })

    return rows


def scrape_all_rankings() -> list[dict]:
    all_rows = []

    # 2010-2014: knowledge pages (top-10)
    for year in sorted(KNOWLEDGE_PAGES, reverse=True):
        print(f"  Baby Calendar {year} (knowledge/top-10)...")
        rows = scrape_knowledge_year(year, KNOWLEDGE_PAGES[year])
        print(f"    {len(rows)} rows")
        all_rows.extend(rows)

    # 2015-2019: special pages (top-10)
    for year in sorted(SPECIAL_YEARS):
        print(f"  Baby Calendar {year} (special/top-10)...")
        rows = scrape_special_year(year, SPECIAL_YEARS[year])
        print(f"    {len(rows)} rows")
        all_rows.extend(rows)

    # 2020-2023: nazuke structured pages (top-100)
    for year in NAZUKE_YEARS:
        print(f"  Baby Calendar {year} (nazuke/top-100)...")
        rows = scrape_nazuke_year(year)
        print(f"    {len(rows)} rows")
        all_rows.extend(rows)

    # 2024-2025: smilenews articles (top-100)
    for year in sorted(SMILENEWS_IDS):
        print(f"  Baby Calendar {year} (smilenews/top-100)...")
        rows = scrape_smilenews_year(year)
        print(f"    {len(rows)} rows")
        all_rows.extend(rows)

    return all_rows


def scrape_episodes() -> list[dict]:
    """
    Scrape name stories (名付けエピソード) from Baby Calendar.
    These appear in the smilenews articles alongside rankings and also on dedicated
    episode pages. We collect episode text from the ranking articles we already know.
    Returns rows: year, gender, rank, orth, pron_raw, episode, url
    """
    episodes = []

    # Check the main ranking articles for embedded episode content
    all_article_ids = []
    for year, ids in SMILENEWS_IDS.items():
        for key, art_id in ids.items():
            all_article_ids.append((year, key, art_id))

    # Also look for dedicated episode pages linked from the ranking pages
    for year in NAZUKE_YEARS:
        url = f"{BASE}/nazuke/nameranking{year}"
        try:
            soup = get_soup(url)
            # Look for episode links (名付けエピソード)
            for a in soup.find_all("a", href=True):
                href = a["href"]
                text = a.get_text(strip=True)
                if "エピソード" in text or "episode" in href.lower() or "nazuke" in href:
                    print(f"    Episode link found: {href} ({text})", file=sys.stderr)
        except Exception as e:
            print(f"  {year} episode search: {e}", file=sys.stderr)

    # Try known episode URL patterns
    # Baby Calendar publishes episode rankings separately
    episode_url_patterns = [
        f"{BASE}/nazuke/nameranking{{year}}/episode",
        f"{BASE}/nazuke/nameranking{{year}}/name_episode",
    ]

    for year in NAZUKE_YEARS + list(SMILENEWS_IDS.keys()):
        for pattern in episode_url_patterns:
            url = pattern.format(year=year)
            try:
                soup = get_soup(url)
                tables = soup.find_all("table")
                if tables:
                    print(f"    Found episode table at {url}", file=sys.stderr)
                    for tbl in tables:
                        tbody = tbl.find("tbody") or tbl
                        for tr in tbody.find_all("tr"):
                            cells = tr.find_all("td")
                            if len(cells) >= 3:
                                rank = parse_rank_int(cells[0].get_text(strip=True))
                                orth = cells[1].get_text(strip=True)
                                episode_text = cells[2].get_text(" ", strip=True)
                                pron_raw = ""
                                episodes.append({
                                    "year": year,
                                    "rank": rank or "",
                                    "orth": orth,
                                    "pron_raw": pron_raw,
                                    "episode": episode_text,
                                    "url": url,
                                    "src": "bc",
                                })
            except requests.HTTPError:
                pass  # Not found at this URL

    return episodes


FIELDNAMES = ["year", "gender", "rank", "orth", "pron_raw", "freq", "prev_rank", "url", "src"]
EPISODE_FIELDNAMES = ["year", "gender", "rank", "orth", "pron_raw", "episode", "url", "src"]


def write_tsv(rows: list[dict], path: Path, fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t",
                                extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    print(f"  Written {len(rows)} rows to {path}")


def main():
    parser = argparse.ArgumentParser(description="Scrape Baby Calendar rankings")
    parser.add_argument("--episodes", action="store_true", help="Also scrape name episodes")
    parser.add_argument("--out", default=str(OUT_DIR), help="Output directory")
    args = parser.parse_args()

    out = Path(args.out)

    print("Scraping Baby Calendar rankings...")
    rows = scrape_all_rankings()
    write_tsv(rows, out / "baby_calendar_rankings.tsv", FIELDNAMES)

    if args.episodes:
        print("\nScraping Baby Calendar name episodes...")
        ep_rows = scrape_episodes()
        write_tsv(ep_rows, out / "baby_calendar_episodes.tsv", EPISODE_FIELDNAMES)


if __name__ == "__main__":
    main()
