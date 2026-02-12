###
###  Pre-compute irregular readings data for all database options.
###  Saves results to web/static/data/irregular_data.json
###
###  The irregular page calls get_irregular() which JOINs namae × mapp.
###  For Heisei this takes ~19s.  Pre-computing reduces it to a JSON read.
###

import sys, os, json, sqlite3

from db import db_options, resolve_src, get_irregular

DB_PATH = os.path.join('..', 'web', 'db', 'namae.db')
OUT_PATH = os.path.join('..', 'web', 'static', 'data', 'irregular_data.json')


def main():
    conn = sqlite3.connect(DB_PATH)
    all_data = {}

    for src_key in db_options:
        table = db_options[src_key][0]
        qsrc = resolve_src(src_key)

        key = src_key
        print(f"  {key} (table={table}, src={qsrc})...", end=' ', flush=True)

        try:
            results, regression_stats, gender_comparison = get_irregular(
                conn, table=table, src=qsrc)
        except Exception as e:
            print(f"SKIP: {e}", file=sys.stderr)
            continue

        # Convert results (list of tuples) to list of dicts for JSON
        data = []
        for row in results:
            year, gender, names, number, irregular_names, proportion = row
            data.append({
                'year': year,
                'gender': gender,
                'names': names,
                'number': number,
                'irregular_names': irregular_names,
                'proportion': proportion,
            })

        all_data[key] = {
            'data': data,
            'regression_stats': regression_stats,
            'gender_comparison': gender_comparison,
        }
        print(f"{len(data)} rows")

    conn.close()

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, ensure_ascii=False, indent=1)
    print(f"Wrote {OUT_PATH} ({len(all_data)} datasets)")


if __name__ == '__main__':
    main()
