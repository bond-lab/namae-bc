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

Rate limiting: archive.org blocks after ~60 req/min. DELAY_FETCH=5s keeps
us well under that limit. MAX_FETCHES caps each run to avoid long blocks.
Run the script repeatedly on different days to fill gaps gradually.
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
DELAY_CDX = 5.0    # between CDX API calls (conservative to avoid throttle)
DELAY_FETCH = 5.0  # between Wayback page fetches
DELAY_AVAIL = 2.0  # between availability API calls
MAX_FETCHES = 40   # max page fetches per run (archive.org blocks after ~60/session)

OUT = Path(__file__).parent.parent / "data" / "raw" / "baby_calendar_nazuke_episodes_archive.tsv"
FIELDNAMES = ["year", "gender", "sound_row", "orth", "pron", "episode",
              "script", "archive_ts", "archive_url", "src"]

SOUND_ROWS = ["あ行", "か行", "さ行", "た行", "な行", "は行", "ま行", "や行", "ら行", "わ行"]

# IDs confirmed live (2020-2023) — skip these
LIVE_IDS = set(range(1512, 1611))

# Known year blocks discovered from CDX results and confirmed via archive fetches.
# Format: year -> {gender -> range of IDs}
#
# ID sequence observed so far:
#   ~373-376:    unknown year (found in CDX, not yet verified)
#   ~485-505:    unknown year (found in CDX, not yet verified)
#   ~549:        unknown year (found in CDX, not yet verified)
#   ~749-800:    unknown year (found in CDX, not yet verified)
#   ~865-899:    unknown year (found in CDX, not yet verified)
#   1030-1049:   2017 confirmed (boys 1030-1039, girls 1040-1049)
#   1050-1511:   2018/2019 — confirmed blocks below
#   1512-1610:   2020-2023 live (skipped)
KNOWN_YEAR_BLOCKS: dict[int, dict[str, range]] = {
    2017: {"M": range(1030, 1040), "F": range(1040, 1050)},
    2018: {"M": range(1286, 1296), "F": range(1296, 1306)},
    2019: {"M": range(1457, 1467), "F": range(1467, 1477)},
    # 2016 and earlier: no archive evidence found yet
}

# IDs still missing from the current TSV (update after each run)
# Only IDs NOT already in data/raw/baby_calendar_nazuke_episodes_archive.tsv
UNFETCHED_IDS = [
    # 2017 — さ行M only (ID 1032)
    1032,
    # 2018 — 7 M + 3 F pages still missing
    1286, 1291, 1292, 1293, 1294, 1295,   # M: あ行 さ行 た行 な行 は行 ま行 や行
    1300, 1301, 1304,                       # F: な行 は行 ら行
    # 2019 — あ行F only (ID 1467)
    1467,
    # Pre-2017 candidates from CDX (year unknown — need content inspection)
    373, 374, 375, 376,
    485, 501, 502, 503, 504, 505,
    549,
    749, 750, 751, 752, 753,
    776, 790, 800,
    865, 890, 891, 892, 893, 894, 895, 896, 897, 898, 899,
    1165,
]


def infer_meta_from_id(id_: int) -> tuple[int | None, str, str]:
    """Use known year blocks to infer year, sound_row, and gender from a page ID."""
    for year, blocks in KNOWN_YEAR_BLOCKS.items():
        for gender, id_range in blocks.items():
            if id_ in id_range:
                idx = id_ - id_range.start
                row = SOUND_ROWS[idx] if idx < len(SOUND_ROWS) else ""
                return year, row, gender
    return None, "", ""


def cdx_search(url_pattern: str, from_year: str = "2008", to_year: str = "2020") -> list[dict]:
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
    delay = DELAY_CDX
    for attempt in range(4):
        try:
            r = requests.get(CDX, params=params, headers=HEADERS, timeout=60)
            if r.status_code == 200 and r.content:
                data = r.json()
                return [{"timestamp": row[0], "url": row[1]} for row in data[1:]]
            elif r.status_code in (503, 429):
                retry_after = int(r.headers.get("Retry-After", delay))
                print(f"  CDX {r.status_code}, waiting {retry_after}s ({attempt+1}/4)...", file=sys.stderr)
                time.sleep(retry_after)
                delay = min(delay * 2, 120)
        except Exception as e:
            print(f"  CDX error: {e}, waiting {delay}s...", file=sys.stderr)
            time.sleep(delay)
            delay = min(delay * 2, 120)
    return []


