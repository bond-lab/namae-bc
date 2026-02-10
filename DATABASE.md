Database overview

This project builds and uses a single SQLite database that consolidates Japanese baby-name data from multiple sources. The build pipeline produces
scripts/namae.db and then copies it to web/db/namae.db for use by the web app and analysis scripts.

Primary data sources
- bc (Baby Calendar): Token-level names with orthography and optional reading from an Excel workbook.
- hs (Heisei): Ranked names with frequencies from plain-text files (per gender); validated and normalized.
- meiji (Meiji Yasuda): Ranked orthography-only and reading-only series from a combined CSV/API and an Excel fix-up for 2013.
- births: Annual live-birth totals (for normalization and coverage charts).
- totals (Meiji): Annual male/female totals recorded alongside the Meiji data.

Where the database lives
- Build-time: scripts/namae.db
- Runtime: web/db/namae.db
The build script makedb.sh regenerates the database and copies it to web/db.

Schema summary

Tables
- namae: Token-level observations (one row per observed name instance).
- nrank: Yearly rankings and frequencies (aggregated counts).
- name_year_cache: Cached yearly totals by source/dtype/gender (accelerates queries/plots).
- attr: Derived attributes per token (lengths, boundary chars, morae, syllables, script type).
- kanji: Kanji metadata harvested via Jamdict/Kanjidic.
- ntok: Link table mapping name tokens (nid) to kanji characters (kid).

Views
- combined: Virtual dataset joining Heisei with Baby Calendar (bc years pooled to anchor years for comparison).

Indexes (optional performance)
Defined in scripts/add_indexes.sql:
- namae: idx_namae_src, idx_namae_gender, idx_namae_orth, idx_namae_pron
- attr: idx_attr_nid
- ntok: idx_ntok_nid, idx_ntok_kid
Note: Indexes are created by `makedb.sh` after copying the database to `web/db/`.

How tables are created and populated

Creation
- scripts/tables.sql defines all tables and the combined view.
- scripts/add-baby-calendar.py creates scripts/namae.db (if needed) and executes tables.sql.

namae (token-level names)
Columns
- nid INTEGER PRIMARY KEY
- year INTEGER — observation year
- orth TEXT — written form (kanji/kana)
- pron TEXT — reading in hiragana (nullable)
- loc TEXT — region/location (bc only)
- gender TEXT — 'M' or 'F'
- explanation TEXT — free text (bc only)
- src TEXT — 'bc', 'hs', 'meiji' (for tokens expanded from Meiji nrank), etc.

Population
- Baby Calendar (bc): add-baby-calendar.py reads the Excel workbook and inserts one row per token with orth, optional pron, gender, location, explanation.
- Heisei (hs): add-heisei.py reads ranked text files (boy/girl dirs), normalizes characters (mapping), validates allowed characters (possible()), and inserts
one row per token by repeating the record frequency times.
- Meiji (meiji): add-meiji-api.py inserts ranked rows into nrank first; then update_namae(db, 'meiji') expands those frequencies into namae tokens via a
recursive CTE (one row per token).
  - Meiji readings are converted to hiragana using jaconv.kata2hira.

nrank (yearly rankings and frequencies)
Columns
- nrid INTEGER PRIMARY KEY
- year INTEGER
- orth TEXT — may be NULL for pron-only rankings
- pron TEXT — may be NULL for orth-only rankings (hiragana if present)
- rank INTEGER — 1 is most frequent; tie behavior depends on source/aggregation
- gender TEXT — 'M' or 'F'
- freq INTEGER — frequency (token count)
- src TEXT — 'bc', 'hs', 'meiji', ...

Population
- Baby Calendar (bc): add-baby-calendar.py aggregates tokens to nrank twice:
  - orth-only: pron is NULL. Rank computed with ROW_NUMBER() over COUNT(*) DESC partitioned by year, gender.
  - pron-only: orth is NULL. Same ranking logic.
  Note: ROW_NUMBER() breaks ties arbitrarily; use DENSE_RANK() with deterministic ordering if strict tie handling is desired.
- Heisei (hs): add-heisei.py inserts source-provided ranks and frequencies directly.
- Meiji (meiji): add-meiji-api.py reads combined CSV (orth-only and reading-only series) and inserts rows with rank/freq. add_missing() updates 2013 orth
frequencies from an Excel sheet.

name_year_cache (cached yearly totals)
Columns
- src TEXT — e.g., 'bc', 'hs', 'meiji', 'births', 'totals'
- dtype TEXT — logical facet such as 'orth', 'pron', 'both', 'total', 'birth' (project commonly uses 'orth' for totals)
- year INTEGER
- gender TEXT — 'M' or 'F'
- count INTEGER
Primary key: (src, dtype, year, gender)

Population and usage
- cache_years(db_path, src) computes token counts by year/gender from namae for a given src and stores them here (dtype typically reflects the aggregation
used by the caller).
- add-births.py loads government live-birth totals with src='births' and dtype='orth'.
- add-meiji-api.py inserts Meiji annual totals with src='totals' and dtype='orth'.
This table speeds up yearly trend queries in the web layer and plotting scripts.

