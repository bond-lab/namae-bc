import os
import sqlite3
from collections import Counter, defaultdict as dd
from pathlib import Path

import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import numpy as np
from tabulate import tabulate

from db import db_options, get_name_year
from web_plot_style import FEMALE_COLOR, MALE_COLOR, WEB_FIGSIZE, save_web_svg

GROUP_META = [
    ('name_full', 'Full name',      'Orthography and reading combined'),
    ('pron',      'Pronunciation',  'Reading only (hiragana)'),
    ('orth',      'Orthography',    'Written form only (kanji)'),
]

PERIOD_META = [
    (2090, '2008_2013', '2008\u20132013'),
    (2095, '2014_2022', '2014\u20132022'),
    (2099, '2008_2022', '2008\u20132022'),
]

BIN_LABELS = (
    ['100% \u2642'] +
    [f'{i * 10}\u2013{(i + 1) * 10}%' for i in range(10)] +
    ['100% \u2640']
)

current_directory = os.path.abspath(os.path.dirname(__file__))

db_path = os.path.join(current_directory, "../web/db/namae.db")
plot_dir = os.path.join(current_directory, "../web/static/plot")

def calculate_proportion(male_names, female_names, ratio=0.2):
 
    # Count the occurrences of each name in both lists
    male_count = Counter(male_names)
    female_count = Counter(female_names)

    # Combine all names from both lists into a unique set
    all_names = set(male_count.keys()).union(set(female_count.keys()))

    # Initialize variables to store total number of children and count of qualifying children
    total_children = 0
    qualifying_children = 0

    for name in all_names:
        male_usage = male_count.get(name, 0)
        female_usage = female_count.get(name, 0)
        total_usage = male_usage + female_usage

        if total_usage > 0:  # To avoid division by zero
            male_proportion = male_usage / total_usage

            # Increment total children by the number of children with this name
            total_children += total_usage

            # Check if the male proportion is between 20% and 80%
            if ratio <= male_proportion <= (1-ratio):
                qualifying_children += total_usage

    # Calculate the proportion of qualifying children relative to the total number of children
    proportion = qualifying_children / total_children if total_children > 0 else 0

    return proportion

def calculate_distribution(male_names, female_names, gname, sample=False):
    if sample:
        smaller = min(len(male_names), len(female_names))
        male_names = random.sample(male_names, smaller)
        female_names = random.sample(female_names, smaller)
    # Count the occurrences of each name in both lists
    male_count = Counter(male_names)
    female_count = Counter(female_names)

    # Combine all names from both lists into a unique set
    all_names = set(male_count.keys()).union(set(female_count.keys()))

    # Initialize variables to store total number of children and count of qualifying children
    total_children = 0
    qualifying_children = 0
    stats = dict()
    total_names = 0
    for i in range(12):
        stats[i] = dd(int)
    for name in all_names:
        male_usage = male_count.get(name, 0)
        female_usage = female_count.get(name, 0)
        total_usage = male_usage + female_usage
        total_names += total_usage
        if total_usage > 0:  # To avoid division by zero
            female_proportion = female_usage / total_usage
            if female_proportion == 0:
                stats[0]['M'] += male_usage
                stats[0]['F'] += female_usage
            elif female_proportion == 1:
                stats[11]['M'] += male_usage
                stats[11]['F'] += female_usage
            elif female_proportion == 0.5:
                 stats[5]['M'] += male_usage
                 stats[6]['F'] += female_usage
            elif female_proportion < 0.5:
                decile = int(10 * female_proportion) + 1
                stats[decile]['M'] += male_usage
                stats[decile]['F'] += female_usage
            elif female_proportion > 0.5:
                decile = int(10 * female_proportion) + 1
                stats[decile]['M'] += male_usage
                stats[decile]['F'] += female_usage
    return stats, total_names


#def merge_sets()


