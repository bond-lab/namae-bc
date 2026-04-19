"""Generate pre-built SVG figures for all static phenomenon pages.

Reads pre-computed JSON data and writes CSS-variable-aware SVGs to
web/static/plot/web_*.svg.  Run during makedb.sh analysis phase.

Pages covered: irregular, genderedness, overlap, androgyny, diversity.
(rankings/topnames stays D3.js — it is genuinely interactive.)
"""

import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from plot_web_charts import (
    plot_irregular,
    plot_genderedness_dataset, load_genderedness,
    plot_overlap_dataset,
    plot_androgyny_dataset,
    plot_diversity_group, diversity_group_keys,
)

DATA_DIR = Path(__file__).parent / ".." / "web" / "static" / "data"
OUT_DIR = Path(__file__).parent / ".." / "web" / "static" / "plot"

# svg.fonttype="path" embeds CJK glyphs correctly
plt.rcParams["svg.fonttype"] = "path"

WEB_FMT = ("svg_web",)


def _load(name: str) -> dict:
    with open(DATA_DIR / name, encoding="utf-8") as f:
        return json.load(f)


def build_irregular() -> None:
    """Generate web/static/plot/web_irregular.svg."""
    out = OUT_DIR / "web_irregular"
    plot_irregular(output_stem=str(out), formats=WEB_FMT)
    print(f"  irregular → {out}.svg")


def build_genderedness() -> None:
    """Generate one SVG per genderedness dataset key."""
    for ds in load_genderedness():
        out = OUT_DIR / f"web_genderedness_{ds['key']}"
        plot_genderedness_dataset(
            ds["data"], ds["regression_stats"], ds["caption"],
            output_stem=str(out), formats=WEB_FMT,
        )
        print(f"  genderedness {ds['key']} → {out}.svg")


def build_overlap() -> None:
    """Generate one SVG per overlap dataset key."""
    blob = _load("overlap_data.json")
    for key, entry in blob.items():
        out = OUT_DIR / f"web_overlap_{key}"
        plot_overlap_dataset(
            entry["data"],
            entry.get("reg_count"),
            entry.get("reg_proportion"),
            caption=key.replace("_", " "),
            output_stem=str(out), formats=WEB_FMT,
        )
        print(f"  overlap {key} → {out}.svg")


def build_androgyny() -> None:
    """Generate one SVG per androgyny dataset key."""
    blob = _load("androgyny_data.json")
    for key, entry in blob.items():
        out = OUT_DIR / f"web_androgyny_{key}"
        plot_androgyny_dataset(
            entry["data"],
            entry.get("regression"),
            caption=key.replace("_", " "),
            output_stem=str(out), formats=WEB_FMT,
        )
        print(f"  androgyny {key} → {out}.svg")


def build_diversity() -> None:
    """Generate three SVGs per diversity dataset key (Var, BP, TTR_Newness)."""
    groups = diversity_group_keys()
    for json_path in sorted(DATA_DIR.glob("diversity_data_*.json")):
        key = json_path.stem.removeprefix("diversity_data_")
        with open(json_path, encoding="utf-8") as f:
            blob = json.load(f)
        metrics_by_gender = blob.get("metrics", {})
        for group_name, metric_names in groups.items():
            out = OUT_DIR / f"web_diversity_{key}_{group_name}"
            plot_diversity_group(
                metrics_by_gender, metric_names,
                output_stem=str(out), formats=WEB_FMT,
            )
            print(f"  diversity {key} {group_name} → {out}.svg")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print("Building irregular figure...")
    build_irregular()

    print("Building genderedness figures...")
    build_genderedness()

    print("Building overlap figures...")
    build_overlap()

    print("Building androgyny figures...")
    build_androgyny()

    print("Building diversity figures...")
    build_diversity()

    print("Done.")


if __name__ == "__main__":
    main()
