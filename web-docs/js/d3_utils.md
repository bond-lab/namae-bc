# d3_utils.js - Shared utilities including:

a shared utility library with reusable functions.
    
## File Structure

```
web/static/js/
├── d3_utils.js              ← NEW: Shared utilities
├── kanji_position_plot.js   ← Uses d3_utils
└── plot_namae.js            ← Uses d3_utils
```

## What's in d3_utils.js

### 1. `downloadSVGasPNG(containerId, filename, scale)`
Converts any SVG to PNG and downloads it.

### 2. `downloadAsSVG(containerId, filename)`
Fallback for browsers with Canvas issues.
- Downloads raw SVG file instead of PNG
- Useful for: Firefox private mode, some mobile browsers

### 3. `setupDownloadButton(buttonId, containerId, filename)`
Convenience function to wire up download buttons.

- `setupDownloadButton('btn-id', 'container-id', 'file.png')`
- Includes automatic fallback to SVG if PNG fails

### 4. `countOccurrences(items)`
Counts items in an array.
- Used by `countByYear()` in plot_namae.js
- Reusable for other counting needs

### 5. `formatNumber(num)`
Adds thousands separators: `1000` → `"1,000"`
- Ready to use when needed

### 6. `getGenderColor(gender, colorOverrides)`
Consistent color scheme for gender across all charts.
- Returns orange/purple by default
- Accepts overrides for custom colors

## Usage Examples

### In Templates

```html
{% block head %}
<script src="https://cdnjs.cloudflare.com/ajax/libs/d3/7.8.5/d3.min.js"></script>
<script src="{{ url_for('static', filename='js/d3_utils.js') }}"></script>
<script src="{{ url_for('static', filename='js/your_chart.js') }}"></script>
{% endblock %}

<script>
  // Simple one-line setup
  setupDownloadButton('download-btn', 'chart-container', 'chart.png');
  
  // Or manually
  document.getElementById('download-btn').addEventListener('click', function() {
    downloadSVGasPNG('chart-container', 'my-chart.png');
  });
</script>
```

### In JavaScript Files

```javascript
// plot_namae.js or any other chart script
function plotMyChart(data, containerId) {
    // ... create chart ...
    
    // Count occurrences (from utils)
    const counts = countOccurrences(data);
    
    // Get consistent colors (from utils)
    const maleColor = getGenderColor('M');
    const femaleColor = getGenderColor('F');
    
    // Download is handled by template using setupDownloadButton()
}
```

## Upgrade Path for Existing Charts

If you add more D3 charts in the future:

```html
<!-- Always include d3_utils.js after D3, before your chart script -->
<script src="d3.min.js"></script>
<script src="d3_utils.js"></script>
<script src="your_new_chart.js"></script>

<script>
  // Instant download functionality!
  setupDownloadButton('download-btn', 'chart-id', 'chart.png');
</script>
```

## No D3 Built-in Alternative

D3.js deliberately **does not** include SVG-to-PNG conversion because:
1. It's focused on visualization, not file I/O
2. Requires browser Canvas API (not part of D3's scope)
3. Different use cases need different approaches

Many D3 projects implement similar utility functions, so having a shared `d3_utils.js` is a common pattern.

## Dependencies

**d3_utils.js requires:**
- D3.js v7+ (for selections, if needed)
- Modern browser with:
  - Canvas API
  - Blob API
  - XMLSerializer

**Works in:**
- ✅ Chrome/Edge 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Mobile browsers (most)

**May fail in:**
- ❌ IE11 (use SVG fallback)
- ❌ Firefox private mode (Canvas tainting issues - use SVG fallback)

The `setupDownloadButton()` automatically offers SVG fallback if PNG fails!

## Testing

Test the download functionality:

```javascript
// In browser console
downloadSVGasPNG('chart-container', 'test.png');  // Should download PNG
downloadAsSVG('chart-container', 'test.svg');      // Should download SVG
setupDownloadButton('btn-id', 'chart-id', 'f.png'); // Should wire up button
```

