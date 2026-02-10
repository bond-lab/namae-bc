# namae-bc

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.18591986.svg)](https://doi.org/10.5281/zenodo.18591986)

Japanese Name Database: data and tools for analyzing trends in Japanese given names.

Part of the research project [Names and Gender — The Growing Trend of
Non-Gender-Specific Names in Contemporary
Japan](https://japanesenames.upol.cz/research/).

## Data Sources

| Source | Label | Years | Contents |
|--------|-------|-------|----------|
| [Baby Calendar](https://baby-calendar.jp/) | bc | 2008-2022 | Individual names with orthography, pronunciation, gender, location |
| [Heisei Namae Jiten](https://www.namaejiten.com/) | hs | 1989-2009 | Ranked name frequencies (orthography only) |
| [Meiji Yasuda Life Insurance](https://www.meijiyasuda.co.jp/enjoy/ranking/) | meiji | 1912-2024 | Top-ranked names (orthography + pronunciation from 2004) |

See [ATTRIBUTIONS.md](ATTRIBUTIONS.md) for copyright and licensing details
for each dataset.

## Building the Database

Rebuild everything from the raw data:

```bash
bash makedb.sh           # build DB + run analysis (default)
bash makedb.sh db        # build DB only
bash makedb.sh analysis  # run analysis only (DB must already exist)
```

`db` creates `web/db/namae.db` (SQLite) and exports TSV files to
`data/download/`.  `analysis` generates plots and JSON files under
`web/static/`.  See [DATABASE.md](DATABASE.md) for the schema and
pipeline details.

## Exporting Data as TSV

To export the cleaned ranked data as tab-separated files:

```bash
python scripts/export_tsv.py
```

This writes six files to `data/download/`:
- `baby_calendar_names.tsv` — Baby Calendar, orth-only & pron-only rankings (2008-2022)
- `baby_calendar_names_both.tsv` — Baby Calendar, orth+pron pairs (2008-2022)
- `heisei_names.tsv` — Heisei Namae Jiten ranked names (1989-2009)
- `meiji_yasuda_names.tsv` — Meiji Yasuda ranked names (1912-2024)
- `meiji_yasuda_totals.tsv` — Meiji Yasuda survey totals (2004-2024)
- `live_births.tsv` — Annual live births in Japan (1873-2023)

See `data/download/README.md` for column descriptions and details of
the cleaning applied to each source.

## Running the Website

```bash
pip install -r requirements.txt
flask --app web run
```

See [Install.md](Install.md) for production deployment notes
(Apache/WSGI on a specific server).

## Citation

See [CITATION.cff](CITATION.cff) or cite:

> Bond, Francis, & Barešová, Ivona. (2025). *Japanese Given Names: Data, Analysis, and Interactive Resources*. Zenodo. https://doi.org/10.5281/zenodo.18591986
