/**
 * Plot kanji position distribution over time using D3.js
 * Equivalent to plot_kanji_position.py
 */

function plotKanjiPositions(data, kanji, gender, src, containerId, options = {}) {
    const {
        width = 800,
        height = 500,
        margin = { top: 40, right: 30, bottom: 60, left: 60 },
        showTitle = true
    } = options;

    // Clear any existing content
    d3.select(`#${containerId}`).selectAll("*").remove();

    // Process data
    const years = Object.keys(data).map(Number).sort((a, b) => a - b);
    
    const processedData = years.map(year => {
        const [solo, initial, middle, end, count] = data[year];
        const total = count > 0 ? count : 1;
        return {
            year: year,
            solo: solo / total,
            initial: initial / total,
            middle: middle / total,
            end: end / total,
            total: (solo + initial + middle + end) / total
        };
    });

    // Calculate max proportion for y-axis
    const maxProp = d3.max(processedData, d => d.total) || 0.1;
    const yMax = Math.ceil(maxProp * 1.1 * 20) / 20;
    const yMaxFinal = Math.max(yMax, 0.05);

    // Determine tick spacing
    let tickSpacing;
    if (yMaxFinal <= 0.1) tickSpacing = 0.02;
    else if (yMaxFinal <= 0.2) tickSpacing = 0.05;
    else if (yMaxFinal <= 0.5) tickSpacing = 0.1;
    else tickSpacing = 0.2;

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
        .domain([d3.min(years), d3.max(years)])
        .range([0, innerWidth]);

    const yScale = d3.scaleLinear()
        .domain([0, yMaxFinal])
        .range([innerHeight, 0]);

    // Color scheme
    const colors = {
        solo: '#d62728',
        initial: '#1f77b4',
        middle: '#2ca02c',
        end: '#ff7f0e'
    };

    // Define the area generators for stacked chart
    const areaSolo = d3.area()
        .x(d => xScale(d.year))
        .y0(innerHeight)
        .y1(d => yScale(d.solo))
        .curve(d3.curveMonotoneX);

    const areaInitial = d3.area()
        .x(d => xScale(d.year))
        .y0(d => yScale(d.solo))
        .y1(d => yScale(d.solo + d.initial))
        .curve(d3.curveMonotoneX);

    const areaMiddle = d3.area()
        .x(d => xScale(d.year))
        .y0(d => yScale(d.solo + d.initial))
        .y1(d => yScale(d.solo + d.initial + d.middle))
        .curve(d3.curveMonotoneX);

    const areaEnd = d3.area()
        .x(d => xScale(d.year))
        .y0(d => yScale(d.solo + d.initial + d.middle))
        .y1(d => yScale(d.solo + d.initial + d.middle + d.end))
        .curve(d3.curveMonotoneX);

    // Draw stacked areas
    g.append("path")
        .datum(processedData)
        .attr("fill", colors.solo)
        .attr("opacity", 0.7)
        .attr("d", areaSolo);

    g.append("path")
        .datum(processedData)
        .attr("fill", colors.initial)
        .attr("opacity", 0.7)
        .attr("d", areaInitial);

    g.append("path")
        .datum(processedData)
        .attr("fill", colors.middle)
        .attr("opacity", 0.7)
        .attr("d", areaMiddle);

    g.append("path")
        .datum(processedData)
        .attr("fill", colors.end)
        .attr("opacity", 0.7)
        .attr("d", areaEnd);

    // Add axes
    const xAxis = d3.axisBottom(xScale)
        .tickFormat(d3.format("d"))
        .ticks(Math.min(years.length, 10));

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

    g.selectAll(".tick line")
        .style("stroke-width", "0.5px")
        .style("stroke", "gray");

    // Y-axis
    g.append("g")
        .call(yAxis)
        .style("font-size", "10px")
        .select(".domain")
        .style("stroke-width", "0.5px")
        .style("stroke", "gray");

    // Y-axis grid lines
    g.append("g")
        .attr("class", "grid")
        .call(d3.axisLeft(yScale)
            .tickValues(d3.range(0, yMaxFinal + tickSpacing / 2, tickSpacing))
            .tickSize(-innerWidth)
            .tickFormat(""))
        .style("stroke-opacity", 0.3)
        .style("stroke", "gray")
        .style("stroke-width", "0.5px")
        .select(".domain")
        .remove();

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
        .text("Proportion");

    // Title
    if (showTitle) {
        svg.append("text")
            .attr("x", width / 2)
            .attr("y", margin.top / 2)
            .attr("text-anchor", "middle")
            .style("font-size", "12px")
            .style("font-weight", "normal")
            .text(`Position Distribution of 「${kanji}」 in Names for ${gender} from ${src}`);
    }

    // Legend
    const legend = g.append("g")
        .attr("transform", `translate(10, 10)`);

    const legendData = [
        { label: "Solo", color: colors.solo },
        { label: "Initial", color: colors.initial },
        { label: "Middle", color: colors.middle },
        { label: "End", color: colors.end }
    ];

    legendData.forEach((item, i) => {
        const legendRow = legend.append("g")
            .attr("transform", `translate(0, ${i * 20})`);

        legendRow.append("rect")
            .attr("width", 15)
            .attr("height", 15)
            .attr("fill", item.color)
            .attr("opacity", 0.7);

        legendRow.append("text")
            .attr("x", 20)
            .attr("y", 12)
            .style("font-size", "10px")
            .text(item.label);
    });
}

/**
 * Fetch kanji position data from server and plot
 */
async function loadAndPlotKanji(kanji, gender, src, containerId, options = {}) {
    try {
        const response = await fetch(`/api/kanji-position?kanji=${encodeURIComponent(kanji)}&gender=${gender}&src=${src}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        plotKanjiPositions(data, kanji, gender, src, containerId, options);
    } catch (error) {
        console.error("Error loading kanji data:", error);
        d3.select(`#${containerId}`)
            .append("p")
            .style("color", "red")
            .text(`Error loading data: ${error.message}`);
    }
}
