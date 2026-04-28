import matplotlib.pyplot as plt
import argparse
import os
from pathlib import Path

def plot_kanji_usage(output_path=None, formats=('png', 'svg'), bw=False, figsize=None):
    # Kanji data
    kanji = {
        1947:(1850, 0),
        1951:(1850, 92),
        1976:(1850, 120),
        1981:(1945, 166),
        1990:(1945, 284),
        1997:(1945, 285),
        2004:(1945, 983),
        2009:(1945, 985),
        2010:(2136, 861),
        2015:(2136, 862),
        2017:(2136, 863),
    }

    # Extract data
    years = list(kanji.keys())
    name_kanji = [k[1] for k in kanji.values()]
    total_kanji = [sum(k) for k in kanji.values()]

    plt.figure(figsize=figsize or (10, 6), facecolor='white')

    if bw:
        from bw_style import BW_LINE_1, BW_LINE_2
        _l1 = dict(**BW_LINE_1, label='Name-only Kanji')
        _l2 = dict(**BW_LINE_2, label='Total Kanji')
        _ann_color = 'black'
    else:
        _l1 = dict(color='#1f77b4', linewidth=2, label='Name-only Kanji')
        _l2 = dict(color='#d62728', linewidth=2, linestyle='--', label='Total Kanji')
        _ann_color = None  # set per-line below

    plt.plot(years, name_kanji, **_l1)
    plt.plot(years, total_kanji, **_l2)

    # Minimalist design elements
    plt.title('Number of Kanji allowed in Names', fontsize=14, fontweight='bold')
    plt.xlabel('Year', fontsize=10)
    plt.ylabel('Number of Kanji', fontsize=10)

    # Sparse grid with light lines
    plt.grid(True, linestyle=':', color='lightgray', linewidth=0.5)

    # Remove chart junk
    plt.gca().spines['top'].set_visible(False)
    plt.gca().spines['right'].set_visible(False)

    # Annotations for key points
    # For narrow figures use a sparser set of annotations to avoid overlap
    narrow = figsize is not None and figsize[0] < 6
    ann_years = [1947, 1976, 1990, 2004, 2010, 2017] if narrow else \
                [1947, 1951, 1976, 1990, 1997, 2004, 2010, 2017]
    for i, year in enumerate(years):
        if year in ann_years:
            plt.annotate(f'{name_kanji[i]}',
                         (year, name_kanji[i]),
                         xytext=(5, 5), textcoords='offset points',
                         fontsize=7 if narrow else 8,
                         color=_ann_color or '#1f77b4')
            plt.annotate(f'{total_kanji[i]}',
                         (year, total_kanji[i]),
                         xytext=(5, -10), textcoords='offset points',
                         fontsize=7 if narrow else 8,
                         color=_ann_color or '#d62728')

    plt.legend(frameon=False)
    plt.tight_layout()

    if output_path:
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        dpi = plt.rcParams.get('savefig.dpi', 300)
        for fmt in formats:
            plt.savefig(f'{output_path}.{fmt}', dpi=dpi, bbox_inches='tight')
        plt.close()
    else:
        plt.show()

def main():
    parser = argparse.ArgumentParser(description='Plot Kanji Usage Over Time')
    parser.add_argument('-o', '--output', 
                        help='Output file path (without extension)', 
                        default=None)
    args = parser.parse_args()
    
    plot_kanji_usage(args.output)

if __name__ == '__main__':
    main()
