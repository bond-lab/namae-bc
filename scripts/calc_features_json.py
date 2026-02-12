###
###  Pre-compute feature/overall page data for all valid combos.
###  Saves results to web/static/data/features_data.json
###
###  Each feature page calls get_feature(short=False) which runs expensive
###  JOINs + fisher_exact on every category.  For Heisei char1, this takes
###  ~143s.  Pre-computing reduces it to a JSON read.
###

import sys, os, json, sqlite3
import numpy as np

from db import db_options, resolve_src, get_feature


class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            return float(obj)
        if isinstance(obj, (np.bool_,)):
            return bool(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)
from settings import features, overall

DB_PATH = os.path.join('..', 'web', 'db', 'namae.db')
OUT_PATH = os.path.join('..', 'web', 'static', 'data', 'features_data.json')

threshold = 2  # same as routes.py



def main():
    conn = sqlite3.connect(DB_PATH)

    # Load existing data to allow incremental updates
    all_data = {}
    if os.path.exists(OUT_PATH):
        with open(OUT_PATH, 'r', encoding='utf-8') as f:
            all_data = json.load(f)

    for group_name, group in [('features', features), ('overall', overall)]:
        for feat1, feat2, name, possible in group:
            for src_key in possible:
                key = f"{src_key}_{feat1}_{feat2}" if feat2 else f"{src_key}_{feat1}"
                if key in all_data:
                    print(f"  {key}: already computed, skipping")
                    continue

                table = db_options[src_key][0]
                qsrc = resolve_src(src_key)

                print(f"  {key} ({name})...", end=' ', flush=True)

                try:
                    data, tests, summ = get_feature(
                        conn, feat1, feat2, threshold,
                        short=False, table=table, src=qsrc)
                except Exception as e:
                    print(f"SKIP: {e}", file=sys.stderr, flush=True)
                    continue

                # Convert tests: each is (key, M, F, ratio, stat, pval, sig, examples_tuple)
                # examples_tuple contains (orth, pron) pairs — convert to lists
                tests_out = []
                for t in tests:
                    tests_out.append(list(t[:7]) + [list(list(x) for x in t[7])])

                all_data[key] = {
                    'data': [list(d) for d in data],
                    'tests': tests_out,
                    'summ': summ,
                    'name': name,
                    'group': group_name,
                }
                print(f"{len(data)} categories, {len(tests)} tests", flush=True)

                # Write after each combo to save progress
                os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
                with open(OUT_PATH, 'w', encoding='utf-8') as f:
                    json.dump(all_data, f, ensure_ascii=False, indent=1, cls=NumpyEncoder)

    conn.close()
    print(f"Done: {OUT_PATH} ({len(all_data)} datasets)")


if __name__ == '__main__':
    main()
