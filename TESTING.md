# Testing Guide

## Automated Tests (pytest)

The test suite lives in `tests/` and runs against the real database
(`web/db/namae.db`).  Build the DB first (`bash makedb.sh db`) if you
haven't already.

```bash
# Run everything (~60s — includes slow performance tests)
.venv/bin/python -m pytest tests/ -v

# Fast subset only (~45s — skip @pytest.mark.slow)
.venv/bin/python -m pytest tests/ -m "not slow" -v

# Single file
.venv/bin/python -m pytest tests/test_routes.py -v
```

Current counts: **359 tests total** — 193 non-slow (~45 s), 166 slow (~60 s total).

### Test files

| File | What it covers |
|------|---------------|
| `conftest.py` | Shared fixtures: `app`, `client` (session-scoped), `client_fresh` (per-test) |
| `test_utils.py` | Pure-Python helpers: `hira2roma`, `whichScript`, `mora_hiragana`, `syllable_hiragana`, `expand_r` |
| `test_routes.py` | HTTP route tests — every endpoint, all 4 models, all search types |
| `test_content.py` | Data correctness — search returns expected content, session switching, error handling |
| `test_performance.py` | Response-time limits for every route × model (`@pytest.mark.slow`) |

---

### `test_routes.py` — route coverage map

#### Static / universal pages

| Class | What it tests |
|-------|--------------|
| `TestHome` | GET and POST on `/` |
| `TestDocs` | All `/docs/*.html` pages |
| `TestBook` | `/book` page |
| `TestSettings` | GET/POST `/settings`; palette and db_option switching |
| `TestNavigation` | Phenomena nav tabs appear on all phenomena pages |

#### Name search

| Class | What it tests |
|-------|--------------|
| `TestNameSearch` | Basic orth, pron, combined search on default (bc); invalid inputs |
| `TestNameSearchAllModels` | All 4 models × all search types; graceful failure when unsupported type used |

**When adding a new source:** add it to `DB_CAPS` at the top of `test_routes.py`
and the parametrized tests will pick it up automatically.

#### Kanji search

| Class | What it tests |
|-------|--------------|
| `TestKanjiSearch` | Single-kanji lookup, multi-char rejection, GLOB injection, names list |
| `TestKanjiSearchAllModels` | Kanji on all orth-supporting models; graceful on pron-only model; `'` injection |

#### DB-dependent pages

| Class | What it tests |
|-------|--------------|
| `TestNames` | `/names.html` skeleton |
| `TestStats` | `/stats.html` |
| `TestYears` | `/years.html` |
| `TestFeatures` | `/features.html` — redirect, char1, last_char, two features |
| `test_model_page_all_dbs` | `/names.html`, `/stats.html`, `/years.html` × all 4 models (`@slow`) |

#### Phenomena pages

| Class | What it tests |
|-------|--------------|
| `TestRedup` | `/phenomena/redup.html` |
| `TestJinmei` | `/phenomena/jinmeiyou.html` |
| `TestProportion` | `/phenomena/proportion.html` |
| `TestIrregular` | `/irregular.html` |
| `TestGenderedness` | `/genderedness.html` |
| `TestDiversity` | `/phenomena/diversity.html` |
| `TestOverlap` | `/overlap.html`; datasets present |
| `TestAndrogyny` | `/phenomena/androgyny.html`; datasets present |
| `TestTopNames` | `/phenomena/topnames.html`; all sources, both genders, top-50 variant |
| `test_universal_page_all_models` | All universal pages × all 4 models (`@slow`) |
| `test_irregular_all_models` | `/irregular.html` × all 4 models (`@slow`) |

**When adding a new phenomenon page:**
1. Add the URL to `_UNIVERSAL_PAGES` in `test_routes.py` for automatic
   per-model coverage.
2. Add a `TestMyPhenomenon` class with content checks specific to that page.
3. Add a time limit in `test_performance.py` under `test_static_routes`.

#### Features

| Test | What it covers |
|------|---------------|
| `test_feature_all_combos` | Every feature × every compatible DB (`@slow`) |
| `test_overall_all_combos` | Every overall feature × every compatible DB (`@slow`) |

**When adding a new feature or overall measure:** update `web/settings.py`.
The parametrized tests expand automatically from `features` and `overall`.

#### Downloads

| Class | What it tests |
|-------|--------------|
| `TestDownload` | Valid TSV download; nonexistent file returns 404 |

---

### `test_content.py` — data correctness map

| Class | What it tests |
|-------|--------------|
| `TestNameSearchContent` | Search for known names returns expected data; unknown names handled |
| `TestKanjiSearchContent` | Kanji page returns chart data; unknown kanji handled gracefully |
| `TestInputEdgeCases` | Katakana pron rejected; very long inputs; emoji rejected |
| `TestErrorHandling` | 404 on nonexistent routes; bad feature name; path traversal on download |
| `TestSessionEffects` | Default source is bc; switching source changes name/kanji results; color palette |
| `TestOverlapContent` | Overlap page has names data |
| `TestAndrogynyContent` | Multiple sources present; proportions in valid range |
| `TestDiversityContent` | Source sections present |

---

### `test_performance.py` — time limits

All tests are `@pytest.mark.slow`.  Each parametrization switches the DB
then measures wall-clock response time.

