# Data Schema

The database (`web/db/namae.db`, built by `makedb.sh`) contains six tables
and one view. The TSV exports in `data/download/` are derived from `nrank`.

---

## Table: `namae` — token-level observations

One row per observed name instance. For sources with frequency data (hs,
meiji), the record is repeated `freq` times so that aggregate statistics
work without joins.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `nid` | INTEGER PK | No | Auto-increment row ID |
| `year` | INTEGER | No | Year of observation (birth year) |
| `orth` | TEXT | Yes | Written form (kanji/kana); NULL if pron-only record |
| `pron` | TEXT | Yes | Reading in hiragana; NULL if orth-only record |
| `loc` | TEXT | Yes | Region/prefecture (bc only; NULL otherwise) |
| `gender` | TEXT | No | `'M'` (male) or `'F'` (female) |
| `explanation` | TEXT | Yes | Free-text name story (bc only; NULL otherwise) |
| `src` | TEXT | No | Source: `'bc'`, `'hs'`, or `'meiji'` |

**Notes:**
- bc rows: one row per individual baby; orth and pron may both be present
  or one may be NULL depending on the original record.
- hs rows: each unique (orth, year, gender) record is repeated `freq` times;
  pron is always NULL (Heisei provides only written forms).
- meiji rows: expanded from `nrank`; freq may be NULL for pre-2004 years
  (no count data available), in which case no rows are inserted.

---

## Table: `nrank` — yearly rankings and frequencies

One row per unique (orth or pron, year, gender, source) ranking entry.
This is the canonical aggregated table used for frequency/rank analyses
and for the downloadable TSV exports.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `nrid` | INTEGER PK | No | Auto-increment row ID |
| `year` | INTEGER | No | Birth year |
| `orth` | TEXT | Yes | Written form; NULL for pron-only rankings |
| `pron` | TEXT | Yes | Reading in hiragana; NULL for orth-only rankings |
| `rank` | INTEGER | No | Rank within (year, gender, source); 1 = most frequent |
| `gender` | TEXT | No | `'M'` or `'F'` |
| `freq` | INTEGER | Yes | Token count; NULL when source provides no frequency |
| `src` | TEXT | No | Source: `'bc'`, `'hs'`, or `'meiji'` |

**Notes on rank:**
- bc: computed by `ROW_NUMBER() OVER (PARTITION BY year, gender ORDER BY COUNT(*) DESC)`;
  ties are broken arbitrarily (non-deterministic for equal counts).
- hs: source-provided rank and frequency inserted directly.
- meiji: source-provided rank and frequency. Pre-2004 years have no
  frequency data (freq = NULL); 2013 orthography frequencies were missing
  from the API and supplemented from a PDF-sourced Excel sheet.

---

## Table: `name_year_cache` — cached yearly totals

Pre-computed counts used to speed up trend plots and web queries.

| Column | Type | Description |
|--------|------|-------------|
| `src` | TEXT | `'bc'`, `'hs'`, `'meiji'`, `'totals'`, or `'births'` |
| `dtype` | TEXT | Logical facet: `'orth'`, `'pron'`, `'both'`, `'total'`, or `'birth'` |
| `year` | INTEGER | Year |
| `gender` | TEXT | `'M'` or `'F'` |
| `count` | INTEGER | Pre-computed count |

Primary key: `(src, dtype, year, gender)`

