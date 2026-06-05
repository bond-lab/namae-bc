# General Bugs

* phenomena/diversity.html is not working
* Names shows both Name and Pron as None for Meiji-orth
* Names shows nothing for Meiji-pron
** make it work properly
* Should add that Meiji is only last N years



# Issues to Address for Zenodo Archiving

### Placeholder DOIs (fill in when known)
- `.zenodo.json` line 29: `"identifier": "10.xxxx/book-doi-placeholder"`
- `ATTRIBUTIONS.md` line 62: `https://doi.org/10.xxxx/zenodo.xxxxx`

### Incomplete book reference
- `ATTRIBUTIONS.md` line 68: marked as FIXME, needs full citation

### Baby Calendar nazuke episode coverage gap (2008-2016)

The structured sound-row episode pages (`/knowledge/common/ID`) only go back
to **2017** — confirmed by the Wayback Machine CDX, which found 70 archived
pages for that URL pattern, all from 2017. The CDX found zero archived pages
for `/knowledge/pregnancy/*` or `/special/name/*` going back to 2008.

The hand-collected bc data (2008–2022) includes an `explanation` column with
per-name naming stories. It is unknown from which URL pattern these were
collected and whether those older pages are archived anywhere.

To investigate:
- When Wayback Machine is stable, retry fetching the low IDs found in CDX
  (373-376, 485, 501-505, 549, 749-753, 776, 790, 800, 865, 890-899) —
  these may be 2015/2016 episode pages.
- Check CDX for any other baby-calendar.jp URL patterns containing
  "エピソード" going back to 2008.
- The pre-2017 episode script (`scrape_baby_calendar_nazuke_archive.py`)
  is ready to run when the archive is stable.

### Meiji survey totals — verify against archived PDFs

- `meiji_total_year.tsv` contains survey totals for 2004-2025.
- 2023 (13,908: M 6,957, F 6,951), 2024 (14,325: M 7,308, F 7,017), and
  2025 (12,505: M 6,312, F 6,193) are confirmed from the official PDFs
  now archived in `data/meiji_yasuda_data/press_releases/`.
- Totals for 2004-2022 were taken from PDFs or from Ogihara (2020/2025);
  should be cross-checked against the archived PDFs (2006-2022 coverage).

### Install.md is server-specific
- Contains paths specific to `compling.upol.cz`; fine as-is if understood
  as deployment notes for that server
