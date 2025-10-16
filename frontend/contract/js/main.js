document.addEventListener('DOMContentLoaded', function () {
  function qs(selector, root) {
    return (root || document).querySelector(selector);
  }

  function qsa(selector, root) {
    return Array.prototype.slice.call((root || document).querySelectorAll(selector));
  }

  function on(selector, event, handler) {
    var el = qs(selector);
    if (el) el.addEventListener(event, handler);
  }

  function toggleModal(modalId, show) {
    var modal = qs('#' + modalId);
    if (!modal) return;
    var shouldShow = typeof show === 'boolean' ? show : modal.getAttribute('aria-hidden') === 'true';
    modal.setAttribute('aria-hidden', shouldShow ? 'false' : 'true');
    if (shouldShow) {
      modal.classList.add('open');
    } else {
      modal.classList.remove('open');
    }
  }

  function closeParentModal(target) {
    var modal = target.closest('.modal');
    if (modal && modal.id) toggleModal(modal.id, false);
  }

  // Backdrop click to close
  qsa('.modal .modal-backdrop').forEach(function (el) {
    el.addEventListener('click', function (e) {
      closeParentModal(e.target);
    });
  });

  // Contract form actions
  on('#btnSelectVehicle', 'click', function () {
    toggleModal('modalSelectVehicle', true);
  });

  on('#btnAddSurcharge', 'click', function () {
    toggleModal('modalSurcharge', true);
  });

  on('#btnPreviewContract', 'click', function () {
    toggleModal('modalContractView', true);
  });

  // Submit creates contract (open confirm modal)
  var contractForm = qs('#contract-form');
  if (contractForm) {
    contractForm.addEventListener('submit', function (e) {
      e.preventDefault();
      toggleModal('modalCreateContract', true);
    });
  }

  // Create Contract modal controls
  on('#btnCloseCreateContract', 'click', function (e) {
    closeParentModal(e.target);
  });
  on('#btnCancelCreateContract', 'click', function (e) {
    closeParentModal(e.target);
  });

  var agree = qs('#createContractAgree');
  var btnConfirmCreate = qs('#btnConfirmCreateContract');
  if (agree && btnConfirmCreate) {
    var updateConfirmState = function () {
      btnConfirmCreate.disabled = !agree.checked;
    };
    agree.addEventListener('change', updateConfirmState);
    updateConfirmState();
  }

  if (btnConfirmCreate) {
    btnConfirmCreate.addEventListener('click', function (e) {
      // Dispatch a custom event for creation; other scripts can handle actual API call
      document.dispatchEvent(new CustomEvent('contract:create:confirm'));
      closeParentModal(e.target);
    });
  }

  // Contract View modal controls
  on('#btnCloseContractView', 'click', function (e) {
    closeParentModal(e.target);
  });
  on('#btnCloseContractViewFooter', 'click', function (e) {
    closeParentModal(e.target);
  });
  on('#btnPrintContract', 'click', function () {
    window.print();
  });

  // Select Vehicle modal controls
  on('#btnCloseSelectVehicle', 'click', function (e) {
    closeParentModal(e.target);
  });
  on('#btnCancelSelectVehicle', 'click', function (e) {
    closeParentModal(e.target);
  });
  on('#btnConfirmSelectVehicle', 'click', function (e) {
    // Let vehicle.js decide which row is selected
    document.dispatchEvent(new CustomEvent('vehicle:select:confirm'));
    closeParentModal(e.target);
  });

  // Surcharge modal controls
  on('#btnCloseSurcharge', 'click', function (e) {
    closeParentModal(e.target);
  });
  on('#btnCancelSurcharge', 'click', function (e) {
    closeParentModal(e.target);
  });
  on('#btnSaveSurcharge', 'click', function (e) {
    document.dispatchEvent(new CustomEvent('surcharge:save'));
    closeParentModal(e.target);
  });

  // Utility controls
  on('#btnRefreshVehicles', 'click', function () {
    document.dispatchEvent(new CustomEvent('vehicles:refresh'));
  });
  on('#btnOpenSurchargeModal', 'click', function () {
    toggleModal('modalSurcharge', true);
  });
  on('#btnRecalculateTotals', 'click', function () {
    document.dispatchEvent(new CustomEvent('payment:recalculate'));
  });
});


