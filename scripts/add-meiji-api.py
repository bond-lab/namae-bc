import pandas as pd
import sqlite3
import sys
import jaconv

def add_meiji(database_path, data_path, total_path):
    """
    Add this data:
    year,rank,name,count,per,sex,code,data_type,gender,yomi
    1938,1.0,勝,,,m,21213,names,male,
    1938,1.0,和子,,,f,21644_23376,names,female,
    2012,1.0,,86.0,0.0254,m,12495_12523_12488,readings,male,ハルト
    2012,1.0,,60.0,0.0186,f,12518_12452,readings,female,ユイ
    """
    data = []
    totals = []
    with open(data_path) as f:
        for l in f:
            if l.startswith('year'):
                continue #lose header
            year,rank,name,count,per,sex,code,data_type,gender,yomi = l.strip().split(",")
            year = int(year)
            rank =  int(float(rank))
            if count:
                count = int(float(count))
            else:
                count = None
            gender = sex.upper()
            name = name if name else None
            yomi = jaconv.kata2hira(yomi) if yomi else None
            data.append((year, name, yomi, rank, gender, count, 'meiji'))

    with open(total_path) as f:
        for l in f:
            if l.startswith('Year'):
                continue
            (year, total, boy, girl) = l.strip().split("\t")
            totals.append((int(year), 'M', boy))
            totals.append((int(year), 'F', girl))
    #print("DATA:", data[:10])
    conn = sqlite3.connect(database_path)
    c = conn.cursor()
    c.executemany(""" 
    INSERT INTO nrank (year, orth, pron, rank, gender, freq, src)
    VALUES (?, ?, ?, ?, ?, ?, ?)""", data)
    ### save the totals (to be loaded with the years)
    c.executemany("""
    INSERT INTO name_year_cache (src, dtype, year, gender, count)
            VALUES ('totals', 'orth', ?, ?, ?)""",
                  totals)
    conn.commit()
    conn.close()         

def add_missing(excel_path, db_path):
    """
    for some reason 2013 is missing counts from the api data for orth only
    """
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    excel_data = pd.read_excel(excel_path,
                               sheet_name='2013',
                               dtype='str',
                               header=None)
    df = pd.DataFrame(excel_data)
    df.fillna('', inplace=True) #
    df.columns = 'male mcount _ _ _ female fcount'.split()
    for index, row in df.iterrows():
        #print (row)
        if row['male'] and row['mcount']:
                # year, orth, pron, loc, gender, explanation, src
            try:
                 c.execute(""" 
                 UPDATE nrank set freq= ?
                 WHERE year = 2013 
                   AND orth = ?
                   AND gender = 'M'
                   AND src = 'meiji'""",
                           ((int(row['mcount']),
                             row['male'].strip())))
            except:
                print('ERROR', 'M', row['male'], row['mcount'])
        if row['female'] and row['fcount']:
            try:
             c.execute(""" 
                 UPDATE nrank set freq= ?
                 WHERE year = 2013 
                   AND orth = ?
                   AND gender = 'M'
                   AND src = 'meiji'""",
                           ((int(row['fcount']),
                             row['female'].strip())))
            except:
                print('ERROR', 'F', row['female'], row['fcount'])

    conn.commit()
    conn.close()
    
def update_namae (db_path, src):
    """
    add the names to meiji
    """
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("""
    WITH RECURSIVE freq_generator AS (
  -- Base case: start with counter = 1 for each record
  SELECT year, orth, pron, rank, gender, src, 1 as counter, freq
  FROM nrank 
  WHERE src = ?
  
  UNION ALL
  
  -- Recursive case: increment counter until it reaches freq
  SELECT year, orth, pron, rank, gender, src, counter + 1, freq
  FROM freq_generator
  WHERE counter < freq
)
INSERT INTO namae (year, orth, pron, loc, gender, explanation, src)
SELECT year, orth, pron, NULL, gender, NULL, src
FROM freq_generator
ORDER BY year, orth, counter""", (src,))
    conn.commit()
    conn.close()

    
if __name__ == "__main__":
    database_path = sys.argv[1]
    data_path = sys.argv[2]
    total_path = sys.argv[3]
    excel_path = sys.argv[4]
    add_meiji(database_path, data_path, total_path)
    add_missing(excel_path, database_path)
    update_namae (database_path, 'meiji')

