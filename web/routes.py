"""Route declaration."""
from flask import current_app as app
from flask import render_template, request, session, make_response, redirect, url_for

import toml
import pathlib
import sqlite3, os
from collections import defaultdict as dd


from web.db import get_db, get_name, get_name_year, get_stats, get_feature, \
                get_redup
from web.visualize import create_gender_plot
from web.utils import whichScript, mora_hiragana, syllable_hiragana

def get_db_connection(root, db):
    dbpath = os.path.join(root, db)
    conn = sqlite3.connect(dbpath)
    #conn.row_factory = sqlite3.Row
    return conn

current_directory = os.path.abspath(os.path.dirname(__file__))



#session['grm']=None
#'db/ERG_(2020).db'
#grm='db/Portuguese_(2022-08-10).db'

threshold = 2

### [(feat1, feat2, name), ...
features = [
    ('char1', '', '1st Char.'),
    ('char_1', '', 'Last Char.'),
    ('char_2', 'char_1', 'Last 2 Chars'),
    ('mora1', '', '1st Mora'),
    ('mora_1', '', 'Last Mora'),
    ('mora_2', 'mora_1', 'Last 2. Moras'),
    ('char_1', 'mora_1', 'Last Char. +  Mora'),
    ('char1', 'mora1', 'First Char. +  Mora'),
    ('syll1', '', '1st Syllable'),
    ('syll_1', '', 'Last Syllable'),
    ('syll_2', 'syll_1', 'Last 2. Syllables'),
    ('char_1', 'syll_1', 'Last Char. +  Syllable'),
    ('char1', 'syll1', 'First Char. +  Syllable'),
    ('uni_ch', '', '1 Char. Name'),
    ('kanji', '', 'Kanji'),
]
overall = [
    ('script', '', 'Script'),
    ('olength', '', 'Length Char.'),
    ('mlength', '', 'Length Mora'),
    ('slength', '', 'Length Syllables'),
]


phenomena = [
    ('redup', '', 'Reduplication'),
    ('jinmei', '', 'Kanji for names')
    ]


@app.route("/settings", methods=["GET", "POST"])
def settings():
    """Settings page to select color palette"""

    if request.method == "POST":
        session['male_color'] = request.form.get('male_color', 'orange')
        session['female_color'] = request.form.get('female_color', 'purple')
        return redirect(url_for('home'))

    return render_template(
        "settings.html",
        male_color=session.get('male_color', 'orange'),
        female_color=session.get('female_color', 'purple')
    )
def home():
    """show the home page"""

    page='index'

    return render_template(
        f"index.html",
        page=page,
        title='Namae',
        features=features,
        overall=overall,
        phenomena=phenomena
    )

@app.route("/docs", methods=["GET", "POST"])
def docs():
    """show documentation"""

    page='overview'

    return render_template(
        f"docs/overview.html",
        page=page,
        title='Overview',
        features=features,
        overall=overall,
        phenomena=phenomena
    )

@app.route("/namae")
def namae():
    """
    Show a name
    """
    orth  = request.args.get('orth', type=str ,default='')
    pron  = request.args.get('pron',type=str , default='')
    conn = get_db(current_directory, "namae.db")
    mfname, kindex, hindex = get_name(conn)
    mora=mora_hiragana(pron)
    
    if pron and orth:
        return render_template(
            f"orth+pron.html",
            name=orth,
            hira=pron,
            mora=mora,
            syll=syllable_hiragana(mora),
            script=whichScript(orth),
            mfname=mfname,
            kindex=kindex,
            hindex=hindex,
            features=features,
            overall=overall,
            phenomena=phenomena
        )
    elif pron:
        return render_template(
            f"namae-pron.html",
            hira=pron
        )
    elif orth:
        return render_template(
            f"namae-orth.html",
            name=orth,
        )
    else:
        return render_template(
            f"namae-nasi.html",
            )
    
