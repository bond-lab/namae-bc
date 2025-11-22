import os
import math
import copy
import random
import sqlite3
import numpy as np
from collections import defaultdict as dd, Counter
import matplotlib.pyplot as plt
import pandas as pd  # For table generation
import json
import sys

# Add the parent directory to the system path for module imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from web.db import db_options, get_name_year, get_name_count_year
from web.visualize import plot_multi_panel_trends
from plot_meiji import calculate_trend_statistics, plot_multi_panel_trends_with_stats

# Constants for sampling runs
MIN_RUNS = 1 #10
MAX_RUNS = 1 # 1000

# Berger-Parker index top N values
BERGER_PARKER_TOP_N = [1, 5, 10, 50, 100]

# Define paths for database and output directories
current_directory = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(current_directory, "../web/db/namae.db")
json_dir = os.path.join(current_directory, "../web/static/data")
plot_dir = os.path.join(current_directory, "../web/static/plot")
os.makedirs(json_dir, exist_ok=True)
os.makedirs(plot_dir, exist_ok=True)




base_metrics = {
    'Shannon-Wiener': [],
    'Evenness': [],
    'Gini-Simpson': [],
    'TTR': [],
    'Newness': [],
    'Char TTR': [],
    'Char Newness': [],
    'Singleton': [],
    'Singleton (types)': []
}
for n in BERGER_PARKER_TOP_N:
    base_metrics[f'Berger-Parker ({n})'] = []


def calculate_shannon_diversity(names):
    """Calculate Shannon-Wiener's diversity index for a given list of names."""
    """Calculate Shannon-Wiener's diversity index for a given list of names."""
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
    """Calculate Pielou's evenness index based on Shannon-Wiener's diversity and species count."""
    return H / math.log(S) if S > 1 else 0

def calculate_gini_simpson(names):
    """Calculate Gini-Simpson index for a given list of names."""
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

def calculate_singleton_ratio_types(names):
    """Calculate singleton ratio - proportion of names that appear only once."""
    name_counts = Counter(names)
    singletons = sum(1 for count in name_counts.values() if count == 1)
    total_unique_names = len(name_counts)
    return singletons / total_unique_names

def calculate_singleton_ratio(names):
    """
    Calculate singleton ratio over tokens - proportion of people who have singleton names.
    
    This measures what percentage of individuals have a name that appears only once
    in the dataset (i.e., a unique name that no one else has).
    
    Args:
        names: List of names (one per person)
    
    Returns:
        float: Proportion of people who have singleton names (0.0 to 1.0)
    
    Example:
        names = ['John', 'Mary', 'Unique1', 'John', 'Unique2']
        # John appears 2 times, Mary appears 1 time, Unique1 appears 1 time, Unique2 appears 1 time
        # 3 out of 5 people have singleton names (Mary, Unique1, Unique2)
        # Returns: 0.6 (60%)
    """
    name_counts = Counter(names)
  
    # Count how many people have singleton names
    people_with_singleton_names = sum(
        count for count in name_counts.values() if count == 1
    )
    
    total_people = len(names)
    return people_with_singleton_names / total_people if total_people > 0 else 0.0

def calculate_ttr(names):
    """Calculate Type Token Ratio (TTR) for a given list of names."""
    unique_names = set(names)
    return len(unique_names) / len(names) if names else 0

def calculate_newness(current_names, previous_names):
    """Calculate newness ratio: new names seen this year over total unique names."""
    new_items = set(current_names) - set(previous_names)
    total_types = len(set(current_names))
    return (len(new_items) / total_types) if total_types > 0 else 0