**src values:**
- `'bc'`, `'hs'`, `'meiji'`: distinct-name counts from `namae` for each source
- `'totals'`: annual survey sample sizes from `data/meiji_total_year.tsv`
  (Meiji Yasuda's own reported survey totals)
- `'births'`: national live-birth totals from IPSS (`data/live_births_year.tsv`)

---

## Table: `attr` — derived attributes per token

One row per `nid` in `namae`. Populated by `scripts/calculate-features.py`.

| Column | Type | Description |
|--------|------|-------------|
| `nid` | INTEGER FK→namae | Row ID in namae |
| `olength` | INTEGER | Length of `orth` in Unicode characters |
| `plength` | INTEGER | Length of `pron` in Unicode characters |
| `mlength` | INTEGER | Mora count (from `web/utils.mora_hiragana`) |
| `slength` | INTEGER | Syllable count (from `web/utils.syllable_hiragana`) |
| `char1` | TEXT | First character of `orth` |
| `char_1` | TEXT | Last character of `orth` |
| `char_2` | TEXT | Second-to-last character of `orth` |
| `mora1` | TEXT | First mora of `pron` |
| `mora_1` | TEXT | Last mora of `pron` |
| `mora_2` | TEXT | Second-to-last mora of `pron` |
| `syll1` | TEXT | First syllable of `pron` |
| `syll_1` | TEXT | Last syllable of `pron` |
| `syll_2` | TEXT | Second-to-last syllable of `pron` |
| `uni_ch` | TEXT | The character itself if `orth` is a single character; NULL otherwise |
| `script` | TEXT | Script classification: `'kanji'`, `'hira'`, `'kata'`, `'mixhira'`, `'mixkata'` |

---

## Table: `kanji` — kanji metadata

One row per unique kanji character appearing in `namae.orth`. Populated
by `scripts/add-kanji.py` using Jamdict/Kanjidic2.

| Column | Type | Description |
|--------|------|-------------|
| `kid` | INTEGER PK | Auto-increment row ID |
| `kanji` | TEXT | The kanji character |
| `yfrom` | INTEGER | Earliest year of appearance in namae (may be empty) |
| `grade` | INTEGER | School grade (jōyō; 0 or NULL for jinmeiyō/other) |
| `freq` | INTEGER | Kanjidic frequency rank |
| `imi` | TEXT | Japanese meaning (from dictionary) |
| `mean` | TEXT | English gloss |
| `kunyomi` | TEXT | Kun readings (space-separated hiragana) |
| `onyomi` | TEXT | On readings (space-separated hiragana, converted from katakana) |
| `other` | TEXT | Other readings |
| `nanori` | TEXT | Name readings (nanori) from Kanjidic |
| `scount` | INTEGER | Stroke count |

**Coverage:** Limited to kanji appearing in name data. Includes jōyō kanji,
jinmeiyō kanji, and the iteration mark 々.

---

## Table: `ntok` — name–kanji link table

Maps each `namae` token to each kanji character it contains.

| Column | Type | Description |
|--------|------|-------------|
| `nid` | INTEGER FK→namae | Row ID in namae |
| `kid` | INTEGER FK→kanji | Row ID in kanji |

One row per (token, kanji character) pair.

---

## View: `combined`

A virtual dataset that aligns Heisei (hs) and Baby Calendar (bc) data to
common anchor years, enabling cross-source comparison despite different
year ranges.

- hs rows are included unchanged.
- bc rows are remapped:
  - bc year < 2015 → 2011
  - bc year ≥ 2015 → 2019
- All rows are labelled `src = 'hs+bc'`.

---

## TSV exports (`data/download/`)

The downloadable exports are derived from `nrank` and `name_year_cache`:

| File | Source table | Content |
|------|-------------|---------|
| `baby_calendar_names.tsv` | nrank (bc) | All bc rankings (orth-only, pron-only, and orth+pron rows) |
| `baby_calendar_names_both.tsv` | nrank (bc) | Only bc rows where both orth and pron are present |
| `heisei_names.tsv` | nrank (hs) | All hs rankings |
| `meiji_yasuda_names.tsv` | nrank (meiji) | All Meiji Yasuda rankings (1912–2025) |
| `meiji_yasuda_totals.tsv` | name_year_cache (totals) | Annual survey sample sizes (2004–2025) |
| `live_births.tsv` | name_year_cache (births) | Annual national live-birth totals |

All TSV files use tab separation, UTF-8 encoding, and a header row.
Generated by `scripts/export_tsv.py`.

---

## Source and coverage summary

| Source | src value | Years | Orth | Pron | Freq | Gender |
|--------|-----------|-------|------|------|------|--------|
| Baby Calendar | `bc` | 2008–2022 | Yes | Partial | Computed | M/F |
| Heisei Namae Jiten | `hs` | 1989–2009 | Yes | No | Yes | M/F |
| Meiji Yasuda | `meiji` | 1912–2025 | Yes (orth series) | Yes (pron series) | Yes (2004–2025) | M/F |

See `docs/sources.md` for full source documentation.
