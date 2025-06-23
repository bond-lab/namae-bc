###
### Calculate the tables used in the book
###
import os, sys
import sqlite3
from collections import defaultdict as dd
import json

from db import db_options


    
### Chapter 1

tables = dd(dict)

base = { 'caption':'',
         'headers':list(),
         'rows':list() # of lists
         }

def DBname(src):
    names = {'totals':'Meiji (Total)',
             'meiji':'Meiji Yasuda',
             'hs':'Heisei Namae',
             'births':'Births'}
    if src in names:
        return names[src]
    if src in db_options:
        return db_options[src][1]
    else:
        'Unknown'
    

def make_overview(c, start=1989, end=2022):
    """
    Summarise the data sources
    """
    table = base.copy()
    table['caption'] = "Overview of data"
    table['headers'] = ["Source", "From", "To", '# Names', "#/year", "Comment"]
    
    c.execute("""SELECT src, min(year), max(year), sum(count) AS freq
    FROM name_year_cache
    WHERE src IN ('bc', 'hs', 'meiji', 'births')
    AND year >= ? AND year <= ?
    GROUP BY src
    ORDER BY freq""", (start, end))

    comment = { 'bc': 'Includes Pronunciation',
                'hs': 'Noisy data',
                'meiji':'Most popular 100 names only',
                'births':'Number of children born each year'
                }

    for row in c:
        cols = [DBname(row[0])] + list(row[1:])
        cols.append(round(row[3] / (1+row[2]-row[1]), 2))
        cols.append(comment[row[0]])
        table['rows'].append(cols)
    return table
    
def make_summary(c, src, start=1989, end=2022):
    table = base.copy()
    
    c.execute("""SELECT
    MIN(year),
    MAX(year),
    SUM(count) FILTER (WHERE gender = 'M') AS boys,
    SUM(count) FILTER (WHERE gender = 'F') AS girls,
    SUM(count) AS total
    FROM name_year_cache 
    WHERE src = ? and count > 0
    AND year >= ? AND year <= ?""", (src, start, end))
    (yfrom, yto, boys, girls, total) = c.fetchone()
    #print (src, start, end, yfrom, yto, boys, girls, total)
    
    table['caption'] = f"Totals {DBname(src)} ({yfrom}-{yto}): ratio = {boys/girls:.2f}"
    table['headers'] = ["", "Frequency"]
    table['rows'] = [ ['Boys', boys],
                      ['Girls', girls],
                      ['Total', total]]

    return table
    

    

if __name__ == "__main__":
    db_path = sys.argv[1] or os.path.join(os.path.dirname(__file__), '../web/db/namae.db')
    data_path = sys.argv[2] or  os.path.join(os.path.dirname(__file__), '../web/static/data/book_tables.json')

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()


    tables['ch01']['data_sum'] = make_overview(cursor)

    target_sources = ['bc', 'hs', 'meiji', 'births']

    for src in target_sources:
        print(f'making tables for {src} ({db_path})')
        tables['ch0A'][f'data_sum_{src}'] =  make_summary(cursor, src)


    with open(data_path, 'w') as out:
        json.dump(tables, out)
