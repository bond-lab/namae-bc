import numpy as np
import pandas as pd
from scipy import stats
from scipy.spatial.distance import jensenshannon
from scipy.stats import wasserstein_distance, chi2_contingency
import matplotlib.pyplot as plt
from itertools import product
import sqlite3
import os
from collections import defaultdict as dd

def extract_name_frequencies(data, year=None, gender=None, years=None, genders=None):
    """
    Extract name frequencies from nested dictionary structure.
    
    Parameters:
    - data: Dict of structure data[year][gender] = list of names
    - year: Single year to extract (if None, combines all years)
    - gender: Single gender to extract (if None, combines all genders)
    - years: List of years to include (if None, uses all available)
    - genders: List of genders to include (if None, uses all available)
    
    Returns:
    - Series with name frequencies
    """
    if years is None:
        years = list(data.keys())
    if genders is None:
        genders = list(data[list(data.keys())[0]].keys())
    
    # If specific year/gender requested, override the lists
    if year is not None:
        years = [year]
    if gender is not None:
        genders = [gender]
    
    name_counts = {}
    
    for y in years:
        if y not in data:
            continue
        for g in genders:
            if g not in data[y]:
                continue
            
            # Count frequencies - assuming names are ordered by frequency (rank 1 = index 0)
            for rank, name in enumerate(data[y][g], 1):
                if name not in name_counts:
                    name_counts[name] = 0
                # Weight by inverse rank (rank 1 gets weight 100, rank 100 gets weight 1)
                # This assumes the original data was ranked by frequency
                name_counts[name] += (101 - rank)
    
    return pd.Series(name_counts)

def compare_datasets(data_h, data_m, comparison_type='overall', **kwargs):
    """
    Compare two datasets with various comparison strategies.
    
    Parameters:
    - data_h: Dataset H with structure data[year][gender] = list of names
    - data_m: Dataset M with structure data[year][gender] = list of names  
    - comparison_type: 'overall', 'by_year', 'by_gender', 'by_year_gender', or 'custom'
    - **kwargs: Additional parameters for custom comparisons
    
    Returns:
    - Dictionary with comparison results
    """
    
    if comparison_type == 'overall':
        return _compare_overall(data_h, data_m)
    elif comparison_type == 'by_year':
        return _compare_by_year(data_h, data_m)
    elif comparison_type == 'by_gender':
        return _compare_by_gender(data_h, data_m)
    elif comparison_type == 'by_year_gender':
        return _compare_by_year_gender(data_h, data_m)
    elif comparison_type == 'custom':
        return _compare_custom(data_h, data_m, **kwargs)
    else:
        raise ValueError("comparison_type must be one of: 'overall', 'by_year', 'by_gender', 'by_year_gender', 'custom'")

def _compare_overall(data_h, data_m):
    """Compare overall distributions across all years and genders."""
    freq_h = extract_name_frequencies(data_h)
    freq_m = extract_name_frequencies(data_m)
    
    result = _single_comparison(freq_h, freq_m, "Overall Comparison")
    return {'overall': result}

def _compare_by_year(data_h, data_m):
    """Compare distributions year by year."""
    results = {}
    
    # Get common years
    years_h = set(data_h.keys())
    years_m = set(data_m.keys())
    common_years = sorted(years_h & years_m)
    
    for year in common_years:
        freq_h = extract_name_frequencies(data_h, year=year)
        freq_m = extract_name_frequencies(data_m, year=year)
        
        result = _single_comparison(freq_h, freq_m, f"Year {year}")
        results[year] = result
    
    return results

def _compare_by_gender(data_h, data_m):
    """Compare distributions by gender."""
    results = {}
    
    # Get common genders
    sample_year_h = list(data_h.keys())[0]
    sample_year_m = list(data_m.keys())[0]
    genders_h = set(data_h[sample_year_h].keys())
    genders_m = set(data_m[sample_year_m].keys())
    common_genders = sorted(genders_h & genders_m)
    
    for gender in common_genders:
        freq_h = extract_name_frequencies(data_h, gender=gender)
        freq_m = extract_name_frequencies(data_m, gender=gender)
        
        result = _single_comparison(freq_h, freq_m, f"Gender: {gender}")
        results[gender] = result
    
    return results

