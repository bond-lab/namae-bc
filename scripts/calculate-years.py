import sqlite3
import os
import matplotlib.pyplot as plt
import numpy as np
from db import db_options

def main():
    db_path = os.path.join(os.path.dirname(__file__), '../web/db/namae.db')
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    for src in db_options:
        table = db_options[src][0]
    
        c.execute(f'''
        INSERT INTO name_year_cache (src, dtype, year, gender, count)
        SELECT src, 'orth', year, gender, COUNT(*)  as freq
        FROM {table}
        WHERE src = '{src}'
        GROUP BY year, gender
        HAVING freq > 0
        ''')

    # let's also add the number of live births
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

    # Example data for plotting
    years = [2000, 2001, 2002]  # Replace with actual years
    male_counts = [100, 150, 200]  # Replace with actual male counts
    female_counts = [120, 130, 180]  # Replace with actual female counts
    db_name = "ExampleDB"  # Replace with actual database name

    create_gender_plot(years, male_counts, female_counts, db_name)

    conn.commit()
    conn.close()

def create_gender_plot(years, male_counts, female_counts, db_name):
    # Create the figure and axis
    fig, ax = plt.subplots(figsize=(10, 6))

    # Plot men and women counts
    ax.bar(years, female_counts, color='purple', label='Women', alpha=0.6)
    ax.bar(years, [-x for x in male_counts], color='orange', label='Men', alpha=0.6)

    # Add numbers on top of each bar for both men and women
    for i, (female, male) in enumerate(zip(female_counts, male_counts)):
        ax.text(years[i], female - 72, str(female),
                ha='center', va='bottom', fontsize=10, color='white')
        ax.text(years[i], - male + 24, str(male),
                ha='center', va='bottom', fontsize=10, color='white')

    # Remove all spines and ticks for a minimalist look
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['bottom'].set_visible(False)

    ax.set_yticks([])  # Remove y-axis numbers
    ax.tick_params(left=False, bottom=False)

    # Add labels and title with subtle text styling
    ax.set_xlabel('Year', fontsize=12)
    ax.set_ylabel('Number of Names', fontsize=12)
    ax.set_title('Number of Names per Year, Divided by Gender', fontsize=14, weight='bold')

    # Add a legend with minimalist styling
    ax.legend(frameon=False)

    # Save the plot to a file
    plot_path = os.path.join(os.path.dirname(__file__), '../web/static/plot/years_gender_plot.png')
    plt.savefig(plot_path, format='png')
    plt.close(fig)
    main()
