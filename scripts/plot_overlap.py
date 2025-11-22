#!/usr/bin/env python3
"""
Name Overlap Analysis Script

Calculates pronunciation/orthography overlap between male and female names
by year and source, saves results as JSON, and creates visualization graphs.

Usage: python overlap_analysis.py <database_file>
"""

import sqlite3
import json
import argparse
import matplotlib.pyplot as plt
from collections import defaultdict as dd
import pandas as pd
from pathlib import Path

def get_overlap_details(db_path, src_filter, data_type, n_top=50):
    """
    Get detailed overlap data showing actual names for each year.
    
    Args:
        db_path: Path to SQLite database
        src_filter: Source filter ('bc', 'meiji', etc.)
        data_type: 'pron' for pronunciation, 'orth' for orthography
        n_top: Number of top names to consider (default 50)
    
    Returns:
        Dict: {year: [list of overlap details]}
    """
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    if data_type == 'pron':
        field_name = 'pron'
        null_check = 'AND m.pron IS NOT NULL AND f.pron IS NOT NULL'
        select_field = 'm.pron'
    else:  # orth
        field_name = 'orth'
        null_check = 'AND m.orth IS NOT NULL AND f.orth IS NOT NULL'
        select_field = 'm.orth'
    
#     # Get years that have at least n_top names for both genders
#     years_query = f"""
# SELECT year
# FROM (
#   SELECT
#       year,
#       gender,
#       COUNT(DISTINCT CASE WHEN nrank <= ? THEN nrank END) AS n_le_top
#   FROM nrank
#   WHERE src = ?
#     AND {field_name} IS NOT NULL
#   GROUP BY year, gender
# ) AS g
# GROUP BY year
# HAVING COUNT(CASE WHEN n_le_top = ? THEN 1 END) = 2
# ORDER BY year;
#     """
    
#     cursor = conn.execute(years_query, (n_top, src_filter, n_top))
#     all_years = [row[0] for row in cursor.fetchall()]
    
    # Get detailed overlap data
    query = f"""
    SELECT 
      m.year,
      m.{field_name} AS overlap_value,
      m.freq AS male_freq,
      f.freq AS female_freq,
      (m.freq + f.freq) AS weighted_overlap
    FROM nrank m
    INNER JOIN nrank f ON f.src = m.src 
                      AND f.year = m.year
                      AND f.gender = 'F'
                      AND m.gender = 'M'
                      AND f.{field_name} = m.{field_name}
    WHERE m.rank <= ?
      AND f.rank <= ?
      AND m.src = ?
      {null_check}
    ORDER BY m.year, (m.freq + f.freq) DESC;
    """
    
    c.execute(query, (n_top, n_top, src_filter))

    # Group by year
    details_by_year = dd(list)
    for row in c:
        year = row[0]
        details_by_year[year].append(row[1:])  # Exclude year from the tuple

    # add the total number of babies
    totals_by_year = dd(int)
    if src_filter == 'meiji':
        src_filter == 'totals'
    c.execute(f"""
    SELECT year, sum(count)
    FROM name_year_cache
    WHERE src = ? AND dtype = ?
    GROUP BY year""", (src_filter, data_type))
    print("totals for", src_filter, data_type)
    for row in c:
        print("totals", row)
        totals_by_year[row[0]] = row[1]
    conn.close()        
    return details_by_year, totals_by_year

def create_json_table(data, src, data_type):
    """Create JSON table format for the overlap data."""
    headers = ["Year", "Overlap Count", "Proportion Overlap"]
    rows = []
    
    for year, overlap_count, weighted_overlap in data:
        rows.append([str(year), str(overlap_count), f"{weighted_overlap:.1f}"])
    
    return {
        "headers": headers,
        "rows": rows,
        "caption": f"{src.upper()} - {data_type.title()} Overlap Summary"
    }

