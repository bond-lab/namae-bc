#!/usr/bin/env python3
"""
Recover Baby Calendar nazuke episode pages from the Wayback Machine.

Strategy:
  1. Use CDX API to find all archived snapshots of
     baby-calendar.jp/knowledge/common/* that contain "エピソード"
  2. For each candidate URL, fetch the best snapshot and parse entries
  3. Also check /knowledge/pregnancy/* and /special/name/*/episode* paths

Only recovers pages not available on the live site (i.e., pre-2020 episodes).

Output: data/raw/baby_calendar_nazuke_episodes_archive.tsv
        (same columns as baby_calendar_nazuke_episodes.tsv)
"""

import csv
import re
import sys
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup

BASE_LIVE = "https://baby-calendar.jp"
WBM = "https://web.archive.org"
CDX = "https://web.archive.org/cdx/search/cdx"
AVAIL = "https://archive.org/wayback/available"
HEADERS = {"User-Agent": "Mozilla/5.0 (research scraper; namae-bc; contact: bond@ieee.org)"}
DELAY_CDX = 2.0    # between CDX API calls
DELAY_FETCH = 2.5  # between Wayback page fetches

OUT = Path(__file__).parent.parent / "data" / "raw" / "baby_calendar_nazuke_episodes_archive.tsv"
FIELDNAMES = ["year", "gender", "sound_row", "orth", "pron", "episode",
              "archive_ts", "archive_url", "src"]

SOUND_ROWS = ["あ行", "か行", "さ行", "た行", "な行", "は行", "ま行", "や行", "ら行", "わ行"]

# IDs confirmed live (2020-2023) — skip these
LIVE_IDS = set(range(1512, 1611))

# Known year blocks discovered from CDX results and confirmed via archive fetches.
# Format: year -> {gender -> range of IDs}
# Update this as more years are confirmed.
#
# ID sequence observed so far:
#   ~373-376:    unknown year (found in CDX, not yet fetched)
#   ~485-505:    unknown year (found in CDX, not yet fetched)
#   ~549:        unknown year (found in CDX, not yet fetched)
#   ~749-800:    unknown year (found in CDX, not yet fetched)
#   ~865-899:    unknown year (found in CDX, not yet fetched)
#   1030-1049:   2017 confirmed (boys 1030-1039, girls 1040-1049)
#   1050-1511:   2018/2019 — TBD
#   1512-1610:   2020-2023 live (skipped)
KNOWN_YEAR_BLOCKS: dict[int, dict[str, range]] = {
    2017: {"M": range(1030, 1040), "F": range(1040, 1050)},
    2018: {"M": range(1286, 1296), "F": range(1296, 1306)},
    2019: {"M": range(1457, 1467), "F": range(1467, 1477)},
    # 2016 and earlier: no archive evidence found
}


def infer_meta_from_id(id_: int) -> tuple[int | None, str, str]:
    """Use known year blocks to infer year, sound_row, and gender from a page ID."""
    for year, blocks in KNOWN_YEAR_BLOCKS.items():
        for gender, id_range in blocks.items():
            if id_ in id_range:
                idx = id_ - id_range.start
                row = SOUND_ROWS[idx] if idx < len(SOUND_ROWS) else ""
                return year, row, gender
    return None, "", ""


def cdx_search(url_pattern: str, from_year: str = "2014", to_year: str = "2020") -> list[dict]:
    """Query CDX API for archived URLs matching a pattern."""
    params = {
        "url": url_pattern,
        "output": "json",
        "fl": "timestamp,original,statuscode",
        "filter": ["statuscode:200", "mimetype:text/html"],
        "collapse": "original",
        "limit": 1000,
        "from": f"{from_year}0101",
        "to": f"{to_year}1231",
    }
    for attempt in range(3):
        try:
            r = requests.get(CDX, params=params, headers=HEADERS, timeout=60)
            if r.status_code == 200 and r.content:
                data = r.json()
                return [{"timestamp": row[0], "url": row[1]} for row in data[1:]]
            elif r.status_code == 503:
                print(f"  CDX 503, retrying ({attempt+1}/3)...", file=sys.stderr)
                time.sleep(10)
        except Exception as e:
            print(f"  CDX error: {e}, retrying...", file=sys.stderr)
            time.sleep(10)
    return []


