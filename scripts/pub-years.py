import os
from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from matplotlib.patches import Rectangle
import matplotlib.patches as mpatches

def create_japanese_names_chart(data_list, output_filename='japanese_names_coverage.png',
                                figsize=None, dpi=None, use_log_scale=False, title=False,
                                formats=('png',), bw=False):
    """
    Create a publication-ready chart showing Japanese names data coverage vs births.
    
    Parameters:
m    -----------
    data_list : list of dicts
        Data in format: [{'src': 'bc', 'year': 2008, 'gender': 'F', 'count': 588}, ...]
        Expected sources: 'bc' (Baby Calendar), 'hs' (Heisei), 'totals' (Meiji), 'births' (Total births)
    output_filename : str
        Output PNG filename
    figsize : tuple
        Figure size in inches (width, height)
    dpi : int
        Resolution for PNG output
    """
    
    # Convert to DataFrame and pivot
    df = pd.DataFrame(data_list)

    pivot_data = {}
    for _, row in df.iterrows():
        key = (row['year'], row['gender'])
        if key not in pivot_data:
            pivot_data[key] = {'year': row['year'], 'gender': row['gender'],
                               'births': 0, 'hs': 0, 'totals': 0, 'bc': 0}
        source = 'births' if row['src'] == 'births' else row['src']
        pivot_data[key][source] = row['count']

    plot_df = pd.DataFrame(list(pivot_data.values()))
    name_data = plot_df[(plot_df['hs'] > 0) | (plot_df['totals'] > 0) | (plot_df['bc'] > 0)]
    female_data = name_data[name_data['gender'] == 'F'].sort_values('year')
    male_data   = name_data[name_data['gender'] == 'M'].sort_values('year')

    if figsize is None:
        figsize = (14, 10)
    if dpi is None:
        import matplotlib.pyplot as _plt
        dpi = _plt.rcParams.get('savefig.dpi', 300)

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=figsize, sharex=True)

    if bw:
        from bw_style import BW_COVERAGE_COLORS
        colors = BW_COVERAGE_COLORS
        alphas = {'births': 0.6, 'hs': 1.0, 'totals': 1.0, 'bc': 1.0}
    else:
        colors = {
            'births': '#b0b0b0',
            'hs':     '#3498db',
            'totals': '#e74c3c',
            'bc':     '#2ecc71',
        }
        alphas = {'births': 0.4, 'hs': 0.85, 'totals': 0.80, 'bc': 0.90}

    # Overlap order: largest background → smallest foreground so smaller datasets stay visible
    _src_order = [('births', 'Total Births', 1),
                  ('hs',     'Heisei',        2),
                  ('totals', 'Meiji',         3),
                  ('bc',     'Baby Calendar', 4)]

    def plot_gender_data(ax, data, gender_label):
        years  = data['year'].values
        x_pos  = np.arange(len(years))

        for src, lbl, zorder in _src_order:
            if src not in data.columns:
                continue
            mask = data[src] > 0
            if not mask.any():
                continue
            ax.bar(x_pos[mask], data.loc[mask, src],
                   width=0.7, color=colors[src], alpha=alphas[src],
                   label=lbl, zorder=zorder)

        ax.set_ylabel(f'{gender_label}\n(records)')
        ax.grid(True, alpha=0.3, axis='y')
        ax.set_xticks(x_pos[::2])
        ax.set_xticklabels(years[::2], rotation=45, ha='right')
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{int(x):,}'))
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)

        if use_log_scale:
            ax.set_yscale('log')
            src_cols = [c for c in ('hs', 'totals', 'bc') if c in data.columns]
            pos = data[src_cols].replace(0, np.nan)
            min_val = pos.min(skipna=True).min()
            max_val = data[['births'] + src_cols].max().max()
            ax.set_ylim(max(1, min_val * 0.5), max_val * 2)
        else:
            src_cols = [c for c in ('births', 'hs', 'totals', 'bc') if c in data.columns]
            ax.set_ylim(0, data[src_cols].max().max() * 1.05)

    plot_gender_data(ax1, female_data, 'Girls')
    plot_gender_data(ax2, male_data,   'Boys')

    legend_elements = [
        mpatches.Patch(facecolor=colors['births'], alpha=alphas['births'],
                       label='Total Births'),
        mpatches.Patch(facecolor=colors['totals'], alpha=alphas['totals'],
                       label='Meiji Data'),
        mpatches.Patch(facecolor=colors['hs'],     alpha=alphas['hs'],
                       label='Heisei Data'),
        mpatches.Patch(facecolor=colors['bc'],     alpha=alphas['bc'],
                       label='Baby Calendar Data'),
    ]
    ncol = 2 if figsize[0] < 6 else 4
    fig.legend(handles=legend_elements, loc='lower center', bbox_to_anchor=(0.5, 0.0),
               ncol=ncol, frameon=False)
    
    ax2.set_xlabel('Year')
    if title:
        plt.suptitle('Japanese Names Dataset Coverage Compared to Total Births',
                     fontweight='bold')

    plt.tight_layout()
    plt.subplots_adjust(bottom=0.18)

    stem = str(Path(str(output_filename)).with_suffix(''))
    for fmt in formats:
        plt.savefig(f'{stem}.{fmt}', dpi=dpi, bbox_inches='tight',
                    facecolor='white', edgecolor='none')
    
    # Print summary statistics for the book
    print(f"\nDataset Coverage Summary:")
    print(f"{'Source':<15} {'Years':<12} {'Peak Sample':<12} {'Avg Sample':<12}")
    print("-" * 55)
    
    for source in ['hs', 'totals', 'bc']:
        source_data = plot_df[plot_df[source] > 0]
        if len(source_data) > 0:
            years_range = f"{source_data['year'].min()}-{source_data['year'].max()}"
            peak_sample = source_data[source].max()
            avg_sample = int(source_data[source].mean())
            source_name = {'hs': 'Heisei', 'totals': 'Meiji', 'bc': 'Baby Calendar'}[source]
            print(f"{source_name:<15} {years_range:<12} {peak_sample:<12,} {avg_sample:<12,}")

