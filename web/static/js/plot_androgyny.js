/**
 * Plotter for single-series time trends with optional regression line.
 * Specifically designed for androgyny data (single proportion over time).
 * 
 * Data format:
 *   [{ year: 2001, proportion: 0.05, total_babies: 1000, androgynous_babies: 50 }, ...]
 * 
 * Options:
 *   { width, height, margin, androgynousColor, yLabel, title, regressionStats }
 * 
 * regressionStats:
 *   { slope, intercept, r_squared, p_value, years: [y1,...] }
 */

function plotAndrogyny(data, containerId, options = {}) {
    const {
        width = 800,
        height = 500,
        margin = { top: 40, right: 120, bottom: 60, left: 60 },
        androgynousColor = '#2ca02c',
        yLabel = 'Proportion',
        title = null,
        regressionStats = null
    } = options;

    // Clear old content
    d3.select(`#${containerId}`).selectAll("*").remove();

    // Validate / prep
    const clean = (data || [])
        .filter(d => d && typeof d.year === 'number' && isFinite(d.proportion))
        .map(d => ({
            year: d.year,
            proportion: +d.proportion,
            total: d.total || 0,
            androgynous: d.androgynous || 0
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
    const yMax = Math.max(0.05, Math.ceil((d3.max(clean, d => d.proportion) || 0.1) * 1.1 * 20) / 20);

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
    if (yMax <= 0.1) tickSpacing = 0.02;
    else if (yMax <= 0.2) tickSpacing = 0.05;
    else if (yMax <= 0.5) tickSpacing = 0.1;
    else tickSpacing = 0.2;

    const lineGen = d3.line()
        .x(d => xScale(d.year))
        .y(d => yScale(d.proportion))
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
        .attr("stroke", androgynousColor)
        .attr("stroke-width", 2.5)
        .attr("d", lineGen);

    // draw points
    const points = g.selectAll(".dot-androgynous")
        .data(clean)
        .enter().append("circle")
        .attr("class", "dot-androgynous")
        .attr("cx", d => xScale(d.year))
        .attr("cy", d => yScale(d.proportion))
        .attr("r", 3)
        .attr("fill", androgynousColor)
        .attr("stroke", "white")
        .attr("stroke-width", 1.5);

    // tooltip
    points.append("title").text(d => {
        const pct = (d.proportion * 100).toFixed(1);
        return `Year: ${d.year}\n${yLabel}: ${formatNumber(d.androgynous)}/${formatNumber(d.total)} (${pct}%)`;
    });

    // regression line (optional)
    if (regressionStats && regressionStats.years && regressionStats.years.length >= 2) {
        const rs = regressionStats;
        const minY = Math.min(...rs.years);
        const maxY = Math.max(...rs.years);
        const lineData = [
            { year: minY, proportion: rs.slope * minY + rs.intercept },
            { year: maxY, proportion: rs.slope * maxY + rs.intercept }
        ];

        const sig = rs.p_value < 0.05;

        g.append("path")
            .datum(lineData)
            .attr("fill", "none")
            .attr("stroke", androgynousColor)
            .attr("stroke-width", sig ? 1.5 : 1.5)
            .attr("stroke-dasharray", sig ? "none" : "5,5")
            .attr("opacity", sig ? 0.9 : 0.6)
            .attr("d", d3.line()
                .x(d => xScale(d.year))
                .y(d => yScale(d.proportion))
            )
            .append("title")
            .text(`Regression: slope=${rs.slope.toFixed(4)}, p=${rs.p_value.toFixed(3)}, `
                + (sig ? 'significant' : 'not significant'));
    }

    // axes
    const xAxis = d3.axisBottom(xScale).tickFormat(d3.format("d")).ticks(Math.min(years.length, 10));
    const yAxis = d3.axisLeft(yScale)
        .tickValues(d3.range(0, yMax + tickSpacing / 2, tickSpacing))
        .tickFormat(d => `${Math.round(d * 100)}%`);

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

    if (title) {
        svg.append("text")
            .attr("x", width / 2)
            .attr("y", margin.top / 2)
            .attr("text-anchor", "middle")
            .style("font-size", "12px")
            .text(title);
    }

    // legend
    const legend = g.append("g").attr("transform", `translate(${innerWidth - 100}, 10)`);
    legend.append("line")
        .attr("x1", 0).attr("x2", 30)
        .attr("y1", 0).attr("y2", 0)
        .attr("stroke", androgynousColor)
        .attr("stroke-width", 2.5);
    legend.append("circle")
        .attr("cx", 15).attr("cy", 0).attr("r", 3)
        .attr("fill", androgynousColor)
        .attr("stroke", "white")
        .attr("stroke-width", 1.5);
    legend.append("text")
        .attr("x", 35).attr("y", 4)
        .style("font-size", "10px")
        .text('Androgynous');

    // summary (bottom left)
    const sum = g.append("g").attr("transform", `translate(10, ${innerHeight - 20})`);
    const totalAndrogynous = d3.sum(clean, d => d.androgynous);
    const totalBabies = d3.sum(clean, d => d.total);
    const overallPct = totalBabies > 0 ? (totalAndrogynous / totalBabies * 100).toFixed(1) : '0.0';
    
    const msg = `Overall: ${overallPct}% (${formatNumber(totalAndrogynous)}/${formatNumber(totalBabies)})`;
    sum.append("text")
        .style("font-size", "10px")
        .style("fill", "#666")
        .text(msg);
}
