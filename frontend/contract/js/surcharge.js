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
    items: [], // { id, name, unitPrice, quantity, amount, note }
    editId: null
  };

  // Expose a tiny API for other scripts (optional)
  window.appSurcharges = {
    getAll: function () { return state.items.slice(); },
    getTotal: function () { return state.items.reduce(function (s, x) { return s + Number(x.amount || 0); }, 0); }
  };

  // Elements
  var tblBody = qs('#surchargeTableBody');
  var countEl = qs('#surchargeCount');
  var totalEl = qs('#surchargeTotalAmount');
  var btnClear = qs('#btnClearSurcharges');

  // Modal elements
  var modal = qs('#modalSurcharge');
  var inputId = qs('#surchargeId');
  var inputName = qs('#surchargeName');
  var inputUnitPrice = qs('#surchargeUnitPrice');
  var inputQuantity = qs('#surchargeQuantity');
  var inputNote = qs('#surchargeNote');

  function renderTable() {
    if (!tblBody) return;
    tblBody.innerHTML = '';
    if (!state.items.length) {
      var trEmpty = document.createElement('tr');
      trEmpty.className = 'muted';
      var td = document.createElement('td');
      td.colSpan = 5;
      td.textContent = 'No surcharges added.';
      trEmpty.appendChild(td);
      tblBody.appendChild(trEmpty);
      return;
    }
    state.items.forEach(function (item, idx) {
      var tr = document.createElement('tr');
      function td(text) {
        var cell = document.createElement('td');
        cell.textContent = text;
        return cell;
      }
      tr.appendChild(td(String(idx + 1)));
      tr.appendChild(td(item.name || ''));
      tr.appendChild(td(fmt(item.unitPrice || 0)));
      tr.appendChild(td(String(item.quantity || 1)));
      tr.appendChild(td(fmt(item.amount || 0)));
      tr.appendChild(td(item.note || ''));
      var tdAct = document.createElement('td');
      var btnEdit = document.createElement('button');
      btnEdit.type = 'button';
      btnEdit.className = 'btn';
      btnEdit.textContent = 'Edit';
      btnEdit.addEventListener('click', function () {
        openEdit(item.id);
      });
      var btnDel = document.createElement('button');
      btnDel.type = 'button';
      btnDel.className = 'btn danger';
      btnDel.textContent = 'Delete';
      btnDel.addEventListener('click', function () {
        removeItem(item.id);
      });
      tdAct.appendChild(btnEdit);
      tdAct.appendChild(btnDel);
      tr.appendChild(tdAct);
      tblBody.appendChild(tr);
    });
  }

  function updateSummary() {
    var total = state.items.reduce(function (s, x) { return s + Number(x.amount || 0); }, 0);
    if (countEl) countEl.textContent = String(state.items.length);
    if (totalEl) totalEl.textContent = fmt(total);
    var summarySurchargeTotal = qs('#summarySurchargeTotal');
    if (summarySurchargeTotal) summarySurchargeTotal.textContent = fmt(total);
    // Let other modules recompute grand totals if they listen
    document.dispatchEvent(new CustomEvent('payment:recalculate'));
  }

  function resetModal() {
    state.editId = null;
    if (inputId) inputId.value = '';
    if (inputName) inputName.value = '';
    if (inputUnitPrice) inputUnitPrice.value = '';
    if (inputQuantity) inputQuantity.value = '1';
    if (inputNote) inputNote.value = '';
  }

  function openEdit(id) {
    var item = state.items.find(function (x) { return x.id === id; });
    if (!item) return;
    state.editId = id;
    if (inputId) inputId.value = String(item.id);
    if (inputName) inputName.value = item.name || '';
    if (inputAmount) inputAmount.value = String(item.amount || 0);
    if (inputNote) inputNote.value = item.note || '';
    // Show modal
    if (modal) {
      modal.setAttribute('aria-hidden', 'false');
      modal.classList.add('open');
    }
  }

  function removeItem(id) {
    state.items = state.items.filter(function (x) { return x.id !== id; });
    renderTable();
    updateSummary();
  }

  function upsertFromModal() {
    if (!inputName || !inputUnitPrice || !inputQuantity) return;
    var name = (inputName.value || '').trim();
    var unitPrice = Number(inputUnitPrice.value || 0);
    var quantity = Math.max(1, Number(inputQuantity.value || 1));
    var note = (inputNote && inputNote.value) || '';
    if (!name) return;
    if (isNaN(unitPrice) || unitPrice < 0) return;
    var amount = unitPrice * quantity;
    if (state.editId) {
      var idx = state.items.findIndex(function (x) { return x.id === state.editId; });
      if (idx >= 0) {
        state.items[idx] = { id: state.editId, name: name, unitPrice: unitPrice, quantity: quantity, amount: amount, note: note };
      }
    } else {
      var newId = Date.now();
      state.items.push({ id: newId, name: name, unitPrice: unitPrice, quantity: quantity, amount: amount, note: note });
    }
    resetModal();
    renderTable();
    updateSummary();
  }

  function clearAll() {
    state.items = [];
    renderTable();
    updateSummary();
  }

  // Events from main.js
  document.addEventListener('surcharge:save', function () {
    upsertFromModal();
  });

  if (btnClear) {
    btnClear.addEventListener('click', function () {
      clearAll();
    });
  }

  // When previewing the contract, populate the surcharge table in the view modal
  function renderContractViewSurcharges() {
    var body = qs('#contractViewSurchargesTableBody');
    var totalCell = qs('#contractViewSurchargeTotal');
    if (!body) return;
    body.innerHTML = '';
    if (!state.items.length) {
      var trEmpty = document.createElement('tr');
      trEmpty.className = 'muted';
      var td = document.createElement('td');
      td.colSpan = 4;
      td.textContent = 'No surcharges.';
      trEmpty.appendChild(td);
      body.appendChild(trEmpty);
    } else {
      state.items.forEach(function (item, idx) {
        var tr = document.createElement('tr');
        function td(text) { var c = document.createElement('td'); c.textContent = text; return c; }
        tr.appendChild(td(String(idx + 1)));
        tr.appendChild(td(item.name || ''));
        tr.appendChild(td(fmt(item.amount)));
        tr.appendChild(td(item.note || ''));
        body.appendChild(tr);
      });
    }
    if (totalCell) totalCell.textContent = fmt(state.items.reduce(function (s, x) { return s + Number(x.amount || 0); }, 0));
  }

  var btnPreview = qs('#btnPreviewContract');
  if (btnPreview) {
    btnPreview.addEventListener('click', function () {
      renderContractViewSurcharges();
    });
  }

  // Initial render
  renderTable();
  updateSummary();
});


