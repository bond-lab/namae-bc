"""Route declaration."""
from flask import current_app as app
from web.settings import DEFAULT_DB_OPTION
from flask import render_template, request, session, make_response, redirect, url_for

import toml
import pathlib
import sqlite3, os
from collections import defaultdict as dd

from web.db import get_db, get_name, get_name_year, get_name_count_year, \
                get_orth, get_pron, \
                get_stats, get_feature, \
                get_redup, db_options, dtypes, \
                get_mapping, get_kanji_distribution, \
                get_irregular, get_androgyny, resolve_src
import json
import markdown
from markupsafe import Markup
from web.utils import whichScript, mora_hiragana, syllable_hiragana

def render_md(filepath, link_map=None):
    """Read a markdown file and return rendered HTML (as Markup).

    *link_map* is an optional dict mapping markdown href targets to
    replacement URLs, so that cross-references between repo files
    resolve to the correct web-app routes.
    """
    with open(filepath, encoding='utf-8') as f:
        text = f.read()
    if link_map:
        for old, new in link_map.items():
            text = text.replace(f']({old})', f']({new})')
    html = markdown.markdown(text, extensions=['tables'])
    return Markup(html)


def get_db_connection(root, db):
    dbpath = os.path.join(root, db)
    conn = sqlite3.connect(dbpath)
    #conn.row_factory = sqlite3.Row
    return conn

current_directory = os.path.abspath(os.path.dirname(__file__))
# Root of the repository (parent of web/)
repo_root = os.path.dirname(current_directory)

threshold = 2


### [(feat1, feat2, name, (possible combinations)), ...
features = [
    ('char1', '', '1st Char.', ('bc', 'hs', 'hs+bc', 'meiji')),
    ('char_1', '', 'Last Char.', ('bc', 'hs', 'hs+bc', 'meiji')),
    ('char_2', 'char_1', 'Last 2 Chars', ('bc', 'hs', 'hs+bc', 'meiji')),
    ('mora1', '', '1st Mora', ('bc', 'meiji_p')),
    ('mora_1', '', 'Last Mora', ('bc', 'meiji_p')),
    ('mora_2', 'mora_1', 'Last 2. Moras', ('bc', 'meiji_p')),
    ('char_1', 'mora_1', 'Last Char. +  Mora', ('bc')),
    ('char1', 'mora1', 'First Char. +  Mora', ('bc')),
    ('syll1', '', '1st Syllable', ('bc', 'meiji_p')),
    ('syll_1', '', 'Last Syllable', ('bc', 'meiji_p')),
    ('syll_2', 'syll_1', 'Last 2. Syllables', ('bc', 'meiji_p')),
    ('char_1', 'syll_1', 'Last Char. +  Syllable', ('bc')),
    ('char1', 'syll1', 'First Char. +  Syllable', ('bc')),
    ('uni_ch', '', '1 Char. Name', ('bc', 'hs', 'hs+bc', 'meiji')),
    ('kanji', '', 'Kanji', ('bc', 'hs', 'hs+bc', 'meiji')),
]

overall = [
    ('script', '', 'Script', ('bc', 'hs', 'hs+bc', 'meiji')),
    ('olength', '', 'Length Char.', ('bc', 'hs', 'hs+bc', 'meiji')),
    ('mlength', '', 'Length Mora', ('bc', 'meiji_p')),
    ('slength', '', 'Length Syllables', ('bc', 'meiji_p')),
]

phenomena = [
    ('jinmei', '', 'Kanji for names'),
    ('redup', '', 'Reduplication'),
    ('irregular', '', 'Irregular Readings'),
    ('genderedness', '', 'Genderedness of names'),
    ('diversity', '', 'Diversity Measures'),
    ('overlap', '', 'Overlapping Names'),
    ('androgyny', '', 'Androgynous Names'),
]

