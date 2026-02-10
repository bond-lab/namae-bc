import sqlite3, os
from collections import defaultdict as dd
import numpy as np
import scipy

from scipy.stats import chi2_contingency, fisher_exact, linregress, ttest_ind


# Database options
##
## table, "Table Name", data_types, range
##
db_options = {
    'bc': ('namae', 'Baby Calendar',
           ('orth', 'pron', 'both'), (2008, 2022)),
    'hs': ('namae', 'Heisei',
           ('orth'), (1989, 2009)),
    'hs+bc': ('combined', 'Combined',
              ('orth'), (1989, 2022)),
    'meiji': ('namae', 'Meiji (orth)',
              ('orth'), (2004, 2024)),
    'meiji_p': ('namae', 'Meiji (phon)',
                ('pron'), (2004, 2024)),   
}

dtypes = ('orth', 'pron', 'both')

# Map UI option keys to actual database src values
_src_alias = {'meiji_p': 'meiji'}

def resolve_src(src):
    """Map UI option key to actual database src value."""
    return _src_alias.get(src, src)

### limit for most queries
### not much point showing more examples than this
###
lim = 512
sentlim = 8


def get_db(root, db):
    from flask import g
    if 'db' not in g:
        g.db = sqlite3.connect(
            os.path.join(root, f'db/{db}')
            #detect_types=sqlite3.PARSE_DECLTYPES
        )
#        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(e=None):
    from flask import g
    db = g.pop('db', None)

    if db is not None:
        db.close()


############################################################


def params(lst):
    return ','.join(['?']*len(lst))

def get_name(conn, table='namae', src='bc', dtype=None):
    c = conn.cursor()
    if dtype == 'orth':
        null_filter = "AND orth IS NOT NULL"
    elif dtype == 'pron':
        null_filter = "AND pron IS NOT NULL"
    else:
        null_filter = ""
    c.execute(f"""SELECT orth, pron, gender, year FROM {table} WHERE src = ? {null_filter}""", (src,))
    mfname = dd(lambda: dd(list))
    kindex = dd(set)
    hindex = dd(set)
    for (orth, pron, gender, year) in c:
        mfname[(orth, pron)][gender].append(year)
        kindex[orth].add((orth, pron))
        hindex[pron].add((orth, pron))
    return mfname, kindex, hindex

def get_orth(conn, orth, src='bc'):
    c = conn.cursor()
    c.execute(f"""SELECT year, gender, sum(freq)
    FROM nrank
    WHERE src = ? AND orth=? AND orth IS NOT NULL
    GROUP BY gender, year""", (src, orth))
    results = c.fetchall()
    return results
    
def get_pron(conn, pron, src='bc'):
    c = conn.cursor()
    c.execute(f"""SELECT year, gender, sum(freq)
    FROM nrank
    WHERE src = ? AND pron=? AND pron IS NOT NULL
    GROUP BY gender, year""", (src, pron))
    results = c.fetchall()
    return results
   

def get_name_count_year(conn, src='bc',
                        dtype='orth',
                        start =1989,
                        end = 2022):
    """
    Retrieve cached counts of names data from the database, 
    organized by year and gender.

    Args:
        conn: SQLite connection object.
        src: Source of the data ('bc', 'hs', 'hs+bc').
        dtype: Type of data to retrieve ('orth', 'pron', 'both').

    Returns:
        A nested defaultdict organized by year and gender containing the number of names.
    Raises:
        ValueError: If an invalid combination of src and dtype is provided.
    """
    if src in ['hs', 'hs+bc'] and dtype != 'orth':
        raise ValueError(f"Invalid combination: {src} with {dtype}. Only 'orth' is allowed for 'hs' and 'hs+bc'.")

    # Use the cache table
    c = conn.cursor()
    c.execute(f"""
    SELECT year, gender, count
    FROM name_year_cache
    WHERE src = ? and dtype = ?
    AND year >= ? and year <= ?
    ORDER BY year
    """, (src, dtype, start, end))
    byyear = dd(lambda: dd(int))
    for year, gender, cnt in c:
        byyear[year][gender] =  cnt  
    return byyear


