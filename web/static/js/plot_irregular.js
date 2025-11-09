/**
 * Generic, reusable plotter for two-series (M/F) time trends with optional regression lines.
 * Data format:
 *   [{ year: 2001, gender: 'M'|'F', value: <number>, numerator?: n, denominator?: d }, ...]
 * Options:
 *   { width, height, margin, maleColor, femaleColor, yLabel, title, regressionStats }
 * regressionStats:
 *   { M: { slope, intercept, r_squared, p_value, years: [y1,...] },
 *     F: { ... } }
 */

function plotDataAndTrend(data, containerId, options = {}) {
    const {
        width = 800,
        height = 500,
        margin = { top: 40, right: 120, bottom: 60, left: 60 },
        maleColor = '#ff7f0e',
        femaleColor = '#9467bd',
        yLabel = 'Proportion',
        title = null,
        regressionStats = null
    } = options;

    // Clear old content
    d3.select(`#${containerId}`).selectAll("*").remove();

    // Validate / prep
    const clean = (data || [])
      .filter(d => d && typeof d.year === 'number' && (d.gender === 'M' || d.gender === 'F') && isFinite(d.value))
      .map(d => ({
          year: d.year,
          gender: d.gender,
          value: +d.value,
          n: d.numerator ?? d.irregular_names,   // allow legacy fields
          N: d.denominator ?? d.number
      }));

    if (clean.length === 0) {
        d3.select(`#${containerId}`)
            .append('div')
            .attr('class', 'alert alert-warning')
            .text('No data available.');
        return;
    }

    const maleData = clean.filter(d => d.gender === 'M').sort((a,b)=>a.year-b.year);
    const femaleData = clean.filter(d => d.gender === 'F').sort((a,b)=>a.year-b.year);

    const years = [...new Set(clean.map(d => d.year))].sort((a,b)=>a-b);
    const yMax = Math.max(0.05, Math.ceil((d3.max(clean, d => d.value) || 0.1) * 1.1 * 20) / 20);

    const svg = d3.select(`#${containerId}`)
        .append("svg")
        .attr("width", width)
        .attr("height", height)
        .style("font-family", "'Noto Sans CJK JP', 'Noto Sans CJK SC', 'DejaVu Sans', sans-serif");

    const g = svg.append("g")
        .attr("transform", `translate(${margin.left},${margin.top})`);

    const innerWidth  = width  - margin.left - margin.right;
    const innerHeight = height - margin.top  - margin.bottom;

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
        .y(d => yScale(d.value))
        .curve(d3.curveMonotoneX);

    // grid
    g.append("g")
        .attr("class", "grid")
        .selectAll("line")
        .data(d3.range(0, yMax + tickSpacing/2, tickSpacing))
        .enter().append("line")
        .attr("x1", 0).attr("x2", innerWidth)
        .attr("y1", d => yScale(d)).attr("y2", d => yScale(d))
        .attr("stroke", "gray").attr("stroke-width", 0.5).attr("stroke-opacity", 0.3);

    // draw series helper
    function drawSeries(series, color, label, dotClass) {
        if (series.length === 0) return;

        g.append("path")
            .datum(series)
            .attr("fill", "none")
            .attr("stroke", color)
            .attr("stroke-width", 2.5)
            .attr("d", lineGen);

        const points = g.selectAll(`.${dotClass}`)
            .data(series)
            .enter().append("circle")
            .attr("class", dotClass)
            .attr("cx", d => xScale(d.year))
            .attr("cy", d => yScale(d.value))
            .attr("r", 3)
            .attr("fill", color)
            .attr("stroke", "white")
            .attr("stroke-width", 1.5);

        // tooltip text (show raw counts if present, else value)
        points.append("title").text(d => {
            const core = `Year: ${d.year}\n${label}\n`;
            if (isFinite(d.n) && isFinite(d.N)) {
                const pct = (d.value * 100).toFixed(1);
                return core + `${yLabel}: ${d.n}/${d.N} (${pct}%)`;
            }
            return core + `${yLabel}: ${d.value}`;
        });
    }

    drawSeries(maleData,   options.maleColor   || '#ff7f0e', 'Male',   'dot-male');
    drawSeries(femaleData, options.femaleColor || '#9467bd', 'Female', 'dot-female');

        // regression lines (optional)
    if (regressionStats) {
        for (const gkey of ['M', 'F']) {
            const rs = regressionStats[gkey];
            if (!rs || !Array.isArray(rs.years) || rs.years.length === 0) continue;

            const minY = Math.min(...rs.years);
            const maxY = Math.max(...rs.years);
            const lineData = [
                { year: minY, value: rs.slope * minY + rs.intercept },
                { year: maxY, value: rs.slope * maxY + rs.intercept }
            ];

            const color = gkey === 'M'
                ? (options.maleColor || '#ff7f0e')
                : (options.femaleColor || '#9467bd');

            const sig = rs.p_value < 0.05; // significance test

            g.append("path")
                .datum(lineData)
                .attr("fill", "none")
                .attr("stroke", color)
                .attr("stroke-width", sig ? 1.5 : 1.5)
                .attr("stroke-dasharray", sig ? "none" : "5,5")
                .attr("opacity", sig ? 0.9 : 0.6)
                .attr("d", d3.line()
                    .x(d => xScale(d.year))
                    .y(d => yScale(d.value))
                )
                .append("title")
                .text(`${gkey === 'M' ? 'Male' : 'Female'} regression:\n`
                      + `slope=${rs.slope.toFixed(4)}, p=${rs.p_value.toFixed(3)}, `
                      + (sig ? 'significant' : 'not significant') );
        }
    }

    // axes
    const xAxis = d3.axisBottom(xScale).tickFormat(d3.format("d")).ticks(Math.min(years.length, 10));
    const yAxis = d3.axisLeft(yScale)
        .tickValues(d3.range(0, yMax + tickSpacing/2, tickSpacing))
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
    function leg(y, color, text) {
        legend.append("line").attr("x1", 0).attr("x2", 30).attr("y1", y).attr("y2", y)
              .attr("stroke", color).attr("stroke-width", 2.5);
        legend.append("circle").attr("cx", 15).attr("cy", y).attr("r", 3)
              .attr("fill", color).attr("stroke", "white").attr("stroke-width", 1.5);
        legend.append("text").attr("x", 35).attr("y", y + 4).style("font-size", "10px").text(text);
    }
    leg(0,  options.maleColor   || '#ff7f0e', 'Male');
    leg(20, options.femaleColor || '#9467bd', 'Female');

    // summary (bottom left)
    const sum = g.append("g").attr("transform", `translate(10, ${innerHeight - 40})`);
    const tot = (arr, f) => d3.sum(arr, f);
    const M_n = tot(maleData, d => d.n || 0), M_N = tot(maleData, d => d.N || 0);
    const F_n = tot(femaleData, d => d.n || 0), F_N = tot(femaleData, d => d.N || 0);
    let msg;

    if (M_N > 0 && F_N > 0) {
        const Mp = (M_n / M_N * 100).toFixed(1);
        const Fp = (F_n / F_N * 100).toFixed(1);
        msg = `Overall: Male ${Mp}% (${formatNumber(M_n)}/${formatNumber(M_N)}), `
            + `Female ${Fp}% (${formatNumber(F_n)}/${formatNumber(F_N)})`;
    } else {
        // fallback to mean values if no counts were supplied
        const mean = arr => d3.mean(arr, d => d.value) * 100;
        msg = `Overall: Male ${mean(maleData).toFixed(1)}%, Female ${mean(femaleData).toFixed(1)}%`;
    }

    sum.append("text").style("font-size", "10px").style("fill", "#666").text(msg);
}

/**
 * Back-compat wrapper so the existing irregular page can keep calling plotIrregularNames(...)
 * It maps {irregular_names, number} to 'value' = irregular_names / number and forwards to the generic plotter.
 */
function plotIrregularNames(irregularData, containerId, options = {}) {
    const mapped = (irregularData || []).map(d => ({
        year: d.year,
        gender: d.gender,
        value: d.number > 0 ? (d.irregular_names / d.number) : 0,
        numerator: d.irregular_names,
        denominator: d.number
    }));
    const merged = Object.assign({ yLabel: 'Irregular Proportion', title: 'Irregular Name Mappings Over Time' }, options);
    plotDataAndTrend(mapped, containerId, merged);
}