def analyze_with_sampling(data, sample_size, min_runs=MIN_RUNS, max_runs=MAX_RUNS):
    """
    Analyze diversity metrics with adaptive sampling.
    
    Parameters:
    - data: Dictionary of names by year.
    - sample_size: Number of samples to draw.
    - min_runs: Minimum number of sampling runs.
    - max_runs: Maximum number of sampling runs.
    
    Returns:
    - results: Calculated metrics for each year.
    - ci_lower: Lower confidence intervals for metrics.
    - ci_upper: Upper confidence intervals for metrics.
    - actual_runs: Number of runs performed for each year.
    """
    results  = dd(lambda: dd(float))
    ci_lower = dd(lambda: dd(float))
    ci_upper = dd(lambda: dd(float))
    actual_runs = {}
    
    # Create a consistent sample of previous year's names for comparison
    previous_year_samples = {}
    years = sorted(data.keys())
    
    # First, create consistent samples for each year
    for year in years:
        names = data[year]
        if sample_size and len(names) > sample_size:
            # For consistent results, use a fixed seed for the initial sampling
            random.seed(42 + int(year))  # Use year in seed for variety but consistency
            previous_year_samples[year] = set(random.sample(names, sample_size))
            random.seed()  # Reset the seed for subsequent random operations
        else:
            previous_year_samples[year] = set(names)
    
    # Now perform the analysis using these consistent samples
    for i, year in enumerate(years):
        names = data[year]
        year_metrics = copy.deepcopy(base_metrics)
        # Get the previous year's sample for comparison
        is_first_year = (i == 0)
        previous_year_sample = set() if is_first_year else previous_year_samples[years[i-1]]
        
        converged = False
        run_count = 0
        
        while not converged and run_count < max_runs:
            if sample_size and len(names) > sample_size:
                sample = random.sample(names, sample_size)
            else:
                sample = names.copy()
            
            # Calculate diversity metrics
            shannon = calculate_shannon_diversity(sample)
            evenness = calculate_evenness(shannon, len(set(sample)))
            gini_simpson = calculate_gini_simpson(sample)
            singleton = calculate_singleton_ratio(sample)
            bp = dict()
            for n in BERGER_PARKER_TOP_N:
                bp[n] = 1 - calculate_berger_parker(sample, top_n=n)
                year_metrics[f'Berger-Parker ({n})'].append(bp[n])
                
            # Store metrics for this run
            year_metrics['Shannon-Wiener'].append(shannon)
            year_metrics['Evenness'].append(evenness)
            year_metrics['Gini-Simpson'].append(gini_simpson)
            year_metrics['Singleton'].append(singleton)
                        
            # Calculate TTR for all years
            ttr = calculate_ttr(sample)
            year_metrics['TTR'].append(ttr)
            
            # Calculate newness only for non-first years
            if not is_first_year:
                newness = calculate_newness(sample, previous_year_sample)
                year_metrics['Newness'].append(newness)
            
            # Calculate character metrics
            all_chars = [char for name in sample for char in name[0]]
            char_ttr = calculate_ttr(all_chars)
            year_metrics['Char TTR'].append(char_ttr)
            
            # Calculate character newness only for non-first years
            if not is_first_year:
                previous_chars = [char for name in previous_year_sample for char in name[0]]
                char_newness = calculate_newness(all_chars, previous_chars)
                year_metrics['Char Newness'].append(char_newness)
            
            if run_count >= min_runs:
                # Check convergence based on Shannon-Wiener diversity
                converged = check_convergence(year_metrics['Shannon-Wiener'])
            run_count += 1
            actual_runs[year] = run_count

        # Calculate statistics for each metric
        for metric in year_metrics:
            if year_metrics[metric]:  # Ensure there are values to calculate
                mean_value = np.mean(year_metrics[metric])
                std_error = np.std(year_metrics[metric]) / np.sqrt(run_count)
                
                # Skip adding newness metrics for first year
                if is_first_year and metric in ['Newness', 'Char Newness']:
                    continue
                
                results[metric][year] = mean_value
                ci_lower[metric][year] = mean_value - 1.96 * std_error
                ci_upper[metric][year] = mean_value + 1.96 * std_error
        
    return results, ci_lower, ci_upper, actual_runs

def check_convergence(diversity_values, threshold=0.001):
    """Check if the diversity estimate has converged based on relative change in standard error."""
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



conn = get_db_connection(db_path)

types = ['orth', 'pron', 'both']