def tabulate_proportion(stats, total_names, gname):

    headers = ["Bin", "All Names", "%", "Female", "%",  "Male", "%"]
    colalign= [None, 'decimal', 'right',
               'decimal', 'right',
               'decimal', 'right', ]
    data = []
    for d in stats:
        data.append([d, stats[d]['M'] + stats[d]['F'],
                     f"{(stats[d]['M'] + stats[d]['F'])/total_names:.1%}",
                     stats[d]['F'], f"{stats[d]['F']/total_names:.1%}",
                     stats[d]['M'], f"{stats[d]['M']/total_names:.1%}",
        ])
    html_table = tabulate(data, headers, tablefmt="html", colalign=colalign)

    ### calculate some other stats
    newstats = dd(lambda: dd(int))
    newstats["Mainly Male"]['M'] =  stats[0]['M'] + stats[1]['M']
    newstats["Mainly Male"]['F'] =  stats[0]['F'] + stats[1]['F']
    newstats["GN - Male"]['M'] =  sum(stats[i]['M'] for i in range(2,6))
    newstats["GN - Male"]['F'] =  sum(stats[i]['F'] for i in range(2,6))

    newstats["GN - Female"]['M'] =   sum(stats[i]['M'] for i in range(6,10))
    newstats["GN - Female"]['F'] =   sum(stats[i]['F'] for i in range(6,10))
    newstats["GN All"]['M'] =  newstats["GN - Male"]['M']  \
        + newstats["GN - Female"]['M']
    newstats["GN All"]['F'] =  newstats["GN - Male"]['F'] \
        + newstats["GN - Female"]['F']
    newstats["Mainly Female"]['M'] =  stats[10]['M'] + stats[11]['M']
    newstats["Mainly Female"]['F'] =  stats[10]['F'] + stats[11]['F']
    data2 = []
    for d in newstats:
        data2.append([d, newstats[d]['M'] + newstats[d]['F'],
                     f"{(newstats[d]['M'] + newstats[d]['F'])/total_names:.1%}",
                     newstats[d]['F'], f"{newstats[d]['F']/total_names:.1%}",
                     newstats[d]['M'], f"{newstats[d]['M']/total_names:.1%}",
        ])
    html_table2 = tabulate(data2, headers, tablefmt="html", colalign=colalign)    


    # Save HTML to a file
    with open(f'proportion/table-{gname}.html', 'w') as file:
        file.write(html_table + html_table2)




        
def graph_proportion(stats, total_names, gname, plot_dir):
    x = list(stats.keys())
    #y = list(stats.values())
    y = list([(x / total_names) for x in stats.values()])
    #y = list([(1000 * x / total_names) for x in stats.values()])

    # Tufte-inspired minimalist style
    plt.figure(figsize=(10, 6))
    plt.bar(x, y, color='#4C72B0', edgecolor='black')

    # Set log scale for y-axis
    #plt.yscale('log')
    # Set fixed y-axis limits
    #plt.ylim(1, 5000)  # Example: setting y-axis from 1 to 1000 /1000
    #y_ticks = [1, 10, 1000]
    #plt.yticks(y_ticks, labels=["{:.3f}".format(yt/1000) for yt in y_ticks])

    # Remove the box around the plot
    plt.gca().spines['top'].set_visible(False)
    plt.gca().spines['right'].set_visible(False)
    plt.gca().spines['left'].set_visible(False)
    plt.gca().spines['bottom'].set_linewidth(0.5)

    # Only show ticks on the bottom and left spines
    plt.gca().xaxis.set_ticks_position('bottom')
    plt.gca().yaxis.set_ticks_position('left')

    # Reduce the number of gridlines
    plt.grid(True, axis='y', color='gray', linestyle='--', linewidth=0.5)
    plt.gca().set_axisbelow(True)

    # Remove y-axis ticks but keep the gridlines
    #plt.yticks([])


    # Set x-axis labels
    plt.xticks(x, labels= ['100% male'] + [f'{i*10}%-{(i+1)*10}%' for i in range(10)]  + ['100% female'], rotation=45)

    # Add labels and title
    plt.xlabel('Proportion Interval (0: 100% male, 11: 100% female)', fontsize=10)
    plt.ylabel('Number of Names', fontsize=10)
    plt.title(f'Distribution of Names by Gender Proportion ({gname})', fontsize=12, weight='bold')

    # Show the plot
    plt.tight_layout()
    out_path = os.path.join(plot_dir, f'pron_gender_proportion_histogram_{gname}.png')
    plt.savefig(out_path, dpi=300, bbox_inches='tight')
    #plt.show()

def blend_colors(color1, color2, blend_ratio):
    """
    Blend two colors based on a ratio.
    
    Parameters:
    color1: tuple or string - first color (RGB tuple or matplotlib color name)
    color2: tuple or string - second color (RGB tuple or matplotlib color name)
    blend_ratio: float - ratio of color2 (0 = all color1, 1 = all color2)
    
    Returns:
    tuple - blended RGB color
    """
    # Convert colors to RGB if they're strings
    if isinstance(color1, str):
        color1 = mcolors.to_rgb(color1)
    if isinstance(color2, str):
        color2 = mcolors.to_rgb(color2)
    
    # Blend the colors
    blended = tuple(
        color1[i] * (1 - blend_ratio) + color2[i] * blend_ratio
        for i in range(3)
    )
    return blended



