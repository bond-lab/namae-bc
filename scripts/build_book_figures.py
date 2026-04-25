"""Build all book figures as PNG and SVG into the book/ directory.

Usage:
    uv run --python .venv-build/bin/python scripts/build_book_figures.py [--formats png,svg] [--skip-existing]

Produces:
    book/Figure_1.png, book/Figure_1.svg, ...
    book/figure_index.md
    book/figure_index.html
"""

import argparse
import importlib.util
import json
import os
import re
import shutil
import signal
import socket
import sqlite3
import subprocess
import sys
import time
from contextlib import contextmanager
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parent
REPO_ROOT = SCRIPTS_DIR.parent
sys.path.insert(0, str(SCRIPTS_DIR))


def _load_script(name: str):
    """Import a scripts/ file by filename (supports hyphens)."""
    module_name = name.replace("-", "_")
    if module_name in sys.modules:
        return sys.modules[module_name]
    path = SCRIPTS_DIR / f"{name}.py"
    spec = importlib.util.spec_from_file_location(module_name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = mod
    spec.loader.exec_module(mod)
    return mod

BOOK_DIR = REPO_ROOT / "book"
PLOT_DIR = REPO_ROOT / "web" / "static" / "plot"
DATA_DIR = REPO_ROOT / "web" / "static" / "data"
DB_PATH = REPO_ROOT / "web" / "db" / "namae.db"
DOC_PATH = REPO_ROOT / "local" / "Barešová_Bond_manuscript_CORR_IB.docx"
FLASK_PORT = 5100
FLASK_FIGURES = {"5a", "5b"}

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.rcParams["svg.fonttype"] = "path"


# ---------------------------------------------------------------------------
# Flask server lifecycle
# ---------------------------------------------------------------------------

def _port_open(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", port)) == 0


@contextmanager
def flask_server():
    """Start the Flask app on FLASK_PORT if not already running; stop on exit."""
    already_running = _port_open(FLASK_PORT)
    proc = None
    if not already_running:
        wsgi = REPO_ROOT / "wsgi.py"
        python = Path(sys.executable).parent.parent / ".venv" / "bin" / "python"
        if not python.exists():
            python = sys.executable
        proc = subprocess.Popen(
            [str(python), str(wsgi)],
            cwd=str(REPO_ROOT),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        deadline = time.monotonic() + 15
        while not _port_open(FLASK_PORT):
            if time.monotonic() > deadline:
                proc.kill()
                raise RuntimeError(
                    f"Flask app did not start on port {FLASK_PORT} within 15s"
                )
            time.sleep(0.2)
    try:
        yield
    finally:
        if proc is not None:
            proc.send_signal(signal.SIGTERM)
            proc.wait(timeout=5)


# ---------------------------------------------------------------------------
# Caption extraction
# ---------------------------------------------------------------------------

def extract_captions(docx_path: Path) -> dict[str, str]:
    """Parse figure captions from the manuscript.

    Returns a dict mapping figure ID (e.g. '1', '7a', '12a') to title text.
    Multi-panel captions ('Figures 12a, 12b: ...') are split across both IDs
    with the same title.
    """
    from docx import Document

    pattern = re.compile(
        r'^Figures?\s+([\d]+[a-c]?(?:[,\s]+[\d]+[a-c]?)*)\s*:(.*)',
        re.IGNORECASE,
    )
    captions: dict[str, str] = {}
    doc = Document(str(docx_path))
    for para in doc.paragraphs:
        text = para.text.strip()
        m = pattern.match(text)
        if not m:
            continue
        raw_ids = m.group(1)
        title = m.group(2).strip().rstrip(".")
        ids = re.findall(r'\d+[a-c]?', raw_ids, re.IGNORECASE)
        for fig_id in ids:
            captions[fig_id.lower()] = title
    return captions


# ---------------------------------------------------------------------------
# Figure manifest: maps figure IDs to generation logic
# ---------------------------------------------------------------------------

# Each entry:  figure_id -> callable(output_stem, formats)
# The callable is responsible for writing <output_stem>.png / .svg
# 'screenshot' entries are skipped with a note.

def build_figure_1(output_stem: Path, formats: tuple[str, ...], bw: bool = False) -> None:
    import pandas as pd
    m = _load_script("pub-agreement")
    conn = sqlite3.connect(str(DB_PATH))
    data_m = m.get_meiji(conn)
    data = m.get_other(conn, data_m, src='hs')
    results = {'M': {}, 'F': {}}
    for year in data:
        if year not in data_m:
            continue
        for gender in data_m[year]:
            results[gender][year] = m._single_comparison(
                pd.Series(data_m[year][gender]),
                pd.Series(data[year][gender]),
                f'{year} {gender}'
            )
    conn.close()
    session = {'female_color': 'purple', 'male_color': 'orange'}
    m.plot_gender_names_analysis(results, session,
                                 output_filename=f"{output_stem}.png",
                                 formats=formats, bw=bw)


def build_figure_2(output_stem: Path, formats: tuple[str, ...], bw: bool = False) -> None:
    import tempfile
    m = _load_script("plot-years")
    with tempfile.TemporaryDirectory() as tmp:
        m.create_gender_plot('births', str(DB_PATH), tmp, formats=formats, bw=bw)
        for fmt in formats:
            src = Path(tmp) / f'years_births.{fmt}'
            if src.exists():
                shutil.copy2(src, Path(f"{output_stem}.{fmt}"))


def build_figure_3(output_stem: Path, formats: tuple[str, ...], bw: bool = False) -> None:
    m = _load_script("pub-years")
    data = m.get_data(str(DB_PATH))
    m.create_japanese_names_chart(data, f"{output_stem}.png", formats=formats, bw=bw)


def build_figure_4(output_stem: Path, formats: tuple[str, ...], bw: bool = False) -> None:
    m = _load_script("pub-years")
    data = m.get_data(str(DB_PATH))
    m.create_japanese_names_chart(data, f"{output_stem}.png",
                                  use_log_scale=True, formats=formats, bw=bw)


def _playwright_capture(url: str, output_stem: Path, formats: tuple[str, ...]) -> None:
    """Capture a single web page via Playwright and save to all requested formats."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as e:
        raise ImportError(
            "playwright is required: uv pip install playwright && playwright install chromium"
        ) from e

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": 1280, "height": 900})
        page.goto(url, wait_until="networkidle")
        page.wait_for_timeout(2000)

        if "png" in formats:
            page.screenshot(path=f"{output_stem}.png", full_page=False)
        if "pdf" in formats:
            page.pdf(path=f"{output_stem}.pdf",
                     width="1280px", height="900px",
                     print_background=True)
        if "svg" in formats:
            svg = page.evaluate("() => { const el = document.querySelector('svg'); return el ? el.outerHTML : null; }")
            if svg:
                Path(f"{output_stem}.svg").write_text(svg, encoding="utf-8")

        browser.close()


def build_figure_5a(output_stem: Path, formats: tuple[str, ...], bw: bool = False) -> None:
    """蓮 (れん /ren/) pronunciation page."""
    _playwright_capture(
        "http://127.0.0.1:5100/namae?pron=%E3%82%8C%E3%82%93",
        output_stem, formats)


def build_figure_5b(output_stem: Path, formats: tuple[str, ...], bw: bool = False) -> None:
    """蓮 (はす /hasu/) pronunciation page."""
    _playwright_capture(
        "http://127.0.0.1:5100/namae?pron=%E3%81%AF%E3%81%99",
        output_stem, formats)


def build_figure_6(output_stem: Path, formats: tuple[str, ...], bw: bool = False) -> None:
    m = _load_script("img-jinmei")
    m.plot_kanji_usage(output_path=str(output_stem), formats=formats, bw=bw)


def _bp_plot(src: str, dtype: str, output_stem: Path, formats: tuple[str, ...], bw: bool = False) -> None:
    from collections import defaultdict as dd
    m = _load_script("plot_meiji")
    conn = sqlite3.connect(str(DB_PATH))
    n_range = [1, 10, 50, 100] if dtype == 'orth' else [1, 5, 10, 50]
    selected_metrics = [f"Berger-Parker ({n})" for n in n_range]
    plot_data: dict = dd(lambda: dd(dict))
    for top_n in n_range:
        byyear = m.get_bp(top_n, dtype, src, conn=conn)
        for gender in ['M', 'F']:
            for year in byyear[gender]:
                if byyear[gender][year][0]:
                    plot_data[gender][year][f'Berger-Parker ({top_n})'] = \
                        1 - byyear[gender][year][0]
    conn.close()
    trend_stats = m.calculate_trend_statistics(plot_data, selected_metrics)
    m.plot_multi_panel_trends_with_stats(
        plot_data, selected_metrics, None,
        f"{output_stem}.png",
        trend_stats=trend_stats,
        formats=formats,
        bw=bw,
    )


def build_figure_7a(output_stem, formats, bw=False):
    _bp_plot('hs', 'orth', output_stem, formats, bw)

def build_figure_7b(output_stem, formats, bw=False):
    _bp_plot('meiji', 'orth', output_stem, formats, bw)

def build_figure_7c(output_stem, formats, bw=False):
    _bp_plot('meiji', 'pron', output_stem, formats, bw)


def build_figure_8(output_stem: Path, formats: tuple[str, ...], bw: bool = False) -> None:
    """Diversity measures for Heisei (hs orth diversity panel)."""
    import math
    from collections import Counter, defaultdict as dd
    m = _load_script("plot_meiji")
    db = _load_script("db")

    conn = sqlite3.connect(str(DB_PATH))
    table_name = db.db_options['hs'][0]
    byyear_raw = db.get_name_year(conn, src='hs', table=table_name, dtype='orth')
    conn.close()

    names: dict = {'M': dd(list), 'F': dd(list)}
    for year, genders in byyear_raw.items():
        for gender, name_list in genders.items():
            names[gender][year] = name_list

    def _shannon(ns):
        counts = Counter(ns)
        total = len(ns)
        return -sum((c/total) * math.log(c/total) for c in counts.values())

    def _gini_simpson(ns):
        counts = Counter(ns)
        total = len(ns)
        return 1 - sum((c/total)**2 for c in counts.values())

    def _singleton(ns):
        counts = Counter(ns)
        return sum(1 for c in counts.values() if c == 1) / len(ns) if ns else 0

    def _ttr(ns):
        return len(set(ns)) / len(ns) if ns else 0

    all_metrics: dict = {'M': {}, 'F': {}}
    for gender in ('M', 'F'):
        for year, ns in names[gender].items():
            if ns:
                all_metrics[gender][year] = {
                    'Shannon-Wiener': _shannon(ns),
                    'Gini-Simpson': _gini_simpson(ns),
                    'Singleton': _singleton(ns),
                    'TTR': _ttr(ns),
                }

    selected = ["Shannon-Wiener", "Gini-Simpson", "Singleton", "TTR"]
    trend_stats = m.calculate_trend_statistics(all_metrics, selected)
    m.plot_multi_panel_trends_with_stats(
        all_metrics, selected, "",
        f"{output_stem}.png",
        trend_stats=trend_stats,
        formats=formats,
        bw=bw,
    )


def build_figure_9(output_stem: Path, formats: tuple[str, ...], bw: bool = False) -> None:
    m = _load_script("plot_web_charts")
    m.plot_irregular(output_stem=str(output_stem), formats=formats, bw=bw)


def _overlap_graph(src: str, dtype: str, n_top: int, kind: str,
                   output_stem: Path, formats: tuple[str, ...], bw: bool = False) -> None:
    m = _load_script("plot_overlap")
    get_overlap_details = m.get_overlap_details
    details, totals = get_overlap_details(str(DB_PATH), src, dtype, n_top)
    data = []
    for year in details:
        total = totals[year]
        if total == 0:
            continue
        data.append((year, len(details[year]),
                     2 * sum(x[3] for x in details[year]) / total))
    if not data:
        print(f"  No overlap data for {src} {dtype} n={n_top}")
        return
    data.sort()
    years = [r[0] for r in data]
    if kind == 'count':
        values = [r[1] for r in data]
        ylabel = "Number of Overlapping Names"
    else:
        values = [r[2] * 100 for r in data]
        ylabel = "Weighted Overlap (%)"

    import numpy as np
    from scipy.stats import linregress
    from scipy.interpolate import PchipInterpolator

    color = 'black' if bw else '#1f77b4'

    fig, ax = plt.subplots(figsize=(8, 5))
    marker = 'o' if kind == 'count' else 's'
    ax.scatter(years, values, marker=marker, color=color, s=25, zorder=5,
               label='Overlap')
    if len(years) >= 3:
        interp = PchipInterpolator(years, values)
        xs = np.linspace(years[0], years[-1], 300)
        ax.plot(xs, interp(xs), color=color, linewidth=1.5)
    slope, intercept, _, p_value, _ = linregress(years, values)
    reg_x = np.array([min(years), max(years)])
    ax.plot(reg_x, slope * reg_x + intercept, color=color,
            linewidth=1.5, linestyle='-' if p_value < 0.05 else '--')
    ax.set_xlabel('Year')
    ax.set_ylabel(ylabel)
    if kind == 'weighted':
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f"{y:.1f}%"))
    ax.grid(True, alpha=0.3, axis='y')
    ax.set_ylim(bottom=0)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.set_xticks(range(min(years), max(years) + 1,
                        max(1, (max(years) - min(years)) // 10)))
    plt.tight_layout()
    for fmt in formats:
        fig.savefig(f"{output_stem}.{fmt}", dpi=300, bbox_inches='tight')
    plt.close(fig)


def build_figure_10(output_stem, formats, bw=False):
    _overlap_graph('bc', 'orth', 50, 'count', output_stem, formats, bw)

def build_figure_11a(output_stem, formats, bw=False):
    _proportion_graph('Pronunciation (2008-2022)', output_stem, formats, bw)

def build_figure_11b(output_stem, formats, bw=False):
    _proportion_graph('Orthography (2008-2022)', output_stem, formats, bw)

def build_figure_11c(output_stem, formats, bw=False):
    _proportion_graph('Name (full) (2008-2022)', output_stem, formats, bw)

def build_figure_12a(output_stem, formats, bw=False):
    _proportion_graph('Pronunciation (2008-2013)', output_stem, formats, bw)

def build_figure_12b(output_stem, formats, bw=False):
    _proportion_graph('Pronunciation (2014-2022)', output_stem, formats, bw)


def _proportion_graph(gname: str, output_stem: Path, formats: tuple[str, ...], bw: bool = False) -> None:
    """Copy or regenerate a proportion histogram."""
    src_png = PLOT_DIR / f"pron_gender_proportion_histogram_{gname}.png"
    if src_png.exists() and 'svg' not in formats:
        shutil.copy2(src_png, Path(f"{output_stem}.png"))
        return
    mp = _load_script("plot_proportion")
    db = _load_script("db")
    conn = sqlite3.connect(str(DB_PATH))
    table_name = db.db_options['bc'][0]
    names_raw = db.get_name_year(conn, src='bc', table=table_name, dtype='both')
    conn.close()

    # Build merged years matching the gname label
    label_map = {
        '2008-2013': lambda y: 2008 <= y <= 2013,
        '2008-2022': lambda y: 2008 <= y <= 2022,
        '2014-2022': lambda y: 2014 <= y <= 2022,
    }
    period_match = re.search(r'(\d{4}[-–]\d{4})', gname)
    period_str = period_match.group(1).replace('–', '-') if period_match else None
    period_fn = label_map.get(period_str, lambda y: True) if period_str else (lambda y: True)

    male: list = []
    female: list = []
    for year, genders in names_raw.items():
        if not period_fn(year):
            continue
        male += genders.get('M', [])
        female += genders.get('F', [])

    if 'Pronunciation' in gname:
        male_f = [p for (_, p) in male]
        female_f = [p for (_, p) in female]
    elif 'Orthography' in gname:
        male_f = [o for (o, _) in male]
        female_f = [o for (o, _) in female]
    else:
        male_f = [o + p for (o, p) in male]
        female_f = [o + p for (o, p) in female]

    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        stats, _ = mp.calculate_distribution(male_f, female_f, period_str or 'all')
        mp.graph_proportion2(stats, gname, title=False, plot_dir=tmp, formats=formats, bw=bw)
        for fmt in formats:
            src = Path(tmp) / f'pron_gender_proportion_histogram_{gname}.{fmt}'
            if src.exists():
                shutil.copy2(src, Path(f"{output_stem}.{fmt}"))


def build_figure_13a(output_stem, formats, bw=False):
    _overlap_graph('meiji', 'pron', 50, 'count', output_stem, formats, bw)

def build_figure_13b(output_stem, formats, bw=False):
    _overlap_graph('meiji', 'pron', 50, 'weighted', output_stem, formats, bw)

def build_figure_14a(output_stem, formats, bw=False):
    _overlap_graph('meiji', 'orth', 100, 'count', output_stem, formats, bw)

def build_figure_14b(output_stem, formats, bw=False):
    _overlap_graph('meiji', 'orth', 100, 'weighted', output_stem, formats, bw)

def build_figure_15a(output_stem, formats, bw=False):
    _overlap_graph('hs', 'orth', 500, 'count', output_stem, formats, bw)

def build_figure_15b(output_stem, formats, bw=False):
    _overlap_graph('hs', 'orth', 500, 'weighted', output_stem, formats, bw)


def build_figure_16(output_stem: Path, formats: tuple[str, ...], bw: bool = False) -> None:
    """Proportion of androgynous names over time in Heisei Namae data."""
    from scipy.interpolate import PchipInterpolator
    from scipy.stats import linregress
    import numpy as np

    with open(DATA_DIR / "androgyny_data.json", encoding="utf-8") as f:
        blob = json.load(f)

    ds = blob["hs_orth_token_tau2"]
    rows = ds["data"]
    years = [r["year"] for r in rows]
    proportions = [r["proportion"] for r in rows]
    reg = ds["regression"]

    color = 'black' if bw else '#2ca02c'
    reg_ls = '-' if reg.get('p_value', 1) < 0.05 else '--'

    fig, ax = plt.subplots(figsize=(10, 5))

    interp = PchipInterpolator(years, proportions)
    xs = np.linspace(min(years), max(years), 300)
    ax.plot(xs, interp(xs), color=color, linewidth=2.5, label="Androgynous")
    ax.scatter(years, proportions, color=color, s=18, zorder=5,
               edgecolors="white" if not bw else color, linewidths=1.2)

    reg_x = np.array([min(years), max(years)])
    ax.plot(reg_x, reg["slope"] * reg_x + reg["intercept"],
            color=color, linewidth=1.5, linestyle=reg_ls, alpha=0.7)

    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f"{y*100:.0f}%"))
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{int(x)}"))
    ax.set_xlabel("Year", fontsize=11)
    ax.set_ylabel("Proportion of Androgynous Names", fontsize=11)
    ax.set_ylim(bottom=0)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.legend(frameon=False, fontsize=10)
    ax.grid(axis="y", linestyle="-", linewidth=0.4, alpha=0.3, color="gray")

    total_a = sum(r["androgynous"] for r in rows)
    total_n = sum(r["total"] for r in rows)
    ax.text(0.02, 0.96, f"Overall: {total_a/total_n*100:.1f}% ({total_a:,}/{total_n:,})",
            transform=ax.transAxes, fontsize=8, color="gray", va="top")

    plt.tight_layout()
    for fmt in formats:
        fig.savefig(f"{output_stem}.{fmt}", dpi=300, bbox_inches="tight")
    plt.close(fig)


def _kanji_pos(kanji: str, gender: str, src: str,
               output_stem: Path, formats: tuple[str, ...], bw: bool = False) -> None:
    m = _load_script("plot_kanji_position")
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()
    meta = (kanji, gender, src)
    data = m.get_distribution(c, meta)
    conn.close()
    m.plot_kanji_positions(data, meta, title=False,
                           output_path=str(output_stem),
                           formats=formats, bw=bw)


def build_figure_17(output_stem, formats, bw=False):
    _kanji_pos('斗', 'M', 'hs', output_stem, formats, bw)

def build_figure_18(output_stem, formats, bw=False):
    _kanji_pos('翔', 'M', 'hs', output_stem, formats, bw)

def build_figure_19a(output_stem, formats, bw=False):
    _kanji_pos('陽', 'M', 'meiji', output_stem, formats, bw)

def build_figure_19b(output_stem, formats, bw=False):
    _kanji_pos('陽', 'F', 'meiji', output_stem, formats, bw)

def build_figure_20a(output_stem, formats, bw=False):
    _kanji_pos('凛', 'M', 'hs', output_stem, formats, bw)

def build_figure_20b(output_stem, formats, bw=False):
    _kanji_pos('凛', 'F', 'hs', output_stem, formats, bw)


def _genderedness_chart(dataset_key: str,
                         output_stem: Path, formats: tuple[str, ...], bw: bool = False) -> None:
    m = _load_script("plot_web_charts")
    datasets = m.load_genderedness()
    for ds in datasets:
        if ds['key'] == dataset_key:
            m.plot_genderedness_dataset(
                ds['data'], ds['regression_stats'], ds['caption'],
                output_stem=str(output_stem), formats=formats, bw=bw)
            return
    if datasets:
        ds = datasets[0]
        m.plot_genderedness_dataset(
            ds['data'], ds['regression_stats'], ds['caption'],
            output_stem=str(output_stem), formats=formats, bw=bw)
    else:
        print(f"  No genderedness data found for key: {dataset_key}")


def _find_genderedness_key(pattern: str) -> str:
    """Find first genderedness.json key matching a substring pattern."""
    with open(DATA_DIR / "genderedness.json", encoding="utf-8") as f:
        blob = json.load(f)
    for key in blob:
        if pattern in key:
            return key
    return next(iter(blob))  # fallback to first


def build_figure_21a(output_stem, formats, bw=False):
    key = _find_genderedness_key('hs_orth')
    _genderedness_chart(key, output_stem, formats, bw)

def build_figure_21b(output_stem, formats, bw=False):
    key = _find_genderedness_key('meiji_orth') if \
        any('meiji_orth' in k for k in json.load(open(DATA_DIR / "genderedness.json")).keys()) \
        else _find_genderedness_key('meiji')
    _genderedness_chart(key, output_stem, formats, bw)

def build_figure_21c(output_stem, formats, bw=False):
    key = _find_genderedness_key('meiji_pron') if \
        any('meiji_pron' in k for k in json.load(open(DATA_DIR / "genderedness.json")).keys()) \
        else _find_genderedness_key('meiji')
    _genderedness_chart(key, output_stem, formats, bw)


# Free-text notes shown in the index alongside each figure
FIGURE_NOTES: dict[str, str] = {
    '5a': 'Browser screenshot (web app, not matplotlib)',
    '5b': 'Browser screenshot (web app, not matplotlib)',
    '20a': 'Uses Heisei Namae Jiten data (1989–2009); manuscript caption references Meiji Yasuda.',
    '20b': 'Uses Heisei Namae Jiten data (1989–2009); manuscript caption references Meiji Yasuda.',
}

# Caption overrides: replaces the manuscript-extracted caption for specific figures.
CAPTION_OVERRIDES: dict[str, str] = {
    '20a': 'Position distribution of 凛 in names and as a single-kanji name (boys; Heisei Namae Jiten data)',
    '20b': 'Position distribution of 凛 in names and as a single-kanji name (girls; Heisei Namae Jiten data)',
}


def _get_caption(captions: dict[str, str], fig_id: str) -> str:
    """Return the caption for fig_id, with fallbacks to parent number and overrides."""
    if fig_id in CAPTION_OVERRIDES:
        return CAPTION_OVERRIDES[fig_id]
    if fig_id in captions:
        return captions[fig_id]
    # Fall back to parent figure number (strip trailing letter, e.g. '19a' -> '19')
    parent = fig_id.rstrip('abcdefgh')
    return captions.get(parent, "")

# Map of figure IDs to their builder functions
BUILDERS: dict[str, object] = {
    '1':   build_figure_1,
    '2':   build_figure_2,
    '3':   build_figure_3,
    '4':   build_figure_4,
    '5a':  build_figure_5a,
    '5b':  build_figure_5b,
    '6':   build_figure_6,
    '7a':  build_figure_7a,
    '7b':  build_figure_7b,
    '7c':  build_figure_7c,
    '8':   build_figure_8,
    '9':   build_figure_9,
    '11a': build_figure_11a,
    '11b': build_figure_11b,
    '11c': build_figure_11c,
    '12a': build_figure_12a,
    '12b': build_figure_12b,
    '13a': build_figure_13a,
    '13b': build_figure_13b,
    '14a': build_figure_14a,
    '14b': build_figure_14b,
    '15a': build_figure_15a,
    '15b': build_figure_15b,
    '16':  build_figure_16,
    '17':  build_figure_17,
    '18':  build_figure_18,
    '19a': build_figure_19a,
    '19b': build_figure_19b,
    '20a': build_figure_20a,
    '20b': build_figure_20b,
    '21a': build_figure_21a,
    '21b': build_figure_21b,
    '21c': build_figure_21c,
}


# ---------------------------------------------------------------------------
# Index generation
# ---------------------------------------------------------------------------

def _figure_label(fig_id: str) -> str:
    return f"Figure {fig_id.upper() if fig_id[-1].isalpha() else fig_id}"


def _manuscript_images(fig_id: str) -> list[str]:
    """Return manuscript image paths (relative to BOOK_DIR) for a figure ID."""
    ms_dir = BOOK_DIR / "manuscript"

    # Exact match: Figure_9_manuscript.png or Figure_7a_manuscript.png
    exact = ms_dir / f"Figure_{fig_id}_manuscript.png"
    if exact.exists():
        return [f"manuscript/Figure_{fig_id}_manuscript.png"]

    # Numbered variants: Figure_9_1_manuscript.png, Figure_9_2_manuscript.png
    numbered = sorted(ms_dir.glob(f"Figure_{fig_id}_[0-9]_manuscript.png"))
    if numbered:
        return [f"manuscript/{p.name}" for p in numbered]

    # Sub-figures like 19a/19b → try Figure_19_1, Figure_19_2
    m = re.match(r'(\d+)([a-z])$', fig_id)
    if m:
        num, letter = m.group(1), m.group(2)
        idx = ord(letter) - ord('a') + 1
        p = ms_dir / f"Figure_{num}_{idx}_manuscript.png"
        if p.exists():
            return [f"manuscript/Figure_{num}_{idx}_manuscript.png"]

    return []


def write_index_md(captions: dict[str, str], figure_ids: list[str],
                   formats: tuple[str, ...]) -> None:
    lines = ["# Book Figures Index\n"]
    for fig_id in figure_ids:
        label = _figure_label(fig_id)
        title = _get_caption(captions, fig_id)
        note = FIGURE_NOTES.get(fig_id, "")
        heading = f"{label}: {title}" if title else label
        lines.append(f"## {heading}\n")
        if note:
            lines.append(f"*{note}*\n")

        ms_imgs = _manuscript_images(fig_id)
        gen_imgs = [(fmt, f"Figure_{fig_id}.{fmt}")
                    for fmt in formats
                    if (BOOK_DIR / f"Figure_{fig_id}.{fmt}").exists()]

        cols: list[tuple[str, str]] = []
        for path in ms_imgs:
            cols.append(("Manuscript", f"![manuscript]({path})"))
        for fmt, fname in gen_imgs:
            if fmt in ("png", "svg"):
                cols.append((fmt.upper(), f"![{fmt}]({fname})"))

        if cols:
            headers = " | ".join(c[0] for c in cols)
            seps = " | ".join("---" for _ in cols)
            cells = " | ".join(c[1] for c in cols)
            lines.append(f"| {headers} |")
            lines.append(f"| {seps} |")
            lines.append(f"| {cells} |")
        lines.append("")

    (BOOK_DIR / "figure_index.md").write_text("\n".join(lines), encoding="utf-8")
    print("Written: book/figure_index.md")


def write_index_html(captions: dict[str, str], figure_ids: list[str],
                     formats: tuple[str, ...]) -> None:
    rows = []
    for fig_id in figure_ids:
        label = _figure_label(fig_id)
        title = _get_caption(captions, fig_id)
        note = FIGURE_NOTES.get(fig_id, "")
        heading = f"{label}: {title}" if title else label
        rows.append(f'  <h2>{heading}</h2>')
        if note:
            rows.append(f'  <p style="color:#888;font-style:italic;margin:.25em 0">{note}</p>')
        rows.append('  <div style="display:flex;gap:12px;align-items:flex-start;flex-wrap:wrap">')

        ms_imgs = _manuscript_images(fig_id)
        for path in ms_imgs:
            rows.append(
                f'    <figure style="flex:1;min-width:200px;margin:0">'
                f'<figcaption style="font-size:.85em;color:#555">Manuscript</figcaption>'
                f'<img src="{path}" style="max-width:100%;border:1px solid #ccc"></figure>'
            )

        for fmt in formats:
            fname = f"Figure_{fig_id}.{fmt}"
            out_path = BOOK_DIR / fname
            if not out_path.exists():
                continue
            if fmt in ("png", "svg"):
                rows.append(
                    f'    <figure style="flex:1;min-width:200px;margin:0">'
                    f'<figcaption style="font-size:.85em;color:#555">{fmt.upper()}</figcaption>'
                    f'<img src="{fname}" style="max-width:100%;border:1px solid #ccc"></figure>'
                )
            else:
                rows.append(f'    <p><a href="{fname}">{fname}</a></p>')

        rows.append('  </div>')

    html = (
        "<!DOCTYPE html>\n<html lang='en'>\n<head>\n"
        "<meta charset='UTF-8'>\n"
        "<title>Book Figures</title>\n"
        "<style>body{font-family:sans-serif;max-width:1400px;margin:2em auto;padding:0 1em}"
        " h2{margin-top:2em} figure img{display:block}"
        " figcaption{margin-bottom:.25em;font-weight:bold}</style>\n"
        "</head>\n<body>\n<h1>Book Figures</h1>\n"
        + "\n".join(rows)
        + "\n</body>\n</html>\n"
    )
    (BOOK_DIR / "figure_index.html").write_text(html, encoding="utf-8")
    print("Written: book/figure_index.html")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def _sorted_fig_ids(ids: list[str]) -> list[str]:
    def key(fid):
        m = re.match(r'(\d+)([a-z]?)', fid)
        return (int(m.group(1)), m.group(2)) if m else (0, fid)
    return sorted(ids, key=key)


def main():
    parser = argparse.ArgumentParser(description="Build all book figures")
    parser.add_argument("--formats", default="png,svg",
                        help="Comma-separated list of output formats (default: png,svg)")
    parser.add_argument("--skip-existing", action="store_true",
                        help="Skip figures whose PNG already exists in book/")
    parser.add_argument("--figures", default="",
                        help="Comma-separated subset of figure IDs to build (e.g. 1,7a,9)")
    parser.add_argument("--bw", action="store_true",
                        help="Build black-and-white SVG versions (output: Figure_X.bw.svg)")
    parser.add_argument("--index-only", action="store_true",
                        help="Regenerate index files without rebuilding any figures")
    args = parser.parse_args()

    formats = tuple(args.formats.split(","))
    BOOK_DIR.mkdir(exist_ok=True)

    print("Extracting figure captions from manuscript...")
    captions = extract_captions(DOC_PATH)
    print(f"  Found {len(captions)} figure captions")

    all_ids = _sorted_fig_ids(list(BUILDERS.keys()))

    if args.index_only:
        print("\nWriting index files...")
        write_index_md(captions, all_ids, formats)
        write_index_html(captions, all_ids, formats)
        return

    # Determine which figures to build
    if args.figures:
        requested = {f.strip() for f in args.figures.split(",")}
        all_ids = [fid for fid in all_ids if fid in requested]

    needs_flask = bool(set(all_ids) & FLASK_FIGURES)

    def _build_all(errors):
        bw_ctx = None
        if args.bw:
            from bw_style import apply_bw_rcparams
            bw_ctx = apply_bw_rcparams()
            bw_ctx.__enter__()

        try:
            for fig_id in all_ids:
                builder = BUILDERS.get(fig_id)
                label = _figure_label(fig_id)
                stem_name = f"Figure_{fig_id}.bw" if args.bw else f"Figure_{fig_id}"
                output_stem = BOOK_DIR / stem_name

                if builder is None:
                    print(f"  {label}: no builder defined — skipped")
                    continue

                if args.skip_existing:
                    existing = [Path(f"{output_stem}.{fmt}") for fmt in formats]
                    if all(p.exists() for p in existing):
                        print(f"  {label}: already exists — skipped")
                        continue

                title = captions.get(fig_id, "")
                suffix = " [B&W]" if args.bw else ""
                print(f"Building {label}{suffix}"
                      f"{': ' + title[:60] if title else ''}...")
                try:
                    builder(output_stem, formats, bw=args.bw)
                except Exception as exc:
                    print(f"  ERROR building {label}: {exc}")
                    errors.append((fig_id, exc))
        finally:
            if bw_ctx is not None:
                bw_ctx.__exit__(None, None, None)

    errors = []
    if needs_flask:
        with flask_server():
            _build_all(errors)
    else:
        _build_all(errors)

    print("\nWriting index files...")
    write_index_md(captions, all_ids, formats)
    write_index_html(captions, all_ids, formats)

    if errors:
        print(f"\n{len(errors)} figure(s) failed:")
        for fig_id, exc in errors:
            print(f"  Figure {fig_id}: {exc}")
        sys.exit(1)
    else:
        print(f"\nDone. {len(all_ids)} figures written to book/")


if __name__ == "__main__":
    main()
