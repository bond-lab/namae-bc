###
###  Pre-compute names page data for all database options.
###  Saves per-source files to web/static/data/names_<src>.json(.gz)
###
###  Uses the nrank table (pre-aggregated) instead of namae for speed.
###  Heisei: ~8s via nrank vs ~87s via namae.
###

import sys, os, json, gzip, sqlite3

from db import db_options, resolve_src, get_names_summary

DB_PATH = os.path.join('..', 'web', 'db', 'namae.db')
OUT_DIR = os.path.join('..', 'web', 'static', 'data')
OLD_PATH = os.path.join(OUT_DIR, 'names_data.json')


def main():
    conn = sqlite3.connect(DB_PATH)

    os.makedirs(OUT_DIR, exist_ok=True)

    # Remove old monolithic file if it exists
    if os.path.exists(OLD_PATH):
        os.remove(OLD_PATH)
        print(f"Removed old {OLD_PATH}")

    for src_key in db_options:
        qsrc = resolve_src(src_key)
        opt_dtypes = db_options[src_key][2]

        # Determine primary dtype: string means single dtype, tuple means 'both'
        if isinstance(opt_dtypes, str):
            primary_dtype = opt_dtypes
        else:
            primary_dtype = 'both'

        print(f"  {src_key} (dtype={primary_dtype})...", end=' ', flush=True)

        try:
            data = get_names_summary(conn, src=qsrc, dtype=primary_dtype)
        except Exception as e:
            print(f"SKIP: {e}", file=sys.stderr)
            continue

        # DataTables AJAX-compatible format
        payload = {"data": [list(row) for row in data]}
        print(f"{len(data)} names")

        # Write uncompressed JSON
        json_path = os.path.join(OUT_DIR, f'names_{src_key}.json')
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(payload, f, ensure_ascii=False, separators=(',', ':'))
        json_size = os.path.getsize(json_path)

        # Write gzipped copy
        gz_path = json_path + '.gz'
        with open(json_path, 'rb') as f_in:
            with gzip.open(gz_path, 'wb', compresslevel=9) as f_out:
                f_out.write(f_in.read())
        gz_size = os.path.getsize(gz_path)

        print(f"    {json_path}: {json_size:,} bytes -> {gz_path}: {gz_size:,} bytes "
              f"({100*(1-gz_size/json_size):.1f}% reduction)")

    conn.close()
    print("Done.")


if __name__ == '__main__':
    main()
