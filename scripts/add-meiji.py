import pandas as pd
import sqlite3
import sys
import re


def normalize(s):
    # Convert full-width numbers to half-width, remove commas/whitespace
    return s.translate(str.maketrans('０１２３４５６７８９', '0123456789')).replace(",", "").replace("，", "").replace(" ", "").replace("：", "")

pattern = re.compile(r'男の子(\d+)人、女の子(\d+)人')

# Load the xlsx file
def load_meiji_data(excel_path, db_path):
    """
    Load the data from Meiji Yasuda
    """
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    data = []
    # from https://osf.io/za6x7/files/osfstorage
    # https://doi.org/10.17605/OSF.IO/ZA6X7
    totals = [(2004, 'M', 4861), (2004, 'F', 4419), (2005, 'M', 4292), (2005, 'F', 4082) ]
    for year in range(2006,2023):
        excel_data = pd.read_excel(excel_path,
                                   sheet_name=str(year),
                                   dtype='str',
                                   header=None)
        df = pd.DataFrame(excel_data)
        df.fillna('', inplace=True) #
        df.columns = 'male mcount _ _ _ female fcount'.split()
        for index, row in df.iterrows():
            #print (row)
            if row['male'].startswith('男の子'):
                # total frequencies
                clean = normalize(row['male'])
                #print (year,  normalize(row['male']))
                match = pattern.search(clean)
                if match:
                    boy = int(match.group(1))
                    girl = int(match.group(2))
                    totals.append((year, 'M', boy))
                    totals.append((year, 'F', girl))
            if row['male'] and row['mcount']:
                # year, orth, pron, loc, gender, explanation, src
                try:
                    for i in range(int(row['mcount'])):
                        data.append((year, row['male'].strip(), 'M', 'meiji'))
                except:
                    print('ERROR', year, row['male'], row['mcount'])
            if row['female'] and row['fcount']:
                try:
                # year, orth, pron, loc, gender, explanation, src
                    for i in range(int(row['fcount'])):
                        data.append((year, row['female'].strip(), 'F', 'meiji'))
                except:
                    print('ERROR', year, row['female'], row['fcount'])
    #print (data[::1000])
    #print(totals)
    c.executemany(""" 
    INSERT INTO namae (year, orth, gender, src)
    VALUES (?, ?, ?, ?)""", data)
    ### save the totals (to be loaded with the years)
    c.executemany("""
    INSERT INTO name_year_cache (src, dtype, year, gender, count)
            VALUES ('totals', 'orth', ?, ?, ?)""",
                  totals)
    conn.commit()
    conn.close()
    

if __name__ == "__main__":
    excel_path = sys.argv[1]
    database_path = "namae.db"
    load_meiji_data(excel_path, database_path)

