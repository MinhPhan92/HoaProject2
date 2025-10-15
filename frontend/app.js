(function () {
	const state = {
		customers: [
			{ id: 'C001', name: 'Nguyen Van A' },
			{ id: 'C002', name: 'Tran Thi B' },
			{ id: 'C003', name: 'Le Van C' }
		],
		vehicles: [
			{ id: 'V001', name: 'Toyota Vios 2020' },
			{ id: 'V002', name: 'Honda City 2021' },
			{ id: 'V003', name: 'Mazda 3 2019' }
		],
		staff: [
			{ id: 'S001', name: 'Pham Minh' },
			{ id: 'S002', name: 'Hoang Anh' },
			{ id: 'S003', name: 'Thu Trang' }
		],
		contracts: [
			{
				code: 'CT-0001', customerId: 'C001', vehicleId: 'V001', staffId: 'S001',
				startDate: '2025-10-01', endDate: '2025-10-05',
				status: 'Active',
				amount: 350.0,
				notes: 'No scratches before rent.'
			}
		]
	};

	// Elements
	const el = {
		customerSelect: document.getElementById('customerSelect'),
		vehicleSelect: document.getElementById('vehicleSelect'),
		staffSelect: document.getElementById('staffSelect'),
		form: document.getElementById('contractForm'),
		tableBody: document.querySelector('#contractsTable tbody'),
		searchInput: document.getElementById('searchInput'),
		openCreateModal: document.getElementById('openCreateModal'),
		modal: document.getElementById('createModal'),
		modalForm: document.getElementById('modalContractForm'),
		modalCustomer: document.getElementById('modalCustomer'),
		modalVehicle: document.getElementById('modalVehicle'),
		modalStaff: document.getElementById('modalStaff'),
		modalStart: document.getElementById('modalStart'),
		modalEnd: document.getElementById('modalEnd'),
		modalStatus: document.getElementById('modalStatus'),
		modalAmount: document.getElementById('modalAmount'),
		modalNotes: document.getElementById('modalNotes'),
		addVehicleBtn: document.getElementById('addVehicleBtn'),
		selectVehicleModal: document.getElementById('selectVehicleModal'),
		confirmAddVehicles: document.getElementById('confirmAddVehicles'),
		saveContractBtn: document.getElementById('saveContractBtn'),
		contractViewModal: document.getElementById('contractViewModal')
	};

	// Elements for surcharge modal
	const surchargeEl = {
		openBtn: document.getElementById('addSurchargeBtn'),
		modal: document.getElementById('surchargeModal'),
		qty: document.getElementById('surchargeQty'),
		price: document.getElementById('surchargePrice'),
		total: document.getElementById('surchargeTotal'),
		confirm: document.getElementById('addSurchargeConfirm')
	};

	function populateOptions(select, items) {
		select.innerHTML = '<option value="" disabled selected>Select</option>' +
			items.map(i => `<option value="${i.id}">${i.name}</option>`).join('');
	}

	function getNameById(list, id) {
		const found = list.find(i => i.id === id);
		return found ? found.name : '';
	}

	function renderTable() {
		if (!el.tableBody) return; // Safety: do nothing if the contracts table is not present in current view
		const q = (el.searchInput && el.searchInput.value ? el.searchInput.value : '').toLowerCase();
		const rows = state.contracts
			.filter(c => {
				const customer = getNameById(state.customers, c.customerId).toLowerCase();
				const vehicle = getNameById(state.vehicles, c.vehicleId).toLowerCase();
				return customer.includes(q) || vehicle.includes(q) || c.code.toLowerCase().includes(q);
			})
			.map(c => `<tr>
				<td>${c.code}</td>
				<td>${getNameById(state.customers, c.customerId)}</td>
				<td>${getNameById(state.vehicles, c.vehicleId)}</td>
				<td>${c.startDate}</td>
				<td>${c.endDate}</td>
				<td>${c.status}</td>
				<td class="right">${formatMoney(c.amount)}</td>
				<td>
					<div style="display:flex; gap:6px;">
						<button class="btn" data-action="details" data-code="${c.code}">Details</button>
						<button class="btn" data-action="edit" data-code="${c.code}">Edit</button>
						<button class="btn danger" data-action="delete" data-code="${c.code}">Delete</button>
					</div>
				</td>
			</tr>`)
			.join('');
		el.tableBody.innerHTML = rows || `<tr><td colspan="8" style="text-align:center; color: var(--text-dim);">No contracts</td></tr>`;
	}

	function formatMoney(v) {
		if (v == null || v === '') return '';
		return new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND', maximumFractionDigits: 0 }).format(Number(v));
	}

	function openModal() {
		populateOptions(el.modalCustomer, state.customers);
		populateOptions(el.modalVehicle, state.vehicles);
		populateOptions(el.modalStaff, state.staff);
		el.modal.setAttribute('aria-hidden', 'false');
	}
	function closeModal() {
		el.modal.setAttribute('aria-hidden', 'true');
		el.modalForm.reset();
	}

	function openSelectVehicleModal() {
		if (!el.selectVehicleModal) return;
		el.selectVehicleModal.setAttribute('aria-hidden', 'false');
	}

	function closeSelectVehicleModal() {
		if (!el.selectVehicleModal) return;
		el.selectVehicleModal.setAttribute('aria-hidden', 'true');
	}

	function wireEvents() {
		populateOptions(el.customerSelect, state.customers);
		populateOptions(el.vehicleSelect, state.vehicles);
		populateOptions(el.staffSelect, state.staff);

		if (el.searchInput) {
			el.searchInput.addEventListener('input', renderTable);
		}

		el.openCreateModal.addEventListener('click', openModal);
		el.modal.addEventListener('click', function (e) {
			if (e.target.matches('[data-close]')) closeModal();
		});

		// Vehicle selection modal wiring
		if (el.addVehicleBtn) el.addVehicleBtn.addEventListener('click', openSelectVehicleModal);
		if (el.selectVehicleModal) {
			el.selectVehicleModal.addEventListener('click', function (e) {
				if (e.target.matches('[data-close]')) closeSelectVehicleModal();
			});
		}
		if (el.confirmAddVehicles) el.confirmAddVehicles.addEventListener('click', closeSelectVehicleModal);

		// Save -> open contract view modal
		if (el.saveContractBtn && el.contractViewModal) {
			el.saveContractBtn.addEventListener('click', function(){
				el.contractViewModal.setAttribute('aria-hidden', 'false');
			});
			el.contractViewModal.addEventListener('click', function(e){
				if (e.target.matches('[data-close]')) {
					el.contractViewModal.setAttribute('aria-hidden', 'true');
				}
			});
		}

		// Inline form submit (top card) just appends a new contract (mock)
		el.form.addEventListener('submit', function (e) {
			e.preventDefault();
			const formData = new FormData(el.form);
			const newContract = {
				code: 'CT-' + String(state.contracts.length + 1).padStart(4, '0'),
				customerId: formData.get('customerSelect') || el.customerSelect.value,
				vehicleId: formData.get('vehicleSelect') || el.vehicleSelect.value,
				staffId: formData.get('staffSelect') || el.staffSelect.value,
				startDate: document.getElementById('startDate').value,
				endDate: document.getElementById('endDate').value,
				status: document.getElementById('vehicleStatus').value || 'Active',
				amount: Number(document.getElementById('totalAmount').value || 0),
				notes: document.getElementById('notes').value || ''
			};
			if (!newContract.customerId || !newContract.vehicleId || !newContract.staffId) return;
			state.contracts.unshift(newContract);
			el.form.reset();
			renderTable();
		});

		// Modal form submit (create)
		el.modalForm.addEventListener('submit', function (e) {
			e.preventDefault();
			const code = 'CT-' + String(state.contracts.length + 1).padStart(4, '0');
			const newContract = {
				code,
				customerId: el.modalCustomer.value,
				vehicleId: el.modalVehicle.value,
				staffId: el.modalStaff.value,
				startDate: el.modalStart.value,
				endDate: el.modalEnd.value,
				status: el.modalStatus.value || 'Active',
				amount: Number(el.modalAmount.value || 0),
				notes: el.modalNotes.value || ''
			};
			if (!newContract.customerId || !newContract.vehicleId || !newContract.staffId) return;
			state.contracts.unshift(newContract);
			closeModal();
			renderTable();
		});

		// Table actions
		if (el.tableBody) el.tableBody.addEventListener('click', function (e) {
			const btn = e.target.closest('button[data-action]');
			if (!btn) return;
			const code = btn.getAttribute('data-code');
			const idx = state.contracts.findIndex(c => c.code === code);
			if (idx < 0) return;
			switch (btn.getAttribute('data-action')) {
				case 'details': {
					const c = state.contracts[idx];
					alert(
						`Contract ${c.code}\n` +
						`Customer: ${getNameById(state.customers, c.customerId)}\n` +
						`Vehicle: ${getNameById(state.vehicles, c.vehicleId)}\n` +
						`Rental: ${c.startDate} → ${c.endDate}\n` +
						`Status: ${c.status}\n` +
						`Amount: ${formatMoney(c.amount)}\n` +
						`Notes: ${c.notes}`
					);
					break;
				}
				case 'edit': {
					// Simple edit: toggle status Active/Completed
					state.contracts[idx].status = state.contracts[idx].status === 'Active' ? 'Completed' : 'Active';
					renderTable();
					break;
				}
				case 'delete': {
					if (confirm('Delete this contract?')) {
						state.contracts.splice(idx, 1);
						renderTable();
					}
					break;
				}
			}
		});
	}

	function init() {
		wireEvents();

		// Surcharge modal interactions
		if (surchargeEl.openBtn) surchargeEl.openBtn.addEventListener('click', function () {
			if (!surchargeEl.modal) return;
			surchargeEl.modal.setAttribute('aria-hidden', 'false');
		});
		if (surchargeEl.modal) surchargeEl.modal.addEventListener('click', function (e) {
			if (e.target.matches('[data-close]')) {
				surchargeEl.modal.setAttribute('aria-hidden', 'true');
			}
		});
		function updateSurchargeTotal() {
			const qty = Number(surchargeEl.qty && surchargeEl.qty.value ? surchargeEl.qty.value : 0);
			const price = Number(surchargeEl.price && surchargeEl.price.value ? surchargeEl.price.value : 0);
			const sum = qty * price;
			if (surchargeEl.total) surchargeEl.total.textContent = new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND', maximumFractionDigits: 0 }).format(sum);
		}
		if (surchargeEl.qty) surchargeEl.qty.addEventListener('input', updateSurchargeTotal);
		if (surchargeEl.price) surchargeEl.price.addEventListener('input', updateSurchargeTotal);
		if (surchargeEl.confirm) surchargeEl.confirm.addEventListener('click', function () {
			// For now, simply close modal
			if (surchargeEl.modal) surchargeEl.modal.setAttribute('aria-hidden', 'true');
		});
		renderTable();
	}

	document.addEventListener('DOMContentLoaded', init);
})();