def _compare_by_year_gender(data_h, data_m):
    """Compare distributions for each year-gender combination."""
    results = {}
    
    # Get common years and genders
    years_h = set(data_h.keys())
    years_m = set(data_m.keys())
    common_years = sorted(years_h & years_m)
    
    sample_year_h = list(data_h.keys())[0]
    sample_year_m = list(data_m.keys())[0]
    genders_h = set(data_h[sample_year_h].keys())
    genders_m = set(data_m[sample_year_m].keys())
    common_genders = sorted(genders_h & genders_m)
    
    for year, gender in product(common_years, common_genders):
        if year not in data_h or gender not in data_h[year]:
            continue
        if year not in data_m or gender not in data_m[year]:
            continue
            
        freq_h = extract_name_frequencies(data_h, year=year, gender=gender)
        freq_m = extract_name_frequencies(data_m, year=year, gender=gender)
        
        result = _single_comparison(freq_h, freq_m, f"{year} - {gender}")
        results[f"{year}_{gender}"] = result
    
    return results

def _compare_custom(data_h, data_m, years_h=None, genders_h=None, years_m=None, genders_m=None):
    """Custom comparison with specific years/genders for each dataset."""
    freq_h = extract_name_frequencies(data_h, years=years_h, genders=genders_h)
    freq_m = extract_name_frequencies(data_m, years=years_m, genders=genders_m)
    
    h_desc = f"H: years={years_h}, genders={genders_h}"
    m_desc = f"M: years={years_m}, genders={genders_m}"
    title = f"Custom Comparison\n{h_desc}\n{m_desc}"
    
    result = _single_comparison(freq_h, freq_m, title)
    return {'custom': result}

def _single_comparison(freq_h, freq_m, title):
    """Perform a single comparison between two frequency distributions."""
    # Find common names
    common_names = sorted(set(freq_h.index) & set(freq_m.index))
    
    if len(common_names) == 0:
        return {
            'error': 'No common names found',
            'title': title,
            'freq_h_total': len(freq_h),
            'freq_m_total': len(freq_m)
        }
    
    # Extract and normalize frequencies for common names
    h_subset = freq_h[common_names]
    m_subset = freq_m[common_names]
    
    h_dist = h_subset / h_subset.sum()
    m_dist = m_subset / m_subset.sum()
    
    # Calculate metrics
    js_div = jensenshannon(h_dist, m_dist)
    emd = wasserstein_distance(h_dist, m_dist)
    
    # Chi-square test
    h_counts = h_subset.astype(int)
    m_counts = m_subset.astype(int)
    
    observed = pd.DataFrame({
        'H': h_counts,
        'M': m_counts
    })
    
    # Remove rows with zero counts
    observed = observed[(observed['H'] > 0) | (observed['M'] > 0)]
    
    if len(observed) > 1:
        chi2, p, dof, expected = chi2_contingency(observed)
        n = observed.sum().sum()
        cramers_v = np.sqrt(chi2 / (n * (min(observed.shape) - 1)))
        
        chi2_result = {
            'chi2': chi2,
            'p_value': p,
            'cramers_v': cramers_v,
            'interpretation': _interpret_chi_square_results(chi2, p, cramers_v)
        }
    else:
        chi2_result = {'error': 'Insufficient data for chi-square test'}
    
    # Calculate coverage
    h_coverage = h_subset.sum() / freq_h.sum()
    m_coverage = m_subset.sum() / freq_m.sum()
    
    # Correlation of frequencies
    correlation = h_dist.corr(m_dist)
    
    return {
        'title': title,
        'js_divergence': js_div,
        'earth_movers_distance': emd,
        'chi_square': chi2_result,
        'correlation': correlation,
        'common_names_count': len(common_names),
        'h_coverage': h_coverage,
        'm_coverage': m_coverage,
        'h_dist': h_dist,
        'm_dist': m_dist,
        'common_names': common_names
    }

def _interpret_chi_square_results(chi2, p, cramers_v):
    """Helper function to interpret chi-square results"""
    if p < 0.001:
        significance = "Highly significant difference (p < 0.001)"
    elif p < 0.01:
        significance = "Very significant difference (p < 0.01)"
    elif p < 0.05:
        significance = "Significant difference (p < 0.05)"
    else:
        significance = "No significant difference (p >= 0.05)"
    
    if cramers_v < 0.1:
        effect = "negligible effect size"
    elif cramers_v < 0.3:
        effect = "small effect size"
    elif cramers_v < 0.5:
        effect = "moderate effect size"
    else:
        effect = "large effect size"
    
    return f"{significance}, {effect} (Cramer's V = {cramers_v:.4f})"