| Test | Route | Limit |
|------|-------|-------|
| `test_static_routes` | Home, all phenomena pages | 2–8 s |
| `test_stats_page` | `/stats.html` × all DBs | 10 s |
| `test_names_page` | `/names.html` × all DBs | 2 s |
| `test_names_api` | `/api/names.json` × all DBs | 25 s |
| `test_years_page` | `/years.html` × all DBs | 5 s |
| `test_irregular_page` | `/irregular.html` × all DBs | 10 s |
| `test_kanji_page` | `/kanji?kanji=美` × all DBs | 5 s |
| `test_feature_page` | `/features.html` × all features × all DBs | 10 s |
| `test_overall_page` | `/features.html` × all overall × all DBs | 10 s |

---

## Manual / Integration Testing

### Prerequisites

- Python 3.9+, `uv`, `sqlite3` command-line tool

### 1. Clone and check key files

```bash
git clone <repo-url> namae-bc-test
cd namae-bc-test
ls .zenodo.json CITATION.cff ATTRIBUTIONS.md README.md LICENSE
ls data/download/*.tsv
ls .github/workflows/release-data.yml
ls scripts/export_tsv.py
```

### 2. Validate metadata

```bash
python -c "import json; json.load(open('.zenodo.json')); print('OK')"
python -c "import yaml; yaml.safe_load(open('CITATION.cff')); print('OK')"
```

Check by eye:
- ORCID `0000-0003-4973-8068` in both `.zenodo.json` and `CITATION.cff`
- No duplicate affiliation lines in `CITATION.cff`
- No FIXME/placeholder text in `.zenodo.json` description

### 3. Build the database

```bash
bash makedb.sh db
```

Expected output: `=== Database build complete ===`

Verify:

```bash
sqlite3 web/db/namae.db "SELECT src, COUNT(*) FROM namae GROUP BY src;"
# bc ~15k, hs ~14.5M, meiji ~154k

sqlite3 web/db/namae.db "SELECT src, COUNT(*) FROM nrank GROUP BY src;"
# bc ~21k, hs ~1.5M, meiji ~9k

sqlite3 web/db/namae.db ".indexes"
# Should list idx_namae_*, idx_nrank_*, idx_attr_*, idx_ntok_*, idx_mapp_*, idx_kanji_*

wc -l data/download/*.tsv
# Expected (including headers):
#   21,307  baby_calendar_names.tsv
#   13,539  baby_calendar_names_both.tsv
#  1,512,880  heisei_names.tsv
#    8,968  meiji_yasuda_names.tsv
#       43  meiji_yasuda_totals.tsv
#      297  live_births.tsv
```

### 4. Run the analysis phase

```bash
bash makedb.sh analysis
```

Expected output: `=== Analysis complete ===`

Verify:

```bash
ls web/static/plot/diversity_*.png | wc -l   # ~20+
ls web/static/data/*.json | wc -l            # ~10+
ls web/static/plot/proportion_*.svg | wc -l  # 9
```

### 5. Run analysis without DB (should fail)

```bash
mv web/db/namae.db web/db/namae.db.tmp
bash makedb.sh analysis
# Should print: ERROR: web/db/namae.db not found...
echo $?   # should be 1
mv web/db/namae.db.tmp web/db/namae.db
```

### 6. Manual smoke test of the web app

```bash
bash run.sh
```

Open http://127.0.0.1:5000/ and verify:

- **Index** — "Japanese Name Database", three data sources, "What You Can Do" section
- **Search (bc)** — search 翔 (orth) → year chart appears; はると (pron) → results appear
- **Search (hs)** — 書き方 input visible, 読み方 input hidden (pron not supported)
- **Search (meiji_p)** — only 読み方 input visible, kanji form hidden
- **Names** — browse list, sorting works
- **Settings** — switch bc/hs/meiji/meiji_p, pages update
- **Phenomena > Diversity** — SVG plots inline
- **Phenomena > Proportion** — U-shaped histogram tabs (Full name / Pronunciation / Orthography)
- **Phenomena > Irregular** — loads with regression chart
- **By Year** — year trend graphs load
- **Kanji search** — search 美, see position chart and names list with links

### 7. Test the TSV export independently

```bash
rm data/download/*.tsv
python scripts/export_tsv.py
ls data/download/*.tsv   # all 6 files should be back

head -3 data/download/baby_calendar_names.tsv
# year<tab>orth<tab>pron<tab>rank<tab>gender<tab>freq

head -3 data/download/heisei_names.tsv
# year<tab>orth<tab>rank<tab>gender<tab>freq (no pron column)
```

### 8. Test the release archive assembly (local dry run)

```bash
mkdir -p release/namae-data
cp data/download/*.tsv release/namae-data/
cp data/download/README.md release/namae-data/
cp data/README.md release/namae-data/DATA.md
cp ATTRIBUTIONS.md release/namae-data/

tar czf release/namae-data-test.tar.gz -C release namae-data/
tar tzf release/namae-data-test.tar.gz
# namae-data/ATTRIBUTIONS.md, namae-data/DATA.md, namae-data/README.md, all 6 .tsv files

rm -rf release
```

### 9. Documentation cross-references

- `ATTRIBUTIONS.md` links to `data/README.md` — should exist
- `data/README.md` links to `../ATTRIBUTIONS.md` and `download/` — should exist
- `README.md` links to `ATTRIBUTIONS.md`, `DATABASE.md`, `Install.md`,
  `CITATION.cff`, `data/download/README.md` — all should exist

## Known issues

See `ISSUES.md`.