def get_db_settings():
    """Get database settings from session."""
    selected_db_option = session.get('db_option', DEFAULT_DB_OPTION)
    opt_dtypes = db_options[selected_db_option][2]
    # Determine primary dtype: string means single dtype, tuple means pick default
    if isinstance(opt_dtypes, str):
        primary_dtype = opt_dtypes
    else:
        primary_dtype = 'orth'
    return {
        'db_src': selected_db_option,
        'db_query_src': resolve_src(selected_db_option),
        'db_table': db_options[selected_db_option][0],
        'db_name': db_options[selected_db_option][1],
        'db_range': db_options[selected_db_option][3],
        'db_dtype': primary_dtype,
    }

@app.context_processor
def inject_common_variables():
    """Inject common variables into all templates."""
    db_settings = get_db_settings()
    return {
        **db_settings,
        'features': features,
        'overall': overall,
        'phenomena': phenomena,
        'page': request.endpoint,
        'show_book': session.get('show_book', False),
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

@app.route("/docs")
def docs():
    """Redirect to docs/data.html"""
    return redirect(url_for('docs_data'))

@app.route("/docs/data.html")
def docs_data():
    """Data sources and cleaning documentation — rendered from data/README.md"""
    content = render_md(
        os.path.join(repo_root, 'data', 'README.md'),
        link_map={
            '../ATTRIBUTIONS.md': url_for('docs_licenses'),
            'download/': url_for('docs_download'),
        })
    return render_template("docs/markdown.html",
                           title='Data: Sources and Cleaning',
                           content=content)

@app.route("/docs/download.html")
def docs_download():
    """Download page — rendered from data/download/README.md"""
    content = render_md(os.path.join(repo_root, 'data', 'download', 'README.md'))
    # Build list of available TSV files for download buttons
    download_dir = os.path.join(repo_root, 'data', 'download')
    tsv_files = sorted(f for f in os.listdir(download_dir) if f.endswith('.tsv'))
    return render_template("docs/download.html",
                           title='Download Data',
                           content=content,
                           tsv_files=tsv_files)

@app.route("/docs/morae.html")
def docs_morae():
    """Morae and syllables documentation"""
    return render_template("docs/morae.html", title='Morae & Syllables')

@app.route("/docs/features.html")
def docs_features():
    """Counting features documentation"""
    return render_template("docs/features.html", title='Counting Features')

@app.route("/docs/licenses.html")
def docs_licenses():
    """Licenses and attributions — rendered from ATTRIBUTIONS.md"""
    content = render_md(
        os.path.join(repo_root, 'ATTRIBUTIONS.md'),
        link_map={
            'data/README.md': url_for('docs_data'),
        })
    return render_template("docs/markdown.html",
                           title='Licenses & Attributions',
                           content=content)

@app.route("/download/<filename>")
def download_file(filename):
    """Serve TSV files from data/download/"""
    from flask import send_from_directory
    download_dir = os.path.join(os.path.dirname(current_directory), 'data', 'download')
    return send_from_directory(download_dir, filename, as_attachment=True)

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
        session['show_book'] = 'show_book' in request.form
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
    qsrc = db_settings['db_query_src']
    mfname, kindex, hindex = get_name(conn, table=db_settings['db_table'],
                                       src=qsrc,
                                       dtype=db_settings['db_dtype'])
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
        data = get_pron(conn, pron, src=qsrc)
        return render_template(
            f"namae-pron.html",
            hira=pron,
            mora=mora,
            syll=syll,
            hindex=hindex,
            data=data,
            male_color=session.get('male_color', 'orange'),
            female_color=session.get('female_color', 'purple')
        )
    elif orth:
        data = get_orth(conn, orth, src=qsrc)
        return render_template(
            f"namae-orth.html",
            name=orth,
            kindex=kindex,
            data=data,
            script=whichScript(orth),
            male_color=session.get('male_color', 'orange'),
            female_color=session.get('female_color', 'purple')
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
    mfname, kindex, hindex = get_name(conn, table=db_settings['db_table'],
                                       src=db_settings['db_query_src'],
                                       dtype=db_settings['db_dtype'])

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
    qsrc = db_settings['db_query_src']
    stats_data = get_stats(conn, table=db_settings['db_table'],
                           src=qsrc)

    feat_stats = list()
    for (feat1, feat2, name, possible) in features:
        if db_settings['db_src'] in possible:
            data, tests, summ = get_feature(conn, feat1, feat2, threshold,
                                            short=True,
                                            table=db_settings['db_table'],
                                            src=qsrc) 
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
                                    src=db_settings['db_query_src'])
    
    # Determine which feature group this belongs to
    is_overall = any(f[0] == feat1 and f[1] == feat2 for f in overall)
    feature_group = overall if is_overall else features

    return render_template(
        f"feature.html",
        data=data,
        feats=(feat1,feat2),
        beta=beta,
        tests=tests,
        summ=summ,
        threshold=threshold,
        title=name,
        feature_group=feature_group,
    )


@app.route("/years.html")
def years():
    """
    show the distribution of the given feature(s) per year
    """
    conn = get_db(current_directory, "namae.db")
    db_settings = get_db_settings()

    dtype = db_settings['db_dtype']
    names = get_name_count_year(conn,
                                src=db_settings['db_query_src'],
                                dtype=dtype)
    births = get_name_count_year(conn,
                                 src='births',
                                 dtype='orth')

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
                                       db_settings['db_query_src'])
    data_female = get_kanji_distribution(conn, kanji_char, 'F',
                                         db_settings['db_query_src'])
   
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


