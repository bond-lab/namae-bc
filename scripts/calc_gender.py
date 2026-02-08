###
###  Calculate how predictable gender is for each gender
###

import sys, os, argparse
import sqlite3
from collections import defaultdict as dd

from scipy.sparse import lil_matrix, csr_matrix
import scipy.sparse as sp
from scipy.stats import linregress
import numpy as np
# import pandas as pd   # <- no longer needed
from sklearn.feature_extraction import DictVectorizer
from sklearn.preprocessing import LabelEncoder
from sklearn.naive_bayes import BernoulliNB

import json

from db import get_name_features


def show_row_info(X, y, vec, label_encoder, years, genders, idx, clf=None, max_feats=25):
    """
    Display info for row `idx`:
      - year
      - true label (and predicted label + probabilities if clf is given)
      - active (non-zero) features with their values (truncated to max_feats)
    """
    # --- metadata ---
    year = years[idx]
    true_label = label_encoder.inverse_transform([y[idx]])[0]

    # --- active features ---
    feature_names = np.array(vec.get_feature_names_out())
    row = X.getrow(idx)
    active_pairs = [(feature_names[j], row.data[k]) for k, j in enumerate(row.indices)]

    # --- prediction (optional) ---
    pred_label = None
    proba_str = ""
    if clf is not None:
        pred = clf.predict(X[idx])
        pred_label = label_encoder.inverse_transform(pred)[0]
        proba = clf.predict_proba(X[idx])[0]
        proba_str = " | " + " ".join(
            [f"p({cls})={p:.3f}" for cls, p in zip(label_encoder.classes_, proba)]
        )

    # --- print nicely ---
    print(f"\n=== Row {idx} ===")
    print(f"Year: {year}")
    line = f"True: {true_label}"
    if pred_label is not None:
        line += f" | Pred: {pred_label}{proba_str}"
    print(line)

    print(f"Active features (showing up to {max_feats}):")
    for name, val in active_pairs[:max_feats]:
        print(f"  {name} = {val}")
    if len(active_pairs) > max_feats:
        print(f"  ... (+{len(active_pairs)-max_feats} more)")