def get_best_snapshot(url: str, year_hint: int | None = None) -> tuple[str, str] | None:
    """Return (timestamp, wayback_url) for best available snapshot."""
    params = {"url": url}
    if year_hint:
        params["timestamp"] = f"{year_hint}1201"
    delay = DELAY_AVAIL
    for attempt in range(3):
        try:
            r = requests.get(AVAIL, params=params, headers=HEADERS, timeout=25)
            time.sleep(DELAY_AVAIL)
            if r.status_code == 200:
                snap = r.json().get("archived_snapshots", {}).get("closest", {})
                if snap.get("available"):
                    return snap["timestamp"], snap["url"]
                return None
            elif r.status_code in (503, 429):
                retry_after = int(r.headers.get("Retry-After", delay))
                print(f"  Avail {r.status_code}, waiting {retry_after}s...", file=sys.stderr)
                time.sleep(retry_after)
                delay = min(delay * 2, 120)
        except Exception as e:
            print(f"  Avail error: {e}, waiting {delay}s...", file=sys.stderr)
            time.sleep(delay)
            delay = min(delay * 2, 120)
    return None


def fetch_wayback(wayback_url: str) -> BeautifulSoup | None:
    delay = DELAY_FETCH
    for attempt in range(3):
        try:
            r = requests.get(wayback_url, headers=HEADERS, timeout=40)
            if r.status_code == 200:
                r.encoding = "utf-8"
                time.sleep(DELAY_FETCH)
                return BeautifulSoup(r.text, "html.parser")
            elif r.status_code in (503, 429):
                retry_after = int(r.headers.get("Retry-After", delay))
                print(f"  Fetch {r.status_code}, waiting {retry_after}s...", file=sys.stderr)
                time.sleep(retry_after)
                delay = min(delay * 2, 120)
        except Exception as e:
            print(f"  Fetch error: {e}, waiting {delay}s...", file=sys.stderr)
            time.sleep(delay)
            delay = min(delay * 2, 120)
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


def parse_episodes(soup: BeautifulSoup, year: int, gender: str, sound_row: str,
                   archive_ts: str, archive_url: str) -> list[dict]:
    text = soup.get_text("\n", strip=True)
    entry_pat = re.compile(
        r'([^\s（）()「」。、\n]{1,15})\s*[（(]([ぁ-ゟァ-ヶー]{1,12})[）)]\s*(?:くん|ちゃん)',
        re.MULTILINE
    )
    matches = list(entry_pat.finditer(text))
    rows = []
    for i, m in enumerate(matches):
        orth = clean_orth(m.group(1))
        if not orth:
            continue
        pron = m.group(2).strip()
        start = m.end()
        end = matches[i+1].start() if i+1 < len(matches) else min(start+1000, len(text))
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
            "archive_ts": archive_ts,
            "archive_url": archive_url,
            "src": "bc",
        })
    return rows


def extract_original_url(archive_url: str) -> str | None:
    """Extract the original baby-calendar.jp URL from a Wayback Machine URL."""
    m = re.search(r'web\.archive\.org/web/\d+/(https?://baby-calendar\.jp[^\s"]*)', archive_url)
    return m.group(1) if m else None


