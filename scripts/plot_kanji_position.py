import sys, os
import sqlite3
from pathlib import Path
from collections import defaultdict as dd, Counter

import numpy as np
import matplotlib.pyplot as plt
from matplotlib import rcParams
from matplotlib.ticker import MaxNLocator
from scipy.interpolate import PchipInterpolator


sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
current_directory = os.path.abspath(os.path.dirname(__file__))

db_path = os.path.join(current_directory, "../web/db/namae.db")
plot_dir = os.path.join(current_directory, "../web/static/plot")

def get_distribution(c, meta):
    (kanji, gender, src) = meta
    data = dd(lambda: [0, 0, 0, 0, 0]) 
    ### get solo, initial, middle, end for that year
    c.execute(f"""
SELECT 
    year,
    sum(CASE WHEN orth GLOB '{kanji}*' AND length(orth) > 1 THEN freq ELSE 0 END) AS initial,
    sum(CASE WHEN orth GLOB '*{kanji}*' AND orth NOT GLOB '{kanji}*' AND orth NOT GLOB '*{kanji}' AND length(orth) > 2 THEN freq ELSE 0 END) AS middle,
    sum(CASE WHEN orth GLOB '*{kanji}' AND length(orth) > 1 THEN freq ELSE 0 END) AS end,
    sum(CASE WHEN orth = '{kanji}' THEN freq ELSE 0 END) AS solo
FROM nrank
WHERE (orth GLOB '*{kanji}*') 
  AND gender = ? 
  AND src=?
  AND freq IS NOT NULL
GROUP BY year""",
              (gender, src))
    for year, initial, middle, end, solo in c:
        data[year] = [solo, initial, middle, end]

    ### get total names for that year
    c.execute(f"""
    SELECT year, count FROM name_year_cache
    WHERE gender = ? and SRC = ?""",
           (gender, src))    
    for year, count in c:
        data[year].append(count)

    return data

