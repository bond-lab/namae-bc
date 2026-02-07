import sys, os
import sqlite3
from collections import defaultdict as dd, Counter
import numpy as np
from scipy import stats
from scipy.stats import pearsonr
import pandas as pd

# Add the parent directory to the system path for module imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from web.db import db_options, get_name_year, get_name_count_year
from web.visualize import plot_multi_panel_trends

current_directory = os.path.abspath(os.path.dirname(__file__))

db_path = os.path.join(current_directory, "../web/db/namae.db")
plot_dir = os.path.join(current_directory, "../web/static/plot")

conn = sqlite3.connect(db_path)

c = conn.cursor()

def get_bp(top_n, dtype='orth', src='meiji', start=1989, end=2024):
    assert dtype in ('orth', 'pron'), f"Unknown data {dtype}, should be orth or list"
    assert src in ('meiji', 'hs'), f"Unknown data {dtype}, should be orth or list"
    if src == 'meiji':
        total_src = 'totals'
    else:
        total_src = src
    c.execute(f"""
WITH top_names AS (
  SELECT 
    year, gender, freq,
    ROW_NUMBER() OVER (PARTITION BY year, gender ORDER BY freq DESC) as freq_rank
  FROM nrank 
  WHERE src = ?
    AND year >= ? and year <= ?
    AND {dtype} IS NOT NULL
)
SELECT 
  t.year,
  t.gender,
  SUM(t.freq) as total_frequency,
  c.count as sample_size,
  CAST(SUM(t.freq) AS FLOAT) / c.count as proportion
FROM top_names t
JOIN name_year_cache c ON t.year = c.year AND t.gender = c.gender
WHERE t.freq_rank <= ?
  AND c.src = ?
    AND t.year >= ? and t.year <= ?
GROUP BY t.year, t.gender, c.count
ORDER BY t.year, t.gender""", (src, start, end, top_n, total_src, start, end))
    byyear = dd(dict)
    for (year, gender, count, sample, proportion) in c:
        byyear[gender][year] =  (proportion, count, sample)
    return byyear


def calculate_trend_statistics(all_metrics, selected_metrics):
    """
    Calculate trend statistics for each metric and gender.
    
    Parameters:
    -----------
    all_metrics : dict
        Dictionary containing metrics data for both genders
    selected_metrics : list
        List of metrics to analyze
    
    Returns:
    --------
    trend_stats : dict
        Dictionary containing trend statistics for each gender and metric
        Structure: {
            'M': {metric: {'correlation': r, 'p_value': p, 'annual_change': pct, 'slope': slope, 'mean': mean}},
            'F': {metric: {'correlation': r, 'p_value': p, 'annual_change': pct, 'slope': slope, 'mean': mean}}
        }
    """
    trend_stats = {'M': {}, 'F': {}}
    
    for gender in ['M', 'F']:
        for metric in selected_metrics:
            # Collect valid data points
            years = []
            values = []
            
            for year in sorted(all_metrics[gender].keys()):
                if metric in all_metrics[gender][year]:
                    years.append(year)
                    values.append(all_metrics[gender][year][metric])
            
            if len(years) >= 3:  # Need at least 3 points for meaningful statistics
                years = np.array(years)
                values = np.array(values)
                mean = np.mean(values)
                # Calculate correlation with year
                correlation, p_value = pearsonr(years, values)
                
                # Calculate linear regression for slope
                slope, intercept, _, _, _ = stats.linregress(years, values)
                
                # Calculate annual change as percentage
                # This is the average percentage change per year
                if len(values) > 1:
                    # Method 1: Average of year-to-year percentage changes
                    pct_changes = []
                    for i in range(1, len(values)):
                        if values[i-1] != 0:  # Avoid division by zero
                            pct_change = ((values[i] - values[i-1]) / values[i-1]) * 100
                            pct_changes.append(pct_change)
                    
                    annual_change = np.mean(pct_changes) if pct_changes else 0
                    
                    # Alternative Method 2: Compound annual growth rate (CAGR)
                    # cagr = ((values[-1] / values[0]) ** (1 / (years[-1] - years[0])) - 1) * 100
                else:
                    annual_change = 0
                
                trend_stats[gender][metric] = {
                    'correlation': correlation,
                    'p_value': p_value,
                    'annual_change': annual_change,
                    'slope': slope,
                    'n_points': len(years),
                    'mean': mean
                }
            else:
                # Not enough data points
                trend_stats[gender][metric] = {
                    'correlation': np.nan,
                    'p_value': np.nan,
                    'annual_change': np.nan,
                    'slope': np.nan,
                    'n_points': len(years),
                    'mean':  np.nan
                }
    
    return trend_stats

