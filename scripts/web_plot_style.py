"""Shared matplotlib style for web SVG figures.

Color constants are the single source of truth for M/F colors used in all
web-facing plots.  The same hex values appear as fallbacks in CSS variables
so the browser color-theme switcher can override them in inlined SVGs.
"""

import io
import re
from pathlib import Path
from typing import Union

import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import PchipInterpolator

# Palette — must match routes.py COLOR_HEX and layout.html CSS var fallbacks
MALE_COLOR = "#ff7f0e"
FEMALE_COLOR = "#9467bd"
NEUTRAL_COLOR = "#1f77b4"   # single-series charts (overlap count/proportion)
ANDROGYNY_COLOR = "#2ca02c"

WEB_FIGSIZE = (9, 4.5)


def apply_axes_style(ax) -> None:
    """Remove top/right spines; add subtle horizontal grid."""
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="y", linestyle="-", linewidth=0.4, alpha=0.3, color="gray")


def smooth_plot(ax, xdata, ydata, n: int = 300, **kwargs) -> None:
    """Plot a PCHIP-smoothed curve (equivalent to D3's curveMonotoneX)."""
    interp = PchipInterpolator(xdata, ydata)
    xs = np.linspace(min(xdata), max(xdata), n)
    ax.plot(xs, interp(xs), **kwargs)


def add_regression_line(ax, reg: dict, color: str) -> None:
    """Overlay a regression line from a {slope, intercept, years, p_value} dict."""
    if not reg or not reg.get("years"):
        return
    years = np.array(reg["years"])
    xs = np.array([years.min(), years.max()])
    ys = reg["slope"] * xs + reg["intercept"]
    sig = reg.get("p_value", 1.0) < 0.05
    ax.plot(xs, ys, color=color, linewidth=1.5,
            linestyle="-" if sig else "--",
            alpha=0.85 if sig else 0.55)


def inject_css_vars(svg: str) -> str:
    """Replace M/F sentinel hex values with CSS vars; make SVG scale to container."""
    svg = svg.replace(MALE_COLOR, f"var(--color-male,{MALE_COLOR})")
    svg = svg.replace(FEMALE_COLOR, f"var(--color-female,{FEMALE_COLOR})")
    svg = re.sub(
        r'(<svg[^>]*?)\s+width="[^"]*pt"\s+height="[^"]*pt"',
        r'\1 style="width:100%;height:auto"',
        svg, count=1,
    )
    return svg


def save_web_svg(fig: plt.Figure, path: Union[str, Path]) -> None:
    """Save a matplotlib figure as a CSS-variable-aware SVG for the web."""
    buf = io.StringIO()
    fig.savefig(buf, format="svg", bbox_inches="tight")
    with open(path, "w", encoding="utf-8") as f:
        f.write(inject_css_vars(buf.getvalue()))
