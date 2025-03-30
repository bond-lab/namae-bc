import sqlite3, os
from flask import current_app, g
from collections import defaultdict as dd
import numpy as np
import scipy
from scipy.stats import chi2_contingency, fisher_exact

### limit for most queries
### not much point showing more examples than this
###
lim = 512
sentlim = 8


def get_db(root, db):
    if 'db' not in g:
        g.db = sqlite3.connect(
            os.path.join(root, f'db/{db}')
            #detect_types=sqlite3.PARSE_DECLTYPES
        )
#        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(e=None):
    db = g.pop('db', None)

    if db is not None:
        db.close()


############################################################


def params(lst):
    return ','.join(['?']*len(lst))

def get_name(conn):
    c = conn.cursor()
    c.execute("""select orth, pron, gender, year from namae""")
    mfname = dd(lambda: dd(list))
    kindex = dd(set)
    hindex = dd(set)
    for (orth, pron, gender, year) in c:
        mfname[(orth, pron)][gender].append(year)
        kindex[orth].add((orth, pron))
        hindex[pron].add((orth, pron))
    return mfname, kindex, hindex

def get_name_year(conn, table='namae', src='bc', data_type='both'):
    """
    Retrieve names data from the database, organized by year and gender.

    Args:
        conn: SQLite connection object.
        table: Name of the table to query.
        src: Source of the data ('bc', 'hs', 'hs+bc').
        data_type: Type of data to retrieve ('orth', 'pron', 'both').

    Returns:
        A nested defaultdict organized by year and gender containing the names data.

    Raises:
        ValueError: If an invalid combination of src and data_type is provided.
    """
    if src in ['hs', 'hs+bc'] and data_type != 'orth':
        raise ValueError(f"Invalid combination: {src} with {data_type}. Only 'orth' is allowed for 'hs' and 'hs+bc'.")
    c = conn.cursor()

    # Determine the columns to select based on data_type
    if data_type == 'orth':
        select_columns = "orth, gender, year"
    elif data_type == 'pron':
        select_columns = "pron, gender, year"
    else:
        select_columns = "orth, pron, gender, year"

    c.execute(f"""SELECT {select_columns}
    FROM {table}
    WHERE src = ? ORDER BY year""", (src,))
    byyear =  dd(lambda:  dd(list))
    for row in c:
        if data_type == 'orth':
            orth, gender, year = row
            byyear[year][gender].append((orth,))
        elif data_type == 'pron':
            pron, gender, year = row
            byyear[year][gender].append((pron,))
        else:
            orth, pron, gender, year = row
            byyear[year][gender].append((orth, pron))
    return byyear

def get_stats(conn):
    """
    return various statistics
    stats[name][gender] = X
    DISTINCT
    stats['dname'][gender] = X
    stats['pron'][gender] = X
    stats['orth'][gender] = X
    """

    stats = dd(lambda: dd(lambda: dd(int))) 
    
    c = conn.cursor()
    c.execute("""SELECT gender, COUNT (gender) 
    FROM (SELECT DISTINCT orth, pron, gender FROM namae) 
    GROUP BY gender""")
    for (gender, freq) in c:
        stats['dname'][gender] = freq

    c.execute("""select gender, count(distinct orth) 
    FROM namae
    GROUP BY gender""")
    for (gender, freq) in c:
        stats['orth'][gender] = freq

    c.execute("""select gender, count(distinct pron) 
    FROM namae
    GROUP BY gender""")
    for (gender, freq) in c:
        stats['pron'][gender] = freq

    c.execute("""select gender, count(gender) 
    FROM namae
    GROUP BY gender""")
    for (gender, freq) in c:
        stats['name'][gender] = freq

    return stats

