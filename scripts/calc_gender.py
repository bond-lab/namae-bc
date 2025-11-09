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
import pandas as pd
from sklearn.feature_extraction import DictVectorizer
from sklearn.preprocessing import LabelEncoder
from sklearn.naive_bayes import BernoulliNB

import json

from db import get_name_features



def analyze_gender_trends(clf, X, y, name_data, gender_labels):
    """
    Helper function to create analysis dataframe from classifier results.
    
    Parameters:
    -----------
    clf : fitted classifier (sklearn or custom)
    X : feature matrix
    y : true labels
    name_data : list of dicts with 'orth', 'pron', 'year'
    gender_labels : array of gender label strings
    
    Returns:
    --------
    results : pandas DataFrame with probabilities and trends
    """
    probs = clf.predict_proba(X)
    
    results = pd.DataFrame({
        'orth': [m['orth'] for m in name_data],
        'pron': [m['pron'] for m in name_data],
        'year': [m['year'] for m in name_data],
        'actual_gender': [m['gender'] for m in name_data],
    })
    
    # Add probability columns
    for i, label in enumerate(gender_labels):
        results[f'P_{label}'] = probs[:, i]
    
    # Add femaleness/maleness if binary classification
    if len(gender_labels) == 2:
        results['femaleness'] = probs[:, 0] if gender_labels[0] == 'F' else probs[:, 1]
        results['maleness'] = probs[:, 1] if gender_labels[0] == 'F' else probs[:, 0]
    
    return results


def show_row_info(X, y, vec, label_encoder, name_data, idx, clf=None, max_feats=25):
    """
    Display info for row `idx`:
      - orth (name), year
      - true label (and predicted label + probabilities if clf is given)
      - active (non-zero) features with their values (truncated to max_feats)
    """
    # --- metadata ---
    meta = name_data[idx]
    orth = meta.get('orth')
    year = meta.get('year')

    # --- labels ---
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
        proba_str = " | " + " ".join([f"p({cls})={p:.3f}" for cls, p in zip(label_encoder.classes_, proba)])

    # --- print nicely ---
    print(f"\n=== Row {idx} ===")
    print(f"Name: {orth}   Year: {year}")
    line = f"True: {true_label}"
    if pred_label is not None:
        line += f" | Pred: {pred_label}{proba_str}"
    print(line)

    print(f"Active features (showing up to {max_feats}):")
    for name, val in active_pairs[:max_feats]:
        print(f"  {name} = {val}")
    if len(active_pairs) > max_feats:
        print(f"  ... (+{len(active_pairs)-max_feats} more)")
 

