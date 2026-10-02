#!/usr/bin/env python3
"""
Cross-source agreement analysis for Benesse and Akachan Honpo.

Computes name overlap (common names count) and Jensen-Shannon divergence
between pairs of sources for overlapping years (2018-2025).

Comparisons:
  benesse vs meiji   (orth, both genders)
  akachan vs meiji   (orth, both genders)
  benesse vs akachan (orth, both genders)
  benesse vs bc      (orth, both genders)
  akachan vs bc      (orth, both genders)

Every comparison here uses a 1/rank proxy weight, even for years/sources
where `nrank.freq` is populated (see `get_nrank` for why).

Benesse vs Akachan 2023 is excluded (see `_EXCLUDE`): Akachan's published
list was already truncated by then, and the year's common-name overlap is
too small for a stable JS estimate.

Output:
  ../web/static/data/book_tables.json  — 'ch_new_sources' key appended
  Plots saved to ../web/static/plot/ (PNG) and ../book/ (PNG+SVG)

Usage:
    python pub-agreement-new-sources.py [DB_PATH]
"""

import json
import os
import sqlite3
import sys
from collections import defaultdict as dd
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.spatial.distance import jensenshannon

# ── paths ──────────────────────────────────────────────────────────────────
_script_dir = Path(__file__).parent
_default_db = _script_dir / ".." / "web" / "db" / "namae.db"
_plot_dir   = _script_dir / ".." / "web" / "static" / "plot"
_book_dir   = _script_dir / ".." / "book"
_tables_json = _script_dir / ".." / "web" / "static" / "data" / "book_tables.json"


# ── data retrieval ─────────────────────────────────────────────────────────

def get_nrank(conn: sqlite3.Connection, src: str, years: list[int] | None = None
              ) -> dict[int, dict[str, dict[str, float]]]:
    """
    Return {year: {gender: {orth: weight}}} from nrank.

    Weight is always 1/rank, never real frequency, even when `nrank.freq`
    is populated. Benesse only has `freq` for 2018 and Akachan never has
    it; weighting some years by real frequency and others by a rank proxy
    within the same series would mix two different distribution shapes for
    reasons unrelated to actual popularity shifts (e.g. this previously
    made 2018 Benesse comparisons look artificially more/less similar than
    neighbouring years purely because 2018 used a different weighting
    scheme). Using 1/rank uniformly keeps every comparison in this script
    internally consistent across its full year range.
    """
    sql = """
        SELECT year, gender, orth, rank
        FROM nrank
        WHERE src = ? AND orth IS NOT NULL AND rank IS NOT NULL
        ORDER BY year, gender, rank
    """
    data: dict = dd(lambda: dd(lambda: dd(float)))
    for year, gender, orth, rank in conn.execute(sql, (src,)):
        if years and year not in years:
            continue
        data[year][gender][orth] = 1.0 / rank
    return {y: dict(g) for y, g in data.items()}


def _compare(freq_a: dict[str, float], freq_b: dict[str, float]
             ) -> dict[str, object]:
    """Compare two {name: weight} dicts; return overlap and JS divergence."""
    common = sorted(set(freq_a) & set(freq_b))
    if not common:
        return {"common": 0, "js": float("nan"), "n_a": len(freq_a), "n_b": len(freq_b)}

    a = np.array([freq_a[n] for n in common], dtype=float)
    b = np.array([freq_b[n] for n in common], dtype=float)
    a /= a.sum(); b /= b.sum()

    return {
        "common": len(common),
        "js": float(jensenshannon(a, b)),
        "n_a": len(freq_a),
        "n_b": len(freq_b),
    }


# Years excluded per (source_a, source_b) pair, and why. Benesse vs Akachan
# 2023: Akachan's list was already truncated (post-2021) to ~10-15 names by
# then, and that year's overlap with Benesse collapses to 6 names (F) / 15
# names (M) -- too few common names for a stable JS divergence estimate; it
# produces the series' most extreme value (JS=0.59), a small-sample artefact
# of the truncation rather than a genuine jump in disagreement.
_EXCLUDE: dict[tuple[str, str], set[int]] = {
    ("benesse", "akachan"): {2023},
}


def compare_sources(data_a: dict, data_b: dict,
                    label: str, exclude_years: set[int] | None = None
                    ) -> dict[str, dict[int, dict]]:
    """Compare two source dicts across all shared years and genders."""
    results: dict[str, dict[int, dict]] = {"M": {}, "F": {}}
    shared_years = sorted(set(data_a) & set(data_b))
    for year in shared_years:
        if exclude_years and year in exclude_years:
            continue
        for gender in ("M", "F"):
            if gender in data_a.get(year, {}) and gender in data_b.get(year, {}):
                results[gender][year] = _compare(
                    data_a[year][gender], data_b[year][gender])
    return results


# ── plotting ───────────────────────────────────────────────────────────────

_GENDER_STYLE = {
    "M": {"color": "#2166ac", "linestyle": "-",  "marker": "o", "label": "Male"},
    "F": {"color": "#d6604d", "linestyle": "--", "marker": "s", "label": "Female"},
}


