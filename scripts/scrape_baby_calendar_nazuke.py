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

CACHE_DIR = Path(__file__).parent.parent / "data" / "raw" / "page_cache"
OUT = Path(__file__).parent.parent / "data" / "raw" / "baby_calendar_nazuke_episodes.tsv"
FIELDNAMES = ["year", "gender", "sound_row", "orth", "pron", "episode", "script", "page_type", "url", "src"]

# Complete map of /knowledge/common/ episode pages
# (year, sound_row, gender) -> ID
# Note: 2017-2019 pages are still live as of 2026-06-08
# Note: ID 1295 (2018 M わ行) returns 404 — that page was never published
# Note: ID 1550 (2021 F わ行) and ID 1530 (2020 F わ行) not published
EPISODE_PAGE_IDS = {
    # 2017
    (2017, "あ行", "M"): 1030, (2017, "か行", "M"): 1031, (2017, "さ行", "M"): 1032,
    (2017, "た行", "M"): 1033, (2017, "な行", "M"): 1034, (2017, "は行", "M"): 1035,
    (2017, "ま行", "M"): 1036, (2017, "や行", "M"): 1037, (2017, "ら行", "M"): 1038,
    (2017, "わ行", "M"): 1039,
    (2017, "あ行", "F"): 1040, (2017, "か行", "F"): 1041, (2017, "さ行", "F"): 1042,
    (2017, "た行", "F"): 1043, (2017, "な行", "F"): 1044, (2017, "は行", "F"): 1045,
    (2017, "ま行", "F"): 1046, (2017, "や行", "F"): 1047, (2017, "ら行", "F"): 1048,
    (2017, "わ行", "F"): 1049,
    # 2018
    (2018, "あ行", "M"): 1286, (2018, "か行", "M"): 1287, (2018, "さ行", "M"): 1288,
    (2018, "た行", "M"): 1289, (2018, "な行", "M"): 1290, (2018, "は行", "M"): 1291,
    (2018, "ま行", "M"): 1292, (2018, "や行", "M"): 1293, (2018, "ら行", "M"): 1294,
    # 1295 (2018 M わ行) → 404, page was never published
    (2018, "あ行", "F"): 1296, (2018, "か行", "F"): 1297, (2018, "さ行", "F"): 1298,
    (2018, "た行", "F"): 1299, (2018, "な行", "F"): 1300, (2018, "は行", "F"): 1301,
    (2018, "ま行", "F"): 1302, (2018, "や行", "F"): 1303, (2018, "ら行", "F"): 1304,
    (2018, "わ行", "F"): 1305,
    # 2019
    (2019, "あ行", "M"): 1457, (2019, "か行", "M"): 1458, (2019, "さ行", "M"): 1459,
    (2019, "た行", "M"): 1460, (2019, "な行", "M"): 1461, (2019, "は行", "M"): 1462,
    (2019, "ま行", "M"): 1463, (2019, "や行", "M"): 1464, (2019, "ら行", "M"): 1465,
    (2019, "わ行", "M"): 1466,
    (2019, "あ行", "F"): 1467, (2019, "か行", "F"): 1468, (2019, "さ行", "F"): 1469,
    (2019, "た行", "F"): 1470, (2019, "な行", "F"): 1471, (2019, "は行", "F"): 1472,
    (2019, "ま行", "F"): 1473, (2019, "や行", "F"): 1474, (2019, "ら行", "F"): 1475,
    (2019, "わ行", "F"): 1476,
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



def get_soup(url: str, page_id: int | None = None) -> BeautifulSoup | None:
    """Fetch URL, using local HTML cache when available (data/raw/page_cache/)."""
    if page_id is not None:
        cache_file = CACHE_DIR / f"bc_episode_{page_id}.html"
        if cache_file.exists():
            html = cache_file.read_text(encoding="utf-8")
            if not html:
                return None  # cached 404
            return BeautifulSoup(html, "html.parser")

    resp = requests.get(url, headers=HEADERS, timeout=20)
    if resp.status_code == 404:
        if page_id is not None:
            CACHE_DIR.mkdir(parents=True, exist_ok=True)
            (CACHE_DIR / f"bc_episode_{page_id}.html").write_bytes(b"")
        return None
    resp.raise_for_status()
    resp.encoding = "utf-8"
    if page_id is not None:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        (CACHE_DIR / f"bc_episode_{page_id}.html").write_text(resp.text, encoding="utf-8")
    time.sleep(DELAY)
    return BeautifulSoup(resp.text, "html.parser")


_SENT_FRAG  = re.compile(
    r'している|いられる|ように|のと|つけた|名前が|名前は|に生まれ|生まれた|甥っ子|元嫁|そんな|["\"""]'
)
_LEAD_JUNK  = re.compile(r'^[・』「」『\'"→\s]+')
_PART_KANJI = re.compile(r'^[のにをはが](?=[一-鿿])')  # lone particle before kanji
_VERB_END   = re.compile(r'^[たてでにしはがをものぞれ]+')
_NAME_CHARS = re.compile(r'[ぁ-ゟ゠-ヿ一-鿿㐀-䶿々〆a-zA-Zａ-ｚＡ-Ｚ]+')


def _script(orth: str) -> str:
    """Classify dominant script of a name orth."""
    has_kanji = bool(re.search(r'[一-鿿㐀-䶿々〆]', orth))
    has_hira  = bool(re.search(r'[ぁ-ゟ]', orth))
    has_kata  = bool(re.search(r'[ァ-ヶー]', orth))
    has_latin = bool(re.search(r'[a-zA-Zａ-ｚＡ-Ｚ]', orth))
    if has_latin:
        return 'mixlatin' if (has_kanji or has_hira or has_kata) else 'latin'
    if has_kanji:
        if has_hira: return 'mixhira'
        if has_kata: return 'mixkata'
        return 'kanji'
    if has_hira: return 'mixhira' if has_kata else 'hira'
    if has_kata: return 'kata'
    return 'unknown'


def clean_orth(raw: str) -> str | None:
    """Strip parse-noise from a matched orth; return None if unrecoverable."""
    raw = _LEAD_JUNK.sub('', raw).strip()
    raw = _PART_KANJI.sub('', raw).strip()  # strip lone particle before kanji
    if _SENT_FRAG.search(raw):
        last = list(_SENT_FRAG.finditer(raw))[-1]
        tail = _VERB_END.sub('', raw[last.end():]).strip()
        if 0 < len(tail) <= 12 and _NAME_CHARS.search(tail):
            raw = tail
        else:
            parts = _NAME_CHARS.findall(raw)
            raw = parts[-1] if parts else ''
    raw = raw.strip()
    if not raw or len(raw) > 12 or not _NAME_CHARS.search(raw):
        return None
    return raw


def parse_episode_page(soup: BeautifulSoup, year: int, gender: str,
                       sound_row: str, url: str, page_type: str) -> list[dict]:
    """Parse a /knowledge/common/{ID} episode page."""
    text = soup.get_text("\n", strip=True)
    rows = []

    entry_pat = re.compile(
        r'([^\s（）()「」。、\n]{1,15})\s*[（(]([ぁ-ゟァ-ヶー]{1,12})[）)]\s*(?:くん|ちゃん)',
        re.MULTILINE
    )

    matches = list(entry_pat.finditer(text))
    for i, m in enumerate(matches):
        orth = clean_orth(m.group(1))
        if not orth:
            continue
        pron = m.group(2).strip()

        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else min(start + 1000, len(text))
        story = text[start:end].strip()
        story = re.sub(r'^[\s→「」。、\n]+', '', story)
        story = re.sub(r'[\s\n]+', ' ', story).strip()
        story = re.sub(r'（[^\)]{2,10}さん）\s*$', '', story).strip()
        story = re.split(r'「[^」]{1,5}」ではじまる|→\s*「', story)[0].strip()

        if not pron or len(story) < 5:
            continue

        rows.append({
            "year": year,
            "gender": gender,
            "sound_row": sound_row,
            "orth": orth,
            "pron": pron,
            "episode": story[:1000],
            "script": _script(orth),
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
        soup = get_soup(url, page_id=page_id)
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
