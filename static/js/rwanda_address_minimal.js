/**
 * Rwanda Address System — Live data from GitHub (ngabovictor/Rwanda)
 * Full 5 provinces → 30 districts → 416 sectors → 2148 cells → 14837 villages
 * Source: https://github.com/ngabovictor/Rwanda (public domain)
 */

const RWANDA_DATA_URL = 'https://raw.githubusercontent.com/ngabovictor/Rwanda/master/data.json';

const PROVINCE_NAMES = {
  'East':   'Eastern Province',
  'West':   'Western Province',
  'North':  'Northern Province',
  'South':  'Southern Province',
  'Kigali': 'Kigali City'
};

let rwandaData = null;

async function loadRwandaData() {
  if (rwandaData) return rwandaData;
  try {
    const res = await fetch(RWANDA_DATA_URL);
    if (!res.ok) throw new Error('Network error ' + res.status);
    rwandaData = await res.json();
    return rwandaData;
  } catch (e) {
    console.error('[Rwanda] Failed to load location data:', e);
    return null;
  }
}

function resetSelect(sel, placeholder) {
  if (!sel) return;
  sel.innerHTML = '<option value="">' + placeholder + '</option>';
  sel.disabled = true;
}

function fillSelect(sel, items, placeholder) {
  if (!sel) return;
  sel.innerHTML = '<option value="">' + placeholder + '</option>';
  [...items].sort().forEach(function(item) {
    const opt = document.createElement('option');
    opt.value = item;
    opt.textContent = item;
    sel.appendChild(opt);
  });
  sel.disabled = false;
}

document.addEventListener('DOMContentLoaded', async function () {
  const provinceEl = document.getElementById('province');
  const districtEl = document.getElementById('district');
  const sectorEl   = document.getElementById('sector');
  const cellEl     = document.getElementById('cell');
  const villageEl  = document.getElementById('village');

  if (!provinceEl) return;

  provinceEl.innerHTML = '<option value="">Loading provinces...</option>';
  provinceEl.disabled = true;

  const data = await loadRwandaData();
  if (!data) {
    provinceEl.innerHTML = '<option value="">Failed to load — check internet connection</option>';
    return;
  }

  // Populate provinces — Kigali first, then alphabetical
  provinceEl.innerHTML = '<option value="">Select Province...</option>';
  const provinceKeys = Object.keys(data).sort(function(a, b) {
    if (a === 'Kigali') return -1;
    if (b === 'Kigali') return 1;
    return a.localeCompare(b);
  });
  provinceKeys.forEach(function(key) {
    const opt = document.createElement('option');
    opt.value = key;
    opt.textContent = PROVINCE_NAMES[key] || key;
    provinceEl.appendChild(opt);
  });
  provinceEl.disabled = false;

  // Province → District
  provinceEl.addEventListener('change', function () {
    resetSelect(districtEl, 'Select District...');
    resetSelect(sectorEl,   'Select Sector...');
    resetSelect(cellEl,     'Select Cell...');
    resetSelect(villageEl,  'Select Village...');
    if (!this.value || !data[this.value]) return;
    fillSelect(districtEl, Object.keys(data[this.value]), 'Select District...');
  });

  // District → Sector
  if (districtEl) districtEl.addEventListener('change', function () {
    resetSelect(sectorEl,  'Select Sector...');
    resetSelect(cellEl,    'Select Cell...');
    resetSelect(villageEl, 'Select Village...');
    const prov = provinceEl.value;
    if (!this.value || !prov) return;
    const sectors = (data[prov] || {})[this.value];
    if (sectors) fillSelect(sectorEl, Object.keys(sectors), 'Select Sector...');
  });

  // Sector → Cell
  if (sectorEl) sectorEl.addEventListener('change', function () {
    resetSelect(cellEl,    'Select Cell...');
    resetSelect(villageEl, 'Select Village...');
    const prov = provinceEl.value;
    const dist = districtEl ? districtEl.value : '';
    if (!this.value || !prov || !dist) return;
    const cells = ((data[prov] || {})[dist] || {})[this.value];
    if (cells) fillSelect(cellEl, Object.keys(cells), 'Select Cell...');
  });

  // Cell → Village
  if (cellEl) cellEl.addEventListener('change', function () {
    resetSelect(villageEl, 'Select Village...');
    const prov = provinceEl.value;
    const dist = districtEl ? districtEl.value : '';
    const sec  = sectorEl   ? sectorEl.value   : '';
    if (!this.value || !prov || !dist || !sec) return;
    const villages = (((data[prov] || {})[dist] || {})[sec] || {})[this.value];
    if (villages && villages.length) fillSelect(villageEl, villages, 'Select Village...');
  });
});
