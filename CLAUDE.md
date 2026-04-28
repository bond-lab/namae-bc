# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Key Commands

```bash
# Run tests (fast)
.venv/bin/python -m pytest tests/ -v

# Run only fast tests (skip slow DB-heavy ones)
.venv/bin/python -m pytest tests/ -v -m "not slow"

# Run a single test
.venv/bin/python -m pytest tests/test_routes.py::TestNameSearch::test_orth_search -v

# Run the web app locally
bash run.sh          # activates .venv, installs deps, starts wsgi.py

# Build the database
bash makedb.sh           # full build: DB + analysis
bash makedb.sh db        # DB only (~5 min)
bash makedb.sh analysis  # analysis only — requires existing DB (~10-15 min)

# Build book figures (web/screen size, colour)
uv run --python .venv-build/bin/python scripts/build_book_figures.py
uv run --python .venv-build/bin/python scripts/build_book_figures.py --figures 10,13a --formats png,svg

# Build book figures (print-ready, 111 mm, Roboto Condensed)
uv run --python .venv-build/bin/python scripts/build_book_figures.py --book --formats svg,png
uv run --python .venv-build/bin/python scripts/build_book_figures.py --book --bw --formats svg,png

# Deploy to production
bash deploy.sh       # rsync to compling.upol.cz + Apache restart (needs SSH)
```

## Two Python Environments

The repo uses two separate venvs:

| Venv | Purpose | Used for |
|------|---------|---------|
| `.venv` | Web app (Python 3.13, Flask, scipy) | Tests, Flask app, `run.sh` |
| `.venv-build` | Build scripts (newer Python, matplotlib, playwright) | `makedb.sh`, book figures |

**Always use `.venv/bin/python` for tests and the web app.** System Python (3.8.10) has incompatible Jinja2/Flask versions.

Build scripts in `scripts/` import via symlinks (`from db import ...`, `from settings import ...`) — not via `web.db` or `web.settings` — to avoid importing Flask.

The production server runs Python 3.8.10 (CGI/Apache). All code in `web/` must be Python 3.8 compatible: use `typing.Dict`/`Optional`/`Union` instead of `dict[...]`/`str | Path`.

## Architecture Overview

```
web/           Flask app (deployed to compling.upol.cz/namae/)
  app.py       Application factory
  routes.py    All route handlers (~900 lines)
  db.py        DB query functions + db_options registry
  settings.py  features/overall/phenomena lists; shared by routes + tests
  utils.py     whichScript, mora_hiragana, syllable_hiragana
  static/
    data/      Pre-computed JSON files (loaded by routes; fall back to live query)
    js/        D3 plotting (d3_utils.js, plot_*.js)
    plot/      Generated PNG/SVG plots (from makedb.sh analysis)
  templates/
    layout.html        Base template; navigation.html included
    phenomena/         Phenomenon pages (androgyny, overlap, diversity, …)
    docs/              Documentation rendered from Markdown

scripts/       Build scripts; run in .venv-build
  add-*.py     Import raw data into SQLite
  calc_*.py    Compute JSON files → web/static/data/
  plot_*.py    Generate PNG/SVG → web/static/plot/ and book/
  build_book_figures.py  Orchestrates all book figure scripts
  db.py        → symlink to web/db.py
  settings.py  → symlink to web/settings.py

book/          Publication-ready figures (PNG + SVG)
  PIPELINE.md  How to regenerate figures; figure inventory
tests/
  test_routes.py   Flask route tests using the real DB
  test_utils.py    Unit tests for utils.py
```

## Data Sources and the `db_options` Registry

Routes use `db_options` (in `web/db.py`) to look up per-source settings:

```python
db_options = {
    'bc':      ('namae', 'Baby Calendar', ('orth','pron','both'), (2008,2022)),
    'hs':      ('namae', 'Heisei',        ('orth'),               (1989,2009)),
    'meiji':   ('namae', 'Meiji (orth)',  ('orth'),               (2004,2024)),
    'meiji_p': ('namae', 'Meiji (phon)',  ('pron'),               (2004,2024)),
}
```

`dtype` is either a string (`'orth'`/`'pron'`) or a tuple `('orth','pron','both')` for bc. Code that needs to distinguish uses `isinstance(dtype, tuple)`. `meiji_p` maps to src `'meiji'` via `resolve_src()`.

## Pre-computed JSON Pattern

Routes that were slow now read from `web/static/data/*.json` and fall back to a live DB query if the file is missing. The cache **only stores successful reads** — missing files are retried on next request (so `makedb.sh analysis` output becomes visible without restarting Apache).

Pre-computation scripts: `scripts/calc_*.py`. All run during `makedb.sh analysis`.

## Session Colors and Theming

Users pick a color palette in Settings. Routes pass `male_color` / `female_color` (color names) and `male_color_hex` / `female_color_hex` to all templates. Templates must use these — never hardcode `red`/`blue`/`pink`/`lightblue` for gender. The JS function `getColorHex()` in `d3_utils.js` maps color names to hex.

For CSS gradients (which can't use CSS variables with hex alpha), use `{{ male_color_hex }}66` (Jinja variable + hex alpha suffix).

## Book Figures

Scripts in `scripts/plot_*.py` generate matplotlib figures for both the web (`web/static/plot/`) and book (`book/`). The book pipeline (`scripts/build_book_figures.py`) has two modes:

- **Default** (`--formats png,svg`): web/screen-size colour figures.
- **`--book`**: print-ready figures at 111 mm wide, Roboto Condensed font, 7 pt body, 150 DPI PNG. Multi-panel figures are split into individual sub-figure files (e.g. Figure 1 → 1a/1b, Figure 7a → 7Aa–7Ad, Figure 8 → 8a–8d).
- Add `--bw` to either mode for B&W output (Girls = dash-dot/circles, Boys = dotted/diamonds).

Style constants live in `scripts/bw_style.py` (`BW_M`, `BW_F`, `BW_FILLS`, `BOOK_RCPARAMS`).
SVGs embed text as paths (`svg.fonttype = "path"`) so CJK glyphs render without font installation.
See `book/PIPELINE.md` for the full figure inventory and rebuild instructions.

## Deployment

Production: `compling.upol.cz` running Apache + `mod_wsgi`, mounted at `/namae/`. Always use `url_for()` for internal links — never hardcode `/namae/` or other paths. `deploy.sh` syncs files but Apache restart requires manual `sudo systemctl restart apache2` on the server.