def get_best_snapshot(url: str, year_hint: int | None = None) -> tuple[str, str] | None:
    """Return (timestamp, wayback_url) for best available snapshot."""
    params = {"url": url}
    if year_hint:
        params["timestamp"] = f"{year_hint}1201"
    try:
        r = requests.get(AVAIL, params=params, headers=HEADERS, timeout=20)
        time.sleep(0.5)
        if r.status_code == 200:
            snap = r.json().get("archived_snapshots", {}).get("closest", {})
            if snap.get("available"):
                return snap["timestamp"], snap["url"]
    except Exception:
        pass
    return None


def fetch_wayback(wayback_url: str) -> BeautifulSoup | None:
    try:
        r = requests.get(wayback_url, headers=HEADERS, timeout=30)
        if r.status_code == 200:
            r.encoding = "utf-8"
            time.sleep(DELAY_FETCH)
            return BeautifulSoup(r.text, "html.parser")
    except Exception as e:
        print(f"  Fetch error: {e}", file=sys.stderr)
    return None


def infer_meta(title: str) -> tuple[int | None, str, str]:
    """Extract (year, sound_row, gender) from page title."""
    year_m = re.search(r'(\d{4})年', title)
    row_m  = re.search(r'[：:]\s*(.行)', title)
    gen_m  = re.search(r'（(男の子|女の子)）', title)
    year   = int(year_m.group(1)) if year_m else None
    row    = row_m.group(1) if row_m else ""
    gender = "M" if gen_m and gen_m.group(1) == "男の子" else ("F" if gen_m else "")
    return year, row, gender


def parse_episodes(soup: BeautifulSoup, year: int, gender: str, sound_row: str,
                   archive_ts: str, archive_url: str) -> list[dict]:
    text = soup.get_text("\n", strip=True)
    entry_pat = re.compile(
        r'([^\s（）「」。、\n]{1,15})\s*（([ぁ-ゟァ-ヶー]{1,12})）\s*(?:くん|ちゃん)',
        re.MULTILINE
    )
    matches = list(entry_pat.finditer(text))
    rows = []
    for i, m in enumerate(matches):
        orth = m.group(1).strip()
        pron = m.group(2).strip()
        start = m.end()
        end = matches[i+1].start() if i+1 < len(matches) else min(start+1000, len(text))
        story = text[start:end].strip()
        story = re.sub(r'^[\s→「」。、\n]+', '', story)
        story = re.sub(r'[\s\n]+', ' ', story).strip()
        story = re.sub(r'（[^\)]{2,10}さん）\s*$', '', story).strip()
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
            "archive_ts": archive_ts,
            "archive_url": archive_url,
            "src": "bc",
        })
    return rows


