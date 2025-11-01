/**
 * Shared utility functions for D3 visualizations
 * Used by kanji_position_plot.js and plot_namae.js
 */

/**
 * Convert any SVG element to PNG and download
 * 
 * @param {string} containerId - ID of container with SVG element
 * @param {string} filename - Name for downloaded file
 * @param {number} scale - Scale factor for output resolution (default: 2 for high quality)
 */
function downloadSVGasPNG(containerId, filename, scale = 2) {
    const svgElement = document.querySelector(`#${containerId} svg`);
    if (!svgElement) {
        console.error(`SVG not found in container: ${containerId}`);
        alert('Chart not found! Please ensure the chart has rendered.');
        return;
    }
    
    // Clone the SVG to avoid modifying the original
    const clonedSvg = svgElement.cloneNode(true);
    
    // Get SVG dimensions
    const width = parseFloat(svgElement.getAttribute('width'));
    const height = parseFloat(svgElement.getAttribute('height'));
    
    if (!width || !height) {
        console.error('SVG has invalid dimensions:', { width, height });
        alert('Chart has invalid dimensions.');
        return;
    }
    
    // Serialize SVG to string
    const serializer = new XMLSerializer();
    const svgString = serializer.serializeToString(clonedSvg);
    
    // Create a canvas
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    
    // Set canvas size (scaled for higher resolution)
    canvas.width = width * scale;
    canvas.height = height * scale;
    
    // Create an image from SVG
    const img = new Image();
    const svgBlob = new Blob([svgString], { type: 'image/svg+xml;charset=utf-8' });
    const url = URL.createObjectURL(svgBlob);
    
    img.onload = function() {
        // Fill white background
        ctx.fillStyle = 'white';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        
        // Draw image scaled up for higher resolution
        ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
        
        // Convert to PNG and download
        canvas.toBlob(function(blob) {
            if (!blob) {
                console.error('Failed to create image blob');
                alert('Error creating image. Please try again.');
                URL.revokeObjectURL(url);
                return;
            }
            
            const link = document.createElement('a');
            link.download = filename;
            link.href = URL.createObjectURL(blob);
            link.click();
            
            // Cleanup
            URL.revokeObjectURL(url);
            URL.revokeObjectURL(link.href);
        }, 'image/png');
    };
    
    img.onerror = function(error) {
        console.error('Error loading SVG for conversion:', error);
        alert('Error creating image. This may happen with complex charts or in some browsers. Try a different browser or save as SVG instead.');
        URL.revokeObjectURL(url);
    };
    
    img.src = url;
}

/**
 * Alternative: Download SVG directly (for browsers with PNG issues)
 * 
 * @param {string} containerId - ID of container with SVG element
 * @param {string} filename - Name for downloaded file (will force .svg extension)
 */
function downloadAsSVG(containerId, filename) {
    const svgElement = document.querySelector(`#${containerId} svg`);
    if (!svgElement) {
        alert('Chart not found!');
        return;
    }
    
    const serializer = new XMLSerializer();
    const svgString = serializer.serializeToString(svgElement);
    
    const blob = new Blob([svgString], { type: 'image/svg+xml;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    
    const link = document.createElement('a');
    link.download = filename.replace(/\.(png|jpg|jpeg)$/i, '.svg'); // Force .svg extension
    link.href = url;
    link.click();
    
    URL.revokeObjectURL(url);
}

/**
 * Setup download button with automatic retry/fallback
 * If PNG download fails, offers SVG download as fallback
 * 
 * @param {string} buttonId - ID of download button
 * @param {string} containerId - ID of container with SVG
 * @param {string} filename - Filename for download
 */
function setupDownloadButton(buttonId, containerId, filename) {
    const button = document.getElementById(buttonId);
    if (!button) {
        console.warn(`Download button not found: ${buttonId}`);
        return;
    }
    
    button.addEventListener('click', function() {
        try {
            downloadSVGasPNG(containerId, filename);
        } catch (error) {
            console.error('PNG download failed:', error);
            if (confirm('PNG download failed. Would you like to download as SVG instead?')) {
                downloadAsSVG(containerId, filename);
            }
        }
    });
}

/**
 * Count occurrences in an array
 * Helper function used by multiple visualizations
 * 
 * @param {Array} items - Array of items to count
 * @returns {Object} Object with items as keys and counts as values
 */
function countOccurrences(items) {
    const counts = {};
    items.forEach(item => {
        counts[item] = (counts[item] || 0) + 1;
    });
    return counts;
}

/**
 * Format number with thousands separator
 * 
 * @param {number} num - Number to format
 * @returns {string} Formatted number
 */
function formatNumber(num) {
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}

/**
 * Get consistent colors based on gender
 * Uses session colors if available, falls back to defaults
 * 
 * @param {string} gender - 'M' or 'F'
 * @param {Object} colorOverrides - Optional color overrides {male: '#color', female: '#color'}
 * @returns {string} Color hex code
 */
function getGenderColor(gender, colorOverrides = {}) {
    const defaults = {
        male: '#ff7f0e',    // Orange
        female: '#9467bd'   // Purple
    };
    
    if (gender === 'M' || gender === 'male') {
        return colorOverrides.male || defaults.male;
    } else if (gender === 'F' || gender === 'female') {
        return colorOverrides.female || defaults.female;
    }
    
    return '#999'; // Gray for unknown
}
