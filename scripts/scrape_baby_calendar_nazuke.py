#!/usr/bin/env python3
"""
Scrape Baby Calendar naming episode (名づけエピソード) pages.

Two source types:
1. Per-sound-row pages at /knowledge/common/{ID}  (2020-2023)
   - One page per sound row (あ-わ行) per gender per year
   - Each entry: kanji name, hiragana reading, story text

2. Annual award pages (2015-2023)
   - 2015-2019: baby-calendar.jp/special/name/{YEAR}/episode
   - 2020-2023: nazuke-nameranking.jp/naduke-episode{YEAR}/
   - Smaller number of award-winning entries per year

Output: data/raw/baby_calendar_nazuke_episodes.tsv
Columns: year, gender, sound_row, orth, pron, episode, page_type, url, src
"""

import csv
import re
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup

BASE = "https://baby-calendar.jp"
HEADERS = {"User-Agent": "Mozilla/5.0 (research scraper; namae-bc project; contact: bond@ieee.org)"}
DELAY = 1.2

OUT = Path(__file__).parent.parent / "data" / "raw" / "baby_calendar_nazuke_episodes.tsv"
FIELDNAMES = ["year", "gender", "sound_row", "orth", "pron", "episode", "page_type", "url", "src"]

# Complete map of /knowledge/common/ episode pages
# (year, sound_row, gender) -> ID
EPISODE_PAGE_IDS = {
    # 2020
    (2020, "あ行", "M"): 1512, (2020, "か行", "M"): 1513, (2020, "さ行", "M"): 1514,
    (2020, "た行", "M"): 1515, (2020, "な行", "M"): 1516, (2020, "は行", "M"): 1517,
    (2020, "ま行", "M"): 1518, (2020, "や行", "M"): 1519, (2020, "ら行", "M"): 1520,
    (2020, "わ行", "M"): 1521,
    (2020, "あ行", "F"): 1522, (2020, "か行", "F"): 1523, (2020, "さ行", "F"): 1524,
    (2020, "た行", "F"): 1525, (2020, "な行", "F"): 1526, (2020, "は行", "F"): 1527,
    (2020, "ま行", "F"): 1528, (2020, "や行", "F"): 1529, (2020, "ら行", "F"): 1530,
    # 2021
    (2021, "あ行", "M"): 1531, (2021, "か行", "M"): 1532, (2021, "さ行", "M"): 1533,
    (2021, "た行", "M"): 1534, (2021, "な行", "M"): 1535, (2021, "は行", "M"): 1536,
    (2021, "ま行", "M"): 1537, (2021, "や行", "M"): 1538, (2021, "ら行", "M"): 1539,
    (2021, "わ行", "M"): 1540,
    (2021, "あ行", "F"): 1541, (2021, "か行", "F"): 1542, (2021, "さ行", "F"): 1543,
    (2021, "た行", "F"): 1544, (2021, "な行", "F"): 1545, (2021, "は行", "F"): 1546,
    (2021, "ま行", "F"): 1547, (2021, "や行", "F"): 1548, (2021, "ら行", "F"): 1549,
    # 2022
    (2022, "あ行", "M"): 1551, (2022, "か行", "M"): 1552, (2022, "さ行", "M"): 1553,
    (2022, "た行", "M"): 1554, (2022, "な行", "M"): 1555, (2022, "は行", "M"): 1556,
    (2022, "ま行", "M"): 1557, (2022, "や行", "M"): 1558, (2022, "ら行", "M"): 1559,
    (2022, "あ行", "F"): 1560, (2022, "か行", "F"): 1561, (2022, "さ行", "F"): 1562,
    (2022, "た行", "F"): 1563, (2022, "な行", "F"): 1564, (2022, "は行", "F"): 1565,
    (2022, "ま行", "F"): 1566, (2022, "や行", "F"): 1567, (2022, "ら行", "F"): 1568,
    (2022, "わ行", "F"): 1569,
    # 2023
    (2023, "あ行", "F"): 1591, (2023, "か行", "F"): 1592, (2023, "さ行", "F"): 1593,
    (2023, "た行", "F"): 1594, (2023, "な行", "F"): 1595, (2023, "は行", "F"): 1596,
    (2023, "ま行", "F"): 1597, (2023, "や行", "F"): 1598, (2023, "ら行", "F"): 1599,
    (2023, "わ行", "F"): 1600,
    (2023, "あ行", "M"): 1601, (2023, "か行", "M"): 1602, (2023, "さ行", "M"): 1603,
    (2023, "た行", "M"): 1604, (2023, "な行", "M"): 1605, (2023, "は行", "M"): 1606,
    (2023, "ま行", "M"): 1607, (2023, "や行", "M"): 1608, (2023, "ら行", "M"): 1609,
    (2023, "わ行", "M"): 1610,
}



