"""Matplotlib equivalents of the web D3.js charts.

Reads pre-computed JSON data and produces SVGs for both the book (via
build_book_figures.py) and the live web app (via calc_web_figures.py).

All M/F colour constants live in web_plot_style so every chart stays
consistent. save_web_svg() injects CSS variable references so inlined SVGs
respond to the site's colour-theme switcher.
"""

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import MaxNLocator
from scipy import stats as scipy_stats

from web_plot_style import (
    MALE_COLOR, FEMALE_COLOR, NEUTRAL_COLOR, ANDROGYNY_COLOR,
    WEB_FIGSIZE,
    apply_axes_style, smooth_plot, add_regression_line, save_web_svg,
)

DATA_DIR = Path(__file__).parent / ".." / "web" / "static" / "data"


# ---------------------------------------------------------------------------
# Irregular names
# ---------------------------------------------------------------------------

def plot_irregular(data_path=None, output_stem=None, formats=("png",),
                   width_in=10, height_in=5):
    """Plot proportion of irregular name readings over time (M vs F).

    Args:
        data_path: Path to irregular_data.json; defaults to repo default.
        output_stem: Output path without extension (e.g. 'book/Figure_9').
        formats: Tuple of formats to save, e.g. ('png', 'svg').
        width_in: Figure width in inches.
        height_in: Figure height in inches.
    """
    if data_path is None:
        data_path = DATA_DIR / "irregular_data.json"

    with open(data_path, encoding="utf-8") as f:
        blob = json.load(f)

    raw = blob.get("bc", blob)
    rows = raw.get("data", raw) if isinstance(raw, dict) else raw

    series = {"M": [], "F": []}
    for row in rows:
        g = row.get("gender")
        if g not in series:
            continue
        n = row.get("number", 0)
        irr = row.get("irregular_names", 0)
        if n > 0:
            series[g].append((int(row["year"]), irr / n, irr, n))

    for g in series:
        series[g].sort(key=lambda x: x[0])

    reg = {}
    for g in ("M", "F"):
        pts = series[g]
        if len(pts) >= 3:
            yrs = np.array([p[0] for p in pts])
            vals = np.array([p[1] for p in pts])
            slope, intercept, _, p_value, _ = scipy_stats.linregress(yrs, vals)
            reg[g] = {"slope": slope, "intercept": intercept,
                      "p_value": p_value, "years": yrs.tolist()}

    fig, ax = plt.subplots(figsize=(width_in, height_in))

    for g, color, label in (("M", MALE_COLOR, "Male"), ("F", FEMALE_COLOR, "Female")):
        pts = series[g]
        if not pts:
            continue
        yrs = [p[0] for p in pts]
        vals = [p[1] for p in pts]
        smooth_plot(ax, yrs, vals, color=color, linewidth=2.5, label=label)
        ax.scatter(yrs, vals, color=color, s=18, zorder=5,
                   edgecolors="white", linewidths=1.2)
        add_regression_line(ax, reg.get(g), color)

    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f"{y*100:.0f}%"))
    ax.set_xlabel("Year", fontsize=11)
    ax.set_ylabel("Irregular Proportion", fontsize=11)
    ax.set_ylim(bottom=0)
    apply_axes_style(ax)
    ax.legend(frameon=False, fontsize=10)

    totals = {g: (sum(p[2] for p in pts), sum(p[3] for p in pts))
              for g, pts in series.items() if pts}
    parts = [f"{'Male' if g == 'M' else 'Female'} {irr/n*100:.1f}% ({irr:,}/{n:,})"
             for g, (irr, n) in sorted(totals.items())]
    ax.text(0.02, 0.04, "Overall: " + "; ".join(parts),
            transform=ax.transAxes, fontsize=8, color="gray", va="bottom")

    plt.tight_layout()

    if output_stem:
        for fmt in formats:
            if fmt == "svg_web":
                save_web_svg(fig, f"{output_stem}.svg")
            else:
                fig.savefig(f"{output_stem}.{fmt}", dpi=300, bbox_inches="tight")
        plt.close(fig)
    return fig, ax


# ---------------------------------------------------------------------------
# Genderedness
# ---------------------------------------------------------------------------

