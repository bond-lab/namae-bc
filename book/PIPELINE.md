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
| `--figures 1,7a,9` | all | Build only the listed figure IDs |
| `--bw` | off | Build black-and-white versions (output: `Figure_X.bw.svg`) |

### Black-and-white style conventions

When `--bw` is used, all figures follow these conventions:

| Element | Style |
|---|---|
| Girls data line | dash-dot `-.`, filled circle markers |
| Boys data line | dotted `:`, open square markers |
| Significant regression | solid line `-` |
| Non-significant regression | dashed line `--` |
| Stacked area fills | four gray levels (0.90 → 0.22) with hatching (`////`, `\\`, `xxxx`, `----`) |
| Dataset coverage bars (Figs 3–4) | four gray levels; existing hatch patterns retained |
| Hatch line width | 1.5 pt (coarser than screen default for legibility in print) |
| Base font size | 12 pt (bumped from 10–11 pt for A5 readability) |

Girls are the primary (dash-dot) series and Boys the secondary (dotted) throughout.
Solid and dashed lines are reserved for regression significance so they remain
unambiguous regardless of which gender is being shown.

### Examples

```bash
# Rebuild everything as PNG + SVG (colour)
uv run --python .venv-build/bin/python scripts/build_book_figures.py

# Build black-and-white SVG versions for the publisher
uv run --python .venv-build/bin/python scripts/build_book_figures.py \
    --formats svg --bw

# Quick PNG-only pass, skipping already-built figures
uv run --python .venv-build/bin/python scripts/build_book_figures.py \
    --formats png --skip-existing

# Rebuild a single figure
uv run --python .venv-build/bin/python scripts/build_book_figures.py --figures 9
```

## Figure inventory

| ID | File(s) | Source script | Notes |
|---|---|---|---|
| 1 | Figure_1.{png,svg} | pub-agreement.py | Meiji vs Heisei ranking agreement |
| 2 | Figure_2.{png,svg} | plot-years.py | Annual birth counts by gender |
| 3 | Figure_3.{png,svg} | pub-years.py | Dataset coverage (linear scale) |
| 4 | Figure_4.{png,svg} | pub-years.py | Dataset coverage (log scale) |
| 5 | Figure_5.{png,pdf} | Playwright | Screenshot of web app (蓮 search) — requires the Flask app running on port 5100 |
| 6 | Figure_6.{png,svg} | img-jinmei.py | Kanji allowed in names over time |
| 7a–c | Figure_7{a,b,c}.{png,svg} | plot_meiji.py | Berger-Parker dominance (hs orth / meiji orth / meiji pron) |
| 8 | Figure_8.{png,svg} | plot_meiji.py | Diversity metrics (Shannon-Wiener, Gini-Simpson, TTR, Singleton) |
| 9 | Figure_9.{png,svg} | plot_web_charts.py | Irregular name-reading proportion over time (BC data) |
| 10 | Figure_10.{png,svg} | plot_overlap.py | Gender-neutral name count (BC orth overlap) |
| 11a–c | Figure_11{a,b,c}.{png,svg} | plot_proportion.py | Pronunciation / orthography / full-name proportion histograms (2008–2022) |
| 12a–b | Figure_12{a,b}.{png,svg} | plot_proportion.py | Pronunciation proportion histograms split by sub-period |
| 13a–b | Figure_13{a,b}.{png,svg} | plot_overlap.py | Meiji pron overlap count / weighted |
| 14a–b | Figure_14{a,b}.{png,svg} | plot_overlap.py | Meiji orth overlap count / weighted |
| 15a–b | Figure_15{a,b}.{png,svg} | plot_overlap.py | Heisei orth overlap count / weighted |
| 16 | Figure_16.{png,svg} | plot_proportion.py | Gender-neutral names (proxy: hs orth proportion) |
| 17 | Figure_17.{png,svg} | plot_kanji_position.py | Position of 斗 in male Heisei names |
| 18 | Figure_18.{png,svg} | plot_kanji_position.py | Position of 翔 in male Heisei names |
| 19a–b | Figure_19{a,b}.{png,svg} | plot_kanji_position.py | Position of 陽 in Meiji names (M/F) |
| 20a–b | Figure_20{a,b}.{png,svg} | plot_kanji_position.py | Position of 凛 in Meiji names (M/F) |
| 21a–c | Figure_21{a,b,c}.{png,svg} | plot_web_charts.py | Genderedness over time (hs orth / meiji orth / meiji pron) |

## SVG and CJK fonts

All matplotlib figures are saved with:

```python
plt.rcParams["svg.fonttype"] = "path"
```

This embeds text (including kanji) as vector paths rather than font references, so the
SVG renders identically on any system regardless of whether Japanese fonts are installed.

## Figure 5 — web app screenshot

Figure 5 is a screenshot of the individual name page at
`http://127.0.0.1:5100/namae?orth=蓮` (蓮, the water lily).
It is captured via Playwright (headless Chromium) and saved as both PNG and PDF.

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
  Figure_1.png
  Figure_1.svg
  Figure_2.png
  ...
  figure_index.md    # Markdown index with embedded images
  figure_index.html  # HTML gallery
  PIPELINE.md        # This file
```
