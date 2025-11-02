"""Route declaration."""
from flask import current_app as app
from web.settings import DEFAULT_DB_OPTION
from flask import render_template, request, session, make_response, redirect, url_for

import toml
import pathlib
import sqlite3, os
from collections import defaultdict as dd

from web.db import get_db, get_name, get_name_year, get_name_count_year, \
                get_stats, get_feature, \
                get_redup, db_options, dtypes, \
                get_mapping, get_kanji_distribution, \
                get_irregular
import json
from web.utils import whichScript, mora_hiragana, syllable_hiragana


def get_db_connection(root, db):
    dbpath = os.path.join(root, db)
    conn = sqlite3.connect(dbpath)
    #conn.row_factory = sqlite3.Row
    return conn

current_directory = os.path.abspath(os.path.dirname(__file__))

threshold = 2


### [(feat1, feat2, name, (possible combinations)), ...
features = [
    ('char1', '', '1st Char.', ('bc', 'hs', 'hs+bc', 'meiji')),
    ('char_1', '', 'Last Char.', ('bc', 'hs', 'hs+bc', 'meiji')),
    ('char_2', 'char_1', 'Last 2 Chars', ('bc', 'hs', 'hs+bc', 'meiji')),
    ('mora1', '', '1st Mora', ('bc')),
    ('mora_1', '', 'Last Mora', ('bc')),
    ('mora_2', 'mora_1', 'Last 2. Moras', ('bc')),
    ('char_1', 'mora_1', 'Last Char. +  Mora', ('bc')),
    ('char1', 'mora1', 'First Char. +  Mora', ('bc')),
    ('syll1', '', '1st Syllable', ('bc')),
    ('syll_1', '', 'Last Syllable', ('bc')),
    ('syll_2', 'syll_1', 'Last 2. Syllables', ('bc')),
    ('char_1', 'syll_1', 'Last Char. +  Syllable', ('bc')),
    ('char1', 'syll1', 'First Char. +  Syllable', ('bc')),
    ('uni_ch', '', '1 Char. Name', ('bc', 'hs', 'hs+bc', 'meiji')),
    ('kanji', '', 'Kanji', ('bc', 'hs', 'hs+bc', 'meiji')),
]

overall = [
    ('script', '', 'Script', ('bc', 'hs', 'hs+bc', 'meiji')),
    ('olength', '', 'Length Char.', ('bc', 'hs', 'hs+bc', 'meiji')),
    ('mlength', '', 'Length Mora', ('bc')),
    ('slength', '', 'Length Syllables', ('bc')),
]

phenomena = [
    ('redup', '', 'Reduplication'),
    ('jinmei', '', 'Kanji for names'),
    ('irregular', '', 'Irregular Readings'),
    
]

def get_db_settings():
    """Get database settings from session."""
    selected_db_option = session.get('db_option', DEFAULT_DB_OPTION)
    return {
        'db_src': selected_db_option,
        'db_table': db_options[selected_db_option][0],
        'db_name': db_options[selected_db_option][1],
    }

@app.context_processor
def inject_common_variables():
    """Inject common variables into all templates."""
    return {
        **get_db_settings(),
        'features': features,
        'overall': overall,
        'phenomena': phenomena,
        'page': request.endpoint
    }

@app.route("/", methods=["GET", "POST"])
def home():
    """show the home page"""
    return render_template(
        "index.html",
        title='Namae',
    )

@app.route("/phenomena/diversity.html")
def diversity():
    """
    Show diversity measures
    """
    diversity_data = {}
    for src in db_options:
        for dtype in dtypes:
            try:
                file_path = os.path.join(current_directory, f"static/data/diversity_data_{src}_{dtype}.json")
                with open(file_path) as f:
                    diversity_data[f"{src}_{dtype}"] = json.load(f)
            except FileNotFoundError:
                continue

    return render_template(
        "phenomena/diversity.html",
        title='Diversity Measures',
        diversity_data=diversity_data
    )

@app.route("/docs", methods=["GET", "POST"])
def docs():
    """show documentation"""
    return render_template(
        f"docs/overview.html",
        title='Overview',
    )

@app.route("/settings", methods=["GET", "POST"])
def settings():
    """Settings page to select color palette"""
    if request.method == "POST":
        color_palette = request.form.get('color_palette', 'purple_orange')
        if color_palette == 'red_blue':
            session['male_color'] = 'blue'
            session['female_color'] = 'red'
        else:
            session['male_color'] = 'orange'
            session['female_color'] = 'purple'
        db_option = request.form.get('db_option', DEFAULT_DB_OPTION)
        session['db_option'] = db_option
        return redirect(url_for('home'))

    return render_template(
        "settings.html",
        db_options=db_options,
        selected_db_option = session.get('db_option', DEFAULT_DB_OPTION),
        male_color=session.get('male_color', 'orange'),
        female_color=session.get('female_color', 'purple')
    )

