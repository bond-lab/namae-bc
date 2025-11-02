/**
 * Plot irregular names proportion over time using D3.js
 * Shows male and female trends on the same chart
 */

function plotIrregularNames(data, containerId, options = {}) {
    const {
        width = 800,
        height = 500,
        margin = { top: 40, right: 120, bottom: 60, left: 60 },
        maleColor = '#ff7f0e',
        femaleColor = '#9467bd',
        showTitle = true,
        regressionStats = null
    } = options;

    // Clear any existing content
    d3.select(`#${containerId}`).selectAll("*").remove();

    // Process data - calculate proportions
    const processedData = data.map(d => ({
        year: d.year,
        gender: d.gender,
        names: d.names,
        number: d.number,
        irregular_names: d.irregular_names,
        irregular_proportion: d.number > 0 ? d.irregular_names / d.number : 0
    }));

    // Separate male and female data
    const maleData = processedData.filter(d => d.gender === 'M').sort((a, b) => a.year - b.year);
    const femaleData = processedData.filter(d => d.gender === 'F').sort((a, b) => a.year - b.year);

    // Get year range
    const allYears = [...new Set(processedData.map(d => d.year))].sort((a, b) => a - b);
    
    if (allYears.length === 0) {
        d3.select(`#${containerId}`)
            .append('div')
            .attr('class', 'alert alert-warning')
            .text('No data available.');
        return;
    }

    // Find max proportion for y-axis
    const maxProp = d3.max(processedData, d => d.irregular_proportion) || 0.1;
    const yMax = Math.ceil(maxProp * 1.1 * 20) / 20; // Round up to nearest 5%
    const yMaxFinal = Math.max(yMax, 0.05);

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

    // Scales
    const xScale = d3.scaleLinear()
        .domain([d3.min(allYears), d3.max(allYears)])
        .range([0, innerWidth]);

    const yScale = d3.scaleLinear()
        .domain([0, yMaxFinal])
        .range([innerHeight, 0]);

    // Determine tick spacing
    let tickSpacing;
    if (yMaxFinal <= 0.1) tickSpacing = 0.02;
    else if (yMaxFinal <= 0.2) tickSpacing = 0.05;
    else if (yMaxFinal <= 0.5) tickSpacing = 0.1;
    else tickSpacing = 0.2;

    // Create line generators
    const lineMale = d3.line()
        .x(d => xScale(d.year))
        .y(d => yScale(d.irregular_proportion))
        .curve(d3.curveMonotoneX);

    const lineFemale = d3.line()
        .x(d => xScale(d.year))
        .y(d => yScale(d.irregular_proportion))
        .curve(d3.curveMonotoneX);

    // Draw grid lines
    g.append("g")
        .attr("class", "grid")
        .selectAll("line")
        .data(d3.range(0, yMaxFinal + tickSpacing / 2, tickSpacing))
        .enter()
        .append("line")
        .attr("x1", 0)
        .attr("x2", innerWidth)
        .attr("y1", d => yScale(d))
        .attr("y2", d => yScale(d))
        .attr("stroke", "gray")
        .attr("stroke-width", 0.5)
        .attr("stroke-opacity", 0.3);

    // Draw male line
    if (maleData.length > 0) {
        g.append("path")
            .datum(maleData)
            .attr("fill", "none")
            .attr("stroke", maleColor)
            .attr("stroke-width", 2.5)
            .attr("d", lineMale);

        // Add dots for male data points
        g.selectAll(".dot-male")
            .data(maleData)
            .enter()
            .append("circle")
            .attr("class", "dot-male")
            .attr("cx", d => xScale(d.year))
            .attr("cy", d => yScale(d.irregular_proportion))
            .attr("r", 3)
            .attr("fill", maleColor)
            .attr("stroke", "white")
            .attr("stroke-width", 1.5)
            .append("title")
            .text(d => `Year: ${d.year}\nMale\nIrregular: ${d.irregular_names}/${d.number} (${(d.irregular_proportion * 100).toFixed(1)}%)`);
    }

    // Draw female line
    if (femaleData.length > 0) {
        g.append("path")
            .datum(femaleData)
            .attr("fill", "none")
            .attr("stroke", femaleColor)
            .attr("stroke-width", 2.5)
            .attr("d", lineFemale);

        // Add dots for female data points
        g.selectAll(".dot-female")
            .data(femaleData)
            .enter()
            .append("circle")
            .attr("class", "dot-female")
            .attr("cx", d => xScale(d.year))
            .attr("cy", d => yScale(d.irregular_proportion))
            .attr("r", 3)
            .attr("fill", femaleColor)
            .attr("stroke", "white")
            .attr("stroke-width", 1.5)
            .append("title")
            .text(d => `Year: ${d.year}\nFemale\nIrregular: ${d.irregular_names}/${d.number} (${(d.irregular_proportion * 100).toFixed(1)}%)`);
    }

    // Draw regression lines if stats are provided
    if (regressionStats) {
        // Male regression line
        if (regressionStats.M && maleData.length > 0) {
            const maleYears = regressionStats.M.years;
            const minYear = Math.min(...maleYears);
            const maxYear = Math.max(...maleYears);
            const slope = regressionStats.M.slope;
            const intercept = regressionStats.M.intercept;
            
            const regressionLine = [
                { year: minYear, value: slope * minYear + intercept },
                { year: maxYear, value: slope * maxYear + intercept }
            ];
            
            g.append("path")
                .datum(regressionLine)
                .attr("fill", "none")
                .attr("stroke", maleColor)
                .attr("stroke-width", 1.5)
                .attr("stroke-dasharray", "5,5")
                .attr("opacity", 0.6)
                .attr("d", d3.line()
                    .x(d => xScale(d.year))
                    .y(d => yScale(d.value))
                );
        }
        
        // Female regression line
        if (regressionStats.F && femaleData.length > 0) {
            const femaleYears = regressionStats.F.years;
            const minYear = Math.min(...femaleYears);
            const maxYear = Math.max(...femaleYears);
            const slope = regressionStats.F.slope;
            const intercept = regressionStats.F.intercept;
            
            const regressionLine = [
                { year: minYear, value: slope * minYear + intercept },
                { year: maxYear, value: slope * maxYear + intercept }
            ];
            
            g.append("path")
                .datum(regressionLine)
                .attr("fill", "none")
                .attr("stroke", femaleColor)
                .attr("stroke-width", 1.5)
                .attr("stroke-dasharray", "5,5")
                .attr("opacity", 0.6)
                .attr("d", d3.line()
                    .x(d => xScale(d.year))
                    .y(d => yScale(d.value))
                );
        }
    }

    // Add axes
    const xAxis = d3.axisBottom(xScale)
        .tickFormat(d3.format("d"))
        .ticks(Math.min(allYears.length, 10));

    const yAxis = d3.axisLeft(yScale)
        .tickValues(d3.range(0, yMaxFinal + tickSpacing / 2, tickSpacing))
        .tickFormat(d => `${Math.round(d * 100)}%`);

    // X-axis
    g.append("g")
        .attr("transform", `translate(0,${innerHeight})`)
        .call(xAxis)
        .style("font-size", "10px")
        .select(".domain")
        .style("stroke-width", "0.5px")
        .style("stroke", "gray");

    // Y-axis
    g.append("g")
        .call(yAxis)
        .style("font-size", "10px")
        .select(".domain")
        .style("stroke-width", "0.5px")
        .style("stroke", "gray");

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
        .text("Irregular Proportion");

    // Title
    if (showTitle) {
        svg.append("text")
            .attr("x", width / 2)
            .attr("y", margin.top / 2)
            .attr("text-anchor", "middle")
            .style("font-size", "12px")
            .style("font-weight", "normal")
            .text("Irregular Name Mappings Over Time");
    }

    // Legend
    const legend = g.append("g")
        .attr("transform", `translate(${innerWidth - 100}, 10)`);

    // Male legend
    legend.append("line")
        .attr("x1", 0)
        .attr("x2", 30)
        .attr("y1", 0)
        .attr("y2", 0)
        .attr("stroke", maleColor)
        .attr("stroke-width", 2.5);

    legend.append("circle")
        .attr("cx", 15)
        .attr("cy", 0)
        .attr("r", 3)
        .attr("fill", maleColor)
        .attr("stroke", "white")
        .attr("stroke-width", 1.5);

    legend.append("text")
        .attr("x", 35)
        .attr("y", 4)
        .style("font-size", "10px")
        .text("Male");

    // Female legend
    legend.append("line")
        .attr("x1", 0)
        .attr("x2", 30)
        .attr("y1", 20)
        .attr("y2", 20)
        .attr("stroke", femaleColor)
        .attr("stroke-width", 2.5);

    legend.append("circle")
        .attr("cx", 15)
        .attr("cy", 20)
        .attr("r", 3)
        .attr("fill", femaleColor)
        .attr("stroke", "white")
        .attr("stroke-width", 1.5);

    legend.append("text")
        .attr("x", 35)
        .attr("y", 24)
        .style("font-size", "10px")
        .text("Female");

    // Add summary statistics at bottom
    const totalMaleIrregular = d3.sum(maleData, d => d.irregular_names);
    const totalMaleNumber = d3.sum(maleData, d => d.number);
    const totalFemaleIrregular = d3.sum(femaleData, d => d.irregular_names);
    const totalFemaleNumber = d3.sum(femaleData, d => d.number);

    const maleAvgPct = totalMaleNumber > 0 ? (totalMaleIrregular / totalMaleNumber * 100).toFixed(1) : '0.0';
    const femaleAvgPct = totalFemaleNumber > 0 ? (totalFemaleIrregular / totalFemaleNumber * 100).toFixed(1) : '0.0';

    const stats = g.append("g")
        .attr("transform", `translate(10, ${innerHeight - 40})`);

    stats.append("text")
        .style("font-size", "10px")
        .style("fill", "#666")
        .text(`Overall: Male ${maleAvgPct}% (${formatNumber(totalMaleIrregular)}/${formatNumber(totalMaleNumber)}), Female ${femaleAvgPct}% (${formatNumber(totalFemaleIrregular)}/${formatNumber(totalFemaleNumber)})`);
}