@app.route("/genderedness.html")
def genderedness():
    """
    Render *all* datasets found in genderedness JSON on a single page.
    Optional ?path=... to point at a different JSON file.
    """
    default_path = os.path.join(current_directory, "static", "data", "genderedness.json")
    data_path = request.args.get("path", default_path)

    if not os.path.exists(data_path):
        abort(404, f"Data file not found: {data_path}")

    with open(data_path, "r", encoding="utf-8") as f:
        blob = json.load(f)

    if not isinstance(blob, dict) or not blob:
        abort(400, "Malformed or empty genderedness JSON.")

    def parse_dataset(key, ds):
        # rows like [year, "M"/"F", value]
        rows = ds.get("rows", [])
        data = []
        for row in rows:
            if not isinstance(row, list) or len(row) < 3:
                continue
            try:
                year, gender, value = int(row[0]), str(row[1]), float(row[2])
            except Exception:
                continue
            if gender not in ("M", "F"):
                continue
            data.append({"year": year, "gender": gender, "value": value})

        # trends per gender (if present)
        trends = ds.get("trends", {})
        regression_stats = {}
        for g in ("M", "F"):
            if g in trends:
                t = trends[g]
                years = sorted({d["year"] for d in data if d["gender"] == g})
                regression_stats[g] = {
                    "slope": float(t.get("slope", 0.0)),
                    "intercept": float(t.get("intercept", 0.0)),
                    "r_squared": float(t.get("r2", t.get("r_squared", 0.0))),
                    "p_value": float(t.get("pvalue", t.get("p_value", 1.0))),
                    "years": years
                }
        return data, regression_stats

    def summarize(reg):
        # Human-readable trend: ↑/↓/→ and significance
        def one(g):
            rs = reg.get(g)
            if not rs or not rs.get("years"):
                return f"{'Male' if g=='M' else 'Female'}: no data."
            slope = rs["slope"]
            p = rs["p_value"]
            r2 = rs["r_squared"]
            if abs(slope) < 1e-12:
                arrow, trend = "→", "flat"
            else:
                arrow, trend = ("↑", "increasing") if slope > 0 else ("↓", "decreasing")
            sig = "significant" if p < 0.05 else "not significant"
            # Show slope per year and R² concisely
            return (f"{'Male' if g=='M' else 'Female'}: {arrow} {trend} "
                    f"(slope={slope:.4g}/yr, p={p:.3g}, R²={r2:.2f}), {sig}.")
        return {"M": one("M"), "F": one("F")}

    datasets = []
    for key, ds in blob.items():
        data, regression_stats = parse_dataset(key, ds)
        caption = ds.get("caption", key)
        summary = summarize(regression_stats)
        datasets.append({
            "key": key,
            "caption": caption,
            "data": data,
            "regression_stats": regression_stats,
            "summary": summary
        })

    return render_template(
        "phenomena/genderedness.html",
        title="Genderedness Over Time",
        datasets=datasets,
        male_color=session.get('male_color', 'orange'),
        female_color=session.get('female_color', 'purple')
    )

