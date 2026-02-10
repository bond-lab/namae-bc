###
###  Pre-compute overlap data for all source/dtype/n_top combos.
###  Saves results to web/static/data/overlap_data.json
###

import sys, os, json, sqlite3

from db import db_options, resolve_src, get_overlap

DB_PATH = os.path.join('..', 'web', 'db', 'namae.db')
OUT_PATH = os.path.join('..', 'web', 'static', 'data', 'overlap_data.json')

# Per-source n_top values (must match routes.py)
source_n_tops = {
    'bc':    [50, 100],
    'hs':    [50, 100, 500],
    'meiji': [50, 100],
}


def main():
    conn = sqlite3.connect(DB_PATH)
    all_data = {}
    seen = set()

    for src in db_options:
        qsrc = resolve_src(src)
        opt_dtypes = db_options[src][2]
        dtype_list = list(opt_dtypes) if isinstance(opt_dtypes, tuple) else [opt_dtypes]
        n_tops = source_n_tops.get(qsrc, [50])

        for dtype in dtype_list:
            if dtype == 'both':
                continue

            for n_top in n_tops:
                key = f"{qsrc}_{dtype}_{n_top}"
                if key in seen:
                    continue
                seen.add(key)

                try:
                    data, reg_count, reg_proportion = get_overlap(
                        conn, src=qsrc, dtype=dtype, n_top=n_top)
                except Exception as e:
                    print(f"  SKIP {key}: {e}", file=sys.stderr)
                    continue

                if not data:
                    continue

                all_data[key] = {
                    'data': data,
                    'reg_count': reg_count,
                    'reg_proportion': reg_proportion,
                    'src': qsrc,
                    'dtype': dtype,
                    'n_top': n_top,
                }
                print(f"  {key}: {len(data)} years")

    conn.close()

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, ensure_ascii=False, indent=1)
    print(f"Wrote {OUT_PATH} ({len(all_data)} datasets)")


if __name__ == '__main__':
    main()