def get_data(db_path):
    """
    Fetch data from SQLite database and return in format needed for charting.
    
    Parameters:
    -----------
    db_path : str
        Path to the SQLite database file
        
    Returns:
    --------
    list of dicts
        Data in format: [{'src': 'bc', 'year': 2008, 'gender': 'F', 'count': 588}, ...]
    """
    import sqlite3
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Execute query
    query = "SELECT * FROM name_year_cache;"
    cursor.execute(query)
    
    # Get column names
    columns = [description[0] for description in cursor.description]
    
    # Fetch all data and convert to list of dicts
    rows = cursor.fetchall()
    data = []
    
    for row in rows:
        row_dict = dict(zip(columns, row))
        # Convert to the expected format
        data.append({
            'src': row_dict['src'],
            'year': int(row_dict['year']),
            'gender': row_dict['gender'],
            'count': int(row_dict['count'])
            # Note: ignoring 'dtype' as mentioned it's always the same
        })
    
    # Close connection
    conn.close()
    
    print(f"Loaded {len(data)} records from database")
    print(f"Sources found: {sorted(set(d['src'] for d in data))}")
    print(f"Year range: {min(d['year'] for d in data)} - {max(d['year'] for d in data)}")
    
    return data

_default_db_path = os.path.join(os.path.dirname(__file__), '../web/db/namae.db')
_default_plot_dir = os.path.join(os.path.dirname(__file__), '../web/static/plot')


def main(db_path=_default_db_path, plot_dir=_default_plot_dir, formats=('png',)):
    """Regenerate book overview coverage charts."""
    data = get_data(db_path)
    create_japanese_names_chart(
        data, os.path.join(plot_dir, 'book_overview.png'), formats=formats)
    create_japanese_names_chart(
        data, os.path.join(plot_dir, 'book_overview_log.png'),
        use_log_scale=True, formats=formats)


if __name__ == "__main__":
    main()
    
