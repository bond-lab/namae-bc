from jamdict import Jamdict
# https://jamdict.readthedocs.io/en/latest/recipes.html#low-level-data-queries
import sqlite3 
import sys, os
from utils import whichScript
from collections import defaultdict as dd
from pprint import pprint
import jaconv

jam = Jamdict()

db = "namae.db"

scriptdir = os.path.dirname(sys.argv[0])

conn = sqlite3.connect(db)    # loads dbfile as con
c = conn.cursor()

c.execute("""select nid, orth, gender from namae""")


kanji = set()            
ntokanji = list()
nid = dd(set)
kid = dict()
for n, o, g in c:
    nid[o].add(n)
    for k in o:
        if whichScript(k) == 'kanji':
            kanji.add(k)

            
            
for k in kanji:
    result = jam.lookup(k)
    chars = result.chars
    if chars:
        char=chars[0]
        imi, on, kun, other = [], [], [], []
        for group in char.rm_groups:
            imi.extend(r.value for r in group.meanings if r.m_lang in ("en", ""))
            on.extend(r.value for r in group.readings if r.r_type == 'ja_on')
            kun.extend(r.value for r in group.readings if r.r_type == 'ja_kun')
            other.extend(r.value for r in group.readings if  r.r_type not in ('ja_kun', 'ja_on'))
        c.execute("""INSERT INTO kanji
(kanji, grade, freq, imi,  kunyomi, onyomi, other, nanori, scount)
VALUES  (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                  (k, 
                   char.grade,
                   char.freq,
                   ', '.join(imi),
                   ' '.join(kun),
                   ' '.join([jaconv.kata2hira(k) for k in on]),
                   ', '.join(other),
                   ' '.join(char.nanoris),
                   char.stroke_count))
        kid[k] = c.lastrowid
    else:
        print(f"Couldn't find {k} in Kanjidic")


         
### Wierd Character!
c.execute("""INSERT INTO kanji
(kanji, grade, freq, imi,  kunyomi, onyomi, other, nanori, scount)
VALUES  (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
          ('々', 
           '',
           '',
           'ditto',
           '',
           '',
           '',
           '',
           3))
kid['々'] = c.lastrowid

for o in nid:
    for k in o:
        #print(k,o, sep='\t')
        if whichScript(k) == 'kanji':
            for n in nid[o]:
                if k in kid:
                    c.execute("""INSERT INTO ntok (nid, kid) 
                    VALUES (?, ?)""", (n, kid[k]))
                else:
                    print(f"Can't add kanji for {k}, not in kanji dictionary")
# for k in  kfreq:
#     print(f'\n--- {k} ---')
#     pprint(kanji[k])
#     pprint(kfreq[k])
#     print(f"F Ratio {kfreq[k]['F']/ (kfreq[k]['F'] + kfreq[k]['M']):.2f}'")
#     print()

# def expand_r(readings):
#     allr = []
#     for r in readings:
#         r = r.strip('-')
#         # deal with '.' and '-'
#         # ['ちい.さい', 'こ-', 'お-', 'さ-']
#         if '.' in r:
#             allr.append(r.replace('.', ''))
#             allr += r.split('.')
#         else:
#             allr.append(r)
#     return allr




# def howRead (orth, pron):
#     """
#     if the pronunication can be made from the kanji readings, 
#       return which kanji were used
#     else
#       return empty list
#     """
#     r_type = ('on', 'kun', 'nanori') 
#     readings = []
#     for k in orth:
#         newreadings = []
#         for rt in r_type:
#             for r in expand_r(kanji[k].get(rt, [])):
#                 if readings:
#                     for (x, y) in readings:
#                         #print('E', x, y)
#                         newreadings.append([x+r, y + [rt]])  
#                 else:
#                     newreadings.append([r, [ rt ] ])
#                     #print ('N', [r, [ rt ] ])
#         readings = newreadings
#         #print(newreadings)
#     for x, y in readings:
#         if pron in x:
#             return y
#     return []
#     #print(orth, readings, pron in [x for x,y in readings])

# c.execute("""select nid, orth, pron,  gender from namae""")
# for n, o, p, g in c:
#     print("YOMI", n, o, p, g, howRead(o, p))
    
conn.commit()
