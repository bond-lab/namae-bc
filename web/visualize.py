from flask import session
import matplotlib.pyplot as plt
import numpy as np
import io

def create_gender_plot(years, male_counts, female_counts, db_name):
    # Create the figure and axis
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Retrieve colors from session or use default values
    female_color = session.get('female_color', 'purple')
    male_color = session.get('male_color', 'orange')
    
    # Option 1: Show values only for selected years when there are too many
    if len(years) > 10:
        # Create simplified x-axis with fewer labels
        step = max(1, len(years) // 8)  # Show approximately 8 labels
        ax.set_xticks([years[i] for i in range(0, len(years), step)])
        
        # Plot all data
        bars_women = ax.bar(years, female_counts, color=female_color, label='Women', alpha=0.6)
        bars_men = ax.bar(years, [-x for x in male_counts], color=male_color, label='Men', alpha=0.6)
        
        # Add numbers only for selected years
        for i in range(0, len(years), step):
            # Add value on top of women bars - moved further away, no border
            ax.text(years[i], female_counts[i] + 20, str(female_counts[i]),
                    ha='center', va='bottom', fontsize=9)
            
            # Add value on bottom of men bars - moved further away, no border
            ax.text(years[i], -male_counts[i] - 20, str(male_counts[i]),
                    ha='center', va='top', fontsize=9)
    else:
        # For fewer years, show all values
        bars_women = ax.bar(years, female_counts, color=female_color, label='Women', alpha=0.6)
        bars_men = ax.bar(years, [-x for x in male_counts], color=male_color, label='Men', alpha=0.6)
        
        for i, (female, male) in enumerate(zip(female_counts, male_counts)):
            # Text moved further from bars with no border, using gender colors
            ax.text(years[i], female + 15, str(female),
                    ha='center', va='bottom', fontsize=10)
            
            ax.text(years[i], -male - 15, str(male),
                    ha='center', va='top', fontsize=10)
    
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
    ax.set_title(f'Number of Names per Year, Divided by Gender ({db_name})',
                 fontsize=14)
    
    # Add a legend with minimalist styling
    ax.legend(frameon=False)
    
    # Optional: Add tooltip functionality with mpld3 for interactive viewing
    # Uncomment if mpld3 is available
    # import mpld3
    # tooltip = mpld3.plugins.PointLabelTooltip(bars_women, labels=[f"{y}: {c}" for y, c in zip(years, female_counts)])
    # mpld3.plugins.connect(fig, tooltip)
    
    # Save the plot to a BytesIO object
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    
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