def main():
    # Load already-recovered entries so we don't re-fetch them
    all_rows = []
    seen_urls = set()
    if OUT.exists():
        with open(OUT, encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter="\t")
            for row in reader:
                all_rows.append(row)
                seen_urls.add(row.get("archive_url", ""))
        print(f"Loaded {len(all_rows)} existing entries (will skip their URLs)")

    # ── Step 1: CDX search for /knowledge/common/* episode pages ────────────
    # BC launched in 2008; search from 2008 to capture all historical episodes.
    print("Step 1: CDX search for /knowledge/common/* ...")
    time.sleep(DELAY_CDX)
    candidates = cdx_search("baby-calendar.jp/knowledge/common/*",
                             from_year="2008", to_year="2020")
    print(f"  {len(candidates)} CDX hits")

    # Filter to plausible episode IDs (not confirmed live, not too low)
    episode_candidates = []
    for c in candidates:
        m = re.search(r'/knowledge/common/(\d+)', c["url"])
        if m:
            id_ = int(m.group(1))
            if id_ not in LIVE_IDS and id_ > 100:
                episode_candidates.append(c)

    print(f"  {len(episode_candidates)} candidate episode URLs to check")

    for c in episode_candidates:
        url = c["url"]
        if url in seen_urls:
            continue
        seen_urls.add(url)
        wb_url = f"{WBM}/web/{c['timestamp']}/{url}"
        soup = fetch_wayback(wb_url)
        if not soup:
            continue
        title = soup.title.string if soup.title else ""
        if "名づけエピソード" not in title and "エピソード" not in title:
            continue
        year, sound_row, gender = infer_meta(title)
        if not year:
            m2 = re.search(r'/knowledge/common/(\d+)', url)
            if m2:
                year, sound_row, gender = infer_meta_from_id(int(m2.group(1)))
        if not year:
            continue
        rows = parse_episodes(soup, year, gender, sound_row, c["timestamp"], wb_url)
        if rows:
            print(f"  {url} ({c['timestamp'][:8]}): {len(rows)} entries ({year} {sound_row} {gender})")
            all_rows.extend(rows)

    # ── Step 2: CDX search for /knowledge/pregnancy/* episode pages ─────────
    print("\nStep 2: CDX search for /knowledge/pregnancy/* ...")
    time.sleep(DELAY_CDX)
    preg_candidates = cdx_search("baby-calendar.jp/knowledge/pregnancy/*",
                                  from_year="2008", to_year="2020")
    print(f"  {len(preg_candidates)} CDX hits")
    for c in preg_candidates:
        url = c["url"]
        if url in seen_urls:
            continue
        seen_urls.add(url)
        wb_url = f"{WBM}/web/{c['timestamp']}/{url}"
        soup = fetch_wayback(wb_url)
        if not soup:
            continue
        title = soup.title.string if soup.title else ""
        if "名づけエピソード" not in title and "エピソード" not in title:
            continue
        year, sound_row, gender = infer_meta(title)
        if not year:
            m2 = re.search(r'/knowledge/common/(\d+)', url)
            if m2:
                year, sound_row, gender = infer_meta_from_id(int(m2.group(1)))
        if not year:
            continue
        rows = parse_episodes(soup, year, gender, sound_row, c["timestamp"], wb_url)
        if rows:
            print(f"  {url} ({c['timestamp'][:8]}): {len(rows)} entries ({year} {sound_row} {gender})")
            all_rows.extend(rows)

    # ── Step 3: CDX search for /special/name/*/episode* paths ───────────────
    print("\nStep 3: CDX search for /special/name/* ...")
    time.sleep(DELAY_CDX)
    special_candidates = cdx_search("baby-calendar.jp/special/name/*",
                                     from_year="2008", to_year="2020")

    # ── Step 4: CDX search for older URL patterns ─────────────────────────
    # Early BC content used /name/ or /nazuke/ paths before /knowledge/common/
    print("\nStep 4: CDX search for /name/* and /nazuke/* ...")
    time.sleep(DELAY_CDX)
    name_candidates  = cdx_search("baby-calendar.jp/name/*",
                                    from_year="2008", to_year="2018")
    time.sleep(DELAY_CDX)
    nazuke_candidates = cdx_search("baby-calendar.jp/nazuke/*",
                                    from_year="2008", to_year="2020")
    # Merge into special_candidates list
    special_candidates = special_candidates + name_candidates + nazuke_candidates
    print(f"  {len(special_candidates)} CDX hits")
    for c in special_candidates:
        url = c["url"]
        if "episode" not in url.lower() and "エピソード" not in url:
            continue
        if url in seen_urls:
            continue
        seen_urls.add(url)
        wb_url = f"{WBM}/web/{c['timestamp']}/{url}"
        soup = fetch_wayback(wb_url)
        if not soup:
            continue
        title = soup.title.string if soup.title else ""
        year, sound_row, gender = infer_meta(title)
        if not year:
            m2 = re.search(r'/knowledge/common/(\d+)', url)
            if m2:
                year, sound_row, gender = infer_meta_from_id(int(m2.group(1)))
        if not year:
            continue
        rows = parse_episodes(soup, year, gender, sound_row, c["timestamp"], wb_url)
        if rows:
            print(f"  {url} ({c['timestamp'][:8]}): {len(rows)} entries ({year} {sound_row} {gender})")
            all_rows.extend(rows)

    # ── Step 5: Retry known CDX-found IDs that previously timed out ─────────
    # IDs found in CDX but not fetched due to archive downtime.
    # Covers the full pre-2017 range to catch 2008-2016 episodes.
    print("\nStep 5: Probing known unfetched candidate IDs ...")
    UNFETCHED_IDS = [
        # 2017 — all 20 pages (overwritten in previous run)
        *range(1030, 1050),
        # 2018 — missing 10 pages (others fetched in current file)
        1286, 1288, 1291, 1292, 1293, 1294, 1295,  # males: あ-さ-は-ま-や-ら-わ行
        1300, 1301, 1304,                            # females: な-は-ら行
        # 2019 — missing 17 pages (1460, 1465, 1475 already in file)
        *range(1457, 1460),  # あ-か-さ行 M
        1461, 1462, 1463, 1464, 1466,               # な-は-ま-や-わ行 M
        *range(1467, 1475),  # あ-か-さ-た-な-は-ま-や行 F
        1476,                                        # わ行 F
    ]
    AVAIL_URL = "https://archive.org/wayback/available"
    for id_ in UNFETCHED_IDS:
        url = f"https://baby-calendar.jp/knowledge/common/{id_}"
        if url in seen_urls:
            continue
        seen_urls.add(url)
        # Find best snapshot via availability API
        try:
            r = requests.get(AVAIL_URL, params={"url": url}, headers=HEADERS, timeout=20)
            time.sleep(0.8)
            if r.status_code != 200:
                continue
            snap = r.json().get("archived_snapshots", {}).get("closest", {})
            if not snap.get("available"):
                continue
            wb_url = snap["url"]
        except Exception as e:
            print(f"  Avail error ID {id_}: {e}", file=sys.stderr)
            continue
        soup = fetch_wayback(wb_url)
        if not soup:
            continue
        title = soup.title.string if soup.title else ""
        year, sound_row, gender = infer_meta(title)
        if not year:
            year, sound_row, gender = infer_meta_from_id(id_)
        if not year:
            # Try to detect year from page content
            m_yr = re.search(r'20(0[89]|1\d)年.*(?:名づけ|エピソード)', title + soup.get_text()[:500])
            if m_yr:
                year = int("20" + m_yr.group(1))
        if not year:
            print(f"  ID {id_}: no year detected (title: {title[:60]})", file=sys.stderr)
            continue
        rows = parse_episodes(soup, year, gender, sound_row, snap["timestamp"], wb_url)
        if rows:
            print(f"  ID {id_} ({snap['timestamp'][:8]}): {len(rows)} entries ({year} {sound_row} {gender})")
            all_rows.extend(rows)

    # ── Summary ──────────────────────────────────────────────────────────────
    print(f"\nTotal recovered: {len(all_rows)} episode entries")
    by_year = {}
    for r in all_rows:
        by_year.setdefault(str(r["year"]), 0)
        by_year[str(r["year"])] += 1
    for y in sorted(by_year):
        print(f"  {y}: {by_year[y]}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES, delimiter="\t",
                                extrasaction="ignore")
        writer.writeheader()
        writer.writerows(all_rows)
    print(f"Written to {OUT}")


if __name__ == "__main__":
    main()