def get_name_year(conn, table='namae',
                  src='bc',
                  dtype='both',
                  start =1989,
                  end = 2022):
    """
    Retrieve names data from the database, organized by year and gender.

    Args:
        conn: SQLite connection object.
        table: Name of the table to query.
        src: Source of the data ('bc', 'hs', 'hs+bc').
        dtype: Type of data to retrieve ('orth', 'pron', 'both').

    Returns:
        A nested defaultdict organized by year and gender containing the names data.

    Raises:
        ValueError: If an invalid combination of src and dtype is provided.
    """
    if src in ['hs', 'hs+bc'] and dtype != 'orth':
        raise ValueError(f"Invalid combination: {src} with {dtype}. Only 'orth' is allowed for 'hs' and 'hs+bc'.")
    c = conn.cursor()

    # Determine the columns to select based on dtype
    if dtype == 'orth':
        select_columns = "orth, gender, year"
    elif dtype == 'pron':
        select_columns = "pron, gender, year"
    else:
        select_columns = "orth, pron, gender, year"

    # Filter out NULL values for the requested dtype
    if dtype == 'orth':
        null_filter = "AND orth IS NOT NULL"
    elif dtype == 'pron':
        null_filter = "AND pron IS NOT NULL"
    else:
        null_filter = "AND orth IS NOT NULL AND pron IS NOT NULL"

    c.execute(f"""SELECT {select_columns}
    FROM {table}
    WHERE src = ?
    AND year >= ? and year <= ?
    {null_filter}
    ORDER BY year""", (src, start, end))
    byyear =  dd(lambda:  dd(list))
    for row in c:
        if dtype == 'orth':
            orth, gender, year = row
            byyear[year][gender].append((orth,))
        elif dtype == 'pron':
            pron, gender, year = row
            byyear[year][gender].append((pron,))
        else:
            orth, pron, gender, year = row
            byyear[year][gender].append((orth, pron))
    return byyear




def get_stats(conn, table='namae', src='bc'):
    """
    return various statistics
    stats[name][gender] = X
    DISTINCT
    stats['dname'][gender] = X   # distinct names
    stats['pron'][gender] = X    # distinct pronunciation
    stats['orth'][gender] = X    # distinct orthography
    """

    stats = dd(lambda: dd(lambda: dd(int))) 
    
    c = conn.cursor()
    c.execute(f"""SELECT gender, COUNT (gender) 
    FROM (SELECT DISTINCT orth, pron, gender FROM {table} WHERE src = ?) 
    GROUP BY gender""", (src,))
    for (gender, freq) in c:
        stats['dname'][gender] = freq

    c.execute(f"""select gender, count(distinct orth) 
    FROM {table}
    WHERE src = ?
    GROUP BY gender""", (src,))
    for (gender, freq) in c:
        stats['orth'][gender] = freq

    c.execute(f"""select gender, count(distinct pron) 
    FROM {table}
    WHERE src = ?
    GROUP BY gender""", (src,))
    for (gender, freq) in c:
        stats['pron'][gender] = freq

    c.execute(f"""select gender, count(gender) 
    FROM {table}
    WHERE src = ?
    GROUP BY gender""", (src,))
    for (gender, freq) in c:
        stats['name'][gender] = freq

    return stats

