"""Black-and-white style constants for publication figures.

Line-style convention:
  -.  dash-dot + filled circles   Female data
  :   dotted   + solid diamonds   Male data
  -   solid     Significant regression line   } shared by both genders,
  --  dashed    Non-significant regression    } distinguished by marker

Apply with the apply_bw_rcparams() context manager, then use the
BW_M / BW_F / BW_FILLS / BW_SESSION constants in plot functions.
"""
from contextlib import contextmanager
import matplotlib as mpl

# Female: dash-dot, filled circles
BW_F = dict(color='black', linestyle='-.', marker='o', markersize=5,
            linewidth=2.0, label='Girls')

# Male: dotted, solid diamonds
BW_M = dict(color='black', linestyle=':', marker='D', markersize=5,
            linewidth=2.0, label='Boys')

# Single-series (no gender): black solid, no marker by default
BW_SINGLE = dict(color='black', linestyle='-', linewidth=2.0)

# Two non-gender series (e.g. jinmei: name-only vs total)
BW_LINE_1 = dict(color='black', linestyle='-', linewidth=2.0)
BW_LINE_2 = dict(color='black', linestyle='--', linewidth=2.0)

# Session dict for scripts that accept male_color / female_color
BW_SESSION = {'male_color': 'black', 'female_color': 'dimgray'}

# Stacked fill styles for kanji-position charts (alpha=1 so hatching is visible)
BW_FILLS = [
    dict(facecolor='0.90', hatch='////', edgecolor='black',
         linewidth=0.0, alpha=1.0, label='Solo'),
    dict(facecolor='0.68', hatch='\\\\', edgecolor='black',
         linewidth=0.0, alpha=1.0, label='Initial'),
    dict(facecolor='0.45', hatch='xxxx', edgecolor='black',
         linewidth=0.0, alpha=1.0, label='Middle'),
    dict(facecolor='0.22', hatch='----', edgecolor='black',
         linewidth=0.0, alpha=1.0, label='End'),
]

# Dataset-coverage bar colors (pub-years.py figures 3/4)
BW_COVERAGE_COLORS = {
    'births':  '0.88',   # near-white background fill
    'hs':      '0.62',   # medium-light gray
    'totals':  '0.40',   # medium-dark gray
    'bc':      '0.20',   # near-black
}

BW_RCPARAMS = {
    'font.size': 12,
    'axes.labelsize': 13,
    'xtick.labelsize': 11,
    'ytick.labelsize': 11,
    'legend.fontsize': 11,
    'lines.linewidth': 2.0,
    'hatch.linewidth': 1.5,  # coarser hatching for print
}


@contextmanager
def apply_bw_rcparams():
    """Context manager: apply B&W rcParams, restore originals on exit."""
    old = {k: mpl.rcParams[k] for k in BW_RCPARAMS if k in mpl.rcParams}
    try:
        mpl.rcParams.update(BW_RCPARAMS)
        yield
    finally:
        mpl.rcParams.update(old)


# ---------- Book print / ebook style ----------

from pathlib import Path as _Path

BOOK_WIDTH_IN: float = 111 / 25.4     # 4.370 inches = 111 mm column width
BOOK_PANEL_H1: float = 3.0             # height (inches) for a single-panel figure
BOOK_PANEL_HN: float = 2.5             # height per panel in stacked multi-panel figures
BOOK_EBOOK_DPI: int = 150

_ROBOTO_DIR = _Path('/usr/share/fonts/truetype/roboto/unhinted')
_ROBOTO_FILES = [
    'RobotoCondensed-Regular.ttf',
    'RobotoCondensed-Bold.ttf',
    'RobotoCondensed-Italic.ttf',
    'RobotoCondensed-BoldItalic.ttf',
]


def register_roboto_condensed() -> None:
    """Register Roboto Condensed TrueType files with matplotlib's font manager."""
    from matplotlib import font_manager as _fm
    for fname in _ROBOTO_FILES:
        fp = _ROBOTO_DIR / fname
        if fp.exists():
            _fm.fontManager.addfont(str(fp))


BOOK_RCPARAMS: dict = {
    'font.family': 'sans-serif',
    'font.sans-serif': ['Roboto Condensed', 'Noto Sans CJK JP',
                        'Noto Sans CJK SC', 'DejaVu Sans'],
    'font.size': 7,
    'axes.labelsize': 7,
    'axes.titlesize': 8,
    'xtick.labelsize': 6,
    'ytick.labelsize': 6,
    'legend.fontsize': 6,
    'lines.linewidth': 0.9,
    'lines.markersize': 3.5,
    'hatch.linewidth': 1.5,
    'savefig.dpi': BOOK_EBOOK_DPI,
}


@contextmanager
def apply_book_rcparams(bw: bool = False):
    """Apply book-style rcParams (Roboto Condensed, 7 pt, 150 DPI), optionally B&W.

    Registers Roboto Condensed at entry.  When bw=True, also temporarily scales down
    BW_F and BW_M line/marker sizes to match the narrower column width.
    """
    register_roboto_condensed()
    params = dict(BOOK_RCPARAMS)
    if bw:
        params['hatch.linewidth'] = BW_RCPARAMS['hatch.linewidth']

    old_rc = {k: mpl.rcParams[k] for k in params if k in mpl.rcParams}

    # Temporarily reduce BW_F / BW_M for the narrow column width
    _book_lw = params['lines.linewidth']
    _book_ms = params['lines.markersize']
    old_bw_f = {k: BW_F[k] for k in ('linewidth', 'markersize')}
    old_bw_m = {k: BW_M[k] for k in ('linewidth', 'markersize')}
    if bw:
        BW_F['linewidth'] = _book_lw
        BW_M['linewidth'] = _book_lw
        BW_F['markersize'] = _book_ms
        BW_M['markersize'] = _book_ms

    try:
        mpl.rcParams.update(params)
        yield
    finally:
        mpl.rcParams.update(old_rc)
        BW_F.update(old_bw_f)
        BW_M.update(old_bw_m)