def graph_proportion2(data, gname, title=True, plot_dir='proportion', formats=('png',)):
    xlabel = {0:'0',
               1:'0-10',
               2:'10-20',
               3:'20-30',
               4:'30-40',
               5:'40-50',
               6:'50-60',
               7:'60-70',
               8:'70-80',
               9:'80-90',
               10:'90-100',
               11:'100',
    }

    # Prepare the data
    bins = list(data.keys())
    total_names = sum(data[bin]['M'] + data[bin]['F'] for bin in data)

    totals = [data[bin]['M'] + data[bin]['F'] for bin in bins]
    male_percentages = [data[bin]['M'] / total if total != 0 else 0 for bin, total in zip(bins, totals)]

    totals = [t/total_names for t in totals]
    male_values = [data[bin]['M'] /total_names for bin in bins]
    female_values = [data[bin]['F'] /total_names for bin in bins]

    # Plot with transparent bars
    plt.figure(figsize=(10, 6))

    # Bar plot with mixed colors and transparency
    for i, bin in enumerate(bins):
        blended_color = blend_colors(FEMALE_COLOR, MALE_COLOR, male_percentages[i])
        plt.bar(bin, totals[i], color=blended_color, alpha=0.6)

    # Line plots for M and F
    #plt.plot(bins, male_values, color='blue', marker='o', label='M')
    #plt.plot(bins, female_values, color='red', marker='o', label='F')

    # Add labels, title, and legend
    plt.xlabel('Gender distribution of names (% female)')
    plt.ylabel('Percentage of babies (%)')
    if title:
        plt.title(f'Gender distribution of names (% female): {gname}')
    plt.xticks(bins, [xlabel[b] for b in bins])

    # Format y-axis as percentages
    ax = plt.gca()
    ax.set_ylim(0, 0.5)
   
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f'{int(y*100)}'))
    ax.set_yticks([0, 0.1, 0.2, 0.3, 0.4, 0.5])
    
    # Remove spines
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    # Horizontal gridlines every 5%
    ax.grid(axis='y', color='white', linewidth=1, alpha=0.7)


    #plt.legend()

    stem = os.path.join(plot_dir, f'pron_gender_proportion_histogram_{gname}')
    print(f"Saving  {stem}")
    for fmt in formats:
        plt.savefig(f'{stem}.{fmt}', dpi=300, bbox_inches='tight')
    plt.close()

    



def androgyny(boys_names, girls_names):
    # Count the occurrences of each name in the boys' and girls' lists
    boys_counts = Counter(boys_names)
    girls_counts = Counter(girls_names)
    
    # Get all unique names in the girls' list
    unique_girls_names = set(girls_names)
    
    # Calculate the Index of Androgyny
    boys_proportions = []
    
    for name in unique_girls_names:
        boys_count = boys_counts.get(name, 0)
        girls_count = girls_counts.get(name, 0)
        total_count = boys_count + girls_count
        
        if total_count > 0:  # To avoid division by zero
            boys_proportion = boys_count / total_count
            boys_proportions.append(boys_proportion)
    
    if boys_proportions:
        index_of_androgyny = sum(boys_proportions) / len(boys_proportions)
    else:
        index_of_androgyny = 0  # If there are no names, index is 0
    
    return index_of_androgyny



def sample_funk(male_names, female_names, funk,
           sample_size=1000, num_runs=1000):
    proportions = []
    for _ in range(num_runs):
        if len(male_names) > sample_size:
            male_sample = random.sample(male_names, sample_size)
        else:
            return -1
        if len(female_names) > sample_size:
            female_sample = random.sample(female_names, sample_size)
        else:
            return -1
        proportions.append(funk(male_sample, female_sample))
    return  sum(proportions) / num_runs


def sample_proportion(male_names, female_names,
                     sample_size=400, num_runs=1000):
    return sample_funk(male_names, female_names, calculate_proportion,
           sample_size=400, num_runs=1000)

def sample_androgyny(male_names, female_names,
                     sample_size=400, num_runs=1000):
    return sample_funk(male_names, female_names, androgyny,
           sample_size=400, num_runs=1000)


