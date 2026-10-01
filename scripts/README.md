# Scripts

This directory contains all Python scripts for building the database,
running analysis, generating figures, and scraping source data.

Quick orientation: **build first, then analyse, then publish.**

```
scrape → add-* → calculate-features → calc_* → pub-* / plot_*
```

---

## Build pipeline (run in order)

These scripts populate the database from raw data files.  Run them once
after a clean checkout, or after updating a source file.

| Script | What it does | Input | Output |
|--------|-------------|-------|--------|
| `add-baby-calendar.py` | Load hand-collected BC data 2008–2022 | `data/jmena 2008-2022.xlsx` | `namae` table |
| `add-bc-scraped.py` | Extend BC with scraped rankings 2023–2025 | `data/raw/baby_calendar_rankings.tsv` | `nrank`, `name_year_cache` |
| `add-heisei.py` | Load Heisei Namae Jiten 1989–2009 | `data/heisei/` TXT files | `namae`, `nrank`, `name_year_cache` |
| `add-meiji-api.py` | Load Meiji Yasuda rankings 1912–2025 from API CSV | `data/meiji_yasuda_data/processed/combined_rankings.csv` | `nrank`, `name_year_cache` |
| `add-meiji.py` | Supplement Meiji from Excel/PDF data (2013 freq patch) | `data/meiji.xlsx` | `nrank`, `name_year_cache` |
| `add-benesse.py` | Load Benesse/Tamahiyo rankings 2018–2025 | `data/raw/benesse_rankings.tsv` | `nrank`, `name_year_cache` |
| `add-akachan.py` | Load Akachan Honpo rankings 2018–2025 | `data/raw/akachan_rankings.tsv` | `nrank`, `name_year_cache` |
| `add-births.py` | Store annual live birth counts | `data/live_births_year.tsv` | `name_year_cache` |
| `add-kanji.py` | Populate kanji metadata table | `namae` table + `kanji.yaml` | `kanji` table |
| `calculate-features.py` | Annotate names with script, length, mora, syllable features | `namae.db` | `attr` table |
| `calc_feat_uniq.py` | Cache unique orth/pron features (run after calculate-features) | `namae.db` | derived feature tables |

The full build sequence is orchestrated by `../makedb.sh`.

---

## Scraping scripts

Fetch raw data from the web.  Run these only when source sites need
refreshing.  All outputs land in `data/raw/`.

| Script | Source | Output |
|--------|--------|--------|
| `scrape_baby_calendar.py` | baby-calendar.jp annual rankings (2010–2025) | `baby_calendar_rankings.tsv` |
| `scrape_baby_calendar_nazuke.py` | BC sound-row episode pages, live site (2017–2023) | `baby_calendar_nazuke_episodes.tsv` |
| `scrape_baby_calendar_nazuke_archive.py` | BC episode pages recovered from Wayback Machine (2017–2019) | `baby_calendar_nazuke_episodes_archive.tsv` |
| `scrape_baby_calendar_archive.py` | BC rankings 2010–2019 via Wayback Machine CDX API | `baby_calendar_rankings_archive.tsv` |
| `scrape_baby_calendar_episodes.py` | BC naming commentary and general episode pages | `baby_calendar_commentary.tsv`, `baby_calendar_episodes.tsv` |
| `scrape_benesse.py` | Benesse/Tamahiyo st.benesse.ne.jp (2018–2025) | `benesse_rankings.tsv` |
| `scrape_akachan.py` | Akachan Honpo akachan.jp (2018–2025) | `akachan_rankings.tsv` |
| `fetch_episode_page_cache.py` | Pre-download and cache BC episode pages locally | `page_cache/bc_episode_*.html` |

**Rate limiting**: The Wayback Machine scrapers throttle to ≤1 req/5 s
and cap each run at 40 fetches (`MAX_FETCHES`) to avoid IP blocks.
Re-run on subsequent days to fill remaining gaps.  The live-site episode
scraper reads from `page_cache/` when available — run
`fetch_episode_page_cache.py` once before developing or testing the parser.

---

## Pre-computation scripts (web app)