def main():
    # Load already-recovered entries so we don't re-fetch them.
    # Track both archive URLs (for CDX step dedup) and original URLs (for Step 5 dedup).
    all_rows = []
    seen_archive_urls = set()    # web.archive.org/web/... URLs
    seen_original_urls = set()   # baby-calendar.jp/... URLs
    if OUT.exists():
        with open(OUT, encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter="\t")
            for row in reader:
                all_rows.append(row)
                arc_url = row.get("archive_url", "")
                seen_archive_urls.add(arc_url)
                orig = extract_original_url(arc_url)
                if orig:
                    seen_original_urls.add(orig)
        print(f"Loaded {len(all_rows)} existing entries")
        print(f"  {len(seen_archive_urls)} unique archive URLs already seen")
        print(f"  {len(seen_original_urls)} unique original URLs already seen")

    fetch_count = 0

    def fetch_and_parse(wayback_url: str, original_url: str,
                        year: int | None, sound_row: str, gender: str,
                        source_label: str = "") -> int:
        """Fetch one wayback URL, parse episodes, append to all_rows. Returns count added."""
        nonlocal fetch_count
        if fetch_count >= MAX_FETCHES:
            return 0
        if wayback_url in seen_archive_urls:
            return 0
        seen_archive_urls.add(wayback_url)
        seen_original_urls.add(original_url)

        soup = fetch_wayback(wayback_url)
        fetch_count += 1
        if not soup:
            return 0
        title = soup.title.string if soup.title else ""

        # Determine metadata from title if not provided
        yr, sr, gn = infer_meta(title)
        if not yr and year:
            yr = year
        if not sr and sound_row:
            sr = sound_row
        if not gn and gender:
            gn = gender

        if not yr:
            return 0

        rows = parse_episodes(soup, yr, gn, sr, "", wayback_url)
        if rows:
            # Fill archive_ts from wayback URL
            ts_m = re.search(r'/web/(\d+)/', wayback_url)
            ts = ts_m.group(1) if ts_m else ""
            for rw in rows:
                rw["archive_ts"] = ts
            label = source_label or f"{yr} {sr} {gn}"
            print(f"  {original_url}: {len(rows)} entries ({label})")
            all_rows.extend(rows)
        return len(rows)

    # ── Step 1: CDX search for /knowledge/common/* episode pages ────────────
    print("Step 1: CDX search for /knowledge/common/* ...")
    time.sleep(DELAY_CDX)
    candidates = cdx_search("baby-calendar.jp/knowledge/common/*",
                             from_year="2008", to_year="2020")
    print(f"  {len(candidates)} CDX hits")

    episode_candidates = []
    for c in candidates:
        m = re.search(r'/knowledge/common/(\d+)', c["url"])
        if m:
            id_ = int(m.group(1))
            if id_ not in LIVE_IDS and id_ > 100:
                episode_candidates.append(c)

    print(f"  {len(episode_candidates)} candidate episode URLs to check")

    for c in episode_candidates:
        if fetch_count >= MAX_FETCHES:
            print(f"  MAX_FETCHES ({MAX_FETCHES}) reached, stopping CDX step 1")
            break
        url = c["url"]
        if url in seen_original_urls:
            continue
        wb_url = f"{WBM}/web/{c['timestamp']}/{url}"
        if wb_url in seen_archive_urls:
            continue
        # Pre-check title to avoid fetching non-episode pages
        id_m = re.search(r'/knowledge/common/(\d+)', url)
        id_ = int(id_m.group(1)) if id_m else 0
        year, sound_row, gender = infer_meta_from_id(id_)
        fetch_and_parse(wb_url, url, year, sound_row, gender)

    # ── Step 2: CDX search for /knowledge/pregnancy/* episode pages ─────────
    print(f"\nStep 2: CDX search for /knowledge/pregnancy/* (fetches so far: {fetch_count}) ...")
    if fetch_count < MAX_FETCHES:
        time.sleep(DELAY_CDX)
        preg_candidates = cdx_search("baby-calendar.jp/knowledge/pregnancy/*",
                                      from_year="2008", to_year="2020")
        print(f"  {len(preg_candidates)} CDX hits")
        for c in preg_candidates:
            if fetch_count >= MAX_FETCHES:
                break
            url = c["url"]
            if url in seen_original_urls:
                continue
            wb_url = f"{WBM}/web/{c['timestamp']}/{url}"
            if wb_url in seen_archive_urls:
                continue
            fetch_and_parse(wb_url, url, None, "", "")

    # ── Step 3/4: CDX search for /special/name/* and older paths ────────────
    print(f"\nStep 3/4: CDX search for /special/name/* and older paths (fetches: {fetch_count}) ...")
    if fetch_count < MAX_FETCHES:
        time.sleep(DELAY_CDX)
        special_candidates = cdx_search("baby-calendar.jp/special/name/*",
                                         from_year="2008", to_year="2020")
        time.sleep(DELAY_CDX)
        name_candidates = cdx_search("baby-calendar.jp/name/*",
                                      from_year="2008", to_year="2018")
        time.sleep(DELAY_CDX)
        nazuke_candidates = cdx_search("baby-calendar.jp/nazuke/*",
                                        from_year="2008", to_year="2020")
        all_special = special_candidates + name_candidates + nazuke_candidates
        print(f"  {len(all_special)} CDX hits")
        for c in all_special:
            if fetch_count >= MAX_FETCHES:
                break
            url = c["url"]
            if "episode" not in url.lower() and "エピソード" not in url:
                continue
            if url in seen_original_urls:
                continue
            wb_url = f"{WBM}/web/{c['timestamp']}/{url}"
            if wb_url in seen_archive_urls:
                continue
            fetch_and_parse(wb_url, url, None, "", "")

    # ── Step 5: Probe specific known candidate IDs ───────────────────────────
    # Only fetches IDs whose original URL is NOT already in seen_original_urls.
    print(f"\nStep 5: Probing {len(UNFETCHED_IDS)} candidate IDs (fetches so far: {fetch_count}) ...")
    for id_ in UNFETCHED_IDS:
        if fetch_count >= MAX_FETCHES:
            print(f"  MAX_FETCHES ({MAX_FETCHES}) reached at ID {id_}")
            break
        url = f"https://baby-calendar.jp/knowledge/common/{id_}"
        if url in seen_original_urls:
            continue

        year, sound_row, gender = infer_meta_from_id(id_)

        snap = get_best_snapshot(url, year_hint=year)
        if not snap:
            print(f"  ID {id_}: no archive found", file=sys.stderr)
            continue
        ts, wb_url = snap
        added = fetch_and_parse(wb_url, url, year, sound_row, gender,
                                source_label=f"ID {id_}")
        if not added:
            print(f"  ID {id_} ({ts[:8]}): 0 episodes parsed")

    # ── Summary ──────────────────────────────────────────────────────────────
    print(f"\nTotal fetch calls this run: {fetch_count}")
    print(f"Total recovered: {len(all_rows)} episode entries")
    by_year: dict[str, int] = {}
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