def plot_comparison(results: dict[str, dict[int, dict]],
                    label_a: str, label_b: str,
                    out_stem: str,
                    formats: tuple[str, ...] = ("png",)) -> None:
    """Two-panel figure: common names (top) and JS divergence (bottom)."""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 8), sharex=True)
    fig.suptitle(f"{label_a} vs {label_b}", fontsize=13)

    for gender, ax, ylabel, key in [
        ("M", ax1, "Common names (M)", "common"),
        ("M", ax1, "Common names", "common"),  # placeholder; overwritten below
    ]:
        break  # just unpack once

    for ax, key, ylabel in [
        (ax1, "common", "Common names (count)"),
        (ax2, "js",     "Jensen-Shannon divergence"),
    ]:
        for gender, style in _GENDER_STYLE.items():
            d = results.get(gender, {})
            if not d:
                continue
            years = sorted(d)
            vals  = [d[y][key] for y in years]
            ax.plot(years, vals, label=style["label"],
                    color=style["color"], linestyle=style["linestyle"],
                    marker=style["marker"], linewidth=1.8, markersize=5)
        ax.set_ylabel(ylabel)
        ax.legend(frameon=False)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.grid(True, alpha=0.25)
        if key == "js":
            ax.set_ylim(0, 1)

    ax2.set_xlabel("Year")
    plt.tight_layout()
    for fmt in formats:
        plt.savefig(f"{out_stem}.{fmt}", dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved {out_stem}.{formats[0]}")


# ── table output ───────────────────────────────────────────────────────────

def to_table(results: dict[str, dict[int, dict]],
             label_a: str, label_b: str) -> dict:
    """Convert comparison results to book_tables.json table format."""
    rows = []
    for gender in ("M", "F"):
        for year in sorted(results.get(gender, {})):
            r = results[gender][year]
            rows.append([
                year, gender,
                r["common"],
                f"{r['js']:.3f}" if not np.isnan(r["js"]) else "—",
                r["n_a"], r["n_b"],
            ])
    return {
        "caption": f"Agreement between {label_a} and {label_b} (orth)",
        "headers": ["Year", "Gender", "Common names", "JS divergence",
                    f"N ({label_a})", f"N ({label_b})"],
        "rows": rows,
    }


# ── main ───────────────────────────────────────────────────────────────────

def main(db_path: str | None = None) -> None:
    db_path = db_path or str(_default_db)
    conn = sqlite3.connect(db_path)

    print("Loading source data from nrank …")
    meiji    = get_nrank(conn, "meiji")
    bc       = get_nrank(conn, "bc")
    benesse  = get_nrank(conn, "benesse")
    akachan  = get_nrank(conn, "akachan")
    conn.close()

    comparisons = [
        ("benesse", benesse, "meiji",   meiji,   "Benesse",  "Meiji Yasuda"),
        ("akachan", akachan, "meiji",   meiji,   "Akachan",  "Meiji Yasuda"),
        ("benesse", benesse, "akachan", akachan, "Benesse",  "Akachan"),
        ("benesse", benesse, "bc",      bc,      "Benesse",  "Baby Calendar"),
        ("akachan", akachan, "bc",      bc,      "Akachan",  "Baby Calendar"),
    ]

    tables: dict[str, dict] = {}
    plot_dir  = Path(_plot_dir);  plot_dir.mkdir(parents=True, exist_ok=True)
    book_dir  = Path(_book_dir);  book_dir.mkdir(parents=True, exist_ok=True)

    for key_a, data_a, key_b, data_b, label_a, label_b in comparisons:
        pair = f"{key_a}_vs_{key_b}"
        print(f"\n{label_a} vs {label_b}")

        exclude = _EXCLUDE.get((key_a, key_b), None)
        results = compare_sources(data_a, data_b, pair, exclude_years=exclude)

        # Print summary
        for gender in ("M", "F"):
            d = results.get(gender, {})
            for year in sorted(d):
                r = d[year]
                js_str = f"{r['js']:.3f}" if not np.isnan(r["js"]) else "  —  "
                print(f"  {year} {gender}: overlap={r['common']:3d}  JS={js_str}"
                      f"  (n_{key_a}={r['n_a']}, n_{key_b}={r['n_b']})")

        # Plot
        stem_web  = str(plot_dir  / f"new_sources_{pair}")
        stem_book = str(book_dir  / f"new_sources_{pair}")
        plot_comparison(results, label_a, label_b, stem_web, ("png",))
        plot_comparison(results, label_a, label_b, stem_book, ("png", "svg"))

        tables[pair] = to_table(results, label_a, label_b)

    # Merge into book_tables.json
    try:
        with open(_tables_json) as f:
            all_tables = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        all_tables = {}

    all_tables["ch_new_sources"] = tables
    Path(_tables_json).parent.mkdir(parents=True, exist_ok=True)
    with open(_tables_json, "w", encoding="utf-8") as f:
        json.dump(all_tables, f, ensure_ascii=False, indent=1)
    print(f"\nTables written to {_tables_json}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
