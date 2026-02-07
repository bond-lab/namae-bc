# Testing Guide — Clean Checkout

## Prerequisites

- Python 3.8+
- `uv` (for venv management in makedb.sh) or plain `pip`
- `sqlite3` command-line tool

## 1. Clone and basic checks

```bash
git clone <repo-url> namae-bc-test
cd namae-bc-test
```

Verify key files exist:

```bash
ls .zenodo.json CITATION.cff ATTRIBUTIONS.md README.md LICENSE
ls data/download/*.tsv
ls .github/workflows/release-data.yml
ls scripts/export_tsv.py
```

## 2. Validate metadata files

```bash
# .zenodo.json must be valid JSON
python -c "import json; json.load(open('.zenodo.json')); print('OK')"

# CITATION.cff should parse as valid YAML
python -c "import yaml; yaml.safe_load(open('CITATION.cff')); print('OK')"
```

Check by eye:
- ORCID in `.zenodo.json` and `CITATION.cff` should both be `0000-0003-4973-8068` for Bond
- No duplicate affiliation lines in `CITATION.cff`
- No FIXME/placeholder text in `.zenodo.json` description

## 3. Build the database only

```bash
bash makedb.sh db
```

This should:
- Create `.venv-build/` and install dependencies
- Build `scripts/namae.db`, copy to `web/db/namae.db`
- Add indexes
- Export TSVs to `data/download/`
- Print `=== Database build complete ===` at the end

Verify:

```bash
# Database exists and has data
sqlite3 web/db/namae.db "SELECT src, COUNT(*) FROM namae GROUP BY src;"
# Expected: bc ~15k, hs ~14.5M, meiji ~154k

sqlite3 web/db/namae.db "SELECT src, COUNT(*) FROM nrank GROUP BY src;"
# Expected: bc ~21k, hs ~1.5M, meiji ~9k

# Indexes were created
sqlite3 web/db/namae.db ".indexes"
# Should list idx_namae_*, idx_nrank_*, idx_attr_*, idx_ntok_*, idx_mapp_*, idx_kanji_*

# TSV files were exported
wc -l data/download/*.tsv
# Expected (including headers):
#   21,307  baby_calendar_names.tsv
#   13,539  baby_calendar_names_both.tsv
#  1,512,880  heisei_names.tsv
#    8,968  meiji_yasuda_names.tsv
#       43  meiji_yasuda_totals.tsv
#      297  live_births.tsv
```

## 4. Run the analysis phase

```bash
bash makedb.sh analysis
```

This should:
- Print `=== Analysis complete ===` at the end
- Generate/update PNG plots in `web/static/plot/`
- Generate/update JSON data in `web/static/data/`

Verify:

```bash
ls web/static/plot/diversity_*.png | wc -l   # should be ~20+
ls web/static/data/*.json | wc -l            # should be ~7+
```

## 5. Run analysis without DB (should fail)

```bash
# Move the DB aside temporarily
mv web/db/namae.db web/db/namae.db.tmp
bash makedb.sh analysis
# Should print: ERROR: web/db/namae.db not found...
# and exit with non-zero status
echo $?   # should be 1
mv web/db/namae.db.tmp web/db/namae.db
```

## 6. Test the website

```bash
pip install -r requirements.txt
flask --app web run
```

Then open http://127.0.0.1:5000/ and check:

- **Index page** — should show "Japanese Name Database" with three
  data sources listed (Baby Calendar, Heisei, Meiji Yasuda), a "What
  You Can Do" section, and a references section.
- **Search** — try searching for 翔 (orth) or はると (pron) in the
  nav bar.
- **Names** — browse the name list, check sorting works.
- **Settings** — switch between data sources (bc, hs, meiji) and
  verify pages update.
- **Phenomena > Diversity** — check plots display.
- **Phenomena > Irregular** — check it loads (uses mapp table).
- **By Year** — check year trend graphs load.
- **Footer** — should say "Please provide feedback here:" (no stray
  "on").

## 7. Test the TSV export independently

```bash
# Remove existing exports and re-run
rm data/download/*.tsv
python scripts/export_tsv.py
ls data/download/*.tsv   # all 6 files should be back

# Spot-check contents
head -3 data/download/baby_calendar_names.tsv
# Should show: year<tab>orth<tab>pron<tab>rank<tab>gender<tab>freq

head -3 data/download/baby_calendar_names_both.tsv
# Both orth and pron should be filled on every data row

head -3 data/download/heisei_names.tsv
# Should show: year<tab>orth<tab>rank<tab>gender<tab>freq

head -3 data/download/meiji_yasuda_names.tsv
# 1912 rows should have empty freq

head -3 data/download/live_births.tsv
# Should show: year<tab>gender<tab>count
```

## 8. Test the release archive assembly (local dry run)

This simulates what the GitHub Action does:

```bash
mkdir -p release/namae-data
cp data/download/*.tsv release/namae-data/
cp data/download/README.md release/namae-data/
cp data/README.md release/namae-data/DATA.md
cp ATTRIBUTIONS.md release/namae-data/

tar czf release/namae-data-test.tar.gz -C release namae-data/

# Check the archive
tar tzf release/namae-data-test.tar.gz
# Should list: namae-data/ATTRIBUTIONS.md, namae-data/DATA.md,
#   namae-data/README.md, and all 6 .tsv files

# Clean up
rm -rf release
```

## 9. Documentation cross-references

Check that links between docs are not broken:

- `ATTRIBUTIONS.md` links to `data/README.md` — should exist
- `data/README.md` links to `../ATTRIBUTIONS.md` and `download/` — should exist
- `data/download/README.md` is self-contained (no external links)
- `README.md` links to `ATTRIBUTIONS.md`, `DATABASE.md`, `Install.md`,
  `CITATION.cff`, `data/download/README.md` — all should exist

## 10. Remaining known issues

See `ISSUES.md` for items that are still open:
- Placeholder DOIs (fill in after Zenodo submission)
- Incomplete book citation
- Install.md is server-specific (intentional)
