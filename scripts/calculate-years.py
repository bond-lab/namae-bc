"""
This script calculates and stores the number of names per year from a database,
and generates plots to visualize the data. It also includes functionality to
store the number of live births per year.
"""

import sqlite3
import os
import matplotlib.pyplot as plt
import numpy as np
from db import db_options, get_name_count_year

def store_years(db_path, src):
    """
    Store the number of names per year in the database for a given source.

    Args:
        src (str): The source identifier for the data.
    """
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    for src in db_options:
        table = db_options[src][0]
        dtypes =  db_options[src][2]
        for dtyps in dtypes:
            print(table, dtyps)
            # Fetch the data that will be inserted
            c.execute(f'''
            SELECT src, 'orth', year, gender, COUNT(*) as freq
            FROM {table}
            WHERE src = '{src}'
            GROUP BY year, gender
            HAVING freq > 0
            ''')
            rows = c.fetchall()
            for row in rows:
                print(f"Attempting to insert: src={row[0]}, dtype='orth', year={row[2]}, gender={row[3]}, count={row[4]}")
            
            c.execute(f'''
            INSERT OR IGNORE INTO name_year_cache (src, dtype, year, gender, count)
            SELECT src, 'orth', year, gender, COUNT(*)  as freq
            FROM {table}
            WHERE src = '{src}'
            GROUP BY year, gender
            HAVING freq > 0
            ''')
            ''')
    conn.commit()
    conn.close()
    
def store_births(db_path):
    """
    Store the number of live births per year in the database.
    """
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    fh = open('../data/live_births_year.tsv')
    for l in fh:
        row = l.strip().split()
        if row[0] == 'Year':
            continue
        else:
            c.execute("""
            INSERT INTO name_year_cache (src, dtype, year, gender, count)
            VALUES ('births', 'orth', ?, 'M', ?)
            """, (int(row[0]), int(row[2])))
            c.execute("""
            INSERT INTO name_year_cache (src, dtype, year, gender, count)
            VALUES ('births', 'orth', ?, 'F', ?)
            """, (int(row[0]), int(row[3])))

    conn.commit()
    conn.close()

def create_gender_plot(src):
    """
    Create and save a bar plot showing the number of names per year divided by gender.

    Args:
        src (str): The source identifier for the data.
    """


    # Get data from the database
    db_path = os.path.join(os.path.dirname(__file__), '../web/db/namae.db')
    conn = sqlite3.connect(db_path)
    names = get_name_count_year(conn,
                                src=src,
                                dtype='orth')
    years = []
    male_counts = []
    female_counts = []

    for year in names:
        if year >= 1989:
            years.append(year)
            male_counts.append(names[year]['M'])
            female_counts.append(names[year]['F'])

    if src == 'births':
        db_name = 'Births'
    elif src == 'totals':
        db_name = 'Meiji total data'
    else:
        db_name = db_options[src][1]
            
    # Create the figure and axis for plotting
    fig, ax = plt.subplots(figsize=(10, 6))

    filename =f'years_{src}'
    plot_path = os.path.join(os.path.dirname(__file__), f'../web/static/plot/{filename}.png')
     
    # Plot male and female counts
    ax.bar(years, female_counts, color='purple', label='Women', alpha=0.6)
    ax.bar(years, [-x for x in male_counts], color='orange', label='Men', alpha=0.6)

    # Function to format numbers based on bar width
    def format_number(num, bar_width):
        if 'hs' in src:
            return f"{round(num / 1000)}"
        else:
            return f"{num}"
    def font_size(years):
        ny = len(years)
        if ny  < 16:
            return 10
        elif ny  < 30:
            return 8
        else:
            return 7
        

    # Add numbers on top of each bar for both male and female counts
    
    for i, (female, male) in enumerate(zip(female_counts, male_counts)):
        bar_width = ax.patches[i].get_width()
        ax.text(years[i],  0.98 * female, format_number(female, bar_width),
                ha='center', va='top', fontsize=font_size(years), color='black')
        ax.text(years[i], -0.98 * male, format_number(male, bar_width),
                ha='center', va='bottom', fontsize=font_size(years), color='black')

    # Remove all spines and ticks for a minimalist look
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['bottom'].set_visible(False)

    ax.set_yticks([])  # Remove y-axis numbers
    ax.tick_params(left=False, bottom=False)

    # Ensure x-axis shows only whole numbers for years
    ax.xaxis.set_major_locator(plt.MaxNLocator(integer=True))

    # Add labels and title with subtle text styling
    ax.set_xlabel('Year', fontsize=12)
    if 'hs' in src:
        ax.set_ylabel('Number of Names (in thousands)', fontsize=12)
    else:
        ax.set_ylabel('Number of Names', fontsize=12)
    ax.set_title(f'Number of Names per Year, Divided by Gender ({db_name})', fontsize=14, weight='bold')

    # Add a legend with minimalist styling
    ax.legend(frameon=False)

    # Save the plot to a file
    plt.savefig(plot_path, format='png')
    plt.close(fig)

# Iterate over each data source and update year counts and create plots

db_path = os.path.join(os.path.dirname(__file__), '../web/db/namae.db')

store_births(db_path)

for src in db_options:
    print(f'Updating Year Counts for {src}')
    store_years(db_path, src)

    print(f'Creating Graph for {src}')
    create_gender_plot(src)

    
print(f'Creating Graph for Births')
create_gender_plot('births')

print(f'Creating Graph for Meiji Totals')
create_gender_plot('totals')
         