def create_details_json(details_data, src, data_type):
    """Create JSON format for detailed overlap data by year."""
    if data_type == 'pron':
        headers = ["Pronunciation", "Male Freq", "Female Freq", "Proportion"]
    else:
        headers = ["Spelling", "Male Freq", "Female Freq", "Proportion"]
    
    tables_by_year = {}
    
    for year, details in details_data.items():
        rows = []
        for detail in details:
            overlap_value, male_freq, female_freq, weighted = detail
            rows.append([
                str(overlap_value or ''),
                str(male_freq),
                str(female_freq),
                f"{weighted:.1f}"
            ])
        
        tables_by_year[str(year)] = {
            "headers": headers,
            "rows": rows,
            "caption": f"{src.upper()} {year} - {data_type.title()} Overlapping Names"
        }
    
    return tables_by_year

import matplotlib.pyplot as plt

def _plot_single_graph(years, values, ylabel, title, marker, output_file, with_title=True):
    """Helper to plot and save a single graph."""
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(years, values, marker=marker, color='blue', linewidth=2, markersize=6)
    if with_title and title:
        ax.set_title(title)
    ax.set_xlabel('Year')
    ax.set_ylabel(ylabel)
    ax.grid(True, alpha=0.3)
    ax.set_ylim(bottom=0)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.set_xticks(range(min(years), max(years) + 1,
                        max(1, (max(years) - min(years)) // 10)))
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Graph saved: {output_file}")


def create_graph(data, src, data_type, output_dir, n_top=50, with_title=True):
    """Create and save overlap graphs separately (count & weighted)."""
    if not data:
        print(f"No data available for {src} {data_type}")
        return

    years = [row[0] for row in data]
    overlap_counts = [row[1] for row in data]
    weighted_overlaps = [row[2] for row in data]

    # Overlap count graph
    _plot_single_graph(
        years, overlap_counts,
        ylabel="Number of Overlapping Names",
        title=f"{src.upper()} - {data_type.title()} Overlap Count Over Time",
        marker="o",
        output_file=output_dir / f"{src}_{data_type}_{n_top}_overlap_count.png",
        with_title=with_title,
    )

    # Weighted overlap graph
    _plot_single_graph(
        years, weighted_overlaps,
        ylabel="Proportion of Overlapping Names",
        title=f"{src.upper()} - {data_type.title()} Weighted Overlap Over Time",
        marker="s",
        output_file=output_dir / f"{src}_{data_type}_{n_top}_overlap_weighted.png",
        with_title=with_title,
    )





def create_html_summary(all_tables, all_details, output_dir):
    """Create a human-readable HTML summary report."""
    html_content = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Name Overlap Analysis Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }
        h1 { color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }
        h2 { color: #34495e; margin-top: 30px; }
        h3 { color: #7f8c8d; margin-top: 25px; }
        table { border-collapse: collapse; width: 100%; margin: 20px 0; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; font-weight: bold; }
        tr:nth-child(even) { background-color: #f9f9f9; }
        .summary-table { max-width: 600px; }
        .details-table { margin-bottom: 30px; }
        .no-overlap { color: #7f8c8d; font-style: italic; }
        .caption { font-weight: bold; margin-bottom: 10px; color: #2c3e50; }
    </style>
</head>
<body>
    <h1>Name Overlap Analysis Report</h1>
    <p>This report shows the overlap in names (same pronunciation or spelling) used for both boys and girls in Japanese naming data.</p>
"""
    
    # Get all source/type combinations
    sources = set()
    data_types = set()
    for key in all_tables.keys():
        if '_summary' in key:
            parts = key.replace('_summary', '').split('_')
            if len(parts) == 2:
                src, dtype = parts
                sources.add(src)
                data_types.add(dtype)
    
    # Create sections for each source and data type
    for src in sorted(sources):
        html_content += f"<h2>{src.upper()} Data</h2>\n"
        
        for data_type in sorted(data_types):
            summary_key = f"{src}_{data_type}_summary"
            details_key = f"{src}_{data_type}_details"
            
            if summary_key in all_tables:
                html_content += f"<h3>{data_type.title()} Overlap</h3>\n"
                
                # Add summary table
                summary_table = all_tables[summary_key]
                html_content += f'<div class="caption">{summary_table["caption"]}</div>\n'
                html_content += '<table class="summary-table">\n<thead><tr>\n'
                for header in summary_table["headers"]:
                    html_content += f"<th>{header}</th>\n"
                html_content += "</tr></thead>\n<tbody>\n"
                
                for row in summary_table["rows"]:
                    html_content += "<tr>\n"
                    for cell in row:
                        html_content += f"<td>{cell}</td>\n"
                    html_content += "</tr>\n"
                html_content += "</tbody></table>\n"
                
                # Add detailed tables for each year
                if details_key in all_details:
                    details_data = all_details[details_key]
                    html_content += f"<h4>Detailed {data_type.title()} Overlap by Year</h4>\n"
                    
                    for year in sorted(details_data.keys(), key=int):
                        year_data = details_data[year]
                        html_content += f'<div class="caption">{year_data["caption"]}</div>\n'
                        
                        if year_data["rows"]:
                            html_content += '<table class="details-table">\n<thead><tr>\n'
                            for header in year_data["headers"]:
                                html_content += f"<th>{header}</th>\n"
                            html_content += "</tr></thead>\n<tbody>\n"
                            
                            for row in year_data["rows"]:
                                html_content += "<tr>\n"
                                for cell in row:
                                    html_content += f"<td>{cell}</td>\n"
                                html_content += "</tr>\n"
                            html_content += "</tbody></table>\n"
                        else:
                            html_content += '<p class="no-overlap">No overlapping names found for this year.</p>\n'
                        
                        html_content += "<br>\n"
    
    html_content += """
    <hr>
    <p><em>Generated by Name Overlap Analysis Script</em></p>
</body>
</html>
"""
    
    # Save HTML file
    html_file = output_dir / 'overlap_report.html'
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"HTML report saved: {html_file}")
    return html_file

def main():
    parser = argparse.ArgumentParser(description='Analyze name overlap between genders')
    parser.add_argument('database', help='Path to SQLite database file')
    parser.add_argument('--output-dir', default='output', help='Output directory for files')
    parser.add_argument('--n-top', type=int, default=50, help='Number of top names to consider (default: 50)')
    
    args = parser.parse_args()
    
    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)
    
    # Define sources and data types
    sources = ['bc', 'meiji', 'hs']
    data_types = ['pron', 'orth']
    
    all_tables = {}
    all_details = {}
    
    # Process each combination
    for src in sources:
        for data_type in data_types:
            print(f"Processing {src} {data_type}...")
            
            # Get overlap data
            data = []
            details, totals = get_overlap_details(args.database, src, data_type, args.n_top)
            print(details)
            print(totals)
            for year in details:
                data.append((year,
                            len(details[year]),
                            2 * sum(x[3] for x in details[year]) / totals[year]))
                            
            
            if data:
                # Create JSON table for summary
                table_key = f"{src}_{data_type}_summary"
                all_tables[table_key] = create_json_table(data, src, data_type)
                
                # Get detailed overlap data
                details_key = f"{src}_{data_type}_details"
                all_details[details_key] = create_details_json(details, src, data_type)
                
                # Create graph
                create_graph(data, src, data_type, output_dir, n_top=args.n_top, with_title=False)
            else:
                print(f"No data found for {src} {data_type} with {args.n_top} top names")
    
    # Save summary JSON file
    json_file = output_dir / 'overlap_summary.json'
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(all_tables, f, indent=2, ensure_ascii=False)

    # Save detailed JSON file
    details_json_file = output_dir / 'overlap_details.json'
    with open(details_json_file, 'w', encoding='utf-8') as f:
        json.dump(all_details, f, indent=2, ensure_ascii=False)
    
    # Create HTML summary report
    html_file = create_html_summary(all_tables, all_details, output_dir)

    print(f"Summary JSON saved: {json_file}")
    print(f"Details JSON saved: {details_json_file}")
    print(f"Analysis complete. Check {output_dir} for results.")

if __name__ == "__main__":
    main()
