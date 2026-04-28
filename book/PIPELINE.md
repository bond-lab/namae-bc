# Book Figures Pipeline

This directory contains publication-ready figures for the Japanese names book manuscript
(`local/Barešová_Bond_manuscript_CORR_IB.doc`).

## Generating figures

```bash
uv run --python .venv-build/bin/python scripts/build_book_figures.py [OPTIONS]
```

### Options

| Flag | Default | Description |
|---|---|---|
| `--formats png,svg` | `png,svg` | Output formats (comma-separated) |
| `--skip-existing` | off | Skip figures whose output files already exist |
| `--figures 1a,7Aa,9` | all | Build only the listed figure IDs |
| `--bw` | off | Build black-and-white versions |
| `--book` | off | Book-print mode: 111 mm wide, Roboto Condensed, 7 pt, 150 DPI PNG |
| `--index-only` | off | Regenerate index files without rebuilding figures |

### Output naming

| Flags | Output stem | Use |
|---|---|---|
| *(none)* | `Figure_X.{fmt}` | Web / screen colour |
| `--bw` | `Figure_X.bw.{fmt}` | Screen B&W |
| `--book` | `Figure_X.book.{fmt}` | Print-ready colour (111 mm, Roboto Condensed) |
| `--book --bw` | `Figure_X.book.bw.{fmt}` | Print-ready B&W |

### Book-print style conventions

When `--book` is used, all figures follow these conventions:

| Element | Style |
|---|---|
| Column width | 111 mm (4.37 in) |
| Font | Roboto Condensed (embedded as SVG paths) |
| Body font size | 7 pt |
| Title font size | 8 pt |
| PNG resolution | 150 DPI |

When `--book --bw` is used, the additional B&W conventions apply:

| Element | Style |
|---|---|
| Girls data line | dash-dot `-.`, filled circle markers |
| Boys data line | dotted `:`, solid diamond markers |
| Significant regression | solid line `-` |
| Non-significant regression | dashed line `--` |
| Stacked area fills | four gray levels (0.90 → 0.22) with hatching (`////`, `\\`, `xxxx`, `----`) |
| Hatch line width | 1.5 pt |
| Line width | 0.9 pt |
| Marker size | 3.5 pt |

Girls are the primary (dash-dot) series and Boys the secondary (dotted) throughout.
Solid and dashed lines are reserved for regression significance so they remain
unambiguous regardless of which gender is being shown.

### Examples

```bash
# Build print-ready colour figures (SVG + PNG)
uv run --python .venv-build/bin/python scripts/build_book_figures.py \
    --book --formats svg,png

# Build print-ready B&W figures (SVG + PNG)
uv run --python .venv-build/bin/python scripts/build_book_figures.py \
    --book --bw --formats svg,png

# Rebuild everything as PNG + SVG (colour, web/screen size)
uv run --python .venv-build/bin/python scripts/build_book_figures.py

# Build legacy B&W SVG versions (screen size, 12 pt)
uv run --python .venv-build/bin/python scripts/build_book_figures.py \
    --formats svg --bw

# Quick pass, skipping already-built figures
uv run --python .venv-build/bin/python scripts/build_book_figures.py \
    --book --formats svg,png --skip-existing

# Rebuild a single figure (book mode)
uv run --python .venv-build/bin/python scripts/build_book_figures.py \
    --book --formats svg,png --figures 9
```

## Figure inventory

In `--book` mode, multi-panel figures are split into individual sub-figure files.
The table shows both the default IDs and the book-mode split IDs.