def mann_kendall_test(data):
    """
    Perform Mann-Kendall trend test.
    More robust alternative to correlation test for trend detection.
    
    Parameters:
    -----------
    data : array-like
        Time series data
    
    Returns:
    --------
    tau : float
        Kendall's tau statistic
    p_value : float
        Two-sided p-value
    """
    n = len(data)
    if n < 3:
        return np.nan, np.nan
    
    # Calculate Kendall's tau
    concordant = 0
    discordant = 0
    
    for i in range(n-1):
        for j in range(i+1, n):
            if data[j] > data[i]:
                concordant += 1
            elif data[j] < data[i]:
                discordant += 1
    
    tau = (concordant - discordant) / (n * (n - 1) / 2)
    
    # Calculate p-value (simplified version)
    # For small samples, use exact distribution; for large samples, use normal approximation
    if n >= 10:
        # Normal approximation
        var_tau = (2 * (2*n + 5)) / (9 * n * (n - 1))
        z = tau / np.sqrt(var_tau)
        p_value = 2 * (1 - stats.norm.cdf(abs(z)))
    else:
        # For small samples, this is a simplified approach
        # In practice, you might want to use scipy.stats.kendalltau
        tau_scipy, p_value = stats.kendalltau(range(n), data)
        tau = tau_scipy
    
    return tau, p_value

def format_trend_text(trend_stats, metric, gender, significance_level=0.05):
    """
    Format trend statistics into readable text for plot annotations.
    
    Parameters:
    -----------
    trend_stats : dict
        Output from calculate_trend_statistics
    metric : str
        Metric name
    gender : str
        Gender ('M' or 'F')
    significance_level : float
        Alpha level for significance testing
    
    Returns:
    --------
    text : str
        Formatted text string
    """
    stats_data = trend_stats[gender][metric]
    
    if np.isnan(stats_data['correlation']):
        return "Insufficient data"
    
    r = stats_data['correlation']
    p = stats_data['p_value']
    annual_change = stats_data['annual_change']
    
    # Determine significance
    is_significant = p < significance_level
    sig_marker = "*" if is_significant else ""
    
    # Format correlation
    if abs(r) < 0.001:
        r_text = f"r≈0{sig_marker}"
    else:
        r_text = f"r={r:.3f}{sig_marker}"
    
    # Format annual change
    if abs(annual_change) < 0.001:
        change_text = "≈0%/yr"
    else:
        change_text = f"{annual_change:+.3f}%/yr"

    mean_text = f"mean = {stats_data['mean']:.3f}"    
        
    return f"{r_text}, {change_text}, {mean_text}"

