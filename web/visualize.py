from flask import session
import matplotlib.pyplot as plt
import matplotlib.style as style
from cycler import cycler
import numpy as np
import io


def plot_multi_panel_trends(all_metrics, selected_metrics, title,
                            filename, confidence_intervals=None):
    """
    Plot multi-panel visualization of selected diversity measures over time.
    Handles missing metrics for certain years (e.g., newness for first year).
    
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
        Dictionary containing confidence intervals for metrics.
        Structure: {
            'M': {year: {metric: (lower_bound, upper_bound)}},
            'F': {year: {metric: (lower_bound, upper_bound)}}
        }
    """
    # Get all years from both genders
    all_years = sorted(set(list(all_metrics['M'].keys()) + list(all_metrics['F'].keys())))
    
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    
    for idx, metric in enumerate(selected_metrics):
        ax = axes[idx // 2, idx % 2]
        
        # For each gender, collect valid data points (years where the metric exists)
        for gender, color, marker, label in [
            ('M', 'blue', 'o', 'Boys'), 
            ('F', 'red', 's', 'Girls')
        ]:
            # Get years where this metric exists for this gender
            valid_years = []
            valid_values = []
            
            for year in all_years:
                # Check if year exists in metrics and if the metric exists for that year
                if year in all_metrics[gender] and metric in all_metrics[gender][year]:
                    valid_years.append(year)
                    valid_values.append(all_metrics[gender][year][metric])
            
            # Only plot if we have valid data
            if valid_years and valid_values:
                ax.plot(valid_years, valid_values, marker=marker, linestyle='-', 
                        color=color, label=label)
                
                # Add confidence intervals if available
                if confidence_intervals is not None:
                    # Check if confidence intervals exist for this metric and gender
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
        
        ax.set_title(metric)
        ax.legend(frameon=False)
        ax.grid(False)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.spines['bottom'].set_visible(False)
    
    plt.tight_layout()
    plt.suptitle(title)
    
    # Save plot to a file
    plt.savefig(filename, dpi=300)
    plt.close(fig)    


 

def setup_tufte_style():
    """Apply Tufte-inspired styling to matplotlib"""
    
    # Tufte color palette (muted)
    tufte_colors = ['#4C72B0', '#55A868', '#C44E52', '#8172B2', 
                   '#CCB974', '#64B5CD', '#DA8BC8']
    
    plt.rcParams.update({
        # Figure
        'figure.facecolor': 'white',
        'figure.edgecolor': 'none',
        'figure.figsize': (10, 6),
        
        # Axes
        'axes.facecolor': 'white',
        'axes.edgecolor': 'none',
        'axes.linewidth': 0,
        'axes.spines.left': False,
        'axes.spines.bottom': False,
        'axes.spines.top': False,
        'axes.spines.right': False,
        'axes.grid': False,
        'axes.prop_cycle': cycler('color', tufte_colors),
        
        # Ticks
        'xtick.bottom': False,
        'xtick.top': False,
        'ytick.left': False,  
        'ytick.right': False,
        
        # Font
        'font.size': 11,
        'axes.labelsize': 12,
        'axes.titlesize': 14,
        'legend.fontsize': 10,
        
        # Lines
        'lines.linewidth': 2,
        'lines.solid_capstyle': 'round',
    })

def add_minimal_labels(ax, show_values=True):
    """Add minimal labels directly to data points (Tufte style)"""
    if show_values:
        # Remove traditional axes labels and add direct labeling
        ax.set_xlabel('')
        ax.set_ylabel('')
        
        # You can add custom direct labeling here
        # This depends on your specific plot type

def save_plot(filename, dpi=300, bbox_inches='tight'):
    """Consistent save settings"""
    plt.savefig(f'static/plot/{filename}', 
               dpi=dpi, 
               bbox_inches=bbox_inches,
               facecolor='white',
               edgecolor='none')
    
# def create_gender_plot(years, male_counts, female_counts, db_name):
#     # Create the figure and axis
#     fig, ax = plt.subplots(figsize=(12, 6))

#     # Retrieve colors from session or use default values
#     female_color = session.get('female_color', 'purple')
#     male_color = session.get('male_color', 'orange')

#     # Plot men and women counts
#     ax.bar(years, female_counts, color=female_color, label='Women', alpha=0.6)
#     ax.bar(years, [-x for x in male_counts], color=male_color, label='Men', alpha=0.6)

#     # Add numbers on top of each bar for both men and women
#     for i, (female, male) in enumerate(zip(female_counts, male_counts)):
#         ax.text(years[i], female - 72, str(female),
#                 ha='center', va='bottom', fontsize=10,color='white')
#         ax.text(years[i], - male + 24, str(male),
#                 ha='center', va='bottom', fontsize=10, color='white')

#     # Remove all spines and ticks for a minimalist look
#     ax.spines['top'].set_visible(False)
#     ax.spines['right'].set_visible(False)
#     ax.spines['left'].set_visible(False)
#     ax.spines['bottom'].set_visible(False)

#     ax.set_yticks([])  # Remove y-axis numbers
#     ax.tick_params(left=False, bottom=False)

#     # Add labels and title with subtle text styling
#     ax.set_xlabel('Year', fontsize=12)
#     ax.set_ylabel('Number of Names', fontsize=12)
#     ax.set_title(f'Number of Names per Year, Divided by Gender ({db_name})',
#                  fontsize=14, weight='bold')

#     # Add a legend with minimalist styling
#     ax.legend(frameon=False)

#     # Save the plot to a BytesIO object
#     buf = io.BytesIO()
#     plt.savefig(buf, format='png')
#     buf.seek(0)
    
#     return buf