def run_experiment(conn, src, dtype, features, verbose=True):
    """
    run an experiment, and return the results as a table
    """
    print(f"⛃ Getting the features for {src} ({dtype}):", features)

    name_data, feature_vocab = get_name_features(conn, features)

    print("🔢 Vectorizing")

    feature_dicts = [d['features'] for d in name_data]
    label_encoder=LabelEncoder()
    y = label_encoder.fit_transform([d['gender'] for d in name_data])
    vec = DictVectorizer(sparse=True, dtype=np.uint8)
    X = vec.fit_transform(feature_dicts)

    if verbose:
        print(f"Data shape: {X.shape}")
        print(f"Features: {features}")
        print(f"Gender labels: {label_encoder.classes_}")
        print("Feature names (first 10):", vec.get_feature_names_out()[:10])

        # Example: Look at a specific name
        idx = 42
        show_row_info(X, y, vec, label_encoder, name_data, idx, clf=None)

    print("🎓 Training Classifier")

    # 3. Train classifier
    clf = BernoulliNB(alpha=1.0)
    clf.fit(X, y)

    if verbose:
        # Example: Look at a specific name
        idx = 42
        show_row_info(X, y, vec, label_encoder, name_data, idx, clf=None)

    print("📊 Analyzing results")

    results = analyze_gender_trends(
        clf, X, y, name_data, label_encoder.classes_
    )

    table = {'caption': f"Change in Genderedness over time ({src} {dtype}, using {features})"}

    table['headers'] = ['Year', 'Gender', 'Genderedness']
    table['rows'] =[]
    table['trends'] = {'F':dict(), 'M':dict()}
    for gender in label_encoder.classes_:
        col = f'P_{gender}'  # dynamically pick the right probability column
        subset = results[results['actual_gender'] == gender]
        yearly_means = subset.groupby('year')[col].mean()
        
        for year, value in yearly_means.items():
            table['rows'].append([year, gender, value])

        x = yearly_means.index.to_numpy(dtype=float)
        y = yearly_means.to_numpy(dtype=float)
    
        res = linregress(x, y)
        table['trends'][gender]['slope']     = res.slope
        table['trends'][gender]['intercept'] = res.intercept
        table['trends'][gender]['r2']        = res.rvalue **2 
        table['trends'][gender]['pvalue']    = res.pvalue

            
    return table
            

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    base = os.path.dirname(__file__)
    parser.add_argument("db_path", nargs="?", default=os.path.join(base, "../web/db/namae.db"))
    parser.add_argument("data_path", nargs="?", default=os.path.join(base, "../web/static/data/genderedness.json"))
    args = parser.parse_args()

    db_path = args.db_path
    data_path = args.data_path

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()


    features = ['char_1', 'syll_1', 'char', 'olength', 'plength']
    #features = ['char_1', 'char', 'olength', 'script']

    tables = {}

    for (src, dtype) in [ ('meiji', 'orth'), ('hs', 'orth'), ('meiji_p', 'pron')
                         ]:
        table = run_experiment(conn, src, dtype, features, verbose=True)

        key = '_'.join([src, dtype] + features)

        tables[key] = table


    with open(data_path, 'w') as out:
        json.dump(tables, out, indent=2)

print("\n\n\n\n\nDONE\n\n\n\n\n")
            




# # Now analyze trends
# print("=== Mean femaleness of female names by year ===")
# print(results[results['actual_gender'] == 'F'].groupby('year')['femaleness'].mean())

# print("\n=== Mean maleness of male names by year ===")
# print(results[results['actual_gender'] == 'M'].groupby('year')['maleness'].mean())

# print(f"\nAccuracy: {clf.score(X, y):.4f}")

# print(results.keys())

# # 6. Compute GNI-like scores
# results['femaleness'] = results['P_F']
# results['maleness'] = results['P_M']
# results['female_GNI'] = np.log(results['P_F'] / results['P_M'])
# results['male_GNI'] = np.log(results['P_M'] / results['P_F'])

# # Show some examples
# print("\n=== Sample predictions ===")
# print(results.head(10))

# # 7. Analyze by actual gender and year
# print("\n=== Mean scores by actual gender ===")
# print(results.groupby('actual_gender')[['femaleness', 'maleness']].mean())

# print("\n=== Trends over time (for females) ===")
# female_names = results[results['actual_gender'] == 'F']
# print(female_names.groupby('year')['femaleness'].mean())

# print("\n=== Trends over time (for males) ===")
# male_names = results[results['actual_gender'] == 'M']
# print(male_names.groupby('year')['maleness'].mean())

# # # 8. Find gender-neutral names
# # neutral_threshold = 0.1  # Within 10% of 0.5
# # results['gender_neutral'] = (
# #     (results['P_F'] > 0.4) & 
# #     (results['P_F'] < 0.6)
# # )
# # print(f"\n=== Gender-neutral names (within 0.4-0.6): {results['gender_neutral'].sum()} ===")
# # print(results[results['gender_neutral']].head(10))

# # # 9. Find cross-gender names
# # print("\n=== Girls with masculine names (P_F < 0.5) ===")
# # masculine_girls = results[(results['actual_gender'] == 'F') & (results['P_F'] < 0.5)]
# # print(f"Count: {len(masculine_girls)}")
# # print(masculine_girls.head())

# # print("\n=== Boys with feminine names (P_M < 0.5) ===")
# # feminine_boys = results[(results['actual_gender'] == 'M') & (results['P_M'] < 0.5)]
# # print(f"Count: {len(feminine_boys)}")
# # print(feminine_boys.head())

# import matplotlib.pyplot as plt
# # For female names over time
# female_names_by_year = results[results['actual_gender'] == 'F'].groupby('year')
# female_femaleness = female_names_by_year['femaleness'].mean()
# female_maleness = female_names_by_year['maleness'].mean()

