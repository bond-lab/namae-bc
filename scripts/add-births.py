# store and cache the births

import sqlite3
import sys
from db import db_options, cache_years

def store_births(db_path):
    """
    Store the number of live births per year in the database.
    """
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    fh = open('../data/live_births_year.tsv')
    for l in fh:
        row = l.strip().split()
        if not row or row[0] == 'Year':
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



if __name__ == "__main__":
    db_path = sys.argv[1]

    store_births(db_path)
    cache_years(db_path, 'births')
