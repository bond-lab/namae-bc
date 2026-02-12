import os
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from matplotlib.patches import Rectangle
import matplotlib.patches as mpatches

def create_japanese_names_chart(data_list, output_filename='japanese_names_coverage.png', 
                                figsize=(14, 10), dpi=300, use_log_scale=False, title=False):
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
    
    # Create pivot table
    pivot_data = {}
    for _, row in df.iterrows():
        key = (row['year'], row['gender'])
        if key not in pivot_data:
            pivot_data[key] = {'year': row['year'], 'gender': row['gender'], 
                              'births': 0, 'hs': 0, 'totals': 0, 'bc': 0}
        
        source = 'births' if row['src'] == 'births' else row['src']
        pivot_data[key][source] = row['count']
    
    # Convert back to DataFrame
    plot_df = pd.DataFrame(list(pivot_data.values()))
    
    # Filter to years with name data (not just births)
    name_data = plot_df[(plot_df['hs'] > 0) | (plot_df['totals'] > 0) | (plot_df['bc'] > 0)]
    
    # Separate by gender
    female_data = name_data[name_data['gender'] == 'F'].sort_values('year')
    male_data = name_data[name_data['gender'] == 'M'].sort_values('year')
    
    # Create figure with subplots
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=figsize, sharex=True)
    
    # Define colors and patterns
    colors = {
        'births': '#808080',     # Gray for births baseline
        'hs': '#3498db',         # Blue for Heisei
        'totals': '#e74c3c',      # Red for Meiji  
        'bc': '#2ecc71'          # Green for Baby Calendar
    }
    
    # Bar width and positioning
    bar_width = 0.6
    
    def plot_gender_data(ax, data, gender_label):
        years = data['year'].values
        x_pos = np.arange(len(years))
        
        # Plot births as background bars (wider, more transparent)
        births_bars = ax.bar(x_pos, data['births'], width=bar_width + 0.2, 
                           color=colors['births'], alpha=0.4, 
                           label='Total Births', zorder=1)
        
        # Plot name data sources (narrower bars, more opaque)
        hs_mask = data['hs'] > 0
        meiji_mask = data['totals'] > 0
        bc_mask = data['bc'] > 0
        
        if hs_mask.any():
            hs_bars = ax.bar(x_pos[hs_mask], data.loc[hs_mask, 'hs'], 
                           width=bar_width, color=colors['hs'], alpha=0.8,
                           hatch='///', label='Heisei Data', zorder=3)
        
        if meiji_mask.any():
            meiji_bars = ax.bar(x_pos[meiji_mask], data.loc[meiji_mask, 'totals'], 
                              width=bar_width, color=colors['totals'], alpha=0.8,
                              hatch='\\\\\\', label='Meiji Data', zorder=2)
        
        if bc_mask.any():
            bc_bars = ax.bar(x_pos[bc_mask], data.loc[bc_mask, 'bc'], 
                           width=bar_width, color=colors['bc'], alpha=0.8,
                           hatch='...', label='Baby Calendar Data', zorder=4)
        
        # Formatting
        ax.set_title(f'{gender_label} Names Data Coverage vs. Total Births', 
                    fontsize=14, fontweight='bold', pad=20)
        ax.set_ylabel('Number of Records', fontsize=12)
        ax.grid(True, alpha=0.3, axis='y')
        
        # Set x-axis
        ax.set_xticks(x_pos[::2])  # Show every other year to avoid crowding
        ax.set_xticklabels(years[::2], rotation=45, ha='right')
        
        # Format y-axis with commas
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{int(x):,}'))

        if use_log_scale:
            ax.set_yscale('log')
            # log scale limits
            min_val = min(data[data[['hs', 'totals', 'bc']].gt(0).any(axis=1)][['hs', 'totals', 'bc']].replace(0, np.nan).min(skipna=True))
            max_val = max(data[['births', 'hs', 'totals', 'bc']].max())
            ax.set_ylim(max(1, min_val * 0.5), max_val * 2)
        else:
            # linear scale limits
            max_val = max(data[['births', 'hs', 'totals', 'bc']].max())
            ax.set_ylim(0, max_val * 1.05)
        
        return ax
    
    # Plot both genders
    plot_gender_data(ax1, female_data, 'Female')
    plot_gender_data(ax2, male_data, 'Male')
    
    # Create custom legend
    legend_elements = [
        mpatches.Patch(color=colors['births'], alpha=0.4, label='Total Births'),
        mpatches.Patch(color=colors['hs'], hatch='///', alpha=0.8, label='Heisei Data'),
        mpatches.Patch(color=colors['totals'], hatch='\\\\\\', alpha=0.8, label='Meiji Data'),
        mpatches.Patch(color=colors['bc'], hatch='...', alpha=0.8, label='Baby Calendar Data')
    ]
    
    # Add legend to the figure
    fig.legend(handles=legend_elements, loc='upper center', bbox_to_anchor=(0.5, 0.95), 
              ncol=4, fontsize=11, frameon=True, fancybox=True, shadow=True)
    
    # Overall formatting
    ax2.set_xlabel('Year', fontsize=12)
    if title:
        plt.suptitle('Japanese Names Dataset Coverage Compared to Total Births', 
                     fontsize=16, fontweight='bold', y=0.98)
    
    # Adjust layout to prevent overlap
    plt.tight_layout()
    plt.subplots_adjust(top=0.92, bottom=0.1)
    
    # Save as high-quality PNG
    plt.savefig(output_filename, dpi=dpi, bbox_inches='tight', 
               facecolor='white', edgecolor='none')
    #plt.show()
    
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

# Example usage:
if __name__ == "__main__":
    # Method 1: Load from database
    db_path = os.path.join(os.path.dirname(__file__), '../web/db/namae.db')
    data = get_data(db_path)
    outdir =  os.path.join(os.path.dirname(__file__), '../web/static/plot')

    figpath = os.path.join(outdir, 'book_overview.png')
    create_japanese_names_chart(data, figpath)

    figpath = os.path.join(outdir, 'book_overview_log.png')
    create_japanese_names_chart(data, figpath,
                                use_log_scale=True)
    
