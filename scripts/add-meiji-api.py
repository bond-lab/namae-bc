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

    conn = sqlite3.connect(database_path)
    c = conn.cursor()
    c.executemany(""" 
    INSERT INTO nrank (year, orth, pron, rank, gender, freq, src)
    VALUES (?, ?, ?, ?, ?, ?, ?)""", data)
    ### save the totals (to be loaded with the years)
    c.executemany("""
    INSERT INTO name_year_cache (src, dtype, year, gender, count)
            VALUES ('totals', 'both', ?, ?, ?)""",
                  totals)
    conn.commit()
    conn.close()         
    

if __name__ == "__main__":
    database_path = sys.argv[1]
    data_path = sys.argv[2]
    total_path = sys.argv[3]
    add_meiji(database_path, data_path, total_path)