def get_soup(url: str) -> BeautifulSoup | None:
    resp = requests.get(url, headers=HEADERS, timeout=20)
    if resp.status_code == 404:
        return None
    resp.raise_for_status()
    resp.encoding = "utf-8"
    time.sleep(DELAY)
    return BeautifulSoup(resp.text, "html.parser")


def parse_episode_page(soup: BeautifulSoup, year: int, gender: str,
                       sound_row: str, url: str, page_type: str) -> list[dict]:
    """
    Parse a /knowledge/common/{ID} episode page.
    Entries follow the pattern: kanji（reading）くん/ちゃん followed by story text.
    """
    text = soup.get_text("\n", strip=True)
    rows = []

    # Pattern: Name（reading）くん or ちゃん then episode text until next entry
    # Also handles: Name（reading）\nくん/ちゃん
    # Build a list of (orth, pron, gender_marker, story) tuples
    # Split text at name entries
    # Name pattern: non-whitespace kanji/kana string followed by （hiragana）
    entry_pat = re.compile(
        r'([^\s（）「」。、\n]{1,15})\s*（([ぁ-ゟァ-ヶー]{1,12})）\s*(?:くん|ちゃん)',
        re.MULTILINE
    )

    matches = list(entry_pat.finditer(text))
    for i, m in enumerate(matches):
        orth = m.group(1).strip()
        pron = m.group(2).strip()

        # Extract story: text between this match end and next match start
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else min(start + 1000, len(text))
        story = text[start:end].strip()
        # Clean up story: remove leading/trailing noise
        story = re.sub(r'^[\s→「」。、\n]+', '', story)
        story = re.sub(r'[\s\n]+', ' ', story).strip()
        # Remove author attribution at end (e.g., "（田中さん）")
        story = re.sub(r'（[^\)]{2,10}さん）\s*$', '', story).strip()
        # Truncate at next section heading
        story = re.split(r'「[^」]{1,5}」ではじまる|→\s*「', story)[0].strip()

        if not orth or not pron or len(story) < 5:
            continue

        rows.append({
            "year": year,
            "gender": gender,
            "sound_row": sound_row,
            "orth": orth,
            "pron": pron,
            "episode": story[:1000],
            "page_type": page_type,
            "url": url,
            "src": "bc",
        })

    return rows



def scrape_all_episodes() -> list[dict]:
    all_rows = []

    # 1. Sound-row episode pages (2020-2023)
    print("Scraping sound-row episode pages...")
    for (year, sound_row, gender), page_id in sorted(EPISODE_PAGE_IDS.items()):
        url = f"{BASE}/knowledge/common/{page_id}"
        soup = get_soup(url)
        if soup is None:
            print(f"  {year} {sound_row} {gender}: 404")
            continue
        rows = parse_episode_page(soup, year, gender, sound_row, url, "sound_row")
        all_rows.extend(rows)
        if len(rows) == 0:
            print(f"  {year} {sound_row} {gender}: 0 entries (ID {page_id})")
        elif len(rows) < 3:
            print(f"  {year} {sound_row} {gender}: {len(rows)} entries")

    by_year = {}
    for r in all_rows:
        by_year.setdefault(r["year"], 0)
        by_year[r["year"]] += 1
    for year in sorted(by_year):
        print(f"  {year}: {by_year[year]} episode entries")

    return all_rows


def main():
    rows = scrape_all_episodes()

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES, delimiter="\t",
                                extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    print(f"\nTotal: {len(rows)} episode entries written to {OUT}")


if __name__ == "__main__":
    main()