def run_experiment(conn, src, dtype, features, verbose=True, chunk_size=50000):
    """
    Run an experiment, and return the results as a table.

    This version avoids pandas and large intermediate DataFrames:
      - compresses name_data -> years (np.array), genders (np.array)
      - deletes feature_dicts once X is built
      - aggregates probabilities in dicts by (gender, year)
    """
    print(f"⛃ Getting the features for {src} ({dtype}):", features)

    # name_data is typically: [{'orth':..., 'pron':..., 'year':..., 'gender':..., 'features': {...}}, ...]
    name_data, feature_vocab = get_name_features(conn, features, src=src, dtype=dtype)

    print("🔢 Vectorizing")

    # Extract only what we really need from name_data
    feature_dicts = [d['features'] for d in name_data]
    years = np.array([d['year'] for d in name_data], dtype=float)
    genders = np.array([d['gender'] for d in name_data])

    # We don't need orth/pron/etc. any more
    del name_data

    label_encoder = LabelEncoder()
    y = label_encoder.fit_transform(genders)

    # Sparse binary features are enough
    vec = DictVectorizer(sparse=True, dtype=np.bool_)
    X = vec.fit_transform(feature_dicts)

    # Drop feature_dicts as soon as X is built
    del feature_dicts

    if verbose:
        print(f"Data shape: {X.shape}")
        print(f"Features: {features}")
        print(f"Gender labels: {label_encoder.classes_}")
        print("Feature names (first 10):", vec.get_feature_names_out()[:10])
        # Example: Look at a specific row (if available)
        if X.shape[0] > 42:
            idx = 42
        else:
            idx = 0
        show_row_info(X, y, vec, label_encoder, years, genders, idx, clf=None)

    print("🎓 Training Classifier")

    clf = BernoulliNB(alpha=1.0)
    clf.fit(X, y)

    if verbose:
        # Show same row with prediction
        if X.shape[0] > 42:
            idx = 42
        else:
            idx = 0
        show_row_info(X, y, vec, label_encoder, years, genders, idx, clf=clf)

    print("📊 Analyzing results (streaming, no DataFrame)")

    gender_labels = label_encoder.classes_
    label_to_idx = {lab: i for i, lab in enumerate(gender_labels)}

    # Aggregators: for each gender, for each year
    from collections import defaultdict
    sum_p_other = {g: defaultdict(float) for g in gender_labels}
    count = {g: defaultdict(int) for g in gender_labels}

    n_rows = X.shape[0]

    for start in range(0, n_rows, chunk_size):
        end = min(n_rows, start + chunk_size)
        X_chunk = X[start:end]
        probs_chunk = clf.predict_proba(X_chunk)

        # Iterate over rows in this chunk
        for offset, row_idx in enumerate(range(start, end)):
            year = years[row_idx]
            g = genders[row_idx]
            g_idx = label_to_idx[g]

            p_correct = probs_chunk[offset, g_idx]
            p_other = 1.0 - p_correct

            sum_p_other[g][year] += p_other
            count[g][year] += 1

    # We can now drop X, y, etc. if we like
    del X, y, vec, clf
    import gc
    gc.collect()

    # Build the table dict
    table = {
        'caption': f"Change in Genderedness over time ({src} {dtype}, using {features})",
        'headers': ['Year', 'Gender', 'Genderedness'],
        'rows': [],
        'trends': {g: {} for g in gender_labels},
    }

    for g in gender_labels:
        years_sorted = sorted(sum_p_other[g].keys())
        xs = []
        ys = []

        for year in years_sorted:
            mean = sum_p_other[g][year] / count[g][year]
            table['rows'].append([year, g, mean])
            xs.append(float(year))
            ys.append(mean)

        if len(xs) >= 2:
            res = linregress(xs, ys)
            table['trends'][g]['slope'] = res.slope
            table['trends'][g]['intercept'] = res.intercept
            table['trends'][g]['r2'] = res.rvalue ** 2
            table['trends'][g]['pvalue'] = res.pvalue
        elif len(xs) == 1:
            table['trends'][g]['slope'] = 0.0
            table['trends'][g]['intercept'] = ys[0]
            table['trends'][g]['r2'] = 0.0
            table['trends'][g]['pvalue'] = 1.0
        else:
            table['trends'][g]['slope'] = 0.0
            table['trends'][g]['intercept'] = 0.0
            table['trends'][g]['r2'] = 0.0
            table['trends'][g]['pvalue'] = 1.0

    # Also free these
    del years, genders, sum_p_other, count
    gc.collect()

    return table


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=(
            "Generate or update the genderedness dataset used for visualization.\n"
            "This script reads from the SQLite name database and writes a JSON summary.\n"
            "By default, it uses the local development paths under ../web/."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    base = os.path.dirname(__file__)
    parser.add_argument(
        "db_path",
        nargs="?",
        default=os.path.join(base, "../web/db/namae.db"),
        metavar="DB_PATH",
        help="Path to the SQLite database containing name statistics."
    )

    parser.add_argument(
        "data_path",
        nargs="?",
        default=os.path.join(base, "../web/static/data/genderedness.json"),
        metavar="JSON_PATH",
        help="Path to the JSON output file for genderedness data."
    )

    parser.add_argument(
        "--no-verbose",
        action="store_true",
        help="Disable verbose diagnostics."
    )

    parser.add_argument(
        "--chunk-size",
        type=int,
        default=50000,
        help="Chunk size for predict_proba calls."
    )

    args = parser.parse_args()

    db_path = args.db_path
    data_path = args.data_path

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    features = {
        'orth': ['char_1', 'char', 'script', 'uni_ch'],
        'pron': ['syll_1', 'syll1'],
    }

    tables = {}

    for (src, dtype) in [
#        ('meiji', 'orth'),
        ('hs', 'orth'),
#        ('meiji', 'pron'),
    ]:
        feats = features[dtype]
        table = run_experiment(
            conn, src, dtype, feats,
            verbose=not args.no_verbose,
            chunk_size=args.chunk_size,
        )

        key = '_'.join([src, dtype] + feats)
        tables[key] = table

    with open(data_path, 'w') as out:
        json.dump(tables, out, indent=2)

    print("\n\nDONE\n\n")