@app.route("/overlap.html")
def overlap():
    """
    """
    datasets = []
    return render_template(
        "phenomena/overlap.html",
        title="Overlapping Names Over Time",
        datasets=datasets
    )
   
@app.route("/phenomena/androgyny.html")
def androgyny():
    """
    Show androgyny statistics over time.
    Androgynous names are those where F/M ratio is between tau and (1-tau).
    Shows multiple datasets for different tau values and type/token analysis.
    """
    conn = get_db(current_directory, "namae.db")
    db_settings = get_db_settings()
    
    # Define tau values to test
    tau_values = [0.0, 0.2]
    
    # Define count types
    count_types = [
        ('token', 'Babies (Token)', 'babies'),
        ('type', 'Names (Type)', 'names')
    ]
    
    datasets = []
    
    # For each dtype (orth/pron)
    qsrc = db_settings['db_query_src']
    if db_settings['db_dtype'] == 'pron':
        dtypes_to_process = ['pron']
    elif db_settings['db_src'] in ['bc', 'meiji']:
        dtypes_to_process = ['orth', 'pron']
    else:
        dtypes_to_process = ['orth']

    for dtype in dtypes_to_process:
        dtype_label = 'Orthography' if dtype == 'orth' else 'Pronunciation'

        # For each count type
        for count_type, count_label, unit in count_types:
            # For each tau value
            for tau in tau_values:
                data, regression = get_androgyny(
                    conn,
                    src=qsrc,
                    dtype=dtype,
                    tau=tau,
                    count_type=count_type
                )
                
                if not data:
                    continue
                
                # Create caption
                if tau == 0.0:
                    tau_desc = "Any Shared Usage"
                elif tau == 0.5:
                    tau_desc = "Perfect Balance Only"
                else:
                    tau_desc = f"τ={tau:.1f} (F/M ∈ [{tau:.1f}, {1-tau:.1f}])"
                
                caption = f"{dtype_label} - {count_label} - {tau_desc}"
                
                # Create summary
                if regression:
                    rs = regression
                    slope = rs['slope']
                    p = rs['p_value']
                    r2 = rs['r_squared']
                    
                    if abs(slope) < 1e-12:
                        arrow, trend = "→", "flat"
                    else:
                        arrow, trend = ("↑", "increasing") if slope > 0 else ("↓", "decreasing")
                    
                    sig = "significant" if p < 0.05 else "not significant"
                    summary = (f"{arrow} {trend} "
                             f"(slope={slope:.4g}/yr, p={p:.3g}, R²={r2:.2f}), {sig}.")
                else:
                    summary = "Insufficient data for trend analysis."
                
                datasets.append({
                    'key': f'androgyny_{dtype}_{count_type}_tau{int(tau*10)}',
                    'caption': caption,
                    'data': data,
                    'regression_stats': regression,
                    'summary': summary,
                    'dtype': dtype,
                    'tau': tau,
                    'count_type': count_type,
                    'unit': unit
                })
    
    return render_template(
        "phenomena/androgyny.html",
        title="Androgynous Names Over Time",
        datasets=datasets,
        male_color=session.get('male_color', 'orange'),
        female_color=session.get('female_color', 'purple')
    )
