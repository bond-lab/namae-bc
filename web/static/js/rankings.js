/* rankings.js — Interactive top-names ranking tables
 *
 * Renders ranking tables from JSON data, with:
 *  - Color coding for names that were ever #1
 *  - Click-to-highlight: clicking a name highlights all its occurrences
 *  - Toggle between top 10 / top 50
 */

// Distinct colors for #1 names (pastel-ish for readability)
const RANK1_COLORS = [
  '#ffadad', '#ffd6a5', '#fdffb6', '#caffbf', '#9bf6ff',
  '#a0c4ff', '#bdb2ff', '#ffc6ff', '#fffffc', '#d4a5a5',
  '#a5d4d4', '#d4d4a5', '#c9a5d4', '#a5c9d4', '#d4bca5',
];

function buildColorMap(numberOnes) {
  const map = {};
  numberOnes.forEach((name, i) => {
    map[name] = RANK1_COLORS[i % RANK1_COLORS.length];
  });
  return map;
}

function renderRankingTable(container, data, colorMap) {
  container.innerHTML = '';
  const years = data.years;
  if (!years || years.length === 0) {
    container.innerHTML = '<p class="text-muted">No data available.</p>';
    return;
  }

  const namesByYear = data.names_by_year;

  // Find max number of rows (max entries in any year)
  let maxRows = 0;
  years.forEach(y => {
    const entries = namesByYear[String(y)] || [];
    if (entries.length > maxRows) maxRows = entries.length;
  });

  const table = document.createElement('table');
  table.className = 'table table-sm table-bordered rankings-table';

  // Header
  const thead = document.createElement('thead');
  const headerRow = document.createElement('tr');
  const rankTh = document.createElement('th');
  rankTh.textContent = '#';
  rankTh.className = 'rank-col';
  headerRow.appendChild(rankTh);
  years.forEach(y => {
    const th = document.createElement('th');
    th.textContent = y;
    th.className = 'year-col';
    headerRow.appendChild(th);
  });
  thead.appendChild(headerRow);
  table.appendChild(thead);

  // Body — one row per rank slot
  const tbody = document.createElement('tbody');
  for (let row = 0; row < maxRows; row++) {
    const tr = document.createElement('tr');

    // Rank label — use rank from first year that has this row
    let rankLabel = row + 1;
    for (const y of years) {
      const entries = namesByYear[String(y)] || [];
      if (entries[row]) {
        rankLabel = entries[row].rank;
        break;
      }
    }
    const rankTd = document.createElement('td');
    rankTd.textContent = rankLabel;
    rankTd.className = 'rank-col text-muted';
    tr.appendChild(rankTd);

    years.forEach(y => {
      const td = document.createElement('td');
      td.className = 'name-cell';
      const entries = namesByYear[String(y)] || [];
      const entry = entries[row];
      if (entry) {
        td.textContent = entry.name;
        td.setAttribute('data-name', entry.name);
        td.title = `${entry.name} — rank ${entry.rank}, freq ${entry.freq}`;
        if (colorMap[entry.name]) {
          td.style.backgroundColor = colorMap[entry.name];
          td.classList.add('name-rank1');
        }
      }
      tr.appendChild(td);
    });

    tbody.appendChild(tr);
  }
  table.appendChild(tbody);
  container.appendChild(table);

  // Setup click-to-highlight
  setupHighlight(container);
}

function setupHighlight(container) {
  const cells = container.querySelectorAll('.name-cell[data-name]');
  cells.forEach(cell => {
    cell.addEventListener('click', function () {
      const name = this.getAttribute('data-name');
      const allCells = container.querySelectorAll('.name-cell');
      const isAlreadyHighlighted = this.classList.contains('highlighted');

      // Clear all highlights first
      allCells.forEach(c => c.classList.remove('highlighted'));

      // If not already highlighted, highlight all matching
      if (!isAlreadyHighlighted) {
        allCells.forEach(c => {
          if (c.getAttribute('data-name') === name) {
            c.classList.add('highlighted');
          }
        });
      }
    });
  });
}

function initRankings(datasets) {
  datasets.forEach((ds, i) => {
    // Build combined color maps (union of #1 names across genders and n_tops)
    const allNumberOnes = new Set();
    ['male', 'female', 'male_50', 'female_50'].forEach(key => {
      if (ds[key] && ds[key].number_ones) {
        ds[key].number_ones.forEach(n => allNumberOnes.add(n));
      }
    });

    // Separate color maps per gender (different names may be #1)
    const maleOnes = new Set();
    ['male', 'male_50'].forEach(k => {
      if (ds[k] && ds[k].number_ones) ds[k].number_ones.forEach(n => maleOnes.add(n));
    });
    const femaleOnes = new Set();
    ['female', 'female_50'].forEach(k => {
      if (ds[k] && ds[k].number_ones) ds[k].number_ones.forEach(n => femaleOnes.add(n));
    });

    const maleColorMap = buildColorMap([...maleOnes]);
    const femaleColorMap = buildColorMap([...femaleOnes]);

    // Store on the dataset for toggle reuse
    ds._maleColorMap = maleColorMap;
    ds._femaleColorMap = femaleColorMap;

    // Render default (top 10)
    renderForDataset(ds, i, 10);

    // Setup toggle buttons
    const btn10 = document.getElementById(`btn-top10-${i}`);
    const btn50 = document.getElementById(`btn-top50-${i}`);
    if (btn10 && btn50) {
      btn10.addEventListener('click', () => {
        btn10.classList.add('active');
        btn50.classList.remove('active');
        renderForDataset(ds, i, 10);
      });
      btn50.addEventListener('click', () => {
        btn50.classList.add('active');
        btn10.classList.remove('active');
        renderForDataset(ds, i, 50);
      });
    }
  });
}

function renderForDataset(ds, idx, nTop) {
  const maleKey = nTop === 10 ? 'male' : 'male_50';
  const femaleKey = nTop === 10 ? 'female' : 'female_50';

  const maleContainer = document.getElementById(`table-male-${idx}`);
  const femaleContainer = document.getElementById(`table-female-${idx}`);

  if (maleContainer && ds[maleKey]) {
    renderRankingTable(maleContainer, ds[maleKey], ds._maleColorMap);
  }
  if (femaleContainer && ds[femaleKey]) {
    renderRankingTable(femaleContainer, ds[femaleKey], ds._femaleColorMap);
  }
}
