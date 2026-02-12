###
###  Pre-compute names page data for all database options.
###  Saves results to web/static/data/names_data.json
###
###  Uses the nrank table (pre-aggregated) instead of namae for speed.
###  Heisei: ~8s via nrank vs ~87s via namae.
###

import sys, os, json, sqlite3

from db import db_options, resolve_src, get_names_summary

DB_PATH = os.path.join('..', 'web', 'db', 'namae.db')
OUT_PATH = os.path.join('..', 'web', 'static', 'data', 'names_data.json')


def main():
    conn = sqlite3.connect(DB_PATH)
    all_data = {}

    for src_key in db_options:
        qsrc = resolve_src(src_key)
        opt_dtypes = db_options[src_key][2]

        # Determine primary dtype (same logic as get_db_settings)
        if isinstance(opt_dtypes, str):
            primary_dtype = opt_dtypes
        else:
            primary_dtype = 'orth'

        key = src_key
        print(f"  {key} (dtype={primary_dtype})...", end=' ', flush=True)

        try:
            data = get_names_summary(conn, src=qsrc, dtype=primary_dtype)
        except Exception as e:
            print(f"SKIP: {e}", file=sys.stderr)
            continue

        all_data[key] = [list(row) for row in data]
        print(f"{len(data)} names")

    conn.close()

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, ensure_ascii=False, indent=1)
    print(f"Wrote {OUT_PATH} ({len(all_data)} datasets)")


if __name__ == '__main__':
    main()
