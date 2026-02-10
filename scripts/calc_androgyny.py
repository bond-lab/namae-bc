###
###  Pre-compute androgyny data for all source/dtype/tau/count_type combos.
###  Saves results to web/static/data/androgyny_data.json
###

import sys, os, json, sqlite3

# Use the symlinked db module (avoids importing Flask via web/__init__.py)
from db import db_options, resolve_src, get_androgyny

DB_PATH = os.path.join('..', 'web', 'db', 'namae.db')
OUT_PATH = os.path.join('..', 'web', 'static', 'data', 'androgyny_data.json')

tau_values = [0.0, 0.2]
count_types = ['token', 'type']


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

            for count_type in count_types:
                for tau in tau_values:
                    key = f"{qsrc}_{dtype}_{count_type}_tau{int(tau*10)}"
                    try:
                        data, regression = get_androgyny(
                            conn, src=qsrc, dtype=dtype,
                            tau=tau, count_type=count_type)
                    except Exception as e:
                        print(f"  SKIP {key}: {e}", file=sys.stderr)
                        continue

                    if not data:
                        continue

                    all_data[key] = {
                        'data': data,
                        'regression': regression,
                        'src': qsrc,
                        'dtype': dtype,
                        'count_type': count_type,
                        'tau': tau,
                    }
                    print(f"  {key}: {len(data)} years")

    conn.close()

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, ensure_ascii=False, indent=1)
    print(f"Wrote {OUT_PATH} ({len(all_data)} datasets)")


if __name__ == '__main__':
    main()