def compute_data(conn: sqlite3.Connection) -> dict:
    """Return {(group_slug, period_slug): stats} for all group × period combos.

    Args:
        conn: Open SQLite connection to namae.db.

    Returns:
        Dict keyed by (group_slug, period_slug) with the 12-bin stats dict
        from calculate_distribution as values.
    """
    raw = get_name_year(conn, src='bc', table=db_options['bc'][0], dtype='both')

    buckets: dict = {key: dd(list) for key, _, _ in PERIOD_META}
    for y, by_gender in raw.items():
        for g in ('M', 'F'):
            buckets[2099][g].extend(by_gender[g])
            target = 2090 if y < 2014 else 2095
            buckets[target][g].extend(by_gender[g])

    result = {}
    for period_key, period_slug, _ in PERIOD_META:
        bkt = buckets[period_key]
        if len(bkt['F']) < 1000:
            continue
        for group_slug, _, _ in GROUP_META:
            if group_slug == 'name_full':
                m, f = bkt['M'], bkt['F']
            elif group_slug == 'pron':
                m = [p for _, p in bkt['M']]
                f = [p for _, p in bkt['F']]
            else:
                m = [o for o, _ in bkt['M']]
                f = [o for o, _ in bkt['F']]
            stats, _ = calculate_distribution(m, f, f"{period_key}")
            result[(group_slug, period_slug)] = stats
    return result


def _make_proportion_fig(stats: dict) -> plt.Figure:
    """Return a U-shaped gender-distribution histogram figure."""
    bins = sorted(stats.keys())
    total = sum(stats[b]['M'] + stats[b]['F'] for b in bins)
    if not total:
        return None

    bar_heights = [(stats[b]['M'] + stats[b]['F']) / total for b in bins]
    male_fracs = [
        stats[b]['M'] / (stats[b]['M'] + stats[b]['F'])
        if (stats[b]['M'] + stats[b]['F']) > 0 else 0
        for b in bins
    ]

    fig, ax = plt.subplots(figsize=WEB_FIGSIZE)
    for i, b in enumerate(bins):
        ax.bar(b, bar_heights[i],
               color=blend_colors(FEMALE_COLOR, MALE_COLOR, male_fracs[i]),
               alpha=0.85)

    ax.set_xticks(bins)
    ax.set_xticklabels(BIN_LABELS, rotation=40, ha='right', fontsize=9)
    ax.set_xlabel('Gender distribution (% female)')
    ax.set_ylabel('Babies (%)')
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f'{int(y * 100)}'))
    ax.set_ylim(0, 0.55)
    ax.set_yticks([0, 0.1, 0.2, 0.3, 0.4, 0.5])
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.grid(axis='y', linestyle='--', linewidth=0.4, alpha=0.3, color='gray')
    fig.tight_layout()
    return fig


def generate_web_svgs(conn: sqlite3.Connection, out_dir) -> None:
    """Generate CSS-variable-aware SVGs for each group × period combination.

    Args:
        conn: Open SQLite connection to namae.db.
        out_dir: Directory to write SVG files into.
    """
    out_dir = Path(out_dir)
    data = compute_data(conn)
    for (group_slug, period_slug), stats in data.items():
        fig = _make_proportion_fig(stats)
        if fig is None:
            continue
        stem = out_dir / f"proportion_{group_slug}_{period_slug}"
        save_web_svg(fig, f"{stem}.svg")
        plt.close(fig)
        print(f"  proportion {group_slug} {period_slug} \u2192 {stem}.svg")


def main(db_path=db_path, plot_dir=plot_dir, formats=('png',)):
    """Regenerate all gender-proportion histogram plots."""
    conn = sqlite3.connect(db_path)

    src = 'bc'
    data_type = 'both'
    table_name = db_options[src][0]
    names = get_name_year(conn, src=src, table=table_name, dtype=data_type)

    for y in list(names.keys()):
        names[2099]['F'] += names[y]['F']
        names[2099]['M'] += names[y]['M']
        if y < 2014:
            names[2090]['F'] += names[y]['F']
            names[2090]['M'] += names[y]['M']
        else:
            names[2095]['F'] += names[y]['F']
            names[2095]['M'] += names[y]['M']
       
        


    title = {2090: '2008\u20132013', 2095: '2014\u20132022', 2099: '2008\u20132022'}

    for year in sorted(names.keys()):
        if len(names[year]['F']) < 1000:
            continue
        mn = names[year]['M']
        fn = names[year]['F']
        mo = [o for (o, p) in names[year]['M']]
        fo = [o for (o, p) in names[year]['F']]
        mp = [p for (o, p) in names[year]['M']]
        fp = [p for (o, p) in names[year]['F']]
        for (group, male, female) in [('Name (full)', mn, fn),
                                      ('Pronunciation', mp, fp),
                                      ('Orthography', mo, fo)]:
            gname = f"{group} ({title[year]})"
            stats, total_names = calculate_distribution(male, female, f"{year}")
            graph_proportion2(stats, gname, title=False, plot_dir=plot_dir,
                              formats=formats)

    conn.close()


if __name__ == "__main__":
    main()
