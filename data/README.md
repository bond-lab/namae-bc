# Data: Sources and Cleaning

This directory contains the raw and intermediate data used to build the
database.  See [ATTRIBUTIONS.md](../ATTRIBUTIONS.md) for copyright and
licensing, and [data/download/](download/) for ready-to-use TSV exports.

---

## Baby Calendar (bc) — 2008-2022

**Raw file:** `jmena 2008-2022.xlsx`

An Excel workbook with one sheet per gender, cut and pasted from
https://baby-calendar.jp/ by Ivona Barešová.

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

---

## Heisei Namae Jiten (hs) — 1989-2009

**Raw files:** `heisei/boy/h01.txt` … `h21.txt`, `heisei/girl/h01.txt` … `h21.txt`

Plain-text files, one per year per gender (h01 = Heisei 1 = 1989),
with lines of the form `rank\tname\tfrequency`.  Downloaded from
https://www.namaejiten.com/.

**Cleaning applied:**

- Character normalization mapped variant kanji to modern standard forms:
  - Dash variants (―, －, -, ‐) → ー (katakana prolonged sound mark)
  - 晴→晴, 昻→昂, 煕→熙, 晧→皓, 逹→達, 瑤→瑶, 翆→翠, 桒→桑, 莱→萊
- Names were validated against the set of kanji permitted in Japanese
  given names (jōyō kanji + jinmeiyō kanji + iteration mark 々).
  239 names using non-permissible characters were excluded
  (e.g. 昻樹, Ｊ映美, すた～ら, 花菜＆太一).
- Names longer than 4 characters consisting entirely of kanji were
  treated as full names rather than given names and excluded.

---

## Meiji Yasuda Life Insurance (meiji) — 1912-2024

**Raw files:**
- `meiji_yasuda_data/processed/combined_rankings.csv` — from the
  Meiji Yasuda API, queried using `get-meiji.py`
- `meiji.xlsx` — supplementary data from PDFs (includes 2013
  frequencies)
- `meiji_total_year.tsv` — annual survey totals

Downloaded from https://www.meijiyasuda.co.jp/enjoy/ranking/.

**Coverage:**

- **1912-2003:** Top 10 written forms only, no frequencies.
- **2004-2024 orthography:** Top 100 written forms with frequencies.
- **2004-2024 pronunciation:** Top 50 pronunciations with frequencies.

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
  > https://doi.org/10.1186/s13104-020-05409-3

  See also Ogihara (2025), Baby names in Japan, 2019-2024,
  DOI [10.17605/OSF.IO/BQUJN](https://doi.org/10.17605/OSF.IO/BQUJN)
  (does not include survey sizes).

---

## Japanese Birth Data (bd) — 1873-2023

**Raw file:** `live_births_year.tsv`

Annual live births by gender from the National Institute of Population
and Social Security Research (IPSS), table 04-01:
https://www.ipss.go.jp/p-info/e/psj2023/PSJ2023-04.xls

Updated with 2022-2023 data from e-Stat.

Used for normalizing name frequencies against total births.