def plot_genderedness_dataset(data, regression_stats, caption,
                              output_stem=None, formats=("png",),
                              width_in=10, height_in=5):
    """Plot a single genderedness dataset (M vs F over time).

    Args:
        data: List of {year, gender, value} dicts.
        regression_stats: Dict with M/F regression info.
        caption: Chart title string.
        output_stem: Output path without extension.
        formats: Tuple of formats to save.
    """
    series = {"M": [], "F": []}
    for row in data:
        g = row.get("gender")
        if g in series:
            series[g].append((int(row["year"]), float(row["value"])))
    for g in series:
        series[g].sort(key=lambda x: x[0])

    fig, ax = plt.subplots(figsize=(width_in, height_in))

    for g, color, label in (("M", MALE_COLOR, "Male"), ("F", FEMALE_COLOR, "Female")):
        pts = series[g]
        if not pts:
            continue
        yrs = [p[0] for p in pts]
        vals = [p[1] for p in pts]
        smooth_plot(ax, yrs, vals, color=color, linewidth=2.5, label=label)
        ax.scatter(yrs, vals, color=color, s=18, zorder=5,
                   edgecolors="white", linewidths=1.2)
        add_regression_line(ax, (regression_stats or {}).get(g), color)

    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{int(x)}"))
    ax.set_xlabel("Year", fontsize=11)
    ax.set_ylabel("Genderedness", fontsize=11)
    apply_axes_style(ax)
    ax.legend(frameon=False, fontsize=10)
    plt.tight_layout()

    if output_stem:
        for fmt in formats:
            if fmt == "svg_web":
                save_web_svg(fig, f"{output_stem}.svg")
            else:
                fig.savefig(f"{output_stem}.{fmt}", dpi=300, bbox_inches="tight")
        plt.close(fig)
    return fig, ax


def load_genderedness(data_path=None):
    """Load and parse genderedness.json, returning a list of dataset dicts.

    Each element has: key, caption, data, regression_stats.
    """
    if data_path is None:
        data_path = DATA_DIR / "genderedness.json"

    with open(data_path, encoding="utf-8") as f:
        blob = json.load(f)

    datasets = []
    for key, ds in blob.items():
        rows = []
        for row in ds.get("rows", []):
            if not isinstance(row, list) or len(row) < 3:
                continue
            try:
                year, gender, value = int(row[0]), str(row[1]), float(row[2])
            except (ValueError, TypeError):
                continue
            if gender in ("M", "F"):
                rows.append({"year": year, "gender": gender, "value": value})

        trends = ds.get("trends", {})
        reg = {}
        for g in ("M", "F"):
            t = trends.get(g)
            if not t:
                continue
            g_years = sorted({r["year"] for r in rows if r["gender"] == g})
            reg[g] = {
                "slope": float(t.get("slope", 0.0)),
                "intercept": float(t.get("intercept", 0.0)),
                "p_value": float(t.get("pvalue", t.get("p_value", 1.0))),
                "years": g_years,
            }

        datasets.append({
            "key": key,
            "caption": ds.get("caption", key),
            "data": rows,
            "regression_stats": reg,
        })

    return datasets


# ---------------------------------------------------------------------------
# Overlap (count + proportion as a two-subplot figure)
# ---------------------------------------------------------------------------

def plot_overlap_dataset(data, reg_count, reg_proportion, caption="",
                         output_stem=None, formats=("svg",),
                         width_in=9, height_in=4):
    """Plot overlap count and weighted proportion over time (2 subplots).

    Args:
        data: List of {year, overlap_count, weighted_proportion} dicts.
        reg_count: Regression stats dict for the count series.
        reg_proportion: Regression stats dict for the proportion series.
        caption: Figure suptitle.
        output_stem: Output path without extension.
        formats: Tuple of formats to save.
    """
    rows = sorted(data, key=lambda d: d["year"])
    if not rows:
        return None, None

    years = [d["year"] for d in rows]
    counts = [d["overlap_count"] for d in rows]
    proportions = [d["weighted_proportion"] for d in rows]

    fig, (ax_c, ax_p) = plt.subplots(1, 2, figsize=(width_in, height_in))

    for ax, vals, reg, ylabel in (
        (ax_c, counts, reg_count, "Overlap Count"),
        (ax_p, proportions, reg_proportion, "Proportion Overlap"),
    ):
        if len(years) >= 3:
            smooth_plot(ax, years, vals, color=NEUTRAL_COLOR, linewidth=2.5)
        else:
            ax.plot(years, vals, color=NEUTRAL_COLOR, linewidth=2.5)
        ax.scatter(years, vals, color=NEUTRAL_COLOR, s=18, zorder=5,
                   edgecolors="white", linewidths=1.2)
        add_regression_line(ax, reg, NEUTRAL_COLOR)
        ax.set_xlabel("Year", fontsize=10)
        ax.set_ylabel(ylabel, fontsize=10)
        apply_axes_style(ax)

    ax_p.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f"{y*100:.1f}%"))
    plt.tight_layout()

    if output_stem:
        for fmt in formats:
            if fmt == "svg_web":
                save_web_svg(fig, f"{output_stem}.svg")
            else:
                fig.savefig(f"{output_stem}.{fmt}", dpi=300, bbox_inches="tight")
        plt.close(fig)
    return fig, (ax_c, ax_p)


