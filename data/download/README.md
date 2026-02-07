# Downloaded Data

These TSV (tab-separated values) files are exported from the cleaned
database by `scripts/export_tsv.py`.  They contain ranked name
frequencies and supporting demographic data ready for direct use in
R, Python, Excel, etc.

To regenerate: `python scripts/export_tsv.py`

---

## Files

### baby_calendar_names.tsv — orth-only & pron-only rankings

Baby Calendar (2008-2022), with separate orthography-only and
pronunciation-only ranking series for easy comparison with the
Heisei (orthography only) and Meiji Yasuda datasets.

| Column | Description |
|--------|-------------|
| year   | Year (2008-2022) |
| orth   | Written form (kanji/kana), or empty for pronunciation-only rows |
| pron   | Pronunciation in hiragana, or empty for orthography-only rows |
| rank   | Rank within year and gender (1 = most frequent) |
| gender | M or F |
| freq   | Number of occurrences in that year |

**Rows:** 21,306

---

### baby_calendar_names_both.tsv — orth+pron rankings

Baby Calendar (2008-2022), with orthography and pronunciation
together.  Each row is a unique (orthography, pronunciation) pair
ranked by frequency — e.g. 結愛 read as ゆあ and 結愛 read as ゆめ
are counted separately.  This is the most informative view, but is
only available for Baby Calendar (the only source recording both
fields per name).

| Column | Description |
|--------|-------------|
| year   | Year (2008-2022) |
| orth   | Written form (kanji/kana) |
| pron   | Pronunciation in hiragana |
| rank   | Rank within year and gender (1 = most frequent) |
| gender | M or F |
| freq   | Number of occurrences in that year |

**Rows:** 13,538

---

### heisei_names.tsv

Heisei Namae Jiten (1989-2009).  The largest dataset, with complete
frequency distributions (not just top-N).  Orthography only.

| Column | Description |
|--------|-------------|
| year   | Year (1989-2009; Heisei 1-21) |
| orth   | Written form (kanji/kana) |
| rank   | Rank within year and gender (1 = most frequent) |
| gender | M or F |
| freq   | Frequency count |

**Rows:** 1,512,879

---

### meiji_yasuda_names.tsv

Meiji Yasuda Life Insurance annual surveys (1912-2024).  The longest
series.  Orthography and pronunciation are ranked as separate series
(one will be empty per row).

| Column | Description |
|--------|-------------|
| year   | Year (1912-2024) |
| orth   | Written form, or empty for pronunciation-only rows |
| pron   | Pronunciation in hiragana, or empty for orthography-only rows |
| rank   | Rank within year, gender, and series |
| gender | M or F |
| freq   | Frequency count (empty before 2004) |

**Rows:** 8,967

**Coverage by period:**

| Period | Orthography | Pronunciation |
|--------|------------|---------------|
| 1912-2003 | Top 10 (no freq) | — |
| 2004-2024 | Top 100 (with freq) | Top 50 (with freq) |

---

### meiji_yasuda_totals.tsv

Total names surveyed by Meiji Yasuda each year (2004-2024).
Useful for computing proportions from the ranked data.

| Column | Description |
|--------|-------------|
| year   | Year (2004-2024) |
| gender | M or F |
| count  | Total names in that year's survey for that gender |

**Rows:** 42

---

### live_births.tsv

Annual live births in Japan by gender (1873-2023).
Useful for normalizing name frequencies against total births.

| Column | Description |
|--------|-------------|
| year   | Year (1873-2023) |
| gender | M or F |
| count  | Number of live births |

**Rows:** 296
