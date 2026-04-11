"""Matplotlib recreations of the D3.js web charts for book figures.

Reads pre-computed JSON data and produces publication-ready PNG/SVG figures
for the irregular names chart and genderedness charts.
"""

import json
import os
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.lines as mlines
import numpy as np
from scipy import stats as scipy_stats

current_directory = os.path.abspath(os.path.dirname(__file__))
DATA_DIR = Path(current_directory) / ".." / "web" / "static" / "data"

MALE_COLOR = "#ff7f0e"
FEMALE_COLOR = "#9467bd"


def _regression_line(years, slope, intercept):
    x = np.array([min(years), max(years)])
    return x, slope * x + intercept


def _add_trend_lines(ax, regression_stats, xscale, yscale, male_color, female_color):
    """Overlay regression lines onto ax using raw year/value data."""
    for gkey, color in (("M", male_color), ("F", female_color)):
        rs = (regression_stats or {}).get(gkey)
        if not rs or not rs.get("years"):
            continue
        xs, ys = _regression_line(rs["years"], rs["slope"], rs["intercept"])
        sig = rs.get("p_value", 1.0) < 0.05
        ax.plot(xs, ys, color=color,
                linewidth=1.5,
                linestyle="-" if sig else "--",
                alpha=0.85 if sig else 0.55)


def plot_irregular(data_path=None, output_stem=None, formats=("png",),
                   width_in=10, height_in=5):
    """Plot proportion of irregular name readings over time (M vs F).

    Args:
        data_path: Path to irregular_data.json; defaults to the repo default.
        output_stem: Output path without extension (e.g. 'book/Figure_9').
        formats: Tuple of formats to save, e.g. ('png', 'svg').
        width_in: Figure width in inches.
        height_in: Figure height in inches.
    """
    if data_path is None:
        data_path = DATA_DIR / "irregular_data.json"

    with open(data_path, encoding="utf-8") as f:
        blob = json.load(f)

    # The JSON has a "bc" key whose "data" list contains row dicts
    raw = blob.get("bc", blob)
    rows = raw.get("data", raw) if isinstance(raw, dict) else raw

    # Separate into gender series and compute proportion
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

    # Compute regression stats
    reg = {}
    for g, color in (("M", MALE_COLOR), ("F", FEMALE_COLOR)):
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
        ax.plot(yrs, vals, color=color, linewidth=2.5, label=label)
        ax.scatter(yrs, vals, color=color, s=18, zorder=5,
                   edgecolors="white", linewidths=1.2)

    _add_trend_lines(ax, reg, None, None, MALE_COLOR, FEMALE_COLOR)

    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f"{y*100:.0f}%"))
    ax.set_xlabel("Year", fontsize=11)
    ax.set_ylabel("Irregular Proportion", fontsize=11)
    ax.set_ylim(bottom=0)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.legend(frameon=False, fontsize=10)
    ax.grid(axis="y", linestyle="-", linewidth=0.4, alpha=0.3, color="gray")

    # Summary stats annotation (overall totals across all years)
    totals = {g: (sum(p[2] for p in pts), sum(p[3] for p in pts))
              for g, pts in series.items() if pts}
    label_map = {"M": "Male", "F": "Female"}
    parts = [f"{label_map[g]} {irr/n*100:.1f}% ({irr:,}/{n:,})"
             for g, (irr, n) in sorted(totals.items())]
    ax.text(0.02, 0.04, "Overall: " + "; ".join(parts),
            transform=ax.transAxes, fontsize=8, color="gray", va="bottom")

    plt.tight_layout()

    if output_stem:
        for fmt in formats:
            fig.savefig(f"{output_stem}.{fmt}", dpi=300, bbox_inches="tight")
        plt.close(fig)
    return fig, ax


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
        ax.plot(yrs, vals, color=color, linewidth=2.5, label=label)
        ax.scatter(yrs, vals, color=color, s=18, zorder=5,
                   edgecolors="white", linewidths=1.2)

    _add_trend_lines(ax, regression_stats, None, None, MALE_COLOR, FEMALE_COLOR)

    ax.set_xlabel("Year", fontsize=11)
    ax.set_ylabel("Genderedness", fontsize=11)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.legend(frameon=False, fontsize=10)
    ax.grid(axis="y", linestyle="-", linewidth=0.4, alpha=0.3, color="gray")
    plt.tight_layout()

    if output_stem:
        for fmt in formats:
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
