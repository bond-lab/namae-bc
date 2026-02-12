import pandas as pd
import sqlite3
import numpy as np
import sys, os

from db import cache_years

db = "namae.db"

scriptdir = os.path.dirname(sys.argv[0])
excelfile = sys.argv[1]

# make the database

conn = sqlite3.connect(db)    # loads dbfile as con
c = conn.cursor()
with open(os.path.join(scriptdir, 'tables.sql'), 'r') as sql_file:
    sql_script = sql_file.read()
c.executescript(sql_script)
conn.commit()

# Load the xlsx file

for (sheet, gender) in [(0, 'M'), (1, 'F')]:

    excel_data = pd.read_excel(excelfile,
                               sheet_name=sheet,
                               dtype='str',
                               header=None)
    df = pd.DataFrame(excel_data)
    df.fillna('', inplace=True) #
    
    df.columns = 'blank1 date kanji hira location gender explanation'.split()
    for index, row in df.iterrows():
        #print(row)
        c.execute("""
        INSERT INTO namae (year, orth, pron, loc, gender, explanation, src)
        VALUES (?, ?, ?, ?, ?, ?, ?)""", (int(row['date']),
                                       row['kanji'],
                                       row['hira'],
                                       row['location'],
                                       gender,
                                       row['explanation'],
                                       'bc'))
conn.commit()

### add bc data to nrank
c.executescript("""
-- Insert aggregated data by orth only (pron = NULL)
INSERT INTO nrank (year, orth, pron, rank, gender, freq, src)
SELECT
  year,
  orth,
  NULL AS pron,
  ROW_NUMBER() OVER (PARTITION BY year, gender ORDER BY COUNT(*) DESC) AS rank,
  gender,
  COUNT(*) AS freq,
  src
FROM namae
WHERE src = 'bc'
GROUP BY year, orth, gender, src
ORDER BY year, gender, COUNT(*) DESC;

-- Insert aggregated data by pron only (orth = NULL)
INSERT INTO nrank (year, orth, pron, rank, gender, freq, src)
SELECT
  year,
  NULL AS orth,
  pron,
  ROW_NUMBER() OVER (PARTITION BY year, gender ORDER BY COUNT(*) DESC) AS rank,
  gender,
  COUNT(*) AS freq,
  src
FROM namae
WHERE src = 'bc'
GROUP BY year, pron, gender, src
ORDER BY year, gender, COUNT(*) DESC;

-- Insert aggregated data by both orth and pron
INSERT INTO nrank (year, orth, pron, rank, gender, freq, src)
SELECT
  year,
  orth,
  pron,
  ROW_NUMBER() OVER (PARTITION BY year, gender ORDER BY COUNT(*) DESC) AS rank,
  gender,
  COUNT(*) AS freq,
  src
FROM namae
WHERE src = 'bc'
GROUP BY year, orth, pron, gender, src
ORDER BY year, gender, COUNT(*) DESC;
""")

cache_years(db, 'bc')

conn.commit()