@app.route("/namae")
def namae():
    """
    Show a name
    """
    orth = request.args.get('orth', type=str, default='')
    pron = request.args.get('pron', type=str, default='')
    conn = get_db(current_directory, "namae.db")
    db_settings = get_db_settings()
    mfname, kindex, hindex = get_name(conn, table=db_settings['db_table'], src=db_settings['db_src'])
    if pron:
        mora = mora_hiragana(pron)
        syll=syllable_hiragana(mora)

    if pron and orth:
        mapp = get_mapping(conn, orth, pron)
        return render_template(
            f"namae-both.html",
            name=orth,
            hira=pron,
            mora=mora,
            syll=syll,
            mapp=mapp,
            script=whichScript(orth),
            mfname=mfname,
            kindex=kindex,
            hindex=hindex,
            male_color=session.get('male_color', 'orange'),
            female_color=session.get('female_color', 'purple')
)
    elif pron:
        return render_template(
            f"namae-pron.html",
            hira=pron,
            hindex=hindex
        )
    elif orth:
        return render_template(
            f"namae-orth.html",
            name=orth,
            kindex=kindex
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
    db_settings = get_db_settings()
    mfname, kindex, hindex = get_name(conn, table=db_settings['db_table'], src=db_settings['db_src'])

    data = list()

    for k, h in mfname:
        data.append((k, h,
                     len(mfname[(k,h)]['M']) + len(mfname[(k,h)]['F']),
                     len(mfname[(k,h)]['F']) / 
                     (len(mfname[(k,h)]['M']) + len(mfname[(k,h)]['F']))))
                    
    return render_template(
        f"names.html",
        data=data,
    )

@app.route("/stats.html")
def stats():
    """
    show some statistics
    """
    conn = get_db(current_directory, "namae.db")
    db_settings = get_db_settings()
    stats_data = get_stats(conn, table=db_settings['db_table'], 
                           src=db_settings['db_src'])
                     
    feat_stats = list()
    for (feat1, feat2, name, possible) in features:
        if db_settings['db_src'] in possible:
            data, tests, summ = get_feature(conn, feat1, feat2, threshold,
                                            short=True,
                                            table=db_settings['db_table'], 
                                            src=db_settings['db_src']) 
            feat_stats.append((name, len(data), summ))
                            
    return render_template(
        f"stats.html",
        stats=stats_data,
        fstats=feat_stats,
    )

@app.route("/features.html")
def feature():
    """
    show the distribution of the given feauture(s)
    """
    beta=0.1
    feat1 = request.args.get('f1', type=str, default='')
    feat2 = request.args.get('f2', type=str, default='')
    name = request.args.get('nm', type=str, default='')
    desc = request.args.get('dc', type=str, default='')

    db_settings = get_db_settings()
    
    conn = get_db(current_directory, "namae.db")
    data, tests, summ = get_feature(conn, feat1, feat2, threshold,
                                    table=db_settings['db_table'], 
                                    src=db_settings['db_src'])
    
    return render_template(
        f"feature.html",
        data=data,
        feats=(feat1,feat2),
        beta=beta,
        tests=tests,
        summ=summ,
        threshold=threshold,
        title=name,
    )


@app.route("/years.html")
def years():
    """
    show the distribution of the given feature(s) per year
    """
    conn = get_db(current_directory, "namae.db")
    db_settings = get_db_settings()
    
    dtype='orth'
    names = get_name_count_year(conn,
                                src=db_settings['db_src'],
                                dtype=dtype) 
    births = get_name_count_year(conn,
                                 src='births',
                                 dtype=dtype)

    def format_percentage(num1, num2):
        try:
            return f"{num1/num2:.1%}"
        except (KeyError, TypeError, ZeroDivisionError):
            return "---"

    
    return render_template(
        f"years.html",
        names=names,
        births=births,
        format_percentage = format_percentage,
        title=f'Data per year ({db_settings["db_name"]})',
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
        stats=stats
    )

@app.route("/phenomena/proportion.html")
def proportion():
    """
    show examples of reduplication
    """
    data ={}
    return render_template(
        f"phenomena/proportion.html",
        data=data,
        title='Gender Proportion',
    )


    
@app.route("/book")
def book():
    """
    Show all diagrams and tables for the book.
    """
    try:
        file_path = os.path.join(current_directory, f"static/data/book_tables.json")
        with open(file_path) as f:
            table_data = json.load(f)
    except FileNotFoundError:
        table_data=dict()    

    
    return render_template(
        "book.html",
        title='Book Diagrams and Tables',
        table_data=table_data,
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
    )

###
### Information about kanji 
###
@app.route("/kanji")
def kanji():
    """
    Show information about a single character
    """
    kanji_char = request.args.get('kanji', type=str, default='')
    conn = get_db(current_directory, "namae.db")
    db_settings = get_db_settings()
    
    data_male = get_kanji_distribution(conn, kanji_char, 'M',
                                       db_settings['db_src'])
    data_female = get_kanji_distribution(conn, kanji_char, 'F',
                                         db_settings['db_src'])
   
    if not kanji_char:
        return render_template(
            "kanji-search.html",
            title='Kanji Position Search'
        )
    
    return render_template(
        "kanji.html",
        kanji=kanji_char,
        title=f'Information about 「{kanji_char}」',
        data_male=data_male,
        data_female=data_female,
    )

###
### Kanji readings
###
@app.route("/irregular.html")
def irregular():
    """Show irregular names statistics"""
    conn = get_db(current_directory, "namae.db")
    db_settings = get_db_settings()
    results, regression_stats, gender_comparison = get_irregular(conn, table='namae', src='bc')
    data = []
    for row in results:
        # Unpack the tuple: (year, gender, names, number, irregular_names)
        year, gender, names, number, irregular_names, proportion = row
        data.append({
            'year': year,
            'gender': gender,
            'names': names,
            'number': number,
            'irregular_names': irregular_names,
            'proportion': proportion
        })
     
    
    return render_template(
        "phenomena/irregular.html",
        data=data,
        regression_stats=regression_stats,
        gender_comparison=gender_comparison,
        title='Irregular Names Statistics',
        male_color=session.get('male_color', 'orange'),
        female_color=session.get('female_color', 'purple')
    )
