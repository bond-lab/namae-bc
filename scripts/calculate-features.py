###
###  Annotate data with various metadata
###

import sqlite3
import sys, os
from utils import whichScript, mora_hiragana, syllable_hiragana

db = "namae.db"
#scriptdir = os.path.dirname(sys.argv[0])
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
                   len(orth),
                   len(pron) if pron else None,
                   len(mora) if mora else None,
                   len (syll) if syll else None,
                   orth[0] if len(orth) > 1 else None,
                   orth[-1] if len(orth) > 1 else None,
                   orth[-2] if len(orth) > 2 else None,
                   mora[0] if mora and len(mora) > 1 else None,
                   mora[-1] if mora and len(mora) > 1 else None,
                   mora[-2] if mora and len(mora) > 2 else None,
                   syll[0] if syll  and len(syll) > 1 else None,
                   syll[-1] if syll and len(syll) > 1 else None,
                   syll[-2] if syll and len(syll) > 2 else None,
                   orth[0] if len(orth) == 1 else None, # uni_ch
                   whichScript(orth)))
        
tagName(conn)
        
conn.commit()
