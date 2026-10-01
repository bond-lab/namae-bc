# Data: Sources and Cleaning

This directory contains the raw and intermediate data used to build the
database.  See [ATTRIBUTIONS.md](../ATTRIBUTIONS.md) for copyright and
licensing, and [data/download/](download/) for ready-to-use TSV exports.

---

## Baby Calendar (bc) — 2008-2025

### Hand-collected data: 2008-2022

**Raw file:** `jmena 2008-2022.xlsx`

An Excel workbook with one sheet per gender, cut and pasted from
<https://baby-calendar.jp/> by Ivona Barešová.

**Cleaning applied:**

- Extracted columns: year, orthography (kanji), pronunciation
  (hiragana), location, gender, explanation.
- 17 names were excluded from the original data.
- One name was changed from boy to girl based on its name selection
  story.
- Hand correction: 2016 — 望月蓮(れん) → 蓮(れん).
- Frequencies and ranks were computed by aggregating the token-level
  records into counts per name per year per gender.  Ties are broken
  arbitrarily by `ROW_NUMBER()`.

### Scraped rankings: 2023-2025

**Raw file:** `raw/baby_calendar_rankings.tsv`
**Script:** `scripts/scrape_baby_calendar.py`

Annual top-name rankings scraped from the live site.  Covers
2010-2025 (top-10 for 2010-2019; top-100 for 2020-2025), but only
2023-2025 rows are loaded into the database — the 2010-2022 records
are superseded by the hand-collected Excel data.

Columns: `year`, `gender`, `rank`, `orth`, `pron_raw`, `freq`,
`prev_rank`, `url`, `src`.

Multiple readings per name are stored as a comma-separated list in
`pron_raw`; only the first reading is used when importing into `nrank`.

**Sources by year range:**
- 2010-2014: `/knowledge/pregnancy/` annual pages
- 2015-2019: `/special/name/` pages
- 2020-2023: `/nazuke/` structured pages
- 2024-2025: SmileNews article pages

### Naming episode stories: 2017-2023 (live site)

**Raw file:** `raw/baby_calendar_nazuke_episodes.tsv`
**Script:** `scripts/scrape_baby_calendar_nazuke.py`

One row per naming story (*名づけエピソード*) from the sound-row
episode pages at `/knowledge/common/{ID}`.  Pages are cached in
`raw/page_cache/bc_episode_{ID}.html`; re-running the scraper uses
the cache and makes no network requests.

Columns: `year`, `gender`, `sound_row`, `orth`, `pron`, `episode`,
`script`, `page_type`, `url`, `src`.

Coverage: 5,970 entries across 2017-2023.  Missing pages: 2018 M
わ行 (ID 1295, never published); 2020 F わ行, 2021 F わ行, 2022 M
わ行 (not published for those years).

**Note on site editing:** Baby Calendar silently replaces or removes
episode entries over time.  The scraped data reflects the current live
state (2026); the hand-collected data (Ivona, 2022) is a point-in-time
snapshot.  For 2020-2022, approximately 87 entries present in the
hand-collected data are no longer on the live site (replaced with
different entries ~50, removed ~16, reading or kanji corrected ~21).
See `paper-namae-dataset/notes/nazuke-episode-comparison.md`.

### Naming episode stories: 2017-2019 (Wayback Machine archive)

**Raw file:** `raw/baby_calendar_nazuke_episodes_archive.tsv`
**Script:** `scripts/scrape_baby_calendar_nazuke_archive.py`

Episodes recovered from archive.org snapshots, used as a
reproducibility cross-check against the hand-collected data and to
cover any pages since removed from the live site.

Columns: `year`, `gender`, `sound_row`, `orth`, `pron`, `episode`,
`script`, `archive_ts`, `archive_url`, `src`.

Coverage (4,341 unique entries after deduplication):
- 2017: 1,692 entries, 10/10 sound rows
- 2018: 1,234 entries, 9/10 sound rows (M わ行 was never published)
- 2019: 1,415 entries, 9/10 sound rows (F あ行 not yet fetched from archive)

Episode text is identical to the hand-collected data where both
sources have the same name, confirming data integrity.

---

## Heisei Namae Jiten (hs) — 1989-2009

**Raw files:** `heisei/boy/h01.txt` … `h21.txt`, `heisei/girl/h01.txt` … `h21.txt`

Plain-text files, one per year per gender (h01 = Heisei 1 = 1989),
with lines of the form `rank\tname\tfrequency`.  Downloaded from
<https://www.namaejiten.com/>.

**Cleaning applied:**

- Character normalization mapped variant kanji to modern standard forms:
  - Dash variants (―, －, -, ‐) → ー (katakana prolonged sound mark)
  - 晴→晴, 昻→昂, 煕→熙, 晧→皓, 逹→達, 瑤→瑶, 翆→翠, 桒→桑, 莱→萊
- Names were validated against the set of kanji permitted in Japanese
  given names (jōyō kanji + jinmeiyō kanji + iteration mark 々) and hiragana and katakana.
  239 names using non-permissible characters were excluded
  (e.g. 昻樹, Ｊ映美, すた～ら, 花菜＆太一).
- Names longer than 4 characters consisting entirely of kanji were
  treated as full names rather than given names and excluded.

---

## Meiji Yasuda Life Insurance (meiji) — 1912-2025

**Raw files:**
- `meiji_yasuda_data/processed/combined_rankings.csv` — from the
  Meiji Yasuda API, queried using `get-meiji.py`
- `meiji.xlsx` — supplementary data from PDFs (includes 2013
  frequencies)
- `meiji_total_year.tsv` — annual survey totals

Downloaded from <https://www.meijiyasuda.co.jp/enjoy/ranking/>.