def create_comparison_summary(results):
    """Create a summary table of all comparison results."""
    summary_data = []
    
    for key, result in results.items():
        if 'error' in result:
            summary_data.append({
                'Comparison': result['title'],
                'JS_Divergence': 'Error',
                'Earth_Movers': 'Error',
                'Correlation': 'Error',
                'Common_Names': result.get('freq_h_total', 0),
                'Chi_Square_p': 'Error'
            })
        else:
            chi2_p = result['chi_square'].get('p_value', np.nan) if 'error' not in result['chi_square'] else np.nan
            
            summary_data.append({
                'Comparison': result['title'],
                'JS_Divergence': f"{result['js_divergence']:.4f}",
                'Earth_Movers': f"{result['earth_movers_distance']:.4f}",
                'Correlation': f"{result['correlation']:.4f}",
                'Common_Names': result['common_names_count'],
                'H_Coverage': f"{result['h_coverage']:.1%}",
                'M_Coverage': f"{result['m_coverage']:.1%}",
                'Chi_Square_p': f"{chi2_p:.4f}" if not np.isnan(chi2_p) else 'N/A'
            })
    
    return pd.DataFrame(summary_data)

def plot_comparison_results(results, metric='js_divergence', figsize=(12, 8)):
    """Plot comparison results across different categories."""
    
    # Extract data for plotting
    plot_data = []
    labels = []
    
    for key, result in results.items():
        if 'error' not in result and metric in result:
            plot_data.append(result[metric])
            labels.append(key)
    
    if not plot_data:
        print("No data available for plotting")
        return None
    
    fig, ax = plt.subplots(figsize=figsize)
    
    # Create bar plot
    bars = ax.bar(range(len(plot_data)), plot_data)
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=45, ha='right')
    
    # Customize plot
    metric_names = {
        'js_divergence': 'Jensen-Shannon Divergence',
        'earth_movers_distance': 'Earth Mover\'s Distance',
        'correlation': 'Correlation'
    }
    
    ax.set_ylabel(metric_names.get(metric, metric))
    ax.set_title(f'{metric_names.get(metric, metric)} Across Comparisons')
    ax.grid(True, alpha=0.3)
    
    # Color bars based on values
    if metric in ['js_divergence', 'earth_movers_distance']:
        # Lower is better - color accordingly
        colors = plt.cm.RdYlGn_r(np.linspace(0.2, 0.8, len(plot_data)))
    else:
        # Higher is better (correlation)
        colors = plt.cm.RdYlGn(np.linspace(0.2, 0.8, len(plot_data)))
    
    for bar, color in zip(bars, colors):
        bar.set_color(color)
    
    plt.tight_layout()
    return fig

# Example usage functions
def quick_overall_comparison(data_h, data_m):
    """Quick overall comparison between datasets."""
    results = compare_datasets(data_h, data_m, 'overall')
    result = results['overall']
    
    if 'error' in result:
        print(f"Error: {result['error']}")
        return None
    
    print(f"""
    Overall Comparison Results:
    ==========================
    Common names: {result['common_names_count']}
    Dataset H coverage: {result['h_coverage']:.1%}
    Dataset M coverage: {result['m_coverage']:.1%}
    
    Similarity Metrics:
    - Jensen-Shannon Divergence: {result['js_divergence']:.4f} (lower = more similar)
    - Earth Mover's Distance: {result['earth_movers_distance']:.4f} (lower = more similar)
    - Correlation: {result['correlation']:.4f} (higher = more similar)
    
    Statistical Test:
    {result['chi_square'].get('interpretation', 'Chi-square test failed')}
    """)
    
    return result

def analyze_trends_over_time(data_h, data_m):
    """Analyze how similarity changes over time."""
    results = compare_datasets(data_h, data_m, 'by_year')
    
    if not results:
        print("No common years found")
        return None
    
    # Create summary
    summary = create_comparison_summary(results)
    print("Yearly Comparison Summary:")
    print("=" * 50)
    print(summary.to_string(index=False))
    
    # Plot trends
    fig = plot_comparison_results(results, 'js_divergence')
    
    return results, summary

