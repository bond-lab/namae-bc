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
