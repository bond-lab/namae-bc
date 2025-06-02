import sqlite3
import os
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

    conn.commit()
    conn.close()

if __name__ == "__main__":
    main()
