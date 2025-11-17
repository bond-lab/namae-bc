###
###  Annotate data with various metadata
###

import sqlite3
import sys, os
from utils import whichScript, mora_hiragana, syllable_hiragana


#scriptdir = os.path.dirname(sys.argv[0])

if len(sys.argv) > 1:
    db  = sys.argv[1]
else:
    db = "namae.db"
conn = sqlite3.connect(db)

  
def tagName (conn):
    """
    Read the database, add information to the database
    script
    length
    
    """
    c = conn.cursor()
    d = conn.cursor()
    c.execute("SELECT nid, orth, pron FROM namae")

    ### add info
    for nid, orth, pron in c:
        if pron:
            mora = mora_hiragana(pron)
            syll = syllable_hiragana(mora)
        else:
            mora = ''
            syll = ''
        
        d.execute(""" INSERT INTO attr 
        (nid, olength, plength, mlength, slength,
        char1, char_1, char_2, 
        mora1, mora_1, mora_2,
        syll1, syll_1, syll_2,
        uni_ch, 
        script)
        VALUES (?, 
        ?, ?, ?, ?,  
        ?, ?, ?,  
        ?, ?, ?,  
        ?, ?, ?,  
        ?, ?)""",    
                  (nid,
                   len(orth) if orth else None,
                   len(pron) if pron else None,
                   len(mora) if mora else None,
                   len (syll) if syll else None,
                   orth[0] if orth and len(orth) > 1 else None,
                   orth[-1] if orth and len(orth) > 1 else None,
                   orth[-2] if orth and len(orth) > 2 else None,
                   mora[0] if mora and len(mora) > 1 else None,
                   mora[-1] if mora and len(mora) > 1 else None,
                   mora[-2] if mora and len(mora) > 2 else None,
                   syll[0] if syll  and len(syll) > 1 else None,
                   syll[-1] if syll and len(syll) > 1 else None,
                   syll[-2] if syll and len(syll) > 2 else None,
                   orth[0] if orth and len(orth) == 1 else None, # uni_ch
                   whichScript(orth) if orth else None))

tagName(conn)
        
conn.commit()
