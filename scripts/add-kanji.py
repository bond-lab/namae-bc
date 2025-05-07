from jamdict import Jamdict
import sqlite3 
import sys, os
from utils import whichScript
from collections import defaultdict as dd
import jaconv

# Initialize Jamdict
jam = Jamdict()

db = "namae.db"
scriptdir = os.path.dirname(sys.argv[0])
conn = sqlite3.connect(db)
c = conn.cursor()

# Begin transaction
conn.execute("BEGIN TRANSACTION")

# Fetch all name data
c.execute("SELECT nid, orth, gender FROM namae")

# Process names and collect kanji
kanji = set()            
nid = dd(set)
for n, o, g in c:
    nid[o].add(n)
    for k in o:
        if whichScript(k) == 'kanji':
            kanji.add(k)

# Prepare batch inserts
kanji_data = []
kid = {}
next_kid = 1  # Assuming auto-increment starts at 1, adjust if needed

# Process all kanji at once
for k in kanji:
    result = jam.lookup(k)
    chars = result.chars
    if chars:
        char = chars[0]
        imi, on, kun, other = [], [], [], []
        for group in char.rm_groups:
            imi.extend(r.value for r in group.meanings if r.m_lang in ("en", ""))
            on.extend(r.value for r in group.readings if r.r_type == 'ja_on')
            kun.extend(r.value for r in group.readings if r.r_type == 'ja_kun')
            other.extend(r.value for r in group.readings if r.r_type not in ('ja_kun', 'ja_on'))
        
        kanji_data.append((
            k, 
            char.grade,
            char.freq,
            ', '.join(imi),
            ' '.join(kun),
            ' '.join([jaconv.kata2hira(k) for k in on]),
            ', '.join(other),
            ' '.join(char.nanoris),
            char.stroke_count
        ))
        kid[k] = next_kid
        next_kid += 1
    else:
        print(f"Couldn't find {k} in Kanjidic")

# Add special character
kanji_data.append(('々', '', '', 'ditto', '', '', '', '', 3))
kid['々'] = next_kid

# Batch insert kanji data
c.executemany("""
    INSERT INTO kanji (kanji, grade, freq, imi, kunyomi, onyomi, other, nanori, scount)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
""", kanji_data)

# Prepare name-to-kanji relations
ntok_data = []
for o in nid:
    for k in o:
        if whichScript(k) == 'kanji':
            if k in kid:
                for n in nid[o]:
                    ntok_data.append((n, kid[k]))
            else:
                print(f"Can't add kanji for {k}, not in kanji dictionary")

# Batch insert name-to-kanji relations
c.executemany("INSERT INTO ntok (nid, kid) VALUES (?, ?)", ntok_data)

# Commit transaction
conn.commit()
conn.close()
