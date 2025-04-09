import os
import math
import random
import sqlite3
import numpy as np
from collections import defaultdict as dd, Counter
import matplotlib.pyplot as plt
import pandas as pd # for table
import json
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from web.db import db_options, get_name_year
from web.visualize import plot_multi_panel_trends

bpn = [1, 5, 10, 50, 100]

# Define paths for database and output directories
current_directory = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(current_directory, "../web/db/namae.db")
json_dir = os.path.join(current_directory, "../web/static/data")
plot_dir = os.path.join(current_directory, "../web/static/plot")
os.makedirs(json_dir, exist_ok=True)
os.makedirs(plot_dir, exist_ok=True)

def calculate_ttr(names):
    """Calculate Type Token Ratio (TTR) for a given list of names."""
    unique_names = set(names)
    return len(unique_names) / len(names) if names else 0

def calculate_newness(current_names, previous_names):
    """Calculate newness: names seen this year that were not seen in the previous year."""
    return len(set(current_names) - set(previous_names))

def analyze_diversity_with_adaptive_sampling(data, sample_size, max_runs=100, min_runs=10):
    results  = dd(lambda: dd(float))
    ci_lower = dd(lambda: dd(float))
    ci_upper = dd(lambda: dd(float))
    actual_runs = {}
    
    for year, names in sorted(data.items()):
        year_metrics = {
            'Shannon': [],
            'Evenness': [],
            'Gini-Simpson': [],
            'TTR': [],
            'Newness': [],
            'Char TTR': [],
            'Char Newness': [],
        }
        previous_names = set()
        for i in bpn:
            year_metrics[f'Berger-Parker ({i})'] = []
            
        converged = False
        run_count = 0
        
        while not converged and run_count < max_runs:
            if len(names) > sample_size:
                sample = random.sample(names, sample_size)
            else:
                sample = names.copy()
            
            # Calculate all metrics for this sample
            shannon = calculate_shannon_diversity(sample)
            evenness = calculate_evenness(shannon, len(set(sample)))
            gini_simpson = calculate_gini_simpson(sample)
            bp = dict()
            for i in bpn:
                bp[i] = 1 - calculate_berger_parker(sample, top_n=i)
                year_metrics[f'Berger-Parker ({i})'].append(bp[i])
                
            # Store metrics for this run
            year_metrics['Shannon'].append(shannon)
            year_metrics['Evenness'].append(evenness)
            year_metrics['Gini-Simpson'].append(gini_simpson)
            
            # Calculate TTR and newness for names
            ttr = calculate_ttr(sample)
            newness = calculate_newness(sample, previous_names)
            previous_names = set(sample)

            # Calculate TTR and newness for characters
            all_chars = [char for name in sample for char in name]
            char_ttr = calculate_ttr(all_chars)
            char_newness = calculate_newness(all_chars, [char for name in previous_names for char in name])

            # Store TTR and newness metrics
            year_metrics['TTR'].append(ttr)
            year_metrics['Newness'].append(newness)
            year_metrics['Char TTR'].append(char_ttr)
            year_metrics['Char Newness'].append(char_newness)
            
            if run_count >= min_runs:
                # Check convergence based on Shannon diversity
                converged = check_convergence(year_metrics['Shannon'])
        
        # Calculate statistics for each metric
        for metric in year_metrics:
            if year_metrics[metric]:  # Ensure there are values to calculate
                mean_value = np.mean(year_metrics[metric])
            std_error = np.std(year_metrics[metric]) / np.sqrt(run_count)
            
            results[metric][year] = mean_value
            ci_lower[metric][year] = mean_value - 1.96 * std_error
            ci_upper[metric][year] = mean_value + 1.96 * std_error
        
            run_count += 1

        actual_runs[year] = run_count
    
    return results, ci_lower, ci_upper, actual_runs

def check_convergence(diversity_values, threshold=0.001):
    """Check if the diversity estimate has converged based on relative change in std error."""
    if len(diversity_values) < 50:
        return False
    
    half_len = len(diversity_values) // 2
    std_err_half = np.std(diversity_values[:half_len]) / np.sqrt(half_len)
    std_err_all = np.std(diversity_values) / np.sqrt(len(diversity_values))
    
    if std_err_half == 0:
        return True
    rel_change = abs(std_err_all - std_err_half) / std_err_half
    
    return rel_change < threshold

def get_db_connection(db_path):
    """Establish a direct connection to the SQLite database."""
    return sqlite3.connect(db_path)

# Define colors for flexibility
BOYS_COLOR = "blue"
GIRLS_COLOR = "red"

minrun, maxrun = 1,10

def calculate_shannon_diversity(names):
    """Calculate Shannon's diversity index for a given list of names."""
    name_counts = dd(int)
    for name in names:
        name_counts[name] += 1
    
    total = len(names)
    diversity = 0
    for count in name_counts.values():
        p = count / total
        diversity -= p * math.log(p)
    return diversity