# ---------------------------------------------------------------------------
# Androgyny (single proportion series)
# ---------------------------------------------------------------------------

def plot_androgyny_dataset(data, regression, caption="",
                           output_stem=None, formats=("svg",),
                           width_in=7, height_in=4):
    """Plot proportion of androgynous names over time.

    Args:
        data: List of {year, proportion} dicts.
        regression: Regression stats dict {slope, intercept, years, p_value}.
        caption: Figure title.
        output_stem: Output path without extension.
        formats: Tuple of formats to save.
    """
    rows = sorted(data, key=lambda d: d["year"])
    if not rows:
        return None, None

    years = [d["year"] for d in rows]
    props = [d["proportion"] for d in rows]

    fig, ax = plt.subplots(figsize=(width_in, height_in))

    if len(years) >= 3:
        smooth_plot(ax, years, props, color=ANDROGYNY_COLOR, linewidth=2.5)
    else:
        ax.plot(years, props, color=ANDROGYNY_COLOR, linewidth=2.5)
    ax.scatter(years, props, color=ANDROGYNY_COLOR, s=18, zorder=5,
               edgecolors="white", linewidths=1.2)
    add_regression_line(ax, regression, ANDROGYNY_COLOR)

    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f"{y*100:.1f}%"))
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    ax.set_xlabel("Year", fontsize=10)
    ax.set_ylabel("Androgynous Proportion", fontsize=10)
    apply_axes_style(ax)
    plt.tight_layout()

    if output_stem:
        for fmt in formats:
            if fmt == "svg_web":
                save_web_svg(fig, f"{output_stem}.svg")
            else:
                fig.savefig(f"{output_stem}.{fmt}", dpi=300, bbox_inches="tight")
        plt.close(fig)
    return fig, ax


# ---------------------------------------------------------------------------
# Diversity (2×2 panel of selected metrics, M vs F)
# ---------------------------------------------------------------------------

_DIVERSITY_GROUPS = {
    "Var": ["Shannon-Wiener", "Evenness", "Gini-Simpson", "Berger-Parker (1)"],
    "BP": ["Berger-Parker (5)", "Berger-Parker (10)", "Berger-Parker (50)", "Berger-Parker (100)"],
    "TTR_Newness": ["TTR", "Newness", "Char TTR", "Char Newness"],
}


def _diversity_trend_stats(metrics_by_gender, metric_names):
    """Compute linear regression stats for each gender × metric combination.

    Returns nested dict: {gender: {metric: {slope, intercept, p_value,
    correlation, annual_change, mean}}}.
    """
    from scipy.stats import pearsonr

    result = {"M": {}, "F": {}}
    for gender in ("M", "F"):
        year_data = metrics_by_gender.get(gender, {})
        for metric in metric_names:
            pts = sorted(
                (int(yr), vals[metric])
                for yr, vals in year_data.items()
                if metric in vals
            )
            if len(pts) < 3:
                result[gender][metric] = None
                continue
            yrs = np.array([p[0] for p in pts], dtype=float)
            vals = np.array([p[1] for p in pts], dtype=float)
            slope, intercept, _, p_value, _ = scipy_stats.linregress(yrs, vals)
            correlation, _ = pearsonr(yrs, vals)
            pct_changes = [
                (vals[i] - vals[i - 1]) / vals[i - 1] * 100
                for i in range(1, len(vals)) if vals[i - 1] != 0
            ]
            result[gender][metric] = {
                "slope": slope, "intercept": intercept,
                "p_value": p_value, "correlation": correlation,
                "annual_change": float(np.mean(pct_changes)) if pct_changes else 0.0,
                "mean": float(np.mean(vals)),
                "years": yrs,
            }
    return result


