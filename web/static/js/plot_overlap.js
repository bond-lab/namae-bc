/**
 * Plotter for overlap data: count or proportion over time with regression.
 *
 * Data format:
 *   [{ year, overlap_count, overlap_freq, total_babies, weighted_proportion }, ...]
 *
 * Options:
 *   { width, height, margin, color, yLabel, measure, regressionStats }
 *
 *   measure: 'count' → plots overlap_count (integer y-axis)
 *            'proportion' → plots weighted_proportion (percentage y-axis)
 */

function plotOverlap(data, containerId, options = {}) {
    const {
        width = 800,
        height = 500,
        margin = { top: 40, right: 120, bottom: 60, left: 70 },
        color = '#1f77b4',
        yLabel = 'Value',
        measure = 'count',
        regressionStats = null
    } = options;

    // Clear old content
    d3.select(`#${containerId}`).selectAll("*").remove();

    const isCount = measure === 'count';
    const valueAccessor = isCount
        ? d => d.overlap_count
        : d => d.weighted_proportion;

    // Validate / prep
    const clean = (data || [])
        .filter(d => d && typeof d.year === 'number' && isFinite(valueAccessor(d)))
        .map(d => ({
            year: d.year,
            value: +valueAccessor(d),
            overlap_count: d.overlap_count || 0,
            overlap_freq: d.overlap_freq || 0,
            total_babies: d.total_babies || 0,
            weighted_proportion: d.weighted_proportion || 0
        }))
        .sort((a, b) => a.year - b.year);

    if (clean.length === 0) {
        d3.select(`#${containerId}`)
            .append('div')
            .attr('class', 'alert alert-warning')
            .text('No data available.');
        return;
    }

    const years = clean.map(d => d.year);

    // Y scale domain
    let yMax;
    if (isCount) {
        yMax = Math.max(1, Math.ceil(d3.max(clean, d => d.value) * 1.15));
    } else {
        const rawMax = d3.max(clean, d => d.value) || 0.1;
        yMax = Math.max(0.05, Math.ceil(rawMax * 1.1 * 20) / 20);
    }

    const svg = d3.select(`#${containerId}`)
        .append("svg")
        .attr("width", width)
        .attr("height", height)
        .style("font-family", "'Noto Sans CJK JP', 'Noto Sans CJK SC', 'DejaVu Sans', sans-serif");

    const g = svg.append("g")
        .attr("transform", `translate(${margin.left},${margin.top})`);

    const innerWidth = width - margin.left - margin.right;
    const innerHeight = height - margin.top - margin.bottom;

    const xScale = d3.scaleLinear()
        .domain([d3.min(years), d3.max(years)])
        .range([0, innerWidth]);

    const yScale = d3.scaleLinear()
        .domain([0, yMax])
        .range([innerHeight, 0]);

    // y tick spacing heuristic
    let tickSpacing;
    if (isCount) {
        if (yMax <= 5) tickSpacing = 1;
        else if (yMax <= 15) tickSpacing = 2;
        else if (yMax <= 30) tickSpacing = 5;
        else tickSpacing = 10;
    } else {
        if (yMax <= 0.1) tickSpacing = 0.02;
        else if (yMax <= 0.2) tickSpacing = 0.05;
        else if (yMax <= 0.5) tickSpacing = 0.1;
        else tickSpacing = 0.2;
    }

    const lineGen = d3.line()
        .x(d => xScale(d.year))
        .y(d => yScale(d.value))
        .curve(d3.curveMonotoneX);

    // grid
    g.append("g")
        .attr("class", "grid")
        .selectAll("line")
        .data(d3.range(0, yMax + tickSpacing / 2, tickSpacing))
        .enter().append("line")
        .attr("x1", 0).attr("x2", innerWidth)
        .attr("y1", d => yScale(d)).attr("y2", d => yScale(d))
        .attr("stroke", "gray").attr("stroke-width", 0.5).attr("stroke-opacity", 0.3);

    // draw main line
    g.append("path")
        .datum(clean)
        .attr("fill", "none")
        .attr("stroke", color)
        .attr("stroke-width", 2.5)
        .attr("d", lineGen);

    // draw points
    const points = g.selectAll(".dot-overlap")
        .data(clean)
        .enter().append("circle")
        .attr("class", "dot-overlap")
        .attr("cx", d => xScale(d.year))
        .attr("cy", d => yScale(d.value))
        .attr("r", 3)
        .attr("fill", color)
        .attr("stroke", "white")
        .attr("stroke-width", 1.5);

    // tooltip
    points.append("title").text(d => {
        const pct = (d.weighted_proportion * 100).toFixed(1);
        return `Year: ${d.year}\nOverlapping names: ${d.overlap_count}\nOverlap babies: ${formatNumber(d.overlap_freq)}/${formatNumber(d.total_babies)} (${pct}%)`;
    });

    // regression line
    if (regressionStats && regressionStats.years && regressionStats.years.length >= 2) {
        const rs = regressionStats;
        const minY = Math.min(...rs.years);
        const maxY = Math.max(...rs.years);
        const lineData = [
            { year: minY, value: rs.slope * minY + rs.intercept },
            { year: maxY, value: rs.slope * maxY + rs.intercept }
        ];

        const sig = rs.p_value < 0.05;

        g.append("path")
            .datum(lineData)
            .attr("fill", "none")
            .attr("stroke", color)
            .attr("stroke-width", 1.5)
            .attr("stroke-dasharray", sig ? "none" : "5,5")
            .attr("opacity", sig ? 0.9 : 0.6)
            .attr("d", d3.line()
                .x(d => xScale(d.year))
                .y(d => yScale(d.value))
            )
            .append("title")
            .text(`Regression: slope=${rs.slope.toFixed(4)}, p=${rs.p_value.toFixed(3)}, `
                + (sig ? 'significant' : 'not significant'));
    }

    // axes
    const xAxis = d3.axisBottom(xScale).tickFormat(d3.format("d")).ticks(Math.min(years.length, 10));
    let yAxis;
    if (isCount) {
        yAxis = d3.axisLeft(yScale)
            .tickValues(d3.range(0, yMax + tickSpacing / 2, tickSpacing))
            .tickFormat(d3.format("d"));
    } else {
        yAxis = d3.axisLeft(yScale)
            .tickValues(d3.range(0, yMax + tickSpacing / 2, tickSpacing))
            .tickFormat(d => `${Math.round(d * 100)}%`);
    }

    g.append("g")
        .attr("transform", `translate(0,${innerHeight})`)
        .call(xAxis)
        .style("font-size", "10px")
        .select(".domain").style("stroke-width", "0.5px").style("stroke", "gray");

    g.append("g")
        .call(yAxis)
        .style("font-size", "10px")
        .select(".domain").style("stroke-width", "0.5px").style("stroke", "gray");

    // labels
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
        .text(yLabel);

    // legend
    const legend = g.append("g").attr("transform", `translate(${innerWidth - 80}, 10)`);
    legend.append("line")
        .attr("x1", 0).attr("x2", 30)
        .attr("y1", 0).attr("y2", 0)
        .attr("stroke", color)
        .attr("stroke-width", 2.5);
    legend.append("circle")
        .attr("cx", 15).attr("cy", 0).attr("r", 3)
        .attr("fill", color)
        .attr("stroke", "white")
        .attr("stroke-width", 1.5);
    legend.append("text")
        .attr("x", 35).attr("y", 4)
        .style("font-size", "10px")
        .text('Overlap');
}
