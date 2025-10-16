document.addEventListener('DOMContentLoaded', function () {
  function qs(selector, root) {
    return (root || document).querySelector(selector);
  }
  function fmt(number) {
    var n = Number(number || 0);
    return n.toLocaleString(undefined, { maximumFractionDigits: 0 });
  }
  function parseNum(el) {
    if (!el) return 0;
    var v = (el.value != null ? el.value : el.textContent) || '0';
    v = String(v).replace(/[^0-9.-]/g, '');
    var n = Number(v);
    return isNaN(n) ? 0 : n;
  }
  function diffDays(start, end) {
    if (!start || !end) return 0;
    var ms = end.getTime() - start.getTime();
    if (ms <= 0) return 0;
    var d = ms / (1000 * 60 * 60 * 24);
    return Math.ceil(d);
  }

  // Form fields
  var fCustomerSelect = qs('#customerSelect');
  var fName = null; // derive from selected customer
  var fPhone = qs('#customerPhone');
  var fId = qs('#customerIdNumber');
  var fAddress = qs('#customerAddress');
  var fStart = qs('#rentalStartDate');
  var fEnd = qs('#rentalEndDate');
  var fDeposit = qs('#depositAmount');
  var fDiscount = qs('#summaryDiscountAmount');
  var fPayNow = qs('#paymentNowAmount');
  var fNotes = qs('#contractNotes');
  var fMethod = qs('#paymentMethod');
  var selPickupBranch = qs('#pickupBranch');
  var selDropoffBranch = qs('#dropoffBranch');

  // Summary fields
  var sCustomer = qs('#summaryCustomerName');
  var sPeriod = qs('#summaryPeriod');
  var sDays = qs('#summaryRentalDays');
  var sDaily = qs('#summaryVehicleDailyPrice');
  var sVehicleSubtotal = qs('#summaryVehicleSubtotal');
  var sSurchargeTotal = qs('#summarySurchargeTotal');
  var sDeposit = qs('#summaryDeposit');
  var sGrand = qs('#summaryGrandTotal');
  var sRemaining = qs('#summaryRemaining');

  function getSurchargeTotal() {
    if (window.appSurcharges && typeof window.appSurcharges.getTotal === 'function') {
      return window.appSurcharges.getTotal();
    }
    return parseNum(sSurchargeTotal);
  }

  function getDailyPrice() {
    return parseNum(sDaily);
  }

  function getSelectedVehicleText() {
    var el = qs('#summaryVehicle');
    return el ? el.textContent || '—' : '—';
  }

  function recalc() {
    var start = fStart && fStart.value ? new Date(fStart.value) : null;
    var end = fEnd && fEnd.value ? new Date(fEnd.value) : null;
    var days = diffDays(start, end);
    if (sDays) sDays.textContent = String(days);

    if (sPeriod) {
      var p = '—';
      if (start && end) p = start.toLocaleString() + ' → ' + end.toLocaleString();
      sPeriod.textContent = p;
    }

    var customerText = (function () {
      if (fCustomerSelect && fCustomerSelect.selectedOptions && fCustomerSelect.selectedOptions[0]) {
        return fCustomerSelect.selectedOptions[0].textContent || '—';
      }
      return '—';
    })();
    if (sCustomer) sCustomer.textContent = customerText;

    var daily = getDailyPrice();
    var vehicleSubtotal = days > 0 ? (daily * days) : 0;
    if (sVehicleSubtotal) sVehicleSubtotal.textContent = fmt(vehicleSubtotal);

    var surchargeTotal = getSurchargeTotal();
    if (sSurchargeTotal) sSurchargeTotal.textContent = fmt(surchargeTotal);

    var deposit = parseNum(fDeposit);
    if (sDeposit) sDeposit.textContent = fmt(deposit);
    var discount = parseNum(fDiscount);
    var grand = Math.max(0, vehicleSubtotal + surchargeTotal - discount);
    if (sGrand) sGrand.textContent = fmt(grand);

    var payNow = parseNum(fPayNow);
    var remaining = Math.max(0, grand - payNow - deposit);
    if (sRemaining) sRemaining.textContent = fmt(remaining);
  }

  // Auto-fill customer info on selection (best-effort parse from display text)
  if (fCustomerSelect) {
    fCustomerSelect.addEventListener('change', function () {
      var sel = fCustomerSelect.selectedOptions && fCustomerSelect.selectedOptions[0];
      if (!sel) return;
      var text = sel.textContent || '';
      var parts = text.split('—');
      if (parts[1] && fPhone) fPhone.value = parts[1].trim();
    });
  }

  // Load branches into dropdowns
  (function loadBranches() {
    if (!(window.api && typeof window.api.listBranches === 'function')) return;
    window.api.listBranches().then(function (list) {
      if (!Array.isArray(list)) return;
      function fill(selectEl) {
        if (!selectEl) return;
        selectEl.innerHTML = '';
        var opt = document.createElement('option');
        opt.value = '';
        opt.textContent = 'Select branch';
        selectEl.appendChild(opt);
        list.forEach(function (b) {
          var o = document.createElement('option');
          o.value = String(b.branch_id);
          o.textContent = b.branch_name + (b.address ? (' — ' + b.address) : '');
          selectEl.appendChild(o);
        });
      }
      fill(selPickupBranch);
      fill(selDropoffBranch);
    }).catch(function () {});
  })();

  function populatePreview() {
    function setText(id, value) {
      var el = qs('#' + id);
      if (el) el.textContent = value;
    }
    var cvName = (function () {
      if (fCustomerSelect && fCustomerSelect.selectedOptions && fCustomerSelect.selectedOptions[0]) {
        return fCustomerSelect.selectedOptions[0].textContent || '—';
      }
      return '—';
    })();
    setText('contractViewCustomer', cvName);
    setText('contractViewCustomerPhone', (fPhone && fPhone.value) || '—');
    setText('contractViewCustomerId', (fId && fId.value) || '—');
    setText('contractViewCustomerAddress', (fAddress && fAddress.value) || '—');

    setText('contractViewVehicle', getSelectedVehicleText());
    setText('contractViewPlate', '—');
    setText('contractViewType', '—');
    setText('contractViewSeats', '—');

    var start = fStart && fStart.value ? new Date(fStart.value) : null;
    var end = fEnd && fEnd.value ? new Date(fEnd.value) : null;
    var days = diffDays(start, end);
    setText('contractViewPeriod', start && end ? (start.toLocaleString() + ' → ' + end.toLocaleString()) : '—');
    setText('contractViewRentalDays', String(days));
    var daily = getDailyPrice();
    setText('contractViewDailyPrice', fmt(daily));
    var vehicleSubtotal = days > 0 ? (daily * days) : 0;
    setText('contractViewVehicleSubtotal', fmt(vehicleSubtotal));

    var surchargeTotal = getSurchargeTotal();
    var deposit = parseNum(fDeposit);
    var discount = parseNum(fDiscount);
    var grand = Math.max(0, vehicleSubtotal + surchargeTotal - discount);
    var payNow = parseNum(fPayNow);
    var remaining = Math.max(0, grand - payNow - deposit);

    setText('contractViewDeposit', fmt(deposit));
    setText('contractViewDiscount', fmt(discount));
    setText('contractViewGrandTotal', fmt(grand));
    setText('contractViewPaidNow', fmt(payNow));
    setText('contractViewRemaining', fmt(remaining));

    var notes = qs('#createContractNotes');
    setText('contractViewNotes', (notes && notes.value) ? notes.value : '—');
  }

  // Event wiring
  ['change', 'input'].forEach(function (evt) {
    [fName, fPhone, fId, fAddress, fStart, fEnd, fDeposit, fDiscount, fPayNow].forEach(function (el) {
      if (el) el.addEventListener(evt, recalc);
    });
  });
  document.addEventListener('payment:recalculate', recalc);

  var btnPreview = qs('#btnPreviewContract');
  if (btnPreview) {
    btnPreview.addEventListener('click', function () {
      recalc();
      populatePreview();
    });
  }

  // Create contract on confirm
  document.addEventListener('contract:create:confirm', function () {
    recalc();
    var selected = (window.appSelectedVehicle || null);
    var days = Number(sDays && sDays.textContent || 0);
    var surcharges = (window.appSurcharges && typeof window.appSurcharges.getAll === 'function') ? window.appSurcharges.getAll() : [];
    var selectedCustomerId = (function () {
      if (fCustomerSelect && fCustomerSelect.value) return Number(fCustomerSelect.value);
      return null;
    })();
    if (!selectedCustomerId) {
      alert('Please select a customer.');
      return;
    }
    if (!selected) {
      alert('Please select at least one vehicle.');
      return;
    }
    var payload = {
      CustomerID: selectedCustomerId,
      StartDate: (fStart && fStart.value) || null,
      EndDate: (fEnd && fEnd.value) || null,
      Notes: (fNotes && fNotes.value) || (qs('#createContractNotes') && qs('#createContractNotes').value) || undefined,
      Cars: selected ? [{ CarID: selected.car_id || selected.id, DailyRate: (selected.daily_rate || selected.price_per_day || 0), Amount: (days * (selected.daily_rate || selected.price_per_day || 0)) }] : [],
      Surcharges: surcharges.map(function (s) { return { SurchargeID: s.id || 0, UnitPrice: s.unitPrice || s.amount || 0, Quantity: s.quantity || 1 }; })
    };

    var payNow = parseNum(fPayNow);
    var deposit = parseNum(fDeposit);
    var method = (fMethod && fMethod.value) || 'Cash';

    if (!(window.api && typeof window.api.createContract === 'function')) {
      console.warn('API client missing, payload:', payload);
      document.dispatchEvent(new CustomEvent('contract:create:ready', { detail: payload }));
      return;
    }
    window.api.createContract(payload).then(function (res) {
      try {
        var id = res && (res.ContractID || res.id);
        if ((payNow > 0 || deposit > 0) && id != null) {
          var base = (window.api && window.api.baseUrl) || (window.API_BASE_URL || 'http://127.0.0.1:8000');
          fetch(String(base).replace(/\/$/, '') + '/contracts/' + id + '/payments?amount=' + encodeURIComponent(payNow + deposit) + '&method=' + encodeURIComponent(method), { method: 'POST', credentials: 'include' }).catch(function () {});
        }
      } catch (_) {}
      document.dispatchEvent(new CustomEvent('contract:create:ready', { detail: res }));
    }).catch(function (err) {
      console.error('Create contract failed', err);
      alert('Create contract failed: ' + (err && (err.data && err.data.detail || err.message) || 'unknown error'));
    });
  });

  // Load customers for dropdown
  (function loadCustomers() {
    if (!(window.api && typeof window.api.listCustomers === 'function')) return;
    window.api.listCustomers({ limit: 100 }).then(function (list) {
      if (!Array.isArray(list)) return;
      var sel = fCustomerSelect;
      if (!sel) return;
      sel.innerHTML = '';
      var optDefault = document.createElement('option');
      optDefault.value = '';
      optDefault.textContent = 'Select customer';
      sel.appendChild(optDefault);
      list.forEach(function (c) {
        var opt = document.createElement('option');
        opt.value = String(c.customer_id);
        opt.textContent = c.full_name + (c.phone ? (' — ' + c.phone) : '');
        sel.appendChild(opt);
      });
    }).catch(function (err) {
      console.warn('Load customers failed', err);
    });
  })();

  // Initial calc
  recalc();
});