def get_feature(conn, feat1, feat2, threshold,
                table='namae', src='bc',
                short=False):

    c = conn.cursor()

    ddata = dd(lambda: dd(int))
    data = list()
    tests = list()
    summ = dict()
    examples = dd(list)

    if feat1 == 'kanji':
       c.execute(f"""select kanji, gender, count(*) as cnt 
       from kanji left join ntok on kanji.kid = ntok.kid 
       left join {table} on ntok.nid = {table}.nid
       where src = ?
       group by kanji, gender""", (src,))

       for ft, gender, count in c:
           ddata[ft][gender] =  int(count)
    
    elif not feat2:
        ## 'char1', 'char2', 'char_1', 'mora1', 'mora_1', 'uni_ch'
        #assert feat1 in ['char1'] 
        c.execute(f"""
        SELECT {feat1}, gender, count(*) as cnt 
        FROM attr left join {table} on attr.nid={table}.nid 
        WHERE {feat1} IS NOT NULL
        AND src = ?
        GROUP BY {feat1}, gender""", (src,))
        
        for ft, gender, count in c:
            ddata[ft][gender] =  int(count)
            
        if not short:
            c.execute(f"""select {feat1}, orth, pron, count({feat1}) 
            from {table} left join attr on {table}.nid = attr.nid
            WHERE src = ?
            group by {feat1}, orth, pron 
            order by {feat1}, count ({feat1}) DESC""", (src,))
        for ft, orth, pron, freq in c:
            examples[ft].append((orth, pron))

    else:  # two features
        c.execute(f"""
        SELECT {feat1}, {feat2}, gender, count(*) as cnt 
        FROM attr left join {table} on attr.nid={table}.nid
        WHERE {feat1} is not Null AND {feat2} is not Null
        AND src = ?
        GROUP BY {feat1}, {feat2}, gender""", (src,))
        for ft1, ft2, gender, count in c:
            ddata[f"{ft1}, {ft2}"][gender] =  int(count)
            
        if not short:
            c.execute(f"""
SELECT {feat1}, {feat2}, orth, pron, count({feat1}) 
FROM {table} left join attr on {table}.nid = attr.nid
WHERE src = ?
GROUP BY {feat1}, {feat2}, orth, pron 
ORDER BY {feat1}, {feat2}, count ({feat1}) DESC""", (src,))
            for ft1, ft2, orth, pron, freq in c:
                examples[f"{ft1}, {ft2}"].append((orth, pron))

            
    for key in ddata:
        #print (key, ddata[key]['M'])
        if ddata[key]['M'] + ddata[key]['F'] >  threshold:
            data.append((key,
                ddata[key]['M'],
                ddata[key]['F'],
                ddata[key]['F'] /  (ddata[key]['M'] + ddata[key]['F'])))

    summ['allm'] = sum(d[1] for d in data)
    summ['allf'] = sum(d[2] for d in data)
    summ['allt'] = summ['allm'] + summ['allf']

    print(feat1, feat2,   summ['allm'],  summ['allf'])
    
    CT = np.array([[d[1], d[2]] for d in data])
    res = chi2_contingency(CT)

    summ['chi2'] = res.statistic
    summ['pval'] = res.pvalue
    summ['phi'] = np.sqrt(res.statistic / summ['allt'] )
    summ['lvl'] = 0.05 / len(data)

    if not short:
        ### Calculate Statistics
        for d in data:
            CT = [[d[2], d[1]],
                  [summ['allm']-d[2], summ['allf']-d[1]]]
            res = fisher_exact(CT)
            exe = [] ## up to three from a list
            if d[0] in examples:
                if len(examples[d[0]]) > 2:
                    exe = examples[d[0]][:3]
                elif len(examples[d[0]]) == 2:
                    exe = examples[d[0]][:2]
                else:
                    exe = examples[d[0]][:1]
                
            tests.append((d[0], d[1], d[2], d[3],
                          res.statistic, res.pvalue,
                          res.pvalue < summ['lvl'],
                          tuple(exe)))

        
    return data, tests, summ

        
def get_redup(conn):
    c = conn.cursor()

    data = dict()
    data['redup'] = dict()
    data['redup+'] = dict()
    c.execute("""
    SELECT orth, pron, count(pron) as freq, gender 
FROM namae 
WHERE src = 'bc'
AND LENGTH(pron) > 1
AND (LENGTH(pron) % 2 = 0 
AND SUBSTR(pron, 1, LENGTH(pron) / 2) = SUBSTR(pron, LENGTH(pron) / 2 + 1)) 
GROUP BY pron, orth, gender
ORDER BY pron, freq DESC, orth""")

    store = dd(dict)
    for (orth, pron, freq, gender)  in c:
        if (pron, gender) not in store:
            store[(pron, gender)]['freq'] = freq
            store[(pron, gender)]['orths'] = [(orth, freq) ]
        else:
            store[(pron, gender)]['freq'] += freq
            store[(pron, gender)]['orths'].append((orth, freq))
    data['redup'] = dict(sorted(store.items(),
                                key=lambda x: x[1]['freq'],
                                reverse=True))
    #print(data['redup'])

### look for XXY
    
    c.execute("""
    SELECT orth, pron, count(pron) as freq, gender 
FROM namae 
WHERE  LENGTH(pron)  > 2 
AND SUBSTR(pron, 1, 1) = SUBSTR(pron, 2,1) 
GROUP BY pron, orth, gender
ORDER BY pron, freq DESC, orth""")

    store = dd(dict)
    for (orth, pron, freq, gender)  in c:
        if (pron, gender) not in store:
            store[(pron, gender)]['freq'] = freq
            store[(pron, gender)]['orths'] = [(orth, freq) ]
        else:
            store[(pron, gender)]['freq'] += freq
            store[(pron, gender)]['orths'].append((orth, freq))
    data['redup+'] = dict(sorted(store.items(),
                                key=lambda x: x[1]['freq'],
                                reverse=True))
    return data

 
def get_readings(conn, kanjis):
    """
    Retrieve the readings of the given kanjis from the database.

    Args:
        conn: SQLite connection object.
        kanjis: List of kanji characters to look up.

    Returns:
        Dictionary with kanji as keys and their readings categorized as 'on', 'kun', and 'nanori'.
    """
    c = conn.cursor()

    # Prepare the results dictionary
    yomi = {}

    # Iterate over the provided kanjis
    for kanji in kanjis:
        # Query the database for readings of the current kanji
        c.execute("SELECT onyomi, kunyomi, nanori FROM kanji WHERE kanji = ?", (kanji,))
        result = c.fetchone()

        if result:
            onyomi, kunyomi, nanori = result
            yomi[kanji] = {
                'on': onyomi.split(',') if onyomi else [],
                'kun': kunyomi.split(',') if kunyomi else [],
                'nanori': nanori.split(',') if nanori else []
            }
        else:
            # If the kanji is not found, set empty readings
            yomi[kanji] = {
                'on': [],
                'kun': [],
                'nanori': []
            }

    return yomi

# Example usage:
# Assuming you have an SQLite connection `conn` to the database
# get_readings(conn, ['妃'])
# Output: { '妃': {'on': ['ひ'], 'kun': ['きさき'], 'nanori': ['き', 'ぴ', 'み']} }

    
