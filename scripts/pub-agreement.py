import numpy as np
import pandas as pd
from pathlib import Path
from scipy.spatial.distance import jensenshannon
from scipy.stats import wasserstein_distance, chi2_contingency
from scipy.interpolate import PchipInterpolator
import matplotlib.pyplot as plt
import sqlite3
import os
from collections import defaultdict as dd
import json

from visualize import setup_tufte_style, save_plot


def _single_comparison(freq_h, freq_m, title):
    """
    Perform a single comparison between two frequency distributions.
    
    This function compares two pandas Series containing name frequencies and calculates
    various similarity metrics including Jensen-Shannon divergence, Earth Mover's distance,
    correlation, and chi-square test statistics.
    
    Parameters:
    -----------
    freq_h : pandas.Series
        Frequency distribution for dataset H (names as index, frequencies as values)
    freq_m : pandas.Series
        Frequency distribution for dataset M (names as index, frequencies as values)
    title : str
        Title for the comparison (used in results)
    
    Returns:
    --------
    dict
        Dictionary containing comparison results with keys:
        - 'title': comparison title
        - 'js_divergence': Jensen-Shannon divergence (0-1, lower = more similar)
        - 'earth_movers_distance': Earth Mover's distance (lower = more similar)
        - 'chi_square': dict with chi-square test results
        - 'correlation': correlation coefficient between distributions
        - 'common_names_count': number of names in both datasets
        - 'h_coverage': proportion of H dataset covered by common names
        - 'm_coverage': proportion of M dataset covered by common names
        - 'h_dist': normalized frequency distribution for H
        - 'm_dist': normalized frequency distribution for M
        - 'common_names': list of common names
    """
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
    """
    Interpret chi-square test results in human-readable format.
    
    Parameters:
    -----------
    chi2 : float
        Chi-square test statistic
    p : float
        P-value from chi-square test
    cramers_v : float
        Cramer's V effect size measure
    
    Returns:
    --------
    str
        Human-readable interpretation of the statistical results
    """
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


def plot_gender_names_analysis(data_dict, session=None, output_filename='gender_names_analysis.png', figsize=(14, 6), formats=('png',), bw=False):
    """
    Create a two-subplot visualization of common names count and JS divergence by gender over time.
    
    This function generates a publication-ready plot showing how name ranking agreement
    changes over time, separated by gender. It creates two subplots: one showing the
    number of common names between datasets, and another showing Jensen-Shannon divergence.
    
    Parameters:
    -----------
    data_dict : dict
        Dictionary with structure: {gender: {year: {'common_names_count': int, 'js_divergence': float}}}
        where gender is 'M' or 'F' and year is typically 2006-2009
    session : dict, optional
        Session dictionary containing color preferences with keys 'female_color' and 'male_color'
        Default colors are 'purple' for female and 'orange' for male
    output_filename : str, optional
        Name of the output PNG file (default: 'gender_names_analysis.png')
    figsize : tuple, optional
        Figure size as (width, height) in inches (default: (14, 6))
    
    Returns:
    --------
    str
        Path to the saved PNG file
    """
    setup_tufte_style()
    
    if bw:
        from bw_style import BW_M, BW_F
        male_color = female_color = 'black'
        male_line  = dict(color='black', linestyle=BW_M['linestyle'],
                          marker=BW_M['marker'], fillstyle='none')
        female_line = dict(color='black', linestyle=BW_F['linestyle'],
                           marker=BW_F['marker'], fillstyle='full')
    else:
        female_color = session.get('female_color', 'purple') if session else 'purple'
        male_color   = session.get('male_color',   'orange') if session else 'orange'
        male_line   = dict(color=male_color,   linestyle='-', marker='o', fillstyle='full')
        female_line = dict(color=female_color, linestyle='-', marker='o', fillstyle='full')

    # Extract years (should be 2006-2009)
    years = list(data_dict['F'].keys())

    male_common_names   = [data_dict['M'][year]['common_names_count'] for year in years]
    male_js_divergence  = [data_dict['M'][year]['js_divergence']      for year in years]
    female_common_names = [data_dict['F'][year]['common_names_count'] for year in years]
    female_js_divergence= [data_dict['F'][year]['js_divergence']      for year in years]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize)

    def _smooth(ax, xs, ys, color, label, ls, mkr, fc):
        if len(xs) >= 3:
            interp = PchipInterpolator(xs, ys)
            x_fine = np.linspace(xs[0], xs[-1], 300)
            ax.plot(x_fine, interp(x_fine), color=color, linewidth=3,
                    linestyle=ls, label=label)
        else:
            ax.plot(xs, ys, color=color, linewidth=3, linestyle=ls, label=label)
        ax.scatter(xs, ys, s=50, zorder=5, marker=mkr,
                   facecolors=fc, edgecolors=color, linewidths=2)

    # Plot 1: Common Names Count
    _smooth(ax1, years, male_common_names,   male_color,   'Boys',
            male_line['linestyle'],   male_line['marker'],
            'none' if male_line['fillstyle'] == 'none' else male_color)
    _smooth(ax1, years, female_common_names, female_color, 'Girls',
            female_line['linestyle'], female_line['marker'], female_color)
    
    ax1.set_title('Common Names Count Over Time', fontsize=14, fontweight='bold', pad=25)
    ax1.set_xlabel('Year', fontsize=12)
    ax1.set_ylabel('Common Names Count', fontsize=12)
    ax1.legend(fontsize=11, frameon=True, fancybox=True, shadow=True)
    ax1.grid(True, alpha=0.3, linestyle='--')
    ax1.set_xticks(years)
    ax1.set_ylim(bottom=0)
    ax1.spines['top'].set_visible(False)
    ax1.spines['right'].set_visible(False)
    
    # Plot 2: JS Divergence
    _smooth(ax2, years, male_js_divergence,   male_color,   'Boys',
            male_line['linestyle'],   male_line['marker'],
            'none' if male_line['fillstyle'] == 'none' else male_color)
    _smooth(ax2, years, female_js_divergence, female_color, 'Girls',
            female_line['linestyle'], female_line['marker'], female_color)
    
    ax2.set_title('JS Divergence Over Time', fontsize=14, fontweight='bold', pad=25)
    ax2.set_xlabel('Year', fontsize=12)
    ax2.set_ylabel('JS Divergence', fontsize=12)
    ax2.legend(fontsize=11, frameon=True, fancybox=True, shadow=True)
    ax2.grid(True, alpha=0.3, linestyle='--')
    ax2.set_xticks(years)
    ax2.set_ylim(bottom=0)
    ax2.spines['top'].set_visible(False)
    ax2.spines['right'].set_visible(False)
    
    plt.tight_layout()
    plt.subplots_adjust(top=0.85)
    stem = str(Path(str(output_filename)).with_suffix(''))
    for fmt in formats:
        plt.savefig(f'{stem}.{fmt}', dpi=300, bbox_inches='tight')
    plt.close()

    return output_filename


