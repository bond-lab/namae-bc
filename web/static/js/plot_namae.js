/**
 * Plot name frequency distribution over time using D3.js
 * Shows male and female distributions in a mirrored butterfly chart
 */

function plotNameFrequency(yearsMale, yearsFemale, name, containerId, options = {}) {
    const {
        width = 800,
        height = 300,
        margin = { top: 40, right: 30, bottom: 60, left: 60 },
        maleColor = '#ff7f0e',
        femaleColor = '#9467bd',
        showTitle = true
    } = options;

    // Clear any existing content
    d3.select(`#${containerId}`).selectAll("*").remove();

    // Process data - count occurrences by year
    const maleData = countByYear(yearsMale);
    const femaleData = countByYear(yearsFemale);
    
    // Get all years from both datasets
    const allYears = [...new Set([...Object.keys(maleData), ...Object.keys(femaleData)])]
        .map(Number)
        .sort((a, b) => a - b);
    
    // Create combined dataset
    const combinedData = allYears.map(year => ({
        year: year,
        male: maleData[year] || 0,
        female: femaleData[year] || 0
    }));

    // Find max value for scaling
    const maxValue = Math.max(
        d3.max(combinedData, d => d.male) || 0,
        d3.max(combinedData, d => d.female) || 0
    );

    // Create SVG
    const svg = d3.select(`#${containerId}`)
        .append("svg")
        .attr("width", width)
        .attr("height", height)
        .style("font-family", "'Noto Sans CJK JP', 'Noto Sans CJK SC', 'DejaVu Sans', sans-serif");

    const g = svg.append("g")
        .attr("transform", `translate(${margin.left},${margin.top})`);

    const innerWidth = width - margin.left - margin.right;
    const innerHeight = height - margin.top - margin.bottom;
    const centerY = innerHeight / 2;

    // Scales
    // Add padding to x-axis for single data points
    let xMin = d3.min(allYears);
    let xMax = d3.max(allYears);
    
    if (combinedData.length === 1) {
        // Add padding of 1 year on each side for single point
        xMin = xMin - 1;
        xMax = xMax + 1;
    }
    
    const xScale = d3.scaleLinear()
        .domain([xMin, xMax])
        .range([0, innerWidth]);

    // Y scale for each half (max value determines scale)
    const yScale = d3.scaleLinear()
        .domain([0, maxValue])
        .range([0, centerY - 10]); // -10 for padding

    // Create area generators
    // Use step curve for single point, monotone for multiple points
    const curveType = combinedData.length === 1 ? d3.curveStep : d3.curveMonotoneX;
    
    const areaFemale = d3.area()
        .x(d => xScale(d.year))
        .y0(centerY)
        .y1(d => centerY - yScale(d.female))
        .curve(curveType);

    const areaMale = d3.area()
        .x(d => xScale(d.year))
        .y0(centerY)
        .y1(d => centerY + yScale(d.male))
        .curve(curveType);

    // Draw areas
    g.append("path")
        .datum(combinedData)
        .attr("fill", femaleColor)
        .attr("opacity", 0.7)
        .attr("d", areaFemale);

    g.append("path")
        .datum(combinedData)
        .attr("fill", maleColor)
        .attr("opacity", 0.7)
        .attr("d", areaMale);

    // For single or very few data points, also add bars for visibility
    if (combinedData.length <= 3) {
        const barWidth = combinedData.length === 1 ? 40 : 
                         Math.min(40, innerWidth / combinedData.length / 3);
        
        // Female bars
        g.selectAll(".female-bar")
            .data(combinedData.filter(d => d.female > 0))
            .enter()
            .append("rect")
            .attr("class", "female-bar")
            .attr("x", d => xScale(d.year) - barWidth / 2)
            .attr("y", d => centerY - yScale(d.female))
            .attr("width", barWidth)
            .attr("height", d => yScale(d.female))
            .attr("fill", femaleColor)
            .attr("opacity", 0.8);
        
        // Male bars
        g.selectAll(".male-bar")
            .data(combinedData.filter(d => d.male > 0))
            .enter()
            .append("rect")
            .attr("class", "male-bar")
            .attr("x", d => xScale(d.year) - barWidth / 2)
            .attr("y", centerY)
            .attr("width", barWidth)
            .attr("height", d => yScale(d.male))
            .attr("fill", maleColor)
            .attr("opacity", 0.8);
    }

    // Add center line
    g.append("line")
        .attr("x1", 0)
        .attr("x2", innerWidth)
        .attr("y1", centerY)
        .attr("y2", centerY)
        .attr("stroke", "#666")
        .attr("stroke-width", 1)
        .attr("stroke-dasharray", "3,3");

    // X-axis
    const xAxis = d3.axisBottom(xScale)
        .tickFormat(d3.format("d"))
        .ticks(Math.min(allYears.length, 10));

    g.append("g")
        .attr("transform", `translate(0,${innerHeight})`)
        .call(xAxis)
        .style("font-size", "10px")
        .select(".domain")
        .style("stroke-width", "0.5px")
        .style("stroke", "gray");

    // Y-axis labels (count)
    const yAxisTicks = [0, Math.ceil(maxValue / 2), maxValue];
    
    // Female side (top)
    const yAxisFemale = d3.axisLeft(d3.scaleLinear()
        .domain([0, maxValue])
        .range([centerY, 0]))
        .tickValues(yAxisTicks)
        .tickFormat(d => d);

    g.append("g")
        .call(yAxisFemale)
        .style("font-size", "10px")
        .select(".domain")
        .style("stroke-width", "0.5px")
        .style("stroke", "gray");

    // Male side (bottom)
    const yAxisMale = d3.axisLeft(d3.scaleLinear()
        .domain([0, maxValue])
        .range([centerY, innerHeight]))
        .tickValues(yAxisTicks)
        .tickFormat(d => d);

    g.append("g")
        .call(yAxisMale)
        .style("font-size", "10px")
        .select(".domain")
        .style("stroke-width", "0.5px")
        .style("stroke", "gray");

    // Add grid lines
    yAxisTicks.forEach(tick => {
        if (tick > 0) {
            // Female side grid
            g.append("line")
                .attr("x1", 0)
                .attr("x2", innerWidth)
                .attr("y1", centerY - yScale(tick))
                .attr("y2", centerY - yScale(tick))
                .attr("stroke", "gray")
                .attr("stroke-width", 0.5)
                .attr("stroke-opacity", 0.3);
            
            // Male side grid
            g.append("line")
                .attr("x1", 0)
                .attr("x2", innerWidth)
                .attr("y1", centerY + yScale(tick))
                .attr("y2", centerY + yScale(tick))
                .attr("stroke", "gray")
                .attr("stroke-width", 0.5)
                .attr("stroke-opacity", 0.3);
        }
    });

    // Labels
    g.append("text")
        .attr("x", innerWidth / 2)
        .attr("y", innerHeight + margin.bottom - 10)
        .attr("text-anchor", "middle")
        .style("font-size", "11px")
        .text("Year");

    g.append("text")
        .attr("transform", "rotate(-90)")
        .attr("x", -innerHeight / 2)
        .attr("y", -margin.left + 15)
        .attr("text-anchor", "middle")
        .style("font-size", "11px")
        .text("Frequency");

    // Title
    if (showTitle) {
        svg.append("text")
            .attr("x", width / 2)
            .attr("y", margin.top / 2)
            .attr("text-anchor", "middle")
            .style("font-size", "12px")
            .style("font-weight", "normal")
            .text(`Frequency of「${name}」Over Time`);
    }

    // Legend
    const legend = g.append("g")
        .attr("transform", `translate(${innerWidth - 100}, 10)`);

    // Female legend
    legend.append("rect")
        .attr("width", 15)
        .attr("height", 15)
        .attr("fill", femaleColor)
        .attr("opacity", 0.7);

    legend.append("text")
        .attr("x", 20)
        .attr("y", 12)
        .style("font-size", "10px")
        .text("Female");

    // Male legend
    legend.append("rect")
        .attr("y", 20)
        .attr("width", 15)
        .attr("height", 15)
        .attr("fill", maleColor)
        .attr("opacity", 0.7);

    legend.append("text")
        .attr("x", 20)
        .attr("y", 32)
        .style("font-size", "10px")
        .text("Male");

    // Add statistics text
    const totalMale = yearsMale.length;
    const totalFemale = yearsFemale.length;
    const total = totalMale + totalFemale;
    const femaleRatio = total > 0 ? (totalFemale / total).toFixed(2) : '0.00';

    const stats = g.append("g")
        .attr("transform", `translate(10, ${innerHeight - 40})`);

    stats.append("text")
        .style("font-size", "10px")
        .style("fill", "#666")
        .text(`Total: ${total} (M: ${totalMale}, F: ${totalFemale}, F-ratio: ${femaleRatio})`);
}

/**
 * Helper function to count occurrences by year
 * Uses shared countOccurrences from d3_utils.js but specialized for year grouping
 */
function countByYear(years) {
    return countOccurrences(years);
}