**Coverage:**

- **1912-2003:** Top 10 written forms only, no frequencies.
- **2004-2025 orthography:** Top 100 written forms with frequencies.
- **2004-2025 pronunciation:** Top 50 pronunciations with frequencies.

**Cleaning applied:**

- Combined API data and PDFs into a single CSV.
- Readings were originally in katakana; converted to hiragana using
  `jaconv.kata2hira()`.
- Frequencies for 2013 orthography rankings were missing from the API
  and were supplemented from the Excel sheet (sourced from PDFs).
- The website does not show survey sizes for most years; these were
  taken from PDFs or from Ogihara (2020):

  > Ogihara, Y. (2020). Baby names in Japan, 2004-2018: Common
  > writings and their readings. *BMC Research Notes*, 13, 553.
  > <https://doi.org/10.1186/s13104-020-05409-3>

  See also Ogihara (2025), Baby names in Japan, 2019-2024,
  DOI [10.17605/OSF.IO/BQUJN](https://doi.org/10.17605/OSF.IO/BQUJN)
  (does not include survey sizes).

- The 2025 survey total in `meiji_total_year.tsv` is taken from the
  official press-release PDF (`press_releases/meiji_names_2025.pdf`,
  published 2025/12/10): male 6,312, female 6,193, total 12,505.

---

## Benesse/Tamahiyo (benesse) — 2018-2025

**Raw file:** `raw/benesse_rankings.tsv`
**Script:** `scripts/scrape_benesse.py`

Annual top-100 name rankings from Benesse Corporation's parenting
magazine *Tamahiyo*, scraped from
<https://st.benesse.ne.jp/ninshin/name/>.

Columns: `year`, `gender`, `rank`, `orth`, `pron`, `freq`, `pct`,
`prev_rank`, `url`, `src`.

1,628 rows covering 2018-2025.  Frequency counts (`freq`, `pct`) are
only available for 2018; the methodology changed in 2019 (sample size
approximately doubled) and counts were discontinued.

**Cleaning applied:**

- Only the first table per page is used (each page has three tables:
  name ranking, reading ranking, kanji ranking).
- Readings extracted from `<span class="yomi">`, `<br/>` split, or
  space-separated "漢字 よみ" format depending on year.
- Dedup key is `(rank, orth, pron, gender)` to preserve tied ranks.

---

## Akachan Honpo (akachan) — 2018-2025

**Raw file:** `raw/akachan_rankings.tsv`
**Script:** `scripts/scrape_akachan.py`

Annual name rankings from Akachan Honpo (赤ちゃん本舗), a baby goods
retailer, scraped from <https://www.akachan.jp/maternity/ranking/>.

Columns: `year`, `gender`, `rank`, `orth`, `pron`, `prev_rank`,
`sample_n`, `url`, `src`.

798 rows covering 2018-2025.  No frequency counts; sample sizes
declined from ~30,000-80,000 (2018-2021, loyalty-programme
registrations) to ~6,000 (2022+, internet survey).  Top-100 for
2018-2020; top-10 to top-30 for 2021+ after the site discontinued
full rankings.

**Cleaning applied:**

- Rank cell is `<th>` not `<td>` on this site; parser uses
  `find_all(["th","td"])`.
- 2021 uses a fallback to the main year page (sub-pages return 404).
- Rows with `rank > 500` are dropped (stray table headers).

---

## Japanese Birth Data (bd) — 1873-2023

**Raw file:** `live_births_year.tsv`

Annual live births by gender from the National Institute of Population
and Social Security Research (IPSS), table 04-01:
<https://www.ipss.go.jp/p-info/e/psj2023/PSJ2023-04.xls>

Updated with 2022-2023 data from e-Stat.

Used for normalizing name frequencies against total births.

---

## What Counts as a Valid Name

### Allowed characters

A Japanese given name may be written with:

- **Jōyō kanji** (常用漢字) — 2,136 characters
- **Jinmeiyō kanji** (人名用漢字) — 863 characters
- **Iteration mark** 々
- **Hiragana** and **katakana**

The allowed kanji are listed in `scripts/kanji.yaml` (jōyō + jinmeiyō +
iterator).  This matches the characters permitted by Japanese law for
registering given names.

### Validation during build

| Source | Script | Rules |
|--------|--------|-------|
| Baby Calendar (2008-2022) | `scripts/add-baby-calendar.py` | No automated validation; data was manually curated before import. |
| Baby Calendar (2023-2025) | `scripts/add-bc-scraped.py` | Only years not already in database are added. Multiple readings stored as first reading only. |
| Heisei | `scripts/add-heisei.py` | Each character must be an allowed kanji, hiragana, or katakana. Names longer than 4 characters consisting entirely of kanji are treated as full names (family + given) and excluded. Variant kanji are mapped to standard forms before validation (e.g. 昻→昂, 逹→達). 239 names were excluded. |
| Meiji Yasuda | `scripts/add-meiji-api.py` | No character validation (pre-processed API data). Katakana pronunciations are converted to hiragana with `jaconv.kata2hira()`. |
| Benesse | `scripts/add-benesse.py` | No character validation. First reading used when multiple readings present. |
| Akachan Honpo | `scripts/add-akachan.py` | No character validation. Rows with rank > 500 dropped (stray headers). |

### Validation in the web interface

The web interface validates user search input before querying the database:

| Input | Route | Rule |
|-------|-------|------|
| Pronunciation (読み方) | `/namae` | Must be entirely hiragana. |
| Orthography (書き方) | `/namae` | Must contain at least one Japanese character (kanji, hiragana, or katakana). |
| Kanji lookup | `/kanji` | Must be exactly one kanji character. |

Invalid input returns the search page with an error message rather than
a server error.