def get_meiji(conn):
    """
    Retrieve Meiji Yasuda baby name data from the database.
    
    This function queries the database for all name frequency data from the Meiji Yasuda
    insurance company dataset, organizing it by year, gender, and name.
    
    Parameters:
    -----------
    conn : sqlite3.Connection
        Database connection object
    
    Returns:
    --------
    defaultdict
        Nested dictionary with structure: {year: {gender: {name: frequency}}}
        where frequency is the count of occurrences for each name
    """
    c = conn.cursor()
    c.execute(f"""
    SELECT year, gender, orth, freq
    FROM nrank
    WHERE src = 'meiji'
    AND orth IS NOT NULL
    AND freq IS NOT NULL
    ORDER by year, rank
    """)
    byyear = dd(lambda: dd(lambda: dd(int)))
    for year, gender, orth, freq in c:
        byyear[year][gender][orth] = freq  
    return byyear


def get_other(conn, meiji, src='hs', cutoff=100):
    """
    Retrieve name data from other sources, matching the years and genders in Meiji data.
    
    This function gets the top N most frequent names from a specified source for each
    year and gender combination that exists in the Meiji dataset. This ensures
    comparable datasets for analysis.
    
    Parameters:
    -----------
    conn : sqlite3.Connection
        Database connection object
    meiji : defaultdict
        Meiji data structure from get_meiji() used to determine which years/genders to query
    src : str, optional
        Source identifier ('hs' for Heisei, 'bc' for Birth Certificate, etc.)
        Default is 'hs'
    cutoff : int, optional
        Maximum number of top names to retrieve per year/gender combination
        Default is 100
    
    Returns:
    --------
    defaultdict
        Nested dictionary with structure: {year: {gender: {name: frequency}}}
        containing the top `cutoff` names for each year/gender combination
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


_default_db_path = os.path.join(os.path.dirname(__file__), '../web/db/namae.db')
_default_plot_dir = os.path.join(os.path.dirname(__file__), '../web/static/plot')


def main(db_path=_default_db_path, plot_dir=_default_plot_dir, formats=('png',)):
    """Regenerate Meiji vs Heisei/BC agreement plots."""
    conn = sqlite3.connect(db_path)

    data_m = get_meiji(conn)
    sample_session = {'female_color': 'purple', 'male_color': 'orange'}
    tables = dd(dict)

    for src in ('hs', 'bc'):
        print(f"Similarity for {src}")
        data = get_other(conn, data_m, src=src)
        results = {'M': dict(), 'F': dict()}

        for year in data:
            if year not in data_m:
                continue
            for gender in data_m[year]:
                results[gender][year] = _single_comparison(
                    pd.Series(data_m[year][gender]),
                    pd.Series(data[year][gender]),
                    f'{year} {gender}'
                )

        for gender in results:
            data_summary = {
                'caption': f"Ranking Agreement between Meiji Yasuda and {src}",
                'headers': ['Year', 'Overlap', 'JS divergence', 'EM distance',
                            'Correlation', 'Difference', 'P-value'],
                'rows': [],
            }
            for year in results[gender]:
                r = results[gender][year]
                data_summary['rows'].append([
                    year, r['common_names_count'], r['js_divergence'],
                    r['earth_movers_distance'], r['correlation'],
                    r['chi_square']['cramers_v'], r['chi_square']['p_value']
                ])
        tables['ch04'][f'meiji_vs_{src}'] = data_summary

        figpath = os.path.join(plot_dir, f'book_meiji_vs_{src}.png')
        plot_gender_names_analysis(results, sample_session,
                                   output_filename=figpath, formats=formats)
        print(f"Plot saved: {figpath}")

    conn.close()

    data_path = os.path.join(os.path.dirname(__file__), '../web/static/data/book_tables.json')
    try:
        with open(data_path) as f:
            old_tables = json.load(f)
        old_tables.update(tables)
        tables = old_tables
    except FileNotFoundError:
        pass
    with open(data_path, 'w') as out:
        json.dump(tables, out)


if __name__ == "__main__":
    main()