attr (derived attributes)
Columns
- nid INTEGER — FK to namae.nid
- olength INTEGER — orth length (characters)
- plength INTEGER — pron length (characters)
- mlength INTEGER — mora count (from web/utils.mora_hiragana)
- slength INTEGER — syllable count (from web/utils.syllable_hiragana)
- char1, char_1, char_2 — first, last, second-to-last characters (orth)
- mora1, mora_1, mora_2 — first, last, second-to-last morae (pron)
- syll1, syll_1, syll_2 — first, last, second-to-last syllables (pron)
- uni_ch TEXT — single-character orth (flag/char)
- script TEXT — 'kata', 'hira', 'kanji', 'mixhira', or 'mixkata' (web/utils.whichScript)

Population
- calculate-features.py iterates over namae and inserts a row per nid computing the above features. It assumes a fresh build to avoid duplicate attr rows.

kanji (kanji metadata)
Columns (from scripts/tables.sql)
- kid INTEGER PRIMARY KEY
- kanji TEXT
- yfrom INTEGER
- grade INTEGER
- freq INTEGER
- imi TEXT
- mean TEXT
- kunyomi TEXT
- onyomi TEXT
- other TEXT
- nanori TEXT
- scount INTEGER

Population
- add-kanji.py scans orth in namae, filters to allowed characters (kanji.yaml: joyo ∪ jinmei ∪ iterator), looks up each unique character via Jamdict/Kanjidic,
and inserts records.
  - kunyomi stored as space-separated strings.
  - onyomi converted to hiragana using jaconv.kata2hira and space-separated.
  - A special entry for 々 (iteration mark) is added.
Note: Some columns (e.g., yfrom, mean) may be empty depending on dictionary data availability.

ntok (name–kanji mapping)
Columns
- nid INTEGER — FK to namae.nid
- kid INTEGER — FK to kanji.kid

Population
- add-kanji.py emits one (nid, kid) per allowed kanji found in each orth string and batch-inserts into ntok.

combined (view)
Definition (see scripts/tables.sql)
- SELECT all rows from namae where src='hs' (unaltered years).
- UNION ALL with rows from namae where src='bc', remapping year:
  - year < 2015 → 2011
  - else → 2019
- The view exposes src='hs+bc' for all rows, enabling aligned comparisons.

Build pipeline

Run from project root:
- makedb.sh orchestrates a clean build, creates a virtual environment, generates the database, and produces plots/tables.
High-level order
1) Initialize DB and tables; ingest Baby Calendar
   - scripts/add-baby-calendar.py "data/jmena 2008-2022.xlsx"
   - Aggregates bc tokens into nrank (orth-only and pron-only) and caches years (cache_years(db, 'bc')).
2) Ingest Heisei
   - scripts/add-heisei.py scripts/namae.db data/heisei
   - Inserts tokens and nrank; caches years for 'hs'.
3) Ingest Meiji
   - scripts/add-meiji-api.py scripts/namae.db data/meiji_yasuda_data/processed/combined_rankings.csv data/meiji_total_year.tsv data/meiji.xlsx
   - Inserts nrank rows, Meiji totals into name_year_cache, patches 2013 frequencies from Excel, expands into namae tokens, caches years for 'meiji'.
4) Ingest births
   - scripts/add-births.py scripts/namae.db
   - Inserts births into name_year_cache and caches years for 'births'.
5) Build kanji tables
   - scripts/add-kanji.py populates kanji and ntok from namae.
6) Compute attributes
   - scripts/calculate-features.py fills attr from web/utils.py functions.
7) Copy DB to web
   - cp scripts/namae.db web/db/namae.db
8) Generate plots/tables
   - Various scripts under scripts/ read web/db/namae.db to produce JSON/plots.

Conventions and notes

- Gender: 'M' for male, 'F' for female.
- Readings (pron): stored in hiragana; upstream katakana are converted via jaconv.
- Source (src): one of 'bc', 'hs', 'meiji', 'births', 'totals'; 'hs+bc' appears only in the combined view.
- Tie handling: bc uses ROW_NUMBER() which breaks ties arbitrarily; consider DENSE_RANK() if you need stable tie treatment.
- Idempotence: makedb.sh moves any existing scripts/namae.db aside (backup) before a rebuild. Individual scripts typically append; prefer a clean rebuild over
re-running single steps on the same DB to avoid duplicates (notably attr).
- Indexing: apply scripts/add_indexes.sql after copying to web/db for faster analytics on large datasets.

Useful commands

- Rebuild from scratch:
  - bash makedb.sh
- Inspect schema:
  - sqlite3 web/db/namae.db ".schema"
- Quick row counts by source:
  - sqlite3 web/db/namae.db "SELECT src, COUNT(*) FROM namae GROUP BY src;"
- Yearly token counts cached (sample):
  - sqlite3 web/db/namae.db "SELECT src, dtype, year, gender, count FROM name_year_cache WHERE src IN ('births','totals') ORDER BY year, gender LIMIT 10;"

External assets

- Input data files referenced in makedb.sh must exist under data/.
- kanji.yaml defines allowed kanji sets used by add-heisei.py (validation) and add-kanji.py (harvesting).
- Jamdict/Kanjidic may download data on first use in add-kanji.py.
