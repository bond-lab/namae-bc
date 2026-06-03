# Data Sources

Documentation of each source dataset: provenance, coverage, harvest method,
cleaning decisions, known biases, and rights.

See also `ATTRIBUTIONS.md` for rights/copyright, and `docs/schema.md` for
field-level documentation.

---

## 1. Baby Calendar (bc) — 2008–2022

### Provider

Baby Calendar Co., Ltd. (株式会社ベビーカレンダー)
<https://baby-calendar.jp/>

Baby Calendar is a Japanese parenting media platform. Users who register the
birth of a child may voluntarily submit the child's name for inclusion in the
site's annual name rankings.

### Coverage

- **Years:** 2008–2022 (15 years)
- **Gender:** Male and female (separate rankings)
- **Fields provided:** Written form (kanji/kana), reading (hiragana), location
  (prefecture), free-text name story (explanation)
- **Ranking basis:** Token-level submissions; frequency and rank computed by
  aggregation (not source-provided)

### Harvest method

Data was manually collected (cut and pasted) from the Baby Calendar website by
Ivona Barešová and assembled into a single Excel workbook
(`data/jmena 2008-2022.xlsx`) with one sheet per gender.

### Cleaning applied

- Columns extracted: year, orthography, pronunciation, location, gender, explanation.
- 17 records excluded (non-name entries or duplicates in the source data).
- One record reassigned from male to female based on the name story.
- Hand correction: 2016 — 望月蓮(れん) → 蓮(れん) (family name incorrectly included).
- Frequencies and ranks computed by aggregating token-level records into counts
  per (name, year, gender). Ties broken arbitrarily by `ROW_NUMBER()`.

### Known biases

- Self-selected sample: only users who register on Baby Calendar and choose to
  submit a name are included. Coverage of the full birth population is unknown.
- Geographic distribution may reflect the platform's user base rather than
  national patterns.
- Coverage ends at 2022; no subsequent years are available in this source.
- Readings (pron) are present for most but not all records; a minority have
  orth only.

### Rights

© 株式会社ベビーカレンダー (Baby Calendar Co., Ltd.)
Included for research and educational purposes. Not for commercial redistribution.

---

## 2. Heisei Namae Jiten (hs) — 1989–2009

### Provider

Heisei Namae Jiten (平成名前辞典)
<https://www.namaejiten.com/>

An online Japanese name dictionary that published annual name frequency rankings
for the Heisei era (1989–2019). The rankings were compiled from birth
registration announcements published in local newspapers.

### Coverage

- **Years:** 1989–2009 (21 years; Heisei 1–21)
- **Gender:** Male and female (separate files)
- **Fields provided:** Written form (kanji/kana), rank, frequency
- **No reading data** (orth only)

### Harvest method

Plain-text files, one per year per gender (`data/heisei/boy/h01.txt` …
`h21.txt`, and `girl/`), downloaded directly from the website. File naming
follows the Heisei year number (h01 = Heisei 1 = 1989). Each line has the
format `rank\tname\tfrequency`.

### Cleaning applied

- **Character normalisation:** Variant kanji mapped to standard modern forms
  before database insertion:
  - Dash variants (―, －, -, ‐) → ー (katakana prolonged sound mark)
  - 晴→晴, 昻→昂, 煕→熙, 晧→皓, 逹→達, 瑤→瑶, 翆→翠, 桒→桑, 莱→萊
- **Character validation:** Each character must be a permitted given-name
  character: jōyō kanji (常用漢字, 2,136 chars), jinmeiyō kanji (人名用漢字,
  863 chars), iteration mark 々, hiragana, or katakana. 239 names were
  excluded (examples: 昻樹, Ｊ映美, すた～ら, 花菜＆太一).
- **Full-name exclusion:** Names longer than 4 kanji characters consisting
  entirely of kanji were treated as family+given name combinations and excluded.

### Known biases

- Source is newspaper birth announcements, which are voluntary and may
  over-represent certain demographics (families who submit announcements).
- Coverage limited to the Heisei era available on the website; data for 2010
  onward was not collected from this source.
- No reading (pronunciation) data available.

### Rights

© 平成名前辞典 (Heisei Name Dictionary)
Included for research and educational purposes. Not for commercial redistribution.

---

## 3. Meiji Yasuda Life Insurance (meiji) — 1912–2025

### Provider

Meiji Yasuda Life Insurance Company (明治安田生命保険相互会社)
<https://www.meijiyasuda.co.jp/enjoy/ranking/>