def plot_multi_panel_trends_with_stats(all_metrics, selected_metrics, title,
                                      filename, confidence_intervals=None, 
                                      trend_stats=None, show_stats=True):
    """
    Enhanced plotting function that includes trend statistics.
    
    Parameters:
    -----------
    all_metrics : dict
        Dictionary containing metrics data for both genders
    selected_metrics : list
        List of metrics to plot
    title : str
        Title for the plot
    filename : str
        Path to save the plot
    confidence_intervals : dict, optional
        Dictionary containing confidence intervals for metrics
    trend_stats : dict, optional
        Dictionary containing trend statistics (output from calculate_trend_statistics)
    show_stats : bool
        Whether to display trend statistics on the plot
    """
    import matplotlib.pyplot as plt
    import matplotlib.lines as mlines
    
    # Get all years from both genders
    all_years = sorted(set(list(all_metrics['M'].keys()) + list(all_metrics['F'].keys())))
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 12))
    
    for idx, metric in enumerate(selected_metrics):
        ax = axes[idx // 2, idx % 2]
        
        # Store info for combined legend+stats box
        legend_stats_info = []
        
        # For each gender, collect valid data points
        for gender, color, marker, label in [
            ('M', 'orange', 'o', 'Boys'), 
            ('F', 'purple', 's', 'Girls')
        ]:
            # Get years where this metric exists for this gender
            valid_years = []
            valid_values = []
            
            for year in all_years:
                if year in all_metrics[gender] and metric in all_metrics[gender][year]:
                    valid_years.append(year)
                    valid_values.append(all_metrics[gender][year][metric])
            
            # Only plot if we have valid data
            if valid_years and valid_values:
                ax.plot(valid_years, valid_values, marker=marker, linestyle=':', 
                        color=color, linewidth=2, markersize=6)
                
                # Add trend line if statistics are significant
                if trend_stats and show_stats:
                    stats_data = trend_stats[gender][metric]
                    if not np.isnan(stats_data['correlation']) and stats_data['p_value'] < 0.05:
                        lstyle = '-'
                    else:
                        lstyle = '--'
                    # Add trend line
                    years_array = np.array(valid_years)
                    trend_line = stats_data['slope'] * years_array + (
                        np.mean(valid_values) - stats_data['slope'] * np.mean(years_array)
                    )
                    ax.plot(years_array, trend_line, color=color, linestyle=lstyle, 
                            alpha=0.7, linewidth=1)
                        
                
                # Add confidence intervals if available
                if confidence_intervals is not None:
                    valid_ci_years = []
                    valid_ci_lower = []
                    valid_ci_upper = []
                    
                    for year in valid_years:
                        if (year in confidence_intervals[gender] and 
                            metric in confidence_intervals[gender][year]):
                            valid_ci_years.append(year)
                            valid_ci_lower.append(confidence_intervals[gender][year][metric][0])
                            valid_ci_upper.append(confidence_intervals[gender][year][metric][1])
                    
                    if valid_ci_years:
                        ax.plot(valid_ci_years, valid_ci_lower, linestyle='--', 
                                color=color, alpha=0.7, linewidth=1)
                        ax.plot(valid_ci_years, valid_ci_upper, linestyle='--', 
                                color=color, alpha=0.7, linewidth=1)
                
                # Collect info for combined legend+stats
                if trend_stats and show_stats:
                    stat_text = format_trend_text(trend_stats, metric, gender)
                    legend_stats_info.append((color, marker, label, stat_text))
                else:
                    legend_stats_info.append((color, marker, label, None))
        
        # Force x-axis ticks to be integers only
        ax.xaxis.set_major_locator(plt.MaxNLocator(integer=True))
        
        ax.set_title(metric, fontsize=12, fontweight='bold')
        ax.grid(False)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.spines['bottom'].set_visible(False)
        
        # Create combined legend+stats box
        if legend_stats_info:
            # Build custom legend handles with stats text
            handles = []
            labels = []
            for color, marker, label, stat_text in legend_stats_info:
                handle = mlines.Line2D([], [], color=color, marker=marker, 
                                       linestyle=':', linewidth=2, markersize=6)
                handles.append(handle)
                if stat_text and show_stats:
                    labels.append(f"{label}: {stat_text}")
                else:
                    labels.append(label)
            
            # Place legend at top left with stats included
            legend = ax.legend(handles, labels, loc='upper left', frameon=True,
                              fontsize=10, handlelength=2.5,
                              fancybox=True, framealpha=0.8, edgecolor='none')
            legend.get_frame().set_facecolor('white')
    
    plt.tight_layout()
    if title:
        plt.suptitle(title, y=0.98, fontsize=14, fontweight='bold')
    
    # Save plot to a file
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    plt.close(fig)

both = dict()
outfile='BP_data.tsv'
out = open(outfile, 'w')
all_metrics = {'M': {}, 'F': {}}
for src in ('meiji', 'hs'):
    for dtype in ('orth', 'pron'):
        if src == 'hs' and dtype == 'pron':
            continue
        plot_data = dd(lambda: dd(dict))
        both[dtype] = plot_data
        if dtype == 'orth':
            n_range = [1, 10, 50, 100]
        else:
            n_range = [1, 5, 10, 50]
        selected_metrics =  [f"Berger-Parker ({n})" for n in n_range]
        
        for top_n in n_range:
            byyear = get_bp(top_n, dtype, src)
            for gender in ['M', 'F']:
                print(f"#\n# Top {top_n} counts and ratios for {gender}: {src} ({dtype})\n#", file = out)
                print("rank\tgender\tyear\tproportion\tcount\tsample", file = out)      
                for year in byyear[gender]:
                    if not byyear[gender][year][0]:
                        continue
                    plot_data[gender][year][f'Berger-Parker ({top_n})'] = 1 - byyear[gender][year][0]
                    print(top_n, gender, year, \
                          byyear[gender][year][0],
                          byyear[gender][year][1],
                          byyear[gender][year][2],
                          sep='\t', file = out)

        plot_path = os.path.join(plot_dir, f"diversity_{src}_{dtype}_BP_all.png")
        plot_multi_panel_trends(plot_data, selected_metrics,
                                "Berger-Parker Index at Different N Values",
                                plot_path )


        plot_path = os.path.join(plot_dir, f"diversity_{src}_{dtype}_BP_slope.png")

        trend_stats = calculate_trend_statistics(plot_data, selected_metrics)
        plot_multi_panel_trends_with_stats(plot_data, selected_metrics,
                                           None, 
                                           plot_path, trend_stats=trend_stats)
