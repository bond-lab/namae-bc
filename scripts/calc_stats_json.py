###
###  Pre-compute stats page data for all database options.
###  Saves results to web/static/data/stats_data.json
###
###  The stats page calls get_stats() + get_feature(short=True) for every
###  feature visible in the selected database.  For Heisei this means
###  15 feature queries over 14.5M rows — ~6 minutes.  Pre-computing
###  reduces it to a JSON read.
###

import sys, os, json, sqlite3
import numpy as np

from db import db_options, resolve_src, get_stats, get_feature


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
from settings import features

DB_PATH = os.path.join('..', 'web', 'db', 'namae.db')
OUT_PATH = os.path.join('..', 'web', 'static', 'data', 'stats_data.json')

threshold = 2  # same as routes.py



def main():
    conn = sqlite3.connect(DB_PATH)

    # Load existing data to allow incremental updates
    all_data = {}
    if os.path.exists(OUT_PATH):
        with open(OUT_PATH, 'r', encoding='utf-8') as f:
            all_data = json.load(f)

    for src_key in db_options:
        if src_key in all_data:
            print(f"  {src_key}: already computed, skipping")
            continue

        table = db_options[src_key][0]
        qsrc = resolve_src(src_key)

        print(f"  {src_key} ({qsrc}, table={table}):", flush=True)

        # get_stats result
        try:
            stats = get_stats(conn, table=table, src=qsrc)
        except Exception as e:
            print(f"    SKIP stats: {e}", file=sys.stderr)
            continue

        # Convert nested defaultdict to plain dict for JSON
        stats_plain = {}
        for k1 in stats:
            stats_plain[k1] = {}
            for k2 in stats[k1]:
                stats_plain[k1][k2] = dict(stats[k1][k2]) if hasattr(stats[k1][k2], 'items') else stats[k1][k2]

        # Feature summaries (short=True → no examples or per-category tests)
        feat_stats = []
        for feat1, feat2, name, possible in features:
            if src_key in possible:
                try:
                    data, tests, summ = get_feature(
                        conn, feat1, feat2, threshold,
                        short=True, table=table, src=qsrc)
                    feat_stats.append({
                        'name': name,
                        'count': len(data),
                        'summ': summ,
                    })
                    print(f"    {name}: {len(data)} categories", flush=True)
                except Exception as e:
                    print(f"    SKIP {name}: {e}", file=sys.stderr, flush=True)
                    continue

        all_data[src_key] = {
            'stats': stats_plain,
            'feat_stats': feat_stats,
        }

        # Write after each source to save progress
        os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
        with open(OUT_PATH, 'w', encoding='utf-8') as f:
            json.dump(all_data, f, ensure_ascii=False, indent=1, cls=NumpyEncoder)
        print(f"  Saved ({len(all_data)} datasets so far)", flush=True)

    conn.close()
    print(f"Done: {OUT_PATH} ({len(all_data)} datasets)")


if __name__ == '__main__':
    main()