def plot_gender_names_analysis(data_dict, session=None, output_filename='gender_names_analysis.png', figsize=(14, 6)):
    """
    Create a two-subplot visualization of common names count and JS divergence by gender over time.
    
    Parameters:
    -----------
    data_dict : dict
        Dictionary with structure: {gender: {year: {'common_names_count': int, 'js_divergence': float}}}
        where gender is 'M' or 'F' and year is 2006-2009
    session : dict, optional
        Session dictionary containing color preferences
    output_filename : str, optional
        Name of the output PNG file (default: 'gender_names_analysis.png')
    figsize : tuple, optional
        Figure size as (width, height) in inches (default: (14, 6))
    
    Returns:
    --------
    str : Path to the saved PNG file
    """
    
    # Get colors from session or use defaults
    female_color = session.get('female_color', 'purple') if session else 'purple'
    male_color = session.get('male_color', 'orange') if session else 'orange'
    
    # Extract years (should be 2006-2009)
    years = list(data_dict['F'].keys())
    
    # Extract data for plotting
    male_common_names = [data_dict['M'][year]['common_names_count'] for year in years]
    male_js_divergence = [data_dict['M'][year]['js_divergence'] for year in years]
    
    female_common_names = [data_dict['F'][year]['common_names_count'] for year in years]
    female_js_divergence = [data_dict['F'][year]['js_divergence'] for year in years]
    
    # Create the figure and subplots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize)
    #fig.suptitle('Gender Names Analysis: Common Names Count & JS Divergence (2006-2009)', 
    #             fontsize=16, fontweight='bold', y=0.95)
    
    # Plot 1: Common Names Count
    ax1.plot(years, male_common_names, marker='.', linewidth=3, markersize=8, 
             color=male_color, label='Male', markerfacecolor='white', markeredgewidth=2)
    ax1.plot(years, female_common_names, marker='.', linewidth=3, markersize=8, 
             color=female_color, label='Female', markerfacecolor='white', markeredgewidth=2)
    
    ax1.set_title('Common Names Count Over Time', fontsize=14, fontweight='bold', pad=25)
    ax1.set_xlabel('Year', fontsize=12)
    ax1.set_ylabel('Common Names Count', fontsize=12)
    ax1.legend(fontsize=11, frameon=True, fancybox=True, shadow=True)
    ax1.grid(True, alpha=0.3, linestyle='--')
    ax1.set_xticks(years)
    ax1.set_ylim(bottom=0)  # Start y-axis at 0
    ax1.spines['top'].set_visible(False)    # Remove top border
    ax1.spines['right'].set_visible(False)  # Remove right border
    
    # Add value labels on points for common names
    # for i, year in enumerate(years):
    #     ax1.annotate(f'{male_common_names[i]}', 
    #                 (year, male_common_names[i]), 
    #                 textcoords="offset points", xytext=(0,10), ha='center', fontsize=9)
    #     ax1.annotate(f'{female_common_names[i]}', 
    #                 (year, female_common_names[i]), 
    #                 textcoords="offset points", xytext=(0,-15), ha='center', fontsize=9)
    
    # Plot 2: JS Divergence
    ax2.plot(years, male_js_divergence, marker='.', linewidth=3, markersize=8, 
             color=male_color, label='Male', markerfacecolor='white', markeredgewidth=2)
    ax2.plot(years, female_js_divergence, marker='.', linewidth=3, markersize=8, 
             color=female_color, label='Female', markerfacecolor='white', markeredgewidth=2)
    
    ax2.set_title('JS Divergence Over Time', fontsize=14, fontweight='bold', pad=25)
    ax2.set_xlabel('Year', fontsize=12)
    ax2.set_ylabel('JS Divergence', fontsize=12)
    ax2.legend(fontsize=11, frameon=True, fancybox=True, shadow=True)
    ax2.grid(True, alpha=0.3, linestyle='--')
    ax2.set_xticks(years)
    ax2.set_ylim(bottom=0)  # Start y-axis at 0
    ax2.spines['top'].set_visible(False)    # Remove top border
    ax2.spines['right'].set_visible(False)  # Remove right border
    
    # Add value labels on points for JS divergence
    # for i, year in enumerate(years):
    #     ax2.annotate(f'{male_js_divergence[i]:.3f}', 
    #                 (year, male_js_divergence[i]), 
    #                 textcoords="offset points", xytext=(0,10), ha='center', fontsize=9)
    #     ax2.annotate(f'{female_js_divergence[i]:.3f}', 
    #                 (year, female_js_divergence[i]), 
    #                 textcoords="offset points", xytext=(0,-15), ha='center', fontsize=9)
    
    # Adjust layout to prevent overlap
    plt.tight_layout()
    plt.subplots_adjust(top=0.85)  # More room for the main title
    
    # Save the plot
    plt.savefig(output_filename, dpi=300, bbox_inches='tight', 
                facecolor='white', edgecolor='none')
    plt.close()  # Close the figure to free memory
    
    return output_filename


