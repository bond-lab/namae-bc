import matplotlib.pyplot as plt
import argparse
import os

def plot_kanji_usage(output_path=None):
    # Kanji data
    kanji = {
        1947:(1850, 0),
        1951:(1850, 92),
        1976:(1850, 120),
        1981:(1945, 166),
        1990:(1945, 284),
        1997:(1945, 285),
        2004:(1945, 983),
        2009:(1945, 985),
        2010:(2136, 861),
        2015:(2136, 862),
        2017:(2136, 863),
    }

    # Extract data
    years = list(kanji.keys())
    name_kanji = [k[1] for k in kanji.values()]
    total_kanji = [sum(k) for k in kanji.values()]

    # Create figure with Tufte-inspired design
    plt.figure(figsize=(10, 6), facecolor='white')

    # Plot lines with minimal styling
    plt.plot(years, name_kanji, color='#1f77b4', linewidth=2, label='Name-only Kanji')
    plt.plot(years, total_kanji, color='#d62728', linewidth=2, linestyle='--', label='Total Kanji')

    # Minimalist design elements
    plt.title('Number of Kanji allowed in Names', fontsize=14, fontweight='bold')
    plt.xlabel('Year', fontsize=10)
    plt.ylabel('Number of Kanji', fontsize=10)

    # Sparse grid with light lines
    plt.grid(True, linestyle=':', color='lightgray', linewidth=0.5)

    # Remove chart junk
    plt.gca().spines['top'].set_visible(False)
    plt.gca().spines['right'].set_visible(False)

    # Annotations for key points
    for i, year in enumerate(years):
        if year in  [1947, 1951, 1976, 1990, 1997, 2004, 2010, 2017]:
            # Annotate name-only kanji
            plt.annotate(f'{name_kanji[i]}', 
                         (year, name_kanji[i]), 
                         xytext=(5, 5), 
                         textcoords='offset points',
                         fontsize=8,
                         color='#1f77b4')
            
            # Annotate total kanji
            plt.annotate(f'{total_kanji[i]}', 
                         (year, total_kanji[i]), 
                         xytext=(5, -10), 
                         textcoords='offset points',
                         fontsize=8,
                         color='#d62728')

    plt.legend(frameon=False)
    plt.tight_layout()

    # Save or display
    if output_path:
        # Ensure directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Save as PNG
         # --- Save without title (PNG) ---
        plt.title("")  # remove title
        book_name = os.path.join(os.path.dirname(output_path),
                                 f"book_{os.path.basename(output_path)}")
        plt.savefig(f"{book_name}.png", dpi=300)
        
        # Save as SVG
        plt.savefig(f'{output_path}.svg')
        
        plt.close()
    else:
        plt.show()

def main():
    parser = argparse.ArgumentParser(description='Plot Kanji Usage Over Time')
    parser.add_argument('-o', '--output', 
                        help='Output file path (without extension)', 
                        default=None)
    args = parser.parse_args()
    
    plot_kanji_usage(args.output)

if __name__ == '__main__':
    main()
