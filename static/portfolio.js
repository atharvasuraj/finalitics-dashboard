'use strict';
const sample = document.getElementById('sampleButton');
const upload = document.getElementById('uploadButton');
const fileInput = document.getElementById('portfolioFile');
const error = document.getElementById('error');
const results = document.getElementById('results');
const loading = document.getElementById('loading');
const percent = value => `${(value * 100).toFixed(2)}%`;

function render(data) {
  document.getElementById('period').textContent = `${data.period.start} to ${data.period.end} · ${data.period.observations} common observations · index starts at 100`;
  const metrics = document.getElementById('metrics');
  metrics.replaceChildren();
  for (const [key, label] of [['total_return', 'Total return'], ['cagr', 'CAGR'], ['annualized_volatility', 'Annualized volatility'], ['max_drawdown', 'Maximum drawdown']]) {
    const card = document.createElement('div');
    card.className = 'metric';
    const name = document.createElement('span');
    name.textContent = label;
    const value = document.createElement('strong');
    value.textContent = percent(data.metrics[key]);
    card.append(name, value);
    metrics.append(card);
  }
  document.getElementById('chart').src = `data:image/png;base64,${data.chart}`;
  const allocations = document.getElementById('allocations');
  allocations.replaceChildren();
  for (const allocation of data.allocations) {
    const row = document.createElement('tr');
    for (const text of [allocation.symbol, `${allocation.weight_percent.toFixed(2)}%`]) {
      const cell = document.createElement('td');
      cell.textContent = text;
      row.append(cell);
    }
    allocations.append(row);
  }
  document.getElementById('dataset').textContent = `${data.dataset.provider} · ${data.dataset.currency} · adjusted stock closing prices (not mutual-fund NAVs). Retrieved ${data.dataset.retrieved_at_utc}.`;
  document.getElementById('provenance').textContent = JSON.stringify({sha256: data.dataset.sha256, coverage: data.dataset.coverage, yfinance_version: data.dataset.yfinance_version}, null, 2);
  results.hidden = false;
}

async function analyse(url, options) {
  sample.disabled = upload.disabled = true;
  loading.hidden = false;
  error.hidden = true;
  results.hidden = true;
  try {
    const response = await fetch(url, options);
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Analysis could not be completed.');
    render(data);
  } catch (failure) {
    error.textContent = failure.message || 'Unable to reach the local analyser. Check that the server is running.';
    error.hidden = false;
  } finally {
    loading.hidden = true;
    sample.disabled = upload.disabled = false;
  }
}

sample.addEventListener('click', () => analyse('/portfolio-sample'));
document.getElementById('uploadForm').addEventListener('submit', event => {
  event.preventDefault();
  const file = fileInput.files[0];
  if (!file) return;
  if (file.size > 1024 * 1024) {
    results.hidden = true;
    error.textContent = 'Upload exceeds the 1 MB limit. Use a small portfolio CSV.';
    error.hidden = false;
    return;
  }
  const data = new FormData();
  data.append('file', file);
  analyse('/portfolio-analyser-upload', {method: 'POST', body: data});
});