| ID (default) | ID (book mode) | File stem(s) | Source script | Notes |
|---|---|---|---|---|
| 1 | 1a, 1b | Figure_1{a,b} | pub-agreement.py | Meiji vs Heisei ranking agreement (a: overlap count, b: JS divergence) |
| 2 | 2 | Figure_2 | plot-years.py | Annual birth counts by gender |
| 3 | 3 | Figure_3 | pub-years.py | Dataset coverage (linear scale) |
| 4 | 4 | Figure_4 | pub-years.py | Dataset coverage (log scale) |
| 5a–b | — | Figure_5{a,b} | Playwright | Screenshot of web app (蓮 search) — skipped in book/bw modes |
| 6 | 6 | Figure_6 | img-jinmei.py | Kanji allowed in names over time |
| 7a | 7Aa–7Ad | Figure_7{Aa,Ab,Ac,Ad} | plot_meiji.py | Berger-Parker dominance, Heisei orth (BP 1/10/50/100) |
| 7b | 7Ba–7Bd | Figure_7{Ba,Bb,Bc,Bd} | plot_meiji.py | Berger-Parker dominance, Meiji orth |
| 7c | 7Ca–7Cd | Figure_7{Ca,Cb,Cc,Cd} | plot_meiji.py | Berger-Parker dominance, Meiji pron |
| 8 | 8a–8d | Figure_8{a,b,c,d} | plot_meiji.py | Diversity metrics (a: Shannon-Wiener, b: Gini-Simpson, c: Singleton, d: TTR) |
| 9 | 9 | Figure_9 | plot_web_charts.py | Irregular name-reading proportion over time (BC data) |
| 10 | 10 | Figure_10 | plot_overlap.py | Gender-neutral name count (BC orth overlap) |
| 11a–c | 11a–c | Figure_11{a,b,c} | plot_proportion.py | Pronunciation / orthography / full-name proportion histograms (2008–2022) |
| 12a–b | 12a–b | Figure_12{a,b} | plot_proportion.py | Pronunciation proportion histograms split by sub-period |
| 13a–b | 13a–b | Figure_13{a,b} | plot_overlap.py | Meiji pron overlap count / weighted |
| 14a–b | 14a–b | Figure_14{a,b} | plot_overlap.py | Meiji orth overlap count / weighted |
| 15a–b | 15a–b | Figure_15{a,b} | plot_overlap.py | Heisei orth overlap count / weighted |
| 16 | 16 | Figure_16 | plot_proportion.py | Gender-neutral names (proxy: hs orth proportion) |
| 17 | 17 | Figure_17 | plot_kanji_position.py | Position of 斗 in male Heisei names |
| 18 | 18 | Figure_18 | plot_kanji_position.py | Position of 翔 in male Heisei names |
| 19a–b | 19a–b | Figure_19{a,b} | plot_kanji_position.py | Position of 陽 in Meiji names (M/F) |
| 20a–b | 20a–b | Figure_20{a,b} | plot_kanji_position.py | Position of 凛 in Heisei names (M/F) |
| 21a–c | 21a–c | Figure_21{a,b,c} | plot_web_charts.py | Genderedness over time (hs orth / meiji orth / meiji pron) |

## SVG and CJK fonts

All matplotlib figures are saved with:

```python
plt.rcParams["svg.fonttype"] = "path"
```

This embeds text (including kanji) as vector paths rather than font references, so the
SVG renders identically on any system regardless of whether Japanese fonts are installed.

In `--book` mode, Roboto Condensed is registered from
`/usr/share/fonts/truetype/roboto/unhinted/` and used as the primary sans-serif font,
with Noto Sans CJK JP as fallback for Japanese characters.

## Figure 5 — web app screenshot

Figure 5 is a screenshot of the individual name page at
`http://127.0.0.1:5100/namae?pron=れん` and `?pron=はす`.
It is captured via Playwright (headless Chromium). Skipped automatically in
`--bw` and `--book` modes.

The Flask app must be running before invoking the builder:

```bash
# In a separate terminal:
uv run --python .venv/bin/python web/app.py
```

Then build Figure 5:

```bash
uv run --python .venv-build/bin/python scripts/build_book_figures.py --figures 5
```

## Dependencies

Build dependencies live in `.venv-build` (managed separately from the main `.venv`):

```bash
uv pip install -r requirements-build.txt --python .venv-build/bin/python
# playwright browsers (first time only)
.venv-build/bin/playwright install chromium
```

## Output structure

```
book/
  Figure_1.png / .svg              # web/screen colour (default build)
  Figure_1.bw.svg                  # screen B&W (--bw)
  Figure_1a.book.svg / .png        # print colour (--book)
  Figure_1a.book.bw.svg / .png     # print B&W (--book --bw)
  ...
  book_figures.zip                 # all .book.* files for publisher delivery
  bw_figures.zip                   # legacy .bw.svg files
  figure_index.md                  # Markdown index with embedded images
  figure_index.html                # HTML gallery
  PIPELINE.md                      # This file
```
