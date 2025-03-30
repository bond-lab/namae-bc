from flask import session
import matplotlib.pyplot as plt
import numpy as np
import io

def create_gender_plot(years, male_counts, female_counts, db_name):
    # Create the figure and axis
    fig, ax = plt.subplots(figsize=(10, 6))

    # Retrieve colors from session or use default values
    female_color = session.get('female_color', 'purple')
    male_color = session.get('male_color', 'orange')

    # Plot men and women counts
    ax.bar(years, female_counts, color=female_color, label='Women', alpha=0.6)
    ax.bar(years, [-x for x in male_counts], color=male_color, label='Men', alpha=0.6)

    # Add numbers on top of each bar for both men and women
    for i, (female, male) in enumerate(zip(female_counts, male_counts)):
        ax.text(years[i], female - 72, str(female),
                ha='center', va='bottom', fontsize=10, color='white')
        ax.text(years[i], - male + 24, str(male),
                ha='center', va='bottom', fontsize=10, color='white')

    # Remove all spines and ticks for a minimalist look
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['bottom'].set_visible(False)

    ax.set_yticks([])  # Remove y-axis numbers
    ax.tick_params(left=False, bottom=False)

    # Add labels and title with subtle text styling
    ax.set_xlabel('Year', fontsize=12)
    ax.set_ylabel('Number of Names', fontsize=12)
    ax.set_title('Number of Names per Year, Divided by Gender', fontsize=14, weight='bold')

    # Add a legend with minimalist styling
    ax.legend(frameon=False)

    # Save the plot to a BytesIO object
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    
    return buf

    
def plot_multi_panel_trends(all_metrics, selected_metrics, title, confidence_intervals=None):
    """
    Plot multi-panel visualization of selected diversity measures over time.
    
    Parameters:
    -----------
    all_metrics : dict
        Dictionary containing metrics data for both genders
    selected_metrics : list
        List of metrics to plot
    title : str
        Title for the plot
    confidence_intervals : dict, optional
        Dictionary containing confidence intervals for metrics.
        Structure: {
            'M': {year: {metric: (lower_bound, upper_bound)}},
            'F': {year: {metric: (lower_bound, upper_bound)}}
        }
    """
    years = sorted(all_metrics['M'].keys())
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    
    for idx, metric in enumerate(selected_metrics):
        ax = axes[idx // 2, idx % 2]
        
        # Plot main lines
        boys_values = [all_metrics['M'][y][metric] for y in years]
        girls_values = [all_metrics['F'][y][metric] for y in years]
        
        ax.plot(years, boys_values, marker='o', linestyle='-', color='blue', label='Boys')
        ax.plot(years, girls_values, marker='s', linestyle='-', color='red', label='Girls')
        
        # Add confidence intervals as lines if provided
        if confidence_intervals is not None:
            if 'M' in confidence_intervals and metric in confidence_intervals['M'].get(years[0], {}):
                boys_lower = [confidence_intervals['M'][y][metric][0] for y in years]
                boys_upper = [confidence_intervals['M'][y][metric][1] for y in years]
                ax.plot(years, boys_lower, linestyle='--', color='blue', alpha=0.7, linewidth=1)
                ax.plot(years, boys_upper, linestyle='--', color='blue', alpha=0.7, linewidth=1)
            
            if 'F' in confidence_intervals and metric in confidence_intervals['F'].get(years[0], {}):
                girls_lower = [confidence_intervals['F'][y][metric][0] for y in years]
                girls_upper = [confidence_intervals['F'][y][metric][1] for y in years]
                ax.plot(years, girls_lower, linestyle='--', color='red', alpha=0.7, linewidth=1)
                ax.plot(years, girls_upper, linestyle='--', color='red', alpha=0.7, linewidth=1)
        
        ax.set_title(metric)
        ax.legend(frameon=False)
        ax.grid(False)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.spines['bottom'].set_visible(False)
    
    plt.tight_layout()
    plt.suptitle(title)
    
    # Save to BytesIO and return
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=300)
    buf.seek(0)
    plt.close(fig)
    return buf


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