These scripts pre-compute data for the web interface.  Run after any
database change.  Outputs go to `../web/static/data/`.

| Script | Output file | Used by |
|--------|-------------|---------|
| `calc_names_json.py` | `names_<src>.json.gz` | Names page |
| `calc_stats_json.py` | `stats_data.json` | Stats page |
| `calc_features_json.py` | `features_data.json` | Features page |
| `calc_overlap_json.py` | `overlap_data.json` | Overlap page |
| `calc_irregular_json.py` | `irregular_data.json` | Irregularity page |
| `calc_androgyny.py` | `androgyny_data.json` | Androgyny page |
| `calc_topnames.py` | `topnames_data.json` | Top names page |
| `calc_gender.py` | JSON (configurable) | Gender prediction |
| `calc_regular.py` | regularity data | Kanji reading regularity |
| `export_tsv.py` | `data/download/*.tsv` | Download page and Zenodo release |

---

## Analysis and publication scripts

Scripts that generate figures and tables for the book and paper.  Outputs
go to `../book/` (PNG+SVG) and `../web/static/plot/` (PNG).  Tables are
written to `../web/static/data/book_tables.json`.

| Script | What it produces |
|--------|-----------------|
| `pub-agreement.py` | Meiji vs Heisei and Meiji vs BC: JS divergence + common names plots |
| `pub-agreement-new-sources.py` | Benesse and Akachan vs Meiji/BC/each other: JS divergence + common names |
| `pub-tables.py` | Summary tables for book chapters (source coverage, counts) |
| `pub-years.py` | Coverage timeline figure (sample sizes vs births) |
| `plot_diversity.py` | Name diversity trends (Shannon entropy, Gini-Simpson, type-token ratio) |
| `plot_meiji.py` | Meiji Yasuda long-run trends (Berger-Parker, concentration) |
| `plot_overlap.py` | Male/female name overlap over time per source |
| `plot_proportion.py` | Proportion of children with gender-ambiguous names |
| `plot_kanji_position.py` | Kanji position distribution in names (initial/middle/final) |
| `plot_web_charts.py` | Matplotlib reproductions of web D3 charts for publication |
| `plot-years.py` | Bar charts of name counts per year by gender |
| `build_book_figures.py` | Master script: generates all publication figures |

---

## Library modules (not run directly)

| Module | Purpose |
|--------|---------|
| `db.py` | Database query functions used by the web app (`get_overlap`, `get_stats`, etc.) |
| `utils.py` | Japanese text utilities: script detection, mora/syllable counting |
| `settings.py` | Flask/web configuration: database options, feature definitions |
| `visualize.py` | Matplotlib helpers: multi-panel trend plots, Tufte-style setup |
| `bw_style.py` | Black-and-white style constants for publication figures |

---

## Refactoring notes

The scripts grew organically and some consolidation would help.
Issues worth addressing before the paper release:

1. **Duplicate parser logic**: `scrape_baby_calendar_nazuke.py` and
   `scrape_baby_calendar_nazuke_archive.py` share `clean_orth()`,
   `_script()`, `parse_episode_page()`, and the entry regex.
   Extract these to a shared `scrape_utils.py`.

2. **Two overlap scripts**: `plot_overlap.py` and `calc_overlap_json.py`
   both compute M/F name overlap with independent SQL.  The web version
   (`calc_overlap_json.py`) uses `db.py`'s `get_overlap()`; the
   standalone script (`plot_overlap.py`) reimplements it.  Could be
   unified around `db.py`.

3. **Two Meiji loaders**: `add-meiji-api.py` loads the main API CSV;
   `add-meiji.py` handles supplementary Excel/PDF data.  Their split
   responsibility is undocumented in the headers — worth a note.

4. **Confusing archive names**: `scrape_baby_calendar_archive.py` archives
   *rankings*; `scrape_baby_calendar_nazuke_archive.py` archives *episode
   stories*.  Consider renaming the former to
   `scrape_baby_calendar_rankings_archive.py`.

5. **`calculate-features.py` vs `calc_feat_uniq.py`**: Both operate on
   derived name features but at different granularities.  Their dependency
   order should be explicit in `makedb.sh`.
