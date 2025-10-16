document.addEventListener('DOMContentLoaded', function () {
  function qs(selector, root) {
    return (root || document).querySelector(selector);
  }
  function qsa(selector, root) {
    return Array.prototype.slice.call((root || document).querySelectorAll(selector));
  }
  function fmt(number) {
    var n = Number(number || 0);
    return n.toLocaleString(undefined, { maximumFractionDigits: 0 });
  }

  var state = {
    allVehicles: [],
    filtered: [],
    selectedVehicleId: null,
    types: [], // from API car-types
    typeIdToName: {}
  };

  // DOM refs
  var tblBody = qs('#vehicleTableBody');
  var totalEl = qs('#vehicleTotal');
  var searchInput = qs('#vehicleSearch');
  var typeFilter = qs('#vehicleTypeFilter');
  var refreshBtn = qs('#btnRefreshVehicles');

  // Modal DOM refs
  var modalTblBody = qs('#selectVehicleTableBody');
  var modalSearch = qs('#selectVehicleSearch');
  var modalTypeFilter = qs('#selectVehicleTypeFilter');
  var btnConfirmSelect = qs('#btnConfirmSelectVehicle');

  function uniqueTypesFromApi(types) {
    return (types || []).map(function (t) { return { id: t.type_id, name: t.type_name }; });
  }

  function populateTypeFilter(selectEl, types) {
    if (!selectEl) return;
    var current = selectEl.value;
    selectEl.innerHTML = '';
    var optAll = document.createElement('option');
    optAll.value = '';
    optAll.textContent = 'All types';
    selectEl.appendChild(optAll);
    (uniqueTypesFromApi(types) || []).forEach(function (t) {
      var opt = document.createElement('option');
      opt.value = String(t.id);
      opt.textContent = t.name;
      selectEl.appendChild(opt);
    });
    // Try to preserve current selection
    selectEl.value = current;
  }

  function filterVehicles(list, term, typeId) {
    term = (term || '').trim().toLowerCase();
    typeId = (typeId || '').trim();
    return list.filter(function (v) {
      var matchesTerm = !term || (
        String(v.license_plate || '').toLowerCase().includes(term) ||
        String(v.status || '').toLowerCase().includes(term)
      );
      var matchesType = !typeId || String(v.type_id || '') === typeId;
      return matchesTerm && matchesType;
    });
  }

  function renderTable(bodyEl, vehicles, withSelectControl) {
    if (!bodyEl) return;
    bodyEl.innerHTML = '';
    if (!vehicles.length) {
      var trEmpty = document.createElement('tr');
      trEmpty.className = 'muted';
      var td = document.createElement('td');
      td.colSpan = withSelectControl ? 6 : 9;
      td.textContent = 'No vehicles loaded.';
      trEmpty.appendChild(td);
      bodyEl.appendChild(trEmpty);
      return;
    }
    vehicles.forEach(function (v) {
      var tr = document.createElement('tr');
      if (withSelectControl) {
        var tdSel = document.createElement('td');
        var radio = document.createElement('input');
        radio.type = 'radio';
        radio.name = 'selectVehicleRadio';
        radio.value = String(v.car_id || v.id || '');
        radio.addEventListener('change', function () {
          state.selectedVehicleId = v.car_id || v.id || null;
          if (btnConfirmSelect) btnConfirmSelect.disabled = false;
        });
        tdSel.appendChild(radio);
        tr.appendChild(tdSel);
      }
      function td(text) {
        var cell = document.createElement('td');
        cell.textContent = text;
        return cell;
      }
      tr.appendChild(td(String(v.car_id || '—')));
      tr.appendChild(td(String(v.license_plate || '—')));
      tr.appendChild(td(fmt(v.daily_rate || v.price_per_day || 0)));
      tr.appendChild(td(fmt(v.hourly_rate || 0)));
      tr.appendChild(td(String(v.status || '—')));
      if (!withSelectControl) {
        var tdAct = document.createElement('td');
        var btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'btn';
        btn.textContent = 'Select';
        btn.addEventListener('click', function () {
          state.selectedVehicleId = v.car_id || v.id || null;
          document.dispatchEvent(new CustomEvent('vehicle:select:confirm'));
        });
        tdAct.appendChild(btn);
        tr.appendChild(tdAct);
      }
      bodyEl.appendChild(tr);
    });
  }

  function updateTotals() {
    if (totalEl) totalEl.textContent = String(state.filtered.length) + ' vehicles';
  }

  function applyFilterAndRender() {
    state.filtered = filterVehicles(
      state.allVehicles,
      (searchInput && searchInput.value) || '',
      (typeFilter && typeFilter.value) || ''
    );
    renderTable(tblBody, state.filtered, false);
    updateTotals();
  }

  function applyModalFilterAndRender() {
    var list = filterVehicles(
      state.allVehicles,
      (modalSearch && modalSearch.value) || '',
      (modalTypeFilter && modalTypeFilter.value) || ''
    );
    renderTable(modalTblBody, list, true);
    if (btnConfirmSelect) btnConfirmSelect.disabled = !state.selectedVehicleId;
  }

  async function loadVehicles() {
    try {
      // Load types once
      if (window.api && typeof window.api.listVehicleTypes === 'function') {
        try {
          state.types = await window.api.listVehicleTypes();
          state.typeIdToName = {};
          (state.types || []).forEach(function (t) {
            state.typeIdToName[String(t.type_id)] = t.type_name;
          });
          populateTypeFilter(typeFilter, state.types);
          populateTypeFilter(modalTypeFilter, state.types);
        } catch (_) {}
      }
      var params = {
        search: (searchInput && searchInput.value) || undefined,
        type_id: (typeFilter && typeFilter.value) || undefined,
        skip: 0,
        limit: 100
      };
      if (window.api && typeof window.api.listVehicles === 'function') {
        var list = await window.api.listVehicles(params);
        state.allVehicles = Array.isArray(list) ? list : [];
      } else {
        state.allVehicles = [];
      }
      applyFilterAndRender();
      applyModalFilterAndRender();
    } catch (err) {
      console.error('Failed to load vehicles:', err);
      state.allVehicles = [];
      applyFilterAndRender();
      applyModalFilterAndRender();
    }
  }

  function updateSelectedVehicleSummary(vehicle) {
    var info = qs('#selectedVehicleInfo');
    if (info) {
      var label = '—';
      if (vehicle) {
        var typeName = state.typeIdToName[String(vehicle.type_id || '')] || '—';
        label = (vehicle.license_plate || '—') + ' · ' + typeName + ' — ' + fmt(vehicle.price_per_day || 0) + '/day';
      }
      info.textContent = label;
    }
    // Update payment summary fields if present
    var priceEl = qs('#summaryVehicleDailyPrice');
    if (priceEl) priceEl.textContent = vehicle ? fmt(vehicle.daily_rate || vehicle.price_per_day || 0) : '0';
    var summaryVehicle = qs('#summaryVehicle');
    if (summaryVehicle) summaryVehicle.textContent = vehicle ? (vehicle.license_plate || '—') : '—';
    // expose selected vehicle globally for contract creation
    window.appSelectedVehicle = vehicle || null;
  }

  // Event wiring
  if (searchInput) searchInput.addEventListener('input', applyFilterAndRender);
  if (typeFilter) typeFilter.addEventListener('change', applyFilterAndRender);
  if (refreshBtn) refreshBtn.addEventListener('click', loadVehicles);

  if (modalSearch) modalSearch.addEventListener('input', applyModalFilterAndRender);
  if (modalTypeFilter) modalTypeFilter.addEventListener('change', applyModalFilterAndRender);

  document.addEventListener('vehicles:refresh', loadVehicles);

  document.addEventListener('vehicle:select:confirm', function () {
    if (!state.selectedVehicleId) return;
    var v = state.allVehicles.find(function (x) { return (x.car_id || x.id) === state.selectedVehicleId; });
    if (!v) return;
    updateSelectedVehicleSummary(v);
    // Reset selection state for next time
    state.selectedVehicleId = null;
    if (btnConfirmSelect) btnConfirmSelect.disabled = true;
  });

  // Initial load
  loadVehicles();
  applyModalFilterAndRender();
});


