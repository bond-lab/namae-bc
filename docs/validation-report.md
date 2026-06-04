# Validation Report

Generated from `web/db/namae.db` on the `resource-paper-2026` branch.
Run `scripts/export_tsv.py` and inspect this file to verify numbers after
any rebuild.

---

## 1. Record counts

### `nrank` table (aggregated rankings — canonical for analysis)

| Source | Total rows | Rows with frequency | Unique orth | Unique pron |
|--------|-----------|---------------------|-------------|-------------|
| bc (Baby Calendar) | 34,844 | 34,844 | 7,943 | 2,376 |
| hs (Heisei Namae Jiten) | 1,512,879 | 1,512,879 | 393,466 | — |
| meiji (Meiji Yasuda) | 9,313 | 7,453 | 1,144 | 246 |

Notes:
- hs has no reading (pron) data.
- meiji: 1,860 rows have NULL freq (pre-2004 years, rank-only data, top 10 per year).
- meiji: 2,290 nrank rows have NULL orth (pron-only series); 7,023 have NULL pron (orth-only series).

### `namae` table (token-level observations)

| Source | Token rows |
|--------|-----------|
| bc | 15,058 |
| hs | 14,534,080 |
| meiji | 161,731 |
| **Total** | **14,710,869** |

The hs and meiji token counts are large because each record is repeated
`freq` times. The bc token count reflects individual baby submissions.

### `attr` table (derived attributes)

- 14,703,435 rows (covers all of `namae` except records inserted after the
  last `calculate-features.py` run; should equal namae row count on a clean build).

### `kanji` table

- 2,521 unique kanji characters from name data.

---

## 2. Year coverage

| Source | First year | Last year | N years | Gender |
|--------|-----------|----------|---------|--------|
| bc | 2008 | 2022 | 15 | M/F |
| hs | 1989 | 2009 | 21 | M/F |
| meiji | 1912 | 2025 | 114 | M/F |

Meiji sub-series coverage:

| Period | Series | Content |
|--------|--------|---------|
| 1912–2003 | Orth only | Top 10 written forms; no frequency |
| 2004–2025 | Orth + pron | Top 100 orth (with freq), top 50 pron (with freq) |

---

## 3. Missing values in `nrank`

| Source | NULL orth | NULL pron | NULL freq | Total rows |
|--------|-----------|-----------|-----------|------------|
| bc | 8,196 | 13,110 | 0 | 34,844 |
| hs | 0 | 1,512,879 | 0 | 1,512,879 |
| meiji | 2,290 | 7,023 | 1,860 | 9,313 |

- **bc NULL orth (8,196):** pron-only ranking rows (reading rankings where orth is not aggregated).
- **bc NULL pron (13,110):** orth-only ranking rows; also bc records where the submitter did not provide a reading.
- **hs NULL pron (1,512,879):** Heisei source provides no reading data.
- **meiji NULL orth (2,290):** pron-only series rows (readings ranked without associated written form).
- **meiji NULL pron (7,023):** orth-only series rows (written forms ranked without reading).
- **meiji NULL freq (1,860):** pre-2004 rank-only data (92 years × 10 ranks × 2 genders = 1,840; small discrepancy from tied ranks or partial years).

---

## 4. BC record breakdown

Baby Calendar `nrank` rows by type:

| Type | Rows |
|------|------|
| Orth-only (orth present, pron NULL) | 13,110 |
| Pron-only (pron present, orth NULL) | 8,196 |
| Both (orth and pron present) | 13,538 |
| **Total** | **34,844** |

---

## 5. Meiji survey sample sizes (`name_year_cache`, src='totals')

Coverage: 2004–2025 (22 years with reported survey sizes).

Recent years confirmed from official press-release PDFs:

| Year | Male | Female | Total |
|------|------|--------|-------|
| 2023 | 6,957 | 6,951 | 13,908 |
| 2024 | 7,308 | 7,017 | 14,325 |
| 2025 | 6,312 | 6,193 | 12,505 |

Earlier years (2004–2022) from Ogihara (2020) and archived press-release PDFs.
See `data/meiji_yasuda_data/press_releases/README.md` for PDF sources.

---

## 6. Normalization decisions

### Heisei — character normalization

Variant kanji mapped to standard forms before insertion (see `data/README.md`):

| Original | Normalized |
|----------|-----------|
| 昻 | 昂 |
| 煕 | 熙 |
| 晧 | 皓 |
| 逹 | 達 |
| 瑤 | 瑶 |
| 翆 | 翠 |
| 桒 | 桑 |
| 莱 | 萊 |
| ―, －, -, ‐ | ー |

### Heisei — exclusions

- 239 names excluded because they contain characters not permitted in Japanese
  given names (not jōyō, jinmeiyō, hiragana, katakana, or iteration mark 々).
- Names consisting entirely of more than 4 kanji excluded as likely
  family+given combinations.

### Baby Calendar — exclusions and corrections

- 17 records excluded (non-name entries or duplicates).
- 1 record reassigned from male to female.
- 1 hand correction: 2016 — 望月蓮(れん) → 蓮(れん).

### Meiji — reading normalization

- All katakana readings converted to hiragana via `jaconv.kata2hira()`.
- 2013 orthography frequencies patched from Excel (API data missing).

---

## 7. Sanity checks

### Top names by source (expected)

**bc** — top 5 pronunciation rankings by cumulative frequency across all years:

| Pron | Gender | Total freq |
|------|--------|-----------|
| はると | M | 174 |
| ゆうと | M | 125 |
| はるき | M | 110 |
| ゆい | F | 107 |
| そうた | M | 100 |

**meiji 2025** — top orth and pron entries:

| Year | Orth | Pron | Gender | Rank | Freq |
|------|------|------|--------|------|------|
| 2025 | 翠 | — | F | 1 | 41 |
| 2025 | 湊 | — | M | 1 | 38 |
| 2025 | — | えま | F | 1 | 104 |
| 2025 | — | はると | M | 1 | 110 |

These match the published 2025 press release (`meiji_names_2025.pdf`). ✓

---

## 8. Known limitations and issues

- **bc coverage ends at 2022.** No more recent data from this source.
- **hs has no reading data.** Pronunciation analyses are limited to bc and meiji.
- **meiji pre-2004 lacks frequency.** Only rank (top 10) is available; no token-level counts.
- **meiji sample is not nationally representative.** Based on Meiji Yasuda policyholders.
- **bc sample is self-selected.** Only parents who register on Baby Calendar and submit a name are included.
- **Tie handling in bc.** `ROW_NUMBER()` breaks ties arbitrarily; equal-frequency names receive different ranks non-deterministically.
- **meiji 2013 frequencies.** Patched from PDF; may differ slightly from API if the PDF used a different aggregation.
- **attr table requires clean rebuild.** Running `calculate-features.py` on an existing database with prior attr rows will create duplicates; always rebuild from scratch.

---

## 9. Reproduction

To verify these numbers against a fresh build:

```bash
# Rebuild database
bash makedb.sh db

# Check counts
sqlite3 web/db/namae.db "SELECT src, COUNT(*) FROM namae GROUP BY src;"
sqlite3 web/db/namae.db "SELECT src, COUNT(*), COUNT(DISTINCT orth), COUNT(DISTINCT pron) FROM nrank GROUP BY src;"
```