def plot_diversity_group(metrics_by_gender, metric_names,
                         output_stem=None, formats=("svg_web",),
                         width_in=11, height_in=9):
    """Plot a 2×2 panel of diversity metrics (M vs F with PCHIP smoothing + regression).

    Args:
        metrics_by_gender: {gender: {year_str: {metric: value}}} dict.
        metric_names: List of up to 4 metric names to plot.
        output_stem: Output path without extension.
        formats: Tuple of formats to save.
        width_in: Figure width in inches.
        height_in: Figure height in inches.
    """
    import matplotlib.lines as mlines

    trend_stats = _diversity_trend_stats(metrics_by_gender, metric_names)

    n = len(metric_names)
    nrows, ncols = (1, n) if n <= 2 else (2, 2)
    fig, axes_grid = plt.subplots(nrows, ncols, figsize=(width_in, height_in))
    axes = np.array(axes_grid).flatten()

    for idx, metric in enumerate(metric_names):
        ax = axes[idx]
        legend_handles, legend_labels = [], []

        for gender, color, label in (("M", MALE_COLOR, "Male"), ("F", FEMALE_COLOR, "Female")):
            year_data = metrics_by_gender.get(gender, {})
            pts = sorted(
                (int(yr), vmap[metric])
                for yr, vmap in year_data.items()
                if metric in vmap
            )
            if not pts:
                continue
            yrs = [p[0] for p in pts]
            vals = [p[1] for p in pts]
            smooth_plot(ax, yrs, vals, color=color, linewidth=2)
            ax.scatter(yrs, vals, color=color, s=16, zorder=5,
                       edgecolors="white", linewidths=1.0)

            ts = trend_stats[gender].get(metric)
            if ts is not None:
                yrs_arr = ts["years"]
                trend_line = ts["slope"] * yrs_arr + (
                    np.mean(vals) - ts["slope"] * np.mean(yrs_arr)
                )
                lstyle = "-" if ts["p_value"] < 0.05 else "--"
                ax.plot(yrs_arr, trend_line, color=color, linestyle=lstyle,
                        alpha=0.7, linewidth=1)

                r, p, ac, mn = ts["correlation"], ts["p_value"], ts["annual_change"], ts["mean"]
                sig = "*" if p < 0.05 else ""
                stat_str = f"r={r:.3f}{sig}, {ac:+.3f}%/yr, mean={mn:.3f}"
                legend_labels.append(f"{label}: {stat_str}")
            else:
                legend_labels.append(label)

            legend_handles.append(
                mlines.Line2D([], [], color=color, marker="o",
                              linestyle=":", linewidth=2, markersize=5)
            )

        ax.xaxis.set_major_locator(MaxNLocator(integer=True))
        ax.set_title(metric, fontsize=10, fontweight="bold")
        apply_axes_style(ax)
        if legend_handles:
            leg = ax.legend(legend_handles, legend_labels, loc="best",
                            frameon=True, fontsize=8, framealpha=0.8,
                            edgecolor="none")
            leg.get_frame().set_facecolor("white")

    for idx in range(n, len(axes)):
        axes[idx].set_visible(False)

    plt.tight_layout()

    if output_stem:
        for fmt in formats:
            if fmt == "svg_web":
                save_web_svg(fig, f"{output_stem}.svg")
            else:
                fig.savefig(f"{output_stem}.{fmt}", dpi=300, bbox_inches="tight")
        plt.close(fig)
    return fig, axes


def diversity_group_keys():
    """Return the canonical dict of group_name → metric list for diversity plots."""
    return dict(_DIVERSITY_GROUPS)


# ---------------------------------------------------------------------------
# CLI entry-point (book figure generation)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Plot web-based charts as matplotlib figures")
    parser.add_argument("--output-dir", default=".", help="Output directory")
    parser.add_argument("--formats", default="png,svg", help="Comma-separated formats")
    args = parser.parse_args()

    fmts = tuple(args.formats.split(","))
    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)

    plt.rcParams["svg.fonttype"] = "path"

    plot_irregular(output_stem=str(out / "irregular"), formats=fmts)
    print("Saved irregular chart")

    for ds in load_genderedness():
        plot_genderedness_dataset(
            ds["data"], ds["regression_stats"], ds["caption"],
            output_stem=str(out / ds["key"]),
            formats=fmts,
        )
        print(f"Saved genderedness chart: {ds['key']}")