Meiji Yasuda conducts an annual survey of baby names among its own
policyholders (個人保険・個人年金保険の既契約情報). The survey has been
conducted since 1989 (37th edition in 2025). Rankings for birth years back to
1912 are published, drawing on historical policyholder records.

### Coverage

- **Years:** 1912–2025 (114 years)
- **Gender:** Male and female (separate rankings)
- **Fields provided:** Written form (orth series), pronunciation in katakana
  (pron series, 2004–2025), rank, frequency (2004–2025 only)

Detailed coverage by sub-series:

| Period | Orth | Pron | Freq | Top-N |
|--------|------|------|------|-------|
| 1912–2003 | Yes | No | No | Top 10 |
| 2004–2025 | Yes | Yes | Yes | Top 100 (orth), Top 50 (pron) |

### Harvest method

- **API data (`data/meiji_yasuda_data/`):** JSON files (`n_YYYY.json` for
  names, `y_YYYY.json` for readings, 2004–2025) downloaded from the Meiji
  Yasuda website's internal API using `data/get-meiji.py`. All years
  available from the API were downloaded and combined into
  `meiji_yasuda_data/processed/combined_rankings.csv`.
- **Press release PDFs (`data/meiji_yasuda_data/press_releases/`):** Annual
  PDF reports for 2006–2025 archived from
  `https://www.meijiyasuda.co.jp/profile/news/release/`. Used to verify
  survey sample sizes (see below).
- **Excel supplement (`data/meiji.xlsx`):** Orthography frequencies for 2013
  were missing from the API and were manually transcribed from the PDF report
  into an Excel sheet.

### Survey sample sizes

Annual survey totals are stored in `data/meiji_total_year.tsv` (male, female,
total counts per year). Sources by period:

| Period | Source |
|--------|--------|
| 2004–2018 | Ogihara (2020), cross-checked against press release PDFs |
| 2019–2025 | Official press-release PDFs archived in `data/meiji_yasuda_data/press_releases/` |

Ogihara (2020): Ogihara, Y. Baby names in Japan, 2004–2018: Common writings
and their readings. *BMC Research Notes*, 13, 553.
<https://doi.org/10.1186/s13104-020-05409-3>

### Cleaning applied

- Katakana readings converted to hiragana using `jaconv.kata2hira()`.
- 2013 orthography frequencies patched from `meiji.xlsx` (source: press
  release PDF).

### Known biases

- Sample is limited to Meiji Yasuda's own policyholders; coverage of the
  national birth population is unknown and varies by year.
- Only top-N names per year are published; the long tail of less common names
  is not captured.
- Pre-2004 data has no frequency information (rank only, top 10).
- The survey methodology changed over time as the policyholder base grew.

### Rights

© 明治安田生命保険相互会社 (Meiji Yasuda Life Insurance Company)
Included for research and educational purposes. Not for commercial redistribution.

---

## 4. Japanese Birth Data (BD) — 1873–2023

### Provider

National Institute of Population and Social Security Research (IPSS)
(国立社会保障・人口問題研究所)
<https://www.ipss.go.jp/>

### Coverage

- **Years:** 1873–2023
- **Fields:** Annual live births by gender (male, female, total)

### Harvest method

Downloaded from IPSS table PSJ2023-04:
<https://www.ipss.go.jp/p-info/e/psj2023/PSJ2023-04.xls>

More recent years (2022–2023) supplemented from e-Stat
(<https://www.e-stat.go.jp/>).

### Use in the resource

Birth totals are stored in `name_year_cache` with `src='births'` and used to
normalise name frequencies against the total birth population, enabling
coverage and diversity metrics to be expressed as proportions.

### Rights

© 国立社会保障・人口問題研究所 (IPSS)
Included for research and educational purposes. Not for commercial redistribution.

---

## Coverage overview

| Source | Years | N years | Orth | Pron | Freq | Gender | Bias |
|--------|-------|---------|------|------|------|--------|------|
| Baby Calendar | 2008–2022 | 15 | Yes | Partial | Computed | M/F | Self-selected web users |
| Heisei Namae Jiten | 1989–2009 | 21 | Yes | No | Yes | M/F | Newspaper birth announcements |
| Meiji Yasuda | 1912–2025 | 114 | Yes | Yes (2004+) | Yes (2004+) | M/F | Policyholder sample |
| Birth data (IPSS) | 1873–2023 | 151 | — | — | Totals | M/F | National register |
