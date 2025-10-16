document.addEventListener('DOMContentLoaded', function () {
  var form = document.getElementById('quickContractForm');
  if (!form) return;
  var elCustomer = document.getElementById('qcCustomerId');
  var elStart = document.getElementById('qcStart');
  var elEnd = document.getElementById('qcEnd');
  var elNotes = document.getElementById('qcNotes');
  var elResult = document.getElementById('qcResult');

  function setResult(text, isError) {
    if (!elResult) return;
    elResult.textContent = text || '';
    elResult.style.color = isError ? '#b00020' : '#0a7d32';
  }

  form.addEventListener('submit', function (e) {
    e.preventDefault();
    setResult('Creating...', false);
    var customerId = Number(elCustomer && elCustomer.value);
    if (!customerId || isNaN(customerId)) {
      setResult('Please enter a valid CustomerID.', true);
      return;
    }
    var payload = {
      CustomerID: customerId,
      StartDate: elStart && elStart.value ? elStart.value : null,
      EndDate: elEnd && elEnd.value ? elEnd.value : null,
      Notes: elNotes && elNotes.value ? elNotes.value : undefined,
      Cars: [],
      Surcharges: []
    };
    if (!(window.api && typeof window.api.createContract === 'function')) {
      setResult('API not ready. Ensure js/api.js is loaded.', true);
      return;
    }
    window.api.createContract(payload).then(function (res) {
      try {
        var id = res && (res.ContractID || res.id);
        setResult('Created contract ID: ' + id, false);
      } catch (_) {
        setResult('Created.', false);
      }
      console.log('Quick create result:', res);
    }).catch(function (err) {
      console.error('Quick create error:', err);
      var msg = (err && (err.data && (err.data.detail || JSON.stringify(err.data))) ) || err && err.message || 'unknown error';
      setResult('Create failed: ' + msg, true);
    });
  });
});


