###
###  Calculate features but only once for each type
###

import sqlite3
import argparse
from utils import whichScript, mora_hiragana, syllable_hiragana
from calc_regular import KanjiReadingAnalyzer


###
### Orthography
###
def calc_orth(conn):
    c = conn.cursor()
    c.execute("""SELECT DISTINCT orth FROM namae
                 WHERE orth IS NOT NULL""")

    data = []
    for (orth, ) in c:
        data.append([orth, whichScript(orth)])

    c.executemany("""INSERT INTO orth (orth, script)
                     VALUES (?,?)""", data)
    conn.commit()

###
### Phonology
###
def calc_pron(conn):
    c = conn.cursor()
    c.execute("""SELECT DISTINCT pron FROM namae
                 WHERE pron IS NOT NULL""")
    data = []
    for (pron, ) in c:
        mora = mora_hiragana(pron)
        syll = syllable_hiragana(mora)
        data.append([pron, 
                     " ".join(mora),
                     " ".join(syll)])
    c.executemany("""INSERT INTO pron (pron, mora, syll)
                     VALUES (?,?,?)""", data)
    conn.commit()

    
###
### Reading
###
def calc_mapp(conn):
    c = conn.cursor()
     
    c.execute("""SELECT DISTINCT orth, pron FROM namae
                 WHERE orth IS NOT NULL AND pron IS NOT NULL""")
    analyzer = KanjiReadingAnalyzer()
    analyzer.load_kanjidic()
    data = []
    for (orth, pron) in c:
        result = analyzer.analyze_name_reading(orth, pron)
        data.append([orth, 
                     pron,
                     " ".join("/".join(x) for x in  result)]) 


    c.executemany("""INSERT INTO mapp (orth, pron, mapping)
                     VALUES (?,?,?)""", data)
    conn.commit()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Calculate various features')
    parser.add_argument('database', help='Path to SQLite database file')
    args = parser.parse_args()

    #scriptdir = os.path.dirname(sys.argv[0])
    conn = sqlite3.connect(args.database)
    calc_orth(conn)
    calc_pron(conn)
    calc_mapp(conn)
        
