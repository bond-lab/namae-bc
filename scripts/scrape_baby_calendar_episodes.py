#!/usr/bin/env python3
"""
Scrape Baby Calendar naming commentary and user episode stories.

Two sources:
1. Editorial commentary from annual ranking articles (2020-2025)
   - Top-3 trend summaries and analysis paragraphs per year
2. User naming experience posts from /knowledge/pregnancy/488
   - Free-text submissions; not linked to specific names

Output: data/raw/baby_calendar_commentary.tsv  (editorial, by year)
        data/raw/baby_calendar_episodes.tsv    (user stories, unstructured)

Note: Per-name naming stories ("explanation" column in original hand-collected
bc data, 2008-2022) came from the original submission form and are not
available from the current ranking pages or the public website.
"""

import csv
import re
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup

BASE = "https://baby-calendar.jp"
HEADERS = {"User-Agent": "Mozilla/5.0 (research scraper; namae-bc project; contact: bond@ieee.org)"}
DELAY = 1.5

OUT_COMMENTARY = Path(__file__).parent.parent / "data" / "raw" / "baby_calendar_commentary.tsv"
OUT_EPISODES   = Path(__file__).parent.parent / "data" / "raw" / "baby_calendar_episodes.tsv"

# URLs for annual ranking articles (same as used in rankings scraper)
RANKING_URLS = {
    2023: f"{BASE}/nazuke/nameranking2023",
    2022: f"{BASE}/nazuke/nameranking2022",
    2021: f"{BASE}/nazuke/nameranking2021",
    2020: f"{BASE}/nazuke/nameranking2020",
    2024: f"{BASE}/smilenews/detail/71825",
    2025: f"{BASE}/smilenews/detail/100184",
}


def get_soup(url: str) -> BeautifulSoup:
    resp = requests.get(url, headers=HEADERS, timeout=20)
    resp.raise_for_status()
    resp.encoding = "utf-8"
    time.sleep(DELAY)
    return BeautifulSoup(resp.text, "html.parser")


def scrape_commentary() -> list[dict]:
    """Extract editorial paragraphs from annual ranking articles."""
    rows = []
    for year, url in sorted(RANKING_URLS.items()):
        print(f"  Commentary {year}...")
        try:
            soup = get_soup(url)
        except requests.HTTPError as e:
            print(f"    Error: {e}")
            continue

        paras = []
        for p in soup.find_all("p"):
            txt = p.get_text(" ", strip=True)
            # Keep substantive paragraphs (>30 chars) that mention names or trends
            if len(txt) > 30 and not txt.startswith(("©", "Cookie", "https://")):
                paras.append(txt)

        for i, para in enumerate(paras):
            rows.append({
                "year": year,
                "seq": i + 1,
                "text": para,
                "url": url,
                "src": "bc",
            })
        print(f"    {len(paras)} paragraphs")
    return rows


def scrape_user_episodes(max_pages: int = 5) -> list[dict]:
    """
    Scrape user naming experience stories from /knowledge/pregnancy/488.
    These are free-text submissions about naming decisions, not tied to specific names.
    """
    base_url = f"{BASE}/knowledge/pregnancy/488"
    rows = []

    for page in range(1, max_pages + 1):
        url = f"{base_url}?page={page}" if page > 1 else base_url
        try:
            soup = get_soup(url)
        except requests.HTTPError as e:
            print(f"    Page {page} error: {e}")
            break

        # Find experience posts
        posts_found = 0
        for elem in soup.find_all(["article", "div", "section"]):
            cls = " ".join(elem.get("class", []))
            if not any(kw in cls for kw in ["experience", "story", "post", "comment", "体験"]):
                continue
            txt = elem.get_text(" ", strip=True)
            if len(txt) > 50:
                # Try to find author
                author_elem = elem.find(class_=re.compile("author|name|user"))
                author = author_elem.get_text(strip=True) if author_elem else ""
                rows.append({
                    "page": page,
                    "seq": len(rows) + 1,
                    "text": txt[:2000],
                    "author": author,
                    "url": url,
                    "src": "bc",
                })
                posts_found += 1

        if posts_found == 0:
            # Try a broader approach
            for p in soup.find_all("p"):
                txt = p.get_text(" ", strip=True)
                if len(txt) > 100 and ("名前" in txt or "名付" in txt or "命名" in txt):
                    rows.append({
                        "page": page,
                        "seq": len(rows) + 1,
                        "text": txt[:2000],
                        "author": "",
                        "url": url,
                        "src": "bc",
                    })
                    posts_found += 1
                    if posts_found > 20:
                        break

        print(f"    Page {page}: {posts_found} posts")
        if posts_found == 0:
            break

    return rows


def write_tsv(rows: list[dict], path: Path, fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t",
                                extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    print(f"  Written {len(rows)} rows to {path}")


def main():
    print("Scraping editorial commentary...")
    commentary = scrape_commentary()
    write_tsv(commentary, OUT_COMMENTARY, ["year", "seq", "text", "url", "src"])

    print("\nScraping user naming episodes...")
    episodes = scrape_user_episodes(max_pages=3)
    write_tsv(episodes, OUT_EPISODES, ["page", "seq", "text", "author", "url", "src"])


if __name__ == "__main__":
    main()