def plot_kanji_positions(data, meta, title=True, output_path=None, formats=('png',),
                         bw=False, ax=None, figsize=None):
    """
    Plot proportions of kanji positions over time.

    Args:
        data: dict where data[year] = [solo, initial, middle, end, count]
        meta: (kanji, gender, source) tuple
        ax: Optional axes to draw into; caller is responsible for saving.
        figsize: Figure size when creating a new figure (default (10, 6)).
    """
    kanji, gender, src = meta

    years = sorted(data.keys())
    solo = np.array([data[y][0] / data[y][4] if data[y][4] > 0 else 0 for y in years])
    initial = np.array([data[y][1] / data[y][4] if data[y][4] > 0 else 0 for y in years])
    middle = np.array([data[y][2] / data[y][4] if data[y][4] > 0 else 0 for y in years])
    end = np.array([data[y][3] / data[y][4] if data[y][4] > 0 else 0 for y in years])
    
    # Calculate total proportion and max for y-axis
    total = solo + initial + middle + end
    max_prop = np.max(total) if len(total) > 0 else 0.1
    
    own_fig = ax is None
    if own_fig:
        if figsize is None:
            figsize = (10, 6)
        fig, ax = plt.subplots(figsize=figsize)
    else:
        fig = ax.get_figure()

    if len(years) >= 3:
        xs = np.linspace(years[0], years[-1], 300)
        s_s = np.clip(PchipInterpolator(years, solo)(xs), 0, None)
        s_i = np.clip(PchipInterpolator(years, initial)(xs), 0, None)
        s_m = np.clip(PchipInterpolator(years, middle)(xs), 0, None)
        s_e = np.clip(PchipInterpolator(years, end)(xs), 0, None)
    else:
        xs, s_s, s_i, s_m, s_e = years, solo, initial, middle, end

    if bw:
        from bw_style import BW_FILLS
        _fills = BW_FILLS
    else:
        _fills = [
            dict(alpha=0.7, label='Solo',    color='#d62728'),
            dict(alpha=0.7, label='Initial', color='#1f77b4'),
            dict(alpha=0.7, label='Middle',  color='#2ca02c'),
            dict(alpha=0.7, label='End',     color='#ff7f0e'),
        ]
    ax.fill_between(xs, 0,             s_s,                   **_fills[0])
    ax.fill_between(xs, s_s,           s_s + s_i,             **_fills[1])
    ax.fill_between(xs, s_s + s_i,     s_s + s_i + s_m,       **_fills[2])
    ax.fill_between(xs, s_s + s_i + s_m, s_s + s_i + s_m + s_e, **_fills[3])
    
    # Tufte styling
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_linewidth(0.5)
    ax.spines['bottom'].set_linewidth(0.5)
    
    # Minimal grid
    ax.yaxis.grid(True, linestyle='-', linewidth=0.5, alpha=0.3, color='gray')
    ax.set_axisbelow(True)
    
    # Labels
    ax.set_xlabel('Year', fontsize=11)
    ax.set_ylabel('Proportion', fontsize=11)
    if title:
        ax.set_title(f'Position Distribution of 「{kanji}」 in Names for {gender} from {src}', fontsize=12, pad=15)
    
    # Legend
    ax.legend(loc='upper left', frameon=False, fontsize=10)
    
    # Dynamic y-axis scaling with some headroom
    y_max = np.ceil(max_prop * 1.1 * 20) / 20  # Round up to nearest 5%
    y_max = max(y_max, 0.05)  # Minimum 5% scale
    
    # Set appropriate tick spacing
    if y_max <= 0.1:
        tick_spacing = 0.02
    elif y_max <= 0.2:
        tick_spacing = 0.05
    elif y_max <= 0.5:
        tick_spacing = 0.1
    else:
        tick_spacing = 0.2
    
    ax.set_ylim(0, y_max)
    yticks = np.arange(0, y_max + tick_spacing/2, tick_spacing)
    ax.set_yticks(yticks)
    ax.set_yticklabels([f'{int(x*100)}%' for x in yticks])
    # Force x-axis to show only integer years
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    
    if own_fig:
        plt.tight_layout()
        if output_path is not None:
            dpi = plt.rcParams.get('savefig.dpi', 300)
            for fmt in formats:
                fig.savefig(f'{output_path}.{fmt}', dpi=dpi, bbox_inches='tight')
            plt.close(fig)
    return fig, ax

# Example usage:
# fig, ax = plot_kanji_positions(data, '美')
# plt.savefig('kanji_position.png', dpi=150, bbox_inches='tight')
def get_unique_characters(c, gender='M', src='hs', min_freq=None):
    """Get all unique characters from names in a source."""
    
    # Get all names with their frequencies
    c.execute("""SELECT orth, SUM(freq) as total_freq FROM nrank
                 WHERE src = ? AND gender = ?
                 GROUP BY orth""",
              (src, gender))
    
    if min_freq is None:
        # All characters
        unique_chars = set()
        for name, _ in c:
            unique_chars.update(name)
    else:
        # Count character frequencies across all names
        char_freq = {}
        for name, name_freq in c:
            for char in name:
                char_freq[char] = char_freq.get(char, 0) + name_freq
        
        unique_chars = {char for char, freq in char_freq.items() if freq >= min_freq}
    
    return sorted(unique_chars)

def main(db_path=db_path, plot_dir=plot_dir, formats=('png',)):
    """Regenerate all kanji-position plots for high-frequency characters."""
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    out_dir = Path(os.path.dirname(__file__)) / 'position'
    out_dir.mkdir(exist_ok=True)

    src = 'meiji'
    for gender in ('M', 'F'):
        characters = get_unique_characters(c, gender, src, min_freq=10000)
        for ch in characters:
            for g in ('M', 'F'):
                meta = (ch, g, src)
                print(f"Processing {ch}, {g}, {src}")
                data = get_distribution(c, meta)
                plot_kanji_positions(data, meta, title=False,
                                     output_path=str(out_dir / '_'.join(meta)),
                                     formats=formats)
    conn.close()


if __name__ == "__main__":
    main()

