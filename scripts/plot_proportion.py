import sys, os
from collections import Counter, defaultdict as dd 
import sqlite3
import random
import matplotlib.pyplot as plt
import numpy as np
from tabulate import tabulate


sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from web.db import db_options, get_name_year

current_directory = os.path.abspath(os.path.dirname(__file__))

db_path = os.path.join(current_directory, "../web/db/namae.db")
plot_dir = os.path.join(current_directory, "../web/static/plot")

conn = sqlite3.connect(db_path)

c = conn.cursor()



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
    with open(f'table-{gname}.html', 'w') as file:
        file.write(html_table + html_table2)




        
def graph_proportion(stats, total_names, gname):
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

    plt.savefig(f'pron_gender_proportion_histogram_{gname}.png', dpi=300, bbox_inches='tight')
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
        color1 = plt.colors.to_rgb(color1)
    if isinstance(color2, str):
        color2 = plt.colors.to_rgb(color2)
    
    # Blend the colors
    blended = tuple(
        color1[i] * (1 - blend_ratio) + color2[i] * blend_ratio
        for i in range(3)
    )
    return blended

# Define your colors
female_color = 'purple'  # or (0.5, 0, 0.5)
male_color = 'orange'    # or (1, 0.65, 0)


def graph_proportion2(data, gname):
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
    blended_color = blend_colors(female_color, male_color, male_percentages[i])
    plt.bar(bin, totals[i], color=blended_color, alpha=0.6)

    # Line plots for M and F
    #plt.plot(bins, male_values, color='blue', marker='o', label='M')
    #plt.plot(bins, female_values, color='red', marker='o', label='F')

    # Add labels, title, and legend
    plt.xlabel('Name percent female')
    plt.ylabel('Percent of babies')
    plt.title(f'Distribution of names in the baby name calendar: {gname}')
    plt.xticks(bins, [xlabel[b] for b in bins])
    plt.legend()

    plt.savefig(f'gender_proportion_histogram_{gname}.png',
              dpi=300, bbox_inches='tight')
    
    #plt.show()# Plot


    



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


#names = get_name_year(conn)

src = 'bc'
data_type = 'both'
table_name = db_options[src][0]
names = get_name_year(conn, src=src,
                      table=table_name, dtype=data_type)

for y in list(names.keys()):
    names[2099]['F'] += names[y]['F']
    names[2099]['M'] += names[y]['M']
    if y < 2014: # first half
        names[2090]['F'] += names[y]['F']
        names[2090]['M'] += names[y]['M']
    else: #last half
        names[2095]['F'] += names[y]['F']
        names[2095]['M'] += names[y]['M']
       
        


###
### make some special years!
###
names[2015.5]['F'] = names[2015]['F'] + names[2016]['F']
names[2015.5]['M'] = names[2015]['M'] + names[2016]['M']
names[2021.5]['F'] = names[2021]['F'] + names[2022]['F']
names[2021.5]['M'] = names[2021]['M'] + names[2022]['M']





stats = dd(lambda: dd(int))

print('year',
      'F', 'M',
      '%A.2', '%A.2o', '%A.2p',
      '%A', '%Ao', '%Ap',
      '%A-L', '%A-Lo', '%A-Lp',
      sep='\t')

title = {2090:'1989-2013', 2095:'1989-2022', 2099:'2014-2022'}


for year in sorted(names.keys()):
    if len(names[year]['F']) < 1000:
        continue
    mn = names[year]['M']
    fn = names[year]['F']
    mo = [o for (o, p) in names[year]['M']]
    fo = [o for (o, p) in names[year]['F']]
    mp = [p for (o, p) in names[year]['M']]
    fp = [p for (o, p) in names[year]['F']]
    print (year,
           len(fn), len(mn),
           ### androgynous by proportion
           f'{calculate_proportion(mn, fn):.3f}',
           f'{calculate_proportion(mo, fo):.3f}',
           f'{calculate_proportion(mp, fp):.3f}',
           #f'{sample_proportion(mn, fn):.3f}',
           #f'{sample_proportion(mo, fo):.3f}',
           #f'{sample_proportion(mp, fp):.3f}',
           f'{androgyny(mn, fn):.3f}',
           f'{androgyny(mo, fo):.3f}',
           f'{androgyny(mp, fp):.3f}',
           #f'{sample_androgyny(mn, fn):.3f}',
           #f'{sample_androgyny(mo, fo):.3f}',
           #f'{sample_androgyny(mp, fp):.3f}',

            sep='\t')
    for (group, male, female) in [('Name (full)', mn, fn),
                                  ('Pronunciation', mp, fp),
                                  ('Orthography', mo, fo),
                                  ]:
        gname = f"{group} ({title[year]})"
        stats, total_names = calculate_distribution(male, female, f"{year}")
        graph_proportion2(stats, gname)
        tabulate_proportion(stats, total_names,  gname)
        #print(stats)




    