def get_feature(conn, feat1, feat2, threshold, table='namae', src='bc', short=False):

    c = conn.cursor()

    ddata = dd(lambda: dd(int))
    data = list()
    tests = list()
    summ = dict()
    examples = dd(list)

    if feat1 == 'kanji':
       c.execute(f"""select kanji, gender, count(*) as cnt 
       from kanji left join ntok on kanji.kid = ntok.kid 
       LEFT JOIN {table} ON ntok.nid = {table}.nid
       WHERE src = ?
       group by kanji, gender""", (src,))

       for ft, gender, count in c:
           ddata[ft][gender] =  int(count)
    
    elif not feat2:
        ## 'char1', 'char2', 'char_1', 'mora1', 'mora_1', 'uni_ch'
        #assert feat1 in ['char1'] 
        c.execute(f"""
        SELECT {feat1}, gender, count(*) as cnt 
        FROM attr LEFT JOIN {table} ON attr.nid={table}.nid 
        WHERE {feat1} IS NOT NULL
        AND src = ?
        GROUP BY {feat1}, gender""", (src,))
        
        for ft, gender, count in c:
            ddata[ft][gender] =  int(count)
            
        if not short:
            c.execute(f"""select {feat1}, orth, pron, count({feat1}) 
            FROM {table} LEFT JOIN attr ON {table}.nid = attr.nid
            WHERE src = ?
            GROUP BY {feat1}, orth, pron 
            ORDER BY {feat1}, count ({feat1}) DESC""", (src,))
        for ft, orth, pron, freq in c:
            examples[ft].append((orth, pron))

    else:  # two features
        c.execute(f"""
        SELECT {feat1}, {feat2}, gender, count(*) as cnt 
        FROM attr LEFT JOIN {table} ON attr.nid={table}.nid
        WHERE {feat1} is not Null AND {feat2} is not Null
        AND src = ?
        GROUP BY {feat1}, {feat2}, gender""", (src,))
        for ft1, ft2, gender, count in c:
            ddata[f"{ft1}, {ft2}"][gender] =  int(count)
            
        if not short:
            c.execute(f"""
            SELECT {feat1}, {feat2}, orth, pron, count({feat1}) 
            FROM {table} LEFT JOIN attr ON {table}.nid = attr.nid
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


def get_name_features(conn, features, src='bc', dtype='orth'):
    """
    Extract name data with specified features for classification.
    
    Parameters:
    -----------
    conn : sqlite3.Connection
        Database connection
    features : list of str
        Feature names to extract. Can include:
        - Any column from attr table: 'olength', 'char1', 'char_1', 'char_2', 
          'mora1', 'mora_1', 'syll_1', 'uni_ch', 'script', etc.
        - 'kanji' : extracts individual kanji as binary features
        - 'char'  : extracts all characters (kanji, hiragana, katakana) as binary features
        - 'year'  : include year information
    table : str
        Name table to query (default 'namae')
    src : str or None
        Source filter (default 'bc'). If None, gets all sources.
    view : str
        Attribute table/view name (default 'attr')
    
    Returns:
    --------
    name_data : list of dict
        Each dict contains: {
            'orth': orthography,
            'pron': pronunciation,
            'gender': gender label,
            'year': year,
            'features': dict of feature_name: feature_value
        }
    feature_vocab : dict
        Vocabulary for each feature type (for encoding)
    """
    
    c = conn.cursor()
    assert src in db_options, f"Source '{src}' not known (try: {', '.join(db_options.keys())})"
    yfrom, yto = db_options[src][3]
    table = db_options[src][0]
    
    # Build query dynamically based on requested features
    attr_cols = [f for f in features if f not in ['kanji', 'char', 'year']]
    
    # Construct SELECT clause
    select_cols = ['n.orth', 'n.pron', 'n.gender', 'n.year']
    if attr_cols:
        select_cols.extend([f'a.{col}' for col in attr_cols])
    
    # Construct query
    query = f"""
        SELECT {', '.join(select_cols)}
        FROM {table} n
        LEFT JOIN attr a ON n.nid = a.nid
    """
    
    query += " WHERE n.src = ? and n.year >= ? and n.year <= ?"
    if dtype == 'orth':
        query += " AND orth IS NOT NULL"
    elif dtype == 'pron':
        query += " AND pron IS NOT NULL"

    c.execute(query, (src, yfrom, yto))



    
    # Collect data
    name_data = []
    feature_vocab = dd(set)
    
    for row in c:
        orth, pron, gender, year = row[:4]
        
        # Skip if no gender label
        if not gender:
            continue
            
        feature_dict = {}
        
        # Extract attr features
        for i, feat in enumerate(attr_cols):
            value = row[4 + i]
            if value is not None:  # Only include non-null features
                feature_dict[feat] = value
                feature_vocab[feat].add(value)
        
        # Extract individual kanji if requested
        if 'kanji' in features and orth:
            kanji_list = [ch for ch in orth if is_kanji(ch)]
            for kanji in kanji_list:
                feature_key = f'has_{kanji}'
                feature_dict[feature_key] = 1  # Binary presence
                feature_vocab['kanji'].add(kanji)
        
        # Extract all characters if requested
        if 'char' in features and orth:
            for ch in orth:
                feature_key = f'has_{ch}'
                feature_dict[feature_key] = 1  # Binary presence
                feature_vocab['char'].add(ch)
        
        # Add year if requested
        if 'year' in features:
            feature_dict['year'] = year
            feature_vocab['year'].add(year)
        
        name_data.append({
            'orth': orth,
            'pron': pron,
            'gender': gender,
            'year': year,
            'features': feature_dict
        })
    
    return name_data, dict(feature_vocab)


def is_kanji(char):
    """Check if character is kanji (CJK Unified Ideographs)."""
    code = ord(char)
    return (0x4E00 <= code <= 0x9FFF or  # CJK Unified Ideographs
            0x3400 <= code <= 0x4DBF or  # CJK Extension A
            0x20000 <= code <= 0x2A6DF)  # CJK Extension B


# Example usage:
"""
# Experiment 1: Just last char and length
features = ['olength', 'char_1']
data, vocab = get_name_features(conn, features, src='bc')

# Experiment 2: First, last, and all characters (kanji + kana)
features = ['olength', 'char1', 'char_1', 'char']
data, vocab = get_name_features(conn, features, src='bc')

# Experiment 3: Compare kanji-only vs all characters
features_kanji = ['olength', 'char_1', 'kanji']
features_all = ['olength', 'char_1', 'char']
data_kanji, vocab_kanji = get_name_features(conn, features_kanji, src='bc')
data_all, vocab_all = get_name_features(conn, features_all, src='bc')

# Experiment 4: Kitchen sink - everything
features = ['olength', 'char1', 'char_1', 'char_2', 'script', 'char', 'year']
data, vocab = get_name_features(conn, features, src='bc')

# Access the data:
for name in data[:3]:
    print(f"{name['orth']} ({name['gender']}): {name['features']}")

# Example output for name "花子":
# 花子 (F): {'olength': 2, 'char1': '花', 'char_1': '子', 
#            'has_花': 1, 'has_子': 1, 'year': 2008}
"""




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

def get_mapping(conn, orth, pron):
    """
    return the mapping between the orthography and the pronunciation
    """
    c = conn.cursor()
    c.execute("""SELECT mapping FROM mapp
    WHERE orth = ? and pron = ?""", (orth, pron))
    return c.fetchone()         

def get_irregular(conn, table='namae', src='bc'):
    """
    Return the irregularity of the mapping of all names in the corpus,
    along with linear regression statistics for each gender.
    
    Returns:
        tuple: (data, regression_stats)
        - data: list of tuples (year, gender, names, number, irregular_names, proportion)
        - regression_stats: dict with keys 'M' and 'F', each containing:
            - slope: regression slope (change in proportion per year)
            - intercept: y-intercept
            - r_value: correlation coefficient
            - p_value: two-tailed p-value for hypothesis test
            - std_err: standard error of the estimate
            - trend: 'increasing', 'decreasing', or 'stable'
            - significant: boolean indicating if trend is significant (p < 0.05)
    """
    
    c = conn.cursor()
    c.execute(f"""SELECT 
    n.year,
    n.gender,
    COUNT(DISTINCT n.orth || '|' || n.pron) AS names,
    COUNT(*) AS number,
    SUM(CASE WHEN m.mapping LIKE '%irregular%' THEN 1 ELSE 0 END) AS irregular_names
    FROM {table} n
    LEFT JOIN mapp m ON n.orth = m.orth AND n.pron = m.pron
    WHERE n.src = ?
    GROUP BY n.year, n.gender
    ORDER BY n.year, n.gender;
    """, (src,))
    results = c.fetchall()
    c.close()
    
    # Process data and calculate proportions
    data = []
    male_data = {'years': [], 'proportions': []}
    female_data = {'years': [], 'proportions': []}
    
    for row in results:
        year, gender, names, number, irregular_names = row
        proportion = irregular_names / number if number > 0 else 0
        data.append((year, gender, names, number, irregular_names, proportion))
        
        # Separate by gender for regression
        if gender == 'M':
            male_data['years'].append(year)
            male_data['proportions'].append(proportion)
        elif gender == 'F':
            female_data['years'].append(year)
            female_data['proportions'].append(proportion)
    
    # Calculate linear regression for each gender
    regression_stats = {}
    
    for gender, gender_data in [('M', male_data), ('F', female_data)]:
        if len(gender_data['years']) >= 2:  # Need at least 2 points for regression
            slope, intercept, r_value, p_value, std_err = linregress(
                gender_data['years'], 
                gender_data['proportions']
            )
            
            # Determine trend
            if p_value < 0.05:
                trend = 'increasing' if slope > 0 else 'decreasing'
            else:
                trend = 'stable'
            
            regression_stats[gender] = {
                'slope': float(slope),
                'intercept': float(intercept),
                'r_value': float(r_value),
                'r_squared': float(r_value ** 2),
                'p_value': float(p_value),
                'std_err': float(std_err),
                'trend': trend,
                'significant': bool(p_value < 0.05),
                'years': list(gender_data['years']),  # Convert to list for JSON serialization
                'proportions': list(gender_data['proportions'])  # Convert to list for JSON serialization
                 }
            
        else:
            regression_stats[gender] = None
       
    # Compare male vs female proportions using independent samples t-test
    gender_comparison = None
    if len(male_data['proportions']) >= 2 and len(female_data['proportions']) >= 2:
        # Use independent samples t-test
        t_stat, t_pvalue = ttest_ind(
            male_data['proportions'], 
            female_data['proportions']
        )
        
        # Calculate means
        male_mean = np.mean(male_data['proportions'])
        female_mean = np.mean(female_data['proportions'])
        
        # Determine which is higher
        if t_pvalue < 0.05:
            if male_mean > female_mean:
                comparison = 'male_higher'
                direction = 'Male names have significantly MORE irregular mappings than female names'
            else:
                comparison = 'female_higher'
                direction = 'Female names have significantly MORE irregular mappings than male names'
        else:
            comparison = 'no_difference'
            direction = 'No significant difference between male and female irregular mappings'
        
        gender_comparison = {
            't_statistic': float(t_stat),
            'p_value': float(t_pvalue),
            'significant': bool(t_pvalue < 0.05),
            'male_mean': float(male_mean),
            'female_mean': float(female_mean),
            'difference': float(male_mean - female_mean),
            'comparison': comparison,
            'direction': direction
        }
  
    return data, regression_stats, gender_comparison


    
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

    

def cache_years(db_path, src):
    """
    Store the number of names per year in the database for a given source.

    Args:
        src (str): The source identifier for the data.
    """
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    if src == 'hs+bc':
        table = db_options[src][0]
        c.execute(f'''
        INSERT INTO name_year_cache (src, dtype, year, gender, count)
        SELECT src, 'orth', year, gender, COUNT(*)  as tfreq
        FROM {table}
        WHERE src = ?
        AND orth IS NOT NULL
        GROUP BY year, gender
        HAVING tfreq > 0
        ORDER BY year, gender
        ''', (src, ))
    else:
        for dtype in  ('orth', 'pron'):
            c.execute(f'''
            INSERT INTO name_year_cache (src, dtype, year, gender, count)
            SELECT src, '{dtype}', year, gender, SUM(freq)  AS tfreq
            FROM nrank
            WHERE src = ?
            AND {dtype} IS NOT NULL
            GROUP BY year, gender
            HAVING tfreq > 0
            ORDER BY year, gender
            ''', (src, ))  
    conn.commit()
    conn.close()
    
def get_kanji_distribution(conn, kanji, gender, src):
    """
    Get kanji position distribution data.
    Returns dict where data[year] = [solo, initial, middle, end, count]
    """
    # Validate: must be exactly one character, no GLOB special chars
    if not kanji or len(kanji) != 1 or kanji in ('*', '?', '[', ']'):
        return {}
    c = conn.cursor()
    data = dd(lambda: [0, 0, 0, 0, 0])

    # Get solo, initial, middle, end for each year
    c.execute(f"""
SELECT 
    year,
    sum(CASE WHEN orth GLOB '{kanji}*' AND length(orth) > 1 THEN freq ELSE 0 END) AS initial,
    sum(CASE WHEN orth GLOB '*{kanji}*' AND orth NOT GLOB '{kanji}*' AND orth NOT GLOB '*{kanji}' AND length(orth) > 2 THEN freq ELSE 0 END) AS middle,
    sum(CASE WHEN orth GLOB '*{kanji}' AND length(orth) > 1 THEN freq ELSE 0 END) AS end,
    sum(CASE WHEN orth = '{kanji}' THEN freq ELSE 0 END) AS solo
FROM nrank
WHERE (orth GLOB '*{kanji}*') 
  AND gender = ? 
  AND src=?
  AND freq IS NOT NULL
GROUP BY year""",
              (gender, src))
    
    for year, initial, middle, end, solo in c:
        data[year] = [solo, initial, middle, end]
    
    # Get total names for each year
    c.execute(f"""
    SELECT year, count FROM name_year_cache
    WHERE gender = ? and SRC = ?""",
              (gender, src))
    
    for year, count in c:
        data[year].append(count)
    
    return dict(data)

def get_overlap(conn, src='bc', dtype='orth', n_top=50):
    """Calculate overlap between male and female names in top-N ranks per year.

    Returns (data_list, regression_count, regression_proportion) where
    data_list: [{year, overlap_count, weighted_proportion, total_babies}, ...]
    regression_count / regression_proportion: linregress dict or None.
    """
    c = conn.cursor()
    name_col = dtype  # 'orth' or 'pron'

    # Find overlapping names: same name_col value in both M and F top-N
    query = f"""
    SELECT
      m.year,
      m.{name_col} AS overlap_name,
      m.freq AS male_freq,
      f.freq AS female_freq
    FROM nrank m
    INNER JOIN nrank f ON f.src = m.src
                      AND f.year = m.year
                      AND f.gender = 'F'
                      AND m.gender = 'M'
                      AND f.{name_col} = m.{name_col}
    WHERE m.rank <= ?
      AND f.rank <= ?
      AND m.src = ?
      AND m.{name_col} IS NOT NULL
      AND f.{name_col} IS NOT NULL
    ORDER BY m.year
    """
    c.execute(query, (n_top, n_top, src))

    # Group by year
    year_overlaps = dd(list)
    for year, name, m_freq, f_freq in c:
        year_overlaps[year].append((name, m_freq, f_freq))

    # Get total babies per year (sum M+F from name_year_cache)
    c.execute("""
    SELECT year, SUM(count)
    FROM name_year_cache
    WHERE src = ? AND dtype = ?
    GROUP BY year
    """, (src, dtype))
    totals = dict(c.fetchall())

    data = []
    years_list = []
    counts = []
    proportions = []

    # Iterate all years that have totals so zero-overlap years are included
    for year in sorted(totals):
        overlaps = year_overlaps.get(year, [])
        overlap_count = len(overlaps)
        overlap_freq = sum(m + f for _, m, f in overlaps)
        total = totals[year]
        proportion = (overlap_freq / total) if total > 0 else 0.0

        # Include the actual names sorted by combined frequency
        names = [{'name': n, 'male_freq': int(m), 'female_freq': int(f)}
                 for n, m, f in sorted(overlaps, key=lambda x: x[1]+x[2], reverse=True)]

        data.append({
            'year': year,
            'overlap_count': overlap_count,
            'overlap_freq': overlap_freq,
            'total_babies': total,
            'weighted_proportion': float(proportion),
            'names': names,
        })
        years_list.append(year)
        counts.append(overlap_count)
        proportions.append(proportion)

    def _regress(xs, ys):
        if len(xs) < 2:
            return None
        slope, intercept, r_value, p_value, std_err = linregress(xs, ys)
        if p_value < 0.05:
            trend = 'increasing' if slope > 0 else 'decreasing'
        else:
            trend = 'stable'
        return {
            'slope': float(slope),
            'intercept': float(intercept),
            'r_value': float(r_value),
            'r_squared': float(r_value ** 2),
            'p_value': float(p_value),
            'std_err': float(std_err),
            'trend': trend,
            'significant': bool(p_value < 0.05),
            'years': list(xs),
        }

    reg_count = _regress(years_list, counts)
    reg_proportion = _regress(years_list, proportions)

    return data, reg_count, reg_proportion


def get_androgyny(conn, src='bc', dtype='orth', tau=0.2, count_type='token'):
    """
    Calculate androgyny proportion over time.
    A name is androgynous if the F/M ratio is between tau and (1-tau).
    
    Args:
        conn: SQLite connection object
        src: Source identifier ('bc', 'hs', etc.)
        dtype: 'orth' or 'pron'
        tau: Threshold parameter (0.0 to 0.5). Name is androgynous if F/M in [tau, 1-tau]
             tau=0.0 means any shared name (both M and F present)
             tau=0.5 means perfectly balanced only (F/M = 1.0)
        count_type: 'token' (weighted by frequency) or 'type' (count distinct names)
    
    Returns:
        tuple: (data, regression_stats)
        - data: list of dicts with keys: year, total, androgynous, proportion
        - regression_stats: dict with slope, intercept, r_squared, p_value, years
    """
    
    c = conn.cursor()
    
    # Build the query based on dtype
    name_col = dtype  # 'orth' or 'pron'
    
    # Calculate the upper bound (1 - tau)
    upper_tau = 1.0 - tau
    
    if count_type == 'type':
        # Count distinct names
        query = f"""
        WITH gender_counts AS (
            SELECT 
                year,
                {name_col},
                SUM(CASE WHEN gender = 'F' THEN freq ELSE 0 END) AS f_count,
                SUM(CASE WHEN gender = 'M' THEN freq ELSE 0 END) AS m_count
            FROM nrank
            WHERE src = ?
            GROUP BY year, {name_col}
        ),
        androgynous_names AS (
            SELECT 
                year,
                {name_col}
            FROM gender_counts
            WHERE f_count > 0 AND m_count > 0
              AND (f_count * 1.0 / m_count) BETWEEN ? AND ?
        )
        SELECT 
            gc.year,
            COUNT(DISTINCT gc.{name_col}) AS total_names,
            COUNT(DISTINCT an.{name_col}) AS androgynous_names
        FROM gender_counts gc
        LEFT JOIN androgynous_names an ON gc.year = an.year AND gc.{name_col} = an.{name_col}
        WHERE gc.f_count + gc.m_count > 0
        GROUP BY gc.year
        ORDER BY gc.year
        """
        c.execute(query, (src, tau, upper_tau))
    else:
        # Token: weighted by frequency
        query = f"""
        WITH gender_counts AS (
            SELECT 
                year,
                {name_col},
                SUM(CASE WHEN gender = 'F' THEN freq ELSE 0 END) AS f_count,
                SUM(CASE WHEN gender = 'M' THEN freq ELSE 0 END) AS m_count,
                SUM(freq) AS total_freq
            FROM nrank
            WHERE src = ?
            GROUP BY year, {name_col}
        ),
        androgynous_names AS (
            SELECT 
                year,
                {name_col},
                total_freq
            FROM gender_counts
            WHERE f_count > 0 AND m_count > 0
              AND (f_count * 1.0 / m_count) BETWEEN ? AND ?
        )
        SELECT 
            gc.year,
            SUM(gc.total_freq) AS total_babies,
            SUM(CASE WHEN an.{name_col} IS NOT NULL THEN an.total_freq ELSE 0 END) AS androgynous_babies
        FROM gender_counts gc
        LEFT JOIN androgynous_names an ON gc.year = an.year AND gc.{name_col} = an.{name_col}
        WHERE gc.f_count + gc.m_count > 0
        GROUP BY gc.year
        ORDER BY gc.year
        """
        c.execute(query, (src, tau, upper_tau))
    
    results = c.fetchall()
    c.close()
    
    # Process data
    data = []
    years = []
    proportions = []
    
    for row in results:
        year, total, androgynous = row
        # Ensure we have integers/floats, not None
        year = int(year)
        total = int(total) if total else 0
        androgynous = int(androgynous) if androgynous else 0
        
        # Calculate proportion with float division
        proportion = float(androgynous) / float(total) if total > 0 else 0.0
        
        data.append({
            'year': year,
            'total': total,
            'androgynous': androgynous,
            'proportion': proportion
        })
        
        years.append(year)
        proportions.append(proportion)
    
    # Calculate linear regression
    regression_stats = None
    if len(years) >= 2:
        slope, intercept, r_value, p_value, std_err = linregress(years, proportions)
        
        # Determine trend
        if p_value < 0.05:
            trend = 'increasing' if slope > 0 else 'decreasing'
        else:
            trend = 'stable'
        
        regression_stats = {
            'slope': float(slope),
            'intercept': float(intercept),
            'r_value': float(r_value),
            'r_squared': float(r_value ** 2),
            'p_value': float(p_value),
            'std_err': float(std_err),
            'trend': trend,
            'significant': bool(p_value < 0.05),
            'years': years
        }

    return data, regression_stats


def get_top_names(conn, src='bc', dtype='orth', gender='F', n_top=10):
    """Get top N names per year with ties at boundary included.

    Uses the existing rank column in nrank. Includes all names whose
    rank <= n_top, so ties at the boundary are naturally included.

    Returns dict with:
      - years: sorted list of years
      - names_by_year: {year: [(name, rank, freq), ...]} sorted by rank
      - number_ones: list of names that were ever rank 1
    """
    name_col = dtype  # 'orth' or 'pron'
    c = conn.cursor()

    query = f"""
    SELECT year, {name_col}, rank, freq
    FROM nrank
    WHERE src = ? AND gender = ? AND {name_col} IS NOT NULL AND rank <= ?
    ORDER BY year, rank
    """
    c.execute(query, (src, gender, n_top))
    rows = c.fetchall()

    years = sorted(set(r[0] for r in rows))
    number_ones = sorted(set(r[1] for r in rows if r[2] == 1))

    names_by_year = {}
    for year in years:
        names_by_year[year] = [
            {'name': r[1], 'rank': r[2], 'freq': r[3]}
            for r in rows if r[0] == year
        ]

    return {
        'years': years,
        'names_by_year': names_by_year,
        'number_ones': number_ones,
    }