def get_meiji(conn):
    """
    get the meiji data
    """
    c = conn.cursor()
    c.execute(f"""
    SELECT year, gender, orth, count(orth)
    FROM namae
    WHERE src = 'meiji'
    GROUP BY year, gender, orth
    """)
    byyear = dd(lambda: dd(lambda: dd(int)))
    for year, gender, orth, freq in c:
        byyear[year][gender][orth] = freq  
    return byyear

def get_other(conn, meiji, src='hs', cutoff=100):
    """
    for each year in the meiji data
    get the same amount of data from the heisei database
    """

    byyear = dd(lambda: dd(lambda: dd(int)))
    c = conn.cursor()
    for year in meiji:
        for gender in meiji[year]:
            c.execute(f"""
            WITH ranked_names AS (
            SELECT orth, 
            COUNT(*) as frequency,
            RANK() OVER (ORDER BY COUNT(*) DESC) as rank
            FROM namae
            WHERE src = ? AND year = ? and gender = ?
            GROUP BY orth
            )
            SELECT orth, frequency
            FROM ranked_names
            WHERE rank <= ?;
            """, (src, year, gender, cutoff))
            for orth, freq in c:
                byyear[year][gender][orth] = freq

    return byyear

db_path = os.path.join(os.path.dirname(__file__), '../web/db/namae.db')
conn = sqlite3.connect(db_path)

data_m = get_meiji(conn)
#data_h = get_other(conn, data_m, src='hs')
#data_bc = get_other(conn, data_m, src='bc')


       

# Sample session with custom colors
sample_session = {
    'female_color': 'purple',
    'male_color': 'orange'
}
   
for src in ('hs', 'bc'):
    print(f"Similarity for {src}")
    data = get_other(conn, data_m, src=src)
    results = {'M':dict(), 'F':dict() }
    for  year in data:
        if year not in data_m:
            continue
        for gender in data_m[year]:
            results[gender][year] = _single_comparison(pd.Series(data_m[year][gender]),
                                                       pd.Series(data[year][gender]),
                                                       f'{year} {gender}')

    for gender in results:
        print(gender)
        print('year', 'overlap', 'JS divergence', 'EM distance', 'Correlation', 'Difference', 'P-value',
              sep= '\t')
        for year in results[gender]:
            r =  results[gender][year]
            #print(r)
            print(year,
                  r['common_names_count'],
                  r['js_divergence'],
                  r['earth_movers_distance'],
                  r['correlation'],
                  r['chi_square']['cramers_v'],
                  r['chi_square']['p_value'], sep='\t')
              
            
    # Create the plot
    filename = plot_gender_names_analysis(results, sample_session, output_filename=f'{src}_vs_meiji.png')
    print(f"Plot saved as: {filename}")
 
        
# # Quick overall comparison
# result = quick_overall_comparison(data_h, data_m)

# # Compare year by year
# yearly_results = compare_datasets(data_h, data_m, 'by_year')
# yearly_summary = create_comparison_summary(yearly_results)
# print(yearly_summary)

# # Compare by gender (across all years)
# gender_results = compare_datasets(data_h, data_m, 'by_gender')

# # Compare each year-gender combination separately
# detailed_results = compare_datasets(data_h, data_m, 'by_year_gender')

# # Custom comparison (e.g., compare 2020-2022 males in H vs 2021-2023 females in M)
# custom_results = compare_datasets(
#     data_h, data_m, 'custom',
#     years_h=[2020, 2021, 2022], genders_h=['M'],
#     years_m=[2021, 2022, 2023], genders_m=['F']
# )

# # Analyze trends over time
# trends, trend_summary = analyze_trends_over_time(data_h, data_m)

# # Plot results
# fig = plot_comparison_results(yearly_results, 'js_divergence')
# plt.show()
