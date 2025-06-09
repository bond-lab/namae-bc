###
### Calculate the tables used in the book
###
import os
import sqlite3
from collections import defaultdict as dd
import json

from db import db_options


db_path = os.path.join(os.path.dirname(__file__), '../web/db/namae.db')
data_path =  os.path.join(os.path.dirname(__file__), '../web/static/data/book_tables.json')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

    
### Chapter 1

tables = dd(dict)

base = { 'caption':'',
         'headers':list(),
         'rows':list() # of lists
         }

def DBname(src):
    names = {'totals':'Meiji (Total)',
             'births':'Births'}
    if src in names:
        return names[src]
    if src in db_options:
        return db_options[src][1]
    else:
        'Unknown'
    

def make_overview(c):
    """
    Summarise the data sources
    """
    table = base.copy()
    table['caption'] = "Overview of data"
    table['headers'] = ["Source", "From", "To", '# Names', "#/year", "Comment"]
    
    c.execute("""select src, min(year), max(year), sum(count) as freq
    from name_year_cache
    where src in ('bc', 'hs', 'meiji', 'births')
    group by src
    order by freq""")

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
    

tables['ch01']['data_sum'] = make_overview(cursor)



with open(data_path, 'w') as out:
    json.dump(tables, out)