@app.route("/names.html")
def names():
    """
    show the names
    name
    hira
    freq
    mratio
    """
    
    conn = get_db(current_directory, "namae.db")
    mfname, kindex, hindex = get_name(conn)

    data = list()

    for k,h in mfname:
        data.append((k, h,
                     len(mfname[(k,h)]['M']) + len(mfname[(k,h)]['F']),
                     len(mfname[(k,h)]['F'])/ \
                     (len(mfname[(k,h)]['M']) + len(mfname[(k,h)]['F']))))
                    
        
    return render_template(
        f"names.html",
        data=data,
        features=features,
        overall=overall,
        phenomena=phenomena
    )

@app.route("/stats.html")
def stats():
    """
    show some statistics
    """
    
    conn = get_db(current_directory, "namae.db")
    stats = get_stats(conn)
                     
    feat_stats = list()
    for (feat1, feat2, name) in features:
         data, tests, summ = get_feature(conn, feat1, feat2, threshold,
                                         short=True) 
         feat_stats.append((name, len(data), summ))
                            # summ['allm'], summ['allf'],
                            # summ['chi2'],
                            # summ['pval'],
                            # summ['phi'] ))
                              
    
    return render_template(
        f"stats.html",
        stats=stats,
        fstats = feat_stats,
        features=features,
        overall=overall,
        phenomena=phenomena
    )

@app.route("/features.html")
def feature():
    """
    show the distribution of the given feauture(s)
    """
    feat1  = request.args.get('f1', type=str ,default='')
    feat2  = request.args.get('f2',type=str , default='')
    name   = request.args.get('nm',type=str , default='')
    desc   = request.args.get('dc',type=str , default='')

    conn = get_db(current_directory, "namae.db")
    data, tests, summ = get_feature(conn, feat1, feat2, threshold)
    
    return render_template(
        f"feature.html",
        data=data,
        tests=tests,
        summ=summ,
        threshold=threshold,
        title=name,
        features=features,
        overall=overall,
        phenomena=phenomena
    )


@app.route('/years.png')
def years_png():
    conn = get_db(current_directory, "namae.db")
    names = get_name_year(conn)
    years = []
    male_counts = []
    female_counts = []

    for year in names:
        years.append(year)
        male_counts.append(len(names[year]['M']))
        female_counts.append(len(names[year]['F']))

    print(male_counts)
        
    # Create the plot using the function
    buf = create_gender_plot(years, male_counts, female_counts)

    return make_response(buf.getvalue(), 200, {'Content-Type': 'image/png'})



@app.route("/years.html")
def years():
    """
    show the distribution of the given feature(s) per year
    """
    
    conn = get_db(current_directory, "namae.db")
    names = get_name_year(conn)
    
    return render_template(
        f"years.html",
        names=names,
        title='Data per year',
        features=features,
        overall=overall,
        phenomena=phenomena
    )


@app.route("/phenomena/redup.html")
def redup():
    """
    show examples of reduplication
    """
    
    conn = get_db(current_directory, "namae.db")
    data = get_redup(conn)

    stats = dd(dict)
    for t in data:
        stats[t]['T'] = sum(data[t][x]['freq'] for x in data[t])
        stats[t]['M'] = sum(data[t][x]['freq'] for x in data[t] if x[1] == 'M')
        stats[t]['F'] = sum(data[t][x]['freq'] for x in data[t] if x[1] == 'F')
    
    
    return render_template(
        f"phenomena/redup.html",
        data=data,
        title='Reduplication in Names',
        features=features,
        overall=overall,
        phenomena=phenomena,
        stats=stats
    )
@app.route("/phenomena/jinmeiyou.html")
def jinmei():
    """
    show change of jinmeiyou kanji
    """
    
   ### graph made by jinmei.py
    
    return render_template(
        f"phenomena/jinmeiyou.html",
        title='Kanji Allowed for Names',
        features=features,
        overall=overall,
        phenomena=phenomena,

    )
