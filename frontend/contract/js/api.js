(function () {
  var DEFAULT_BASE = (window.API_BASE_URL || '').trim() || 'http://127.0.0.1:8000';
  var BASE = DEFAULT_BASE.replace(/\/$/, '');

  function toQuery(params) {
    if (!params) return '';
    var usp = new URLSearchParams();
    Object.keys(params).forEach(function (k) {
      var v = params[k];
      if (v === undefined || v === null || v === '') return;
      usp.append(k, String(v));
    });
    var s = usp.toString();
    return s ? ('?' + s) : '';
  }

  function buildUrl(path, params) {
    var clean = String(path || '').replace(/^\/*/, '');
    return BASE + '/' + clean + toQuery(params);
  }

  function isJsonResponse(resp) {
    var ct = resp.headers.get('content-type') || '';
    return ct.indexOf('application/json') >= 0;
  }

  async function request(method, path, options) {
    options = options || {};
    var url = buildUrl(path, options.params);
    var headers = Object.assign({ 'Accept': 'application/json' }, options.headers || {});
    var fetchOpts = { method: method || 'GET', headers: headers, credentials: 'include' };
    if (options.body !== undefined) {
      headers['Content-Type'] = 'application/json';
      fetchOpts.body = JSON.stringify(options.body);
    }
    var resp = await fetch(url, fetchOpts);
    var payload = null;
    if (isJsonResponse(resp)) {
      try { payload = await resp.json(); } catch (_) { payload = null; }
    } else {
      payload = await resp.text();
    }
    if (!resp.ok) {
      var err = new Error('Request failed: ' + resp.status + ' ' + resp.statusText);
      err.status = resp.status;
      err.data = payload;
      throw err;
    }
    return payload;
  }

  // API endpoints (adjust paths to your backend routes)
  var api = {
    baseUrl: BASE,
    // Vehicles
    listVehicles: function (opts) {
      opts = opts || {};
      return request('GET', 'cars/', {
        params: {
          search: opts.search,
          type_id: opts.type_id,
          skip: opts.skip,
          limit: opts.limit
        }
      });
    },
    listVehicleTypes: function () {
      return request('GET', 'car-types/');
    },
    // Contracts
    createContract: function (payload) {
      return request('POST', 'contracts', { body: payload });
    },
    // Customers
    listCustomers: function (opts) {
      opts = opts || {};
      return request('GET', 'customers/', { params: { search: opts.search, skip: opts.skip, limit: opts.limit } });
    },
    listBranches: function () {
      return request('GET', 'branches/');
    },
    // Customers (optional helpers)
    findCustomerByPhone: function (phone) {
      return request('GET', 'customers/by-phone', { params: { phone: phone } });
    }
  };

  // Expose globally
  window.api = api;
})();