# # For male names over time  
# male_names_by_year = results[results['actual_gender'] == 'M'].groupby('year')
# male_femaleness = male_names_by_year['femaleness'].mean()
# male_maleness = male_names_by_year['maleness'].mean()

# plt.figure(figsize=(10, 6))
# plt.plot(female_femaleness.index, female_femaleness.values, 
#          label='Girls names - femaleness', color='pink', linewidth=2)
# plt.plot(male_maleness.index, male_maleness.values, 
#          label='Boys names - maleness', color='blue', linewidth=2)
# plt.xlabel('Year')
# plt.ylabel('Gender-typicality score')
# plt.title('Are names becoming less gender-typical over time?')
# plt.legend()
# plt.grid(alpha=0.3)
# plt.show()


# plt.figure(figsize=(10, 6))
# plt.plot(female_femaleness.index, female_femaleness.values, 
#          label='Girls - femaleness', color='pink', linewidth=2, linestyle='-')
# plt.plot(female_maleness.index, female_maleness.values, 
#          label='Girls - maleness', color='pink', linewidth=2, linestyle='--')
# plt.plot(male_maleness.index, male_maleness.values, 
#          label='Boys - maleness', color='blue', linewidth=2, linestyle='-')
# plt.plot(male_femaleness.index, male_femaleness.values, 
#          label='Boys - femaleness', color='blue', linewidth=2, linestyle='--')
# plt.xlabel('Year')
# plt.ylabel('Score')
# plt.title('Cross-gender name adoption patterns')
# plt.legend()
# plt.grid(alpha=0.3)
# plt.show()




# # Convergence = both moving toward 0.5
# convergence = (1 - female_femaleness) + (1 - male_maleness)

# # OR: Track the gap
# gap = abs(female_femaleness - 0.5) + abs(male_maleness - 0.5)

# plt.figure(figsize=(10, 6))
# plt.plot(gap.index, gap.values, linewidth=2)
# plt.xlabel('Year')
# plt.ylabel('Total distance from gender-neutral (0.5)')
# plt.title('Gender convergence over time (lower = more convergence)')
# plt.grid(alpha=0.3)
# plt.show()

# from scipy.stats import linregress
# import numpy as np
# import matplotlib.pyplot as plt

# def describe_trend(series, label):
#     x = np.array(series.index)
#     y = np.array(series.values)
    
#     res = linregress(x, y)
#     slope, intercept, rvalue, pvalue = res.slope, res.intercept, res.rvalue, res.pvalue
#     trend = "increasing 📈" if slope > 0 else "decreasing 📉" if slope < 0 else "flat ⏸"
#     sig = "significant ✅" if pvalue < 0.05 else "not significant ❌"
    
#     print(f"{label}: slope = {slope:.4f}, R² = {rvalue**2:.3f}, p = {pvalue:.3g} → {trend}, {sig}")
#     return slope, intercept, rvalue, pvalue

# # --- Run for both series ---
# female_slope, female_intercept, _, _ = describe_trend(female_femaleness, "Female names")
# male_slope, male_intercept, _, _     = describe_trend(male_maleness, "Male names")

# # --- Plot ---
# plt.figure(figsize=(10, 6))
# plt.plot(female_femaleness.index, female_femaleness.values, 
#          label='Girls names - femaleness', color='pink', linewidth=2)
# plt.plot(male_maleness.index, male_maleness.values, 
#          label='Boys names - maleness', color='blue', linewidth=2)

# # Regression lines
# for series, slope, intercept, color in [
#     (female_femaleness, female_slope, female_intercept, 'deeppink'),
#     (male_maleness, male_slope, male_intercept, 'navy')
# ]:
#     x = np.array(series.index)
#     y_pred = slope * x + intercept
#     plt.plot(x, y_pred, '--', color=color, alpha=0.7)

# plt.xlabel('Year')
# plt.ylabel('Gender-typicality score')
# plt.title('Are names becoming less gender-typical over time?')
# plt.legend()
# plt.grid(alpha=0.3)
# plt.show()