for src in db_options:
#    if src != 'hs': #'hs' not in src:
#        continue
    for data_type in types:
        if src in ['hs', 'hs+bc'] and data_type != 'orth':
            print(f"Skipping invalid combination: {src} with {data_type}")
            continue

        print(f"Processing {src} with {data_type}")

        table_name = db_options[src][0]
        byyear = get_name_year(conn, src=src,
                               table=table_name, dtype=data_type)

        # Transform the data structure to be by gender first
        names = {'M': dd(list), 'F': dd(list)}
        for year, genders in byyear.items():
            for gender, name_list in genders.items():
                names[gender][year] = name_list
        if not names:
            raise ValueError("No data fetched from the database. Please check the database connection and data.")

        # Determine the smallest sample size across all years and genders
        #all_counts = [len(names[y][g]) for y in names.keys() for g in names[y].keys()]
        #min_size = min(all_counts)
        #print(f'Smallest sample is: {min_size}')
        #sample_size = int(0.9 * min_size)  # Use 90% of the smallest sample size
        #print(f'Using sample size: {sample_size}')
        sample_size=None

        
        # Initialize structures to store metrics and confidence intervals
        all_metrics = {'M': {}, 'F': {}}
        confidence_intervals  = {'M': dd(lambda: dd(list)),
                                 'F': dd(lambda: dd(list))}

        for gender in ['M', 'F']:
            print(f"Analyzing diversity for gender: {gender}")
            results, ci_lower, ci_upper, run_counts = analyze_with_sampling(
                names[gender], sample_size, min_runs=MIN_RUNS, max_runs=MAX_RUNS
            )
            # Using Shannon-Wiener as reference since all metrics will have the same years
            for year in results['Shannon-Wiener'].keys():
                all_metrics[gender][year] = dict()
                for metric in base_metrics:
                      if year in results[metric]:
                          all_metrics[gender][year][metric] = results[metric][year]
                #     "Evenness": results['Evenness'][year],
                #     "Gini-Simpson": results['Gini-Simpson'][year],
                #     "Runs": run_counts[year]
                # }
                
                # # Add TTR metric (should be available for all years)
                # all_metrics[gender][year]["TTR"] = results['TTR'][year]
                # all_metrics[gender][year]["Char TTR"] = results['Char TTR'][year]
                
                # Add newness metrics only if they exist for this year
                # (they won't exist for the first year)
                # if year in results['Newness']:
                #     all_metrics[gender][year]["Newness"] = results['Newness'][year]
                # if year in results['Char Newness']:
                #     all_metrics[gender][year]["Char Newness"] = results['Char Newness'][year]
                
                # # Add Berger-Parker metrics
                # for i in BERGER_PARKER_TOP_N:
                #     all_metrics[gender][year][f'Berger-Parker ({i})'] = results[f'Berger-Parker ({i})'][year]
                
                # # Add confidence intervals
                confidence_intervals[gender][year]['Shannon-Wiener'] = (ci_lower['Shannon-Wiener'][year], ci_upper['Shannon-Wiener'][year])

        print("\nDiversity analysis completed with adaptive sampling including Number, Evenness, Gini-Simpson and Berger-parker.")
        # Plot diversity measures and save to JSON
        if all_metrics['M']:  # Check if there are metrics to plot
            plot_path = os.path.join(plot_dir, f"diversity_{src}_{data_type}_Var.png") 
            plot_multi_panel_trends(all_metrics, ["Shannon-Wiener", "Evenness",
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

        # plot for book
        plot_path = os.path.join(plot_dir, f"diversity_{src}_{data_type}_diversity.png")
        selected_metrics= ["Shannon-Wiener", "Gini-Simpson", "Singleton", "TTR"]
        trend_stats = calculate_trend_statistics(all_metrics, selected_metrics)
        plot_multi_panel_trends_with_stats(all_metrics, selected_metrics,
                                           "", # "Diversity Measures",
                                           plot_path,
                                           trend_stats=trend_stats,  
                                           confidence_intervals=None)
            
        # Save diversity metrics to JSON
        diversity_data = {
            "metrics": all_metrics
        }

        output_path = os.path.join(json_dir, f"diversity_data_{src}_{data_type}.json")
        with open(output_path, 'w') as f:
            json.dump(diversity_data, f)

        print(f"Diversity data saved to {output_path}")