def calculate_evenness(H, S):
    """Calculate Pielou's evenness index."""
    return H / math.log(S) if S > 1 else 0

def calculate_gini_simpson(names):
    """Calculate Gini-Simpson index."""
    name_counts = dd(int)
    for name in names:
        name_counts[name] += 1
    
    total = len(names)
    simpson_D = sum((count / total) ** 2 for count in name_counts.values())
    return 1 - simpson_D

def calculate_berger_parker(names, top_n=1):
    """Calculate Berger–Parker index considering the top_n most frequent names."""
    name_counts = Counter(names)
    total = len(names)
    top_counts = sum(count for _, count in name_counts.most_common(top_n))
    return top_counts / total





# Connect to the database and fetch data
current_directory = os.path.abspath(os.path.dirname(__file__))
conn = get_db_connection(db_path)

# Define the options for corpus and type
# Use db_options from web.db
types = ['orth', 'pron', 'both']

for src in db_options:
    for data_type in types:
        if src in ['hs', 'hs+bc'] and data_type != 'orth':
            print(f"Skipping invalid combination: {src} with {data_type}")
            continue

        print(f"Processing {src} with {data_type}")

        table_name = db_options[src][0]
        byyear = get_name_year(conn, table=table_name, src=src, data_type=data_type)

        # Transform the data structure to be by gender first
        names = {'M': dd(list), 'F': dd(list)}
        for year, genders in byyear.items():
            for gender, name_list in genders.items():
                names[gender][year] = name_list
                print(gender, year)
                print(name_list)
                
        if not names:
            raise ValueError("No data fetched from the database. Please check the database connection and data.")

        all_counts = [len(names[y][g]) for y in names.keys() for g in names[y].keys()]
        min_size = min(all_counts)
        print(f'Smallest sample is: {min_size}')
        sample_size = int(0.9 * min_size)
        print(f'Using sample size: {sample_size}')
        all_metrics = {'M': {}, 'F': {}}
        confidence_intervals  = {'M': dd(lambda: dd(list)),
                                 'F': dd(lambda: dd(list))}

        for gender in ['M', 'F']:
            print(f"Analyzing diversity for gender: {gender}")
            results, ci_lower, ci_upper, run_counts = analyze_diversity_with_adaptive_sampling(names[gender], sample_size)
            for year in results['Shannon'].keys():  # Using Shannon as reference since all metrics will have the same years
                all_metrics[gender][year] = {
                    "Shannon": results['Shannon'][year],
                    "Evenness": results['Evenness'][year],
                    "Gini-Simpson": results['Gini-Simpson'][year],
                    "Runs": run_counts[year]
                }
                all_metrics[gender][year]["TTR"] = results['TTR'][year]
                all_metrics[gender][year]["Newness"] = results['Newness'][year]
                all_metrics[gender][year]["Char TTR"] = results['Char TTR'][year]
                all_metrics[gender][year]["Char Newness"] = results['Char Newness'][year]
                for i in bpn:
                    all_metrics[gender][year][f'Berger-Parker ({i})'] = results[f'Berger-Parker ({i})'][year]
                confidence_intervals[gender][year]['Shannon'] = (ci_lower['Shannon'][year], ci_upper['Shannon'][year])

        print("\nDiversity analysis completed with adaptive sampling including Number, Evenness, Gini-Simpson and Berger-parker.")
        if all_metrics['M']:
            plot_path = os.path.join(plot_dir, f"diversity_{src}_{data_type}_Var.png") 
            plot_multi_panel_trends(all_metrics, ["Shannon", "Evenness",
                                                  "Gini-Simpson", "Berger-Parker (1)"],
                                    "Diversity Measures",
                                    plot_path,
                                    confidence_intervals=confidence_intervals)
            plot_path = os.path.join(plot_dir, f"diversity_{src}_{data_type}_BP.png") 
            plot_multi_panel_trends(all_metrics, ["Berger-Parker (5)",
                                                  "Berger-Parker (10)",
                                                  "Berger-Parker (50)",
                                                  "Berger-Parker (100)"],
                                    "Berger-Parker Index at Different N Values",
                                   plot_path )
        # Plot new diversity measures
        if all_metrics['M']:
            plot_path = os.path.join(plot_dir, f"diversity_{src}_{data_type}_TTR_Newness.png")
            plot_multi_panel_trends(all_metrics, ["TTR", "Newness", "Char TTR", "Char Newness"],
                                    "TTR and Newness Measures",
                                    plot_path)
        diversity_data = {
            "metrics": all_metrics
        }

        output_path = os.path.join(json_dir, f"diversity_data_{src}_{data_type}.json")
        with open(output_path, 'w') as f:
            json.dump(diversity_data, f)

        # Save diversity metrics and plot paths to JSON
        diversity_data = {
            "metrics": all_metrics
        }

        output_path = os.path.join(json_dir, f"diversity_data_{src}_{data_type}.json")
        with open(output_path, 'w') as f:
            json.dump(diversity_data, f)

        print(f"Diversity data saved to {output_path}")
