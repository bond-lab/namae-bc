import sys, os
import sqlite3
from collections import defaultdict as dd, Counter

# Add the parent directory to the system path for module imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from web.db import db_options, get_name_year, get_name_count_year

current_directory = os.path.abspath(os.path.dirname(__file__))

db_path = os.path.join(current_directory, "../web/db/namae.db")

conn = sqlite3.connect(db_path)


def calculate_berger_parker(names, total, top_n=1):
    """Calculate Berger–Parker index considering the top_n most frequent names."""
    name_counts = Counter(names)
    top_counts = sum(count for _, count in name_counts.most_common(top_n))
    return top_counts / total


all_names=get_name_year(conn, src='meiji',
                    table='namae', dtype='orth')
counts= get_name_count_year(conn, src='totals', dtype='orth')

for top_n in [1, 5, 10, 25]:
    for gender in ['M', 'F']:
        for year in counts:
            total = counts[year][gender]
            names = all_names[year][gender]
            subtotal =len(names)
            bp = calculate_berger_parker(names, total, top_n=1)
            print(top_n, gender, year, bp, subtotal, total, sep='\t')
