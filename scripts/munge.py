import pandas as pd
import sqlite3
import numpy as np
import sys, os

db = "namae.db"

scriptdir = os.path.dirname(sys.argv[0])

# make the database

conn = sqlite3.connect(db)    # loads dbfile as con
c = conn.cursor()
with open(os.path.join(scriptdir, 'tables.sql'), 'r') as sql_file:
    sql_script = sql_file.read()
c.executescript(sql_script)
conn.commit()

# Load the xlsx file

for (sheet, gender) in [(0, 'M'), (1, 'F')]:

    excel_data = pd.read_excel(os.path.join(scriptdir,
                                            "../data/jmena 2008-2022.xlsx"),
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






# kanji = dd(lambda: dd(lambda: dd(list)))


# for index, row in df.iterrows():
#     kanji[row['kanji']][row['hira']][row['date']].append((row['gender'], row['explanation']))


# for nom in kanji:
#     print(nom)
#     for hira in kanji[nom]:
#         print(f"  {hira}")
#         for year in kanji[nom][hira]:
#             print(f"     {year}")
#             for gen, exp in kanji[nom][hira][year]:
#                 print(f"    {gen} {exp}")
