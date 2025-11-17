# Kanji Position Visualization Implementation


### JavaScript
- **plot_kanji_position.js** - D3.js-based plotting function equivalent to the Python version


## Features

### Visualization
- **Stacked area chart** showing distribution across positions over time
- **Tufte-style design** with minimal chrome
- **Responsive** - adapts to window size
- **Dynamic y-axis scaling** based on data range
- **Dual charts** for male and female names side-by-side

### Position Types
- **Solo**: Single-character names using only this kanji
- **Initial**: Kanji at the beginning of multi-character names
- **Middle**: Kanji in the middle (names with 3+ characters)
- **End**: Kanji at the end of multi-character names

### Search Interface
- **Validation**: Only accepts single kanji characters
- **Examples**: Quick-click examples for common kanji
- **Error handling**: Clear messaging when kanji not found
- **Data source awareness**: Respects current database selection

## Technical Details

### JavaScript Function Signature
```javascript
plotKanjiPositions(data, kanji, gender, src, containerId, options)
```

Parameters:
- `data`: Object with year keys and [solo, initial, middle, end, count] arrays
- `kanji`: String - the kanji character
- `gender`: String - 'M' or 'F'
- `src`: String - data source identifier
- `containerId`: String - ID of container div
- `options`: Object with optional width, height, margin, showTitle


## Database Requirements

The routes expect these database structures:
- `nrank` table with columns: orth, year, freq, gender, src
- `name_year_cache` table with columns: year, count, gender, src

SQL queries use GLOB patterns for flexible kanji matching.

## Customization

### Colors
Edit the colors object in `kanji_position_plot.js`:
```javascript
const colors = {
    solo: '#d62728',    // Red
    initial: '#1f77b4', // Blue
    middle: '#2ca02c',  // Green
    end: '#ff7f0e'      // Orange
};
```

### Chart Dimensions
Default dimensions can be changed in the options:
```javascript
{
    width: 800,
    height: 500,
    margin: { top: 40, right: 30, bottom: 60, left: 60 }
}
```

### Font Support
The visualization uses CJK-compatible fonts:
- Noto Sans CJK JP (Japanese)
- Noto Sans CJK SC (Simplified Chinese)
- DejaVu Sans (fallback)

## Dependencies

- **Python**: Flask, sqlite3
- **JavaScript**: D3.js v7+
- **HTML/CSS**: Bootstrap 5 (for styling)
