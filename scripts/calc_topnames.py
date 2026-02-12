###
###  Pre-compute top names data for all source/dtype/gender/n_top combos.
###  Saves results to web/static/data/topnames_data.json
###

import sys, os, json, sqlite3

from db import db_options, resolve_src, get_top_names

DB_PATH = os.path.join('..', 'web', 'db', 'namae.db')
OUT_PATH = os.path.join('..', 'web', 'static', 'data', 'topnames_data.json')


def main():
    conn = sqlite3.connect(DB_PATH)
    all_data = {}
    seen = set()

    for src in db_options:
        qsrc = resolve_src(src)
        opt_dtypes = db_options[src][2]
        dtype_list = list(opt_dtypes) if isinstance(opt_dtypes, tuple) else [opt_dtypes]

        for dtype in dtype_list:
            if dtype == 'both':
                continue
            src_dtype_key = f"{qsrc}_{dtype}"
            if src_dtype_key in seen:
                continue
            seen.add(src_dtype_key)

            ds_key = f"{qsrc}_{dtype}"
            ds = {}

            for gender, gkey in [('M', 'male'), ('F', 'female')]:
                for n_top, suffix in [(10, ''), (50, '_50')]:
                    try:
                        result = get_top_names(
                            conn, src=qsrc, dtype=dtype,
                            gender=gender, n_top=n_top)
                    except Exception as e:
                        print(f"  SKIP {ds_key} {gkey}{suffix}: {e}",
                              file=sys.stderr)
                        result = {'years': [], 'names_by_year': {}, 'number_ones': []}

                    # Convert int keys to strings for JSON
                    result['names_by_year'] = {
                        str(k): v for k, v in result['names_by_year'].items()
                    }
                    ds[f'{gkey}{suffix}'] = result

            all_data[ds_key] = ds
            print(f"  {ds_key}: done")

    conn.close()

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, ensure_ascii=False, indent=1)
    print(f"Wrote {OUT_PATH} ({len(all_data)} datasets)")


if __name__ == '__main__':
    main()
