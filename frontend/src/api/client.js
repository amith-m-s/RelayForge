const API_BASE = '/api/v1';

let accessToken = localStorage.getItem('rf_access_token');
let refreshToken = localStorage.getItem('rf_refresh_token');
let isRefreshing = false;
let refreshSubscribers = [];

function onRefreshed(newToken) {
  refreshSubscribers.forEach(cb => cb(newToken));
  refreshSubscribers = [];
}

function addRefreshSubscriber(cb) {
  refreshSubscribers.push(cb);
}

export function setTokens(access, refresh) {
  accessToken = access;
  refreshToken = refresh;
  localStorage.setItem('rf_access_token', access);
  localStorage.setItem('rf_refresh_token', refresh);
}

export function clearTokens() {
  accessToken = null;
  refreshToken = null;
  localStorage.removeItem('rf_access_token');
  localStorage.removeItem('rf_refresh_token');
  localStorage.removeItem('rf_org_id');
}

export function getOrgId() {
  return localStorage.getItem('rf_org_id');
}

export function setOrgId(id) {
  localStorage.setItem('rf_org_id', id);
}

async function refreshAccessToken() {
  if (!refreshToken) throw new Error('No refresh token');
  const res = await fetch(`${API_BASE}/auth/refresh`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh_token: refreshToken }),
  });
  if (!res.ok) {
    clearTokens();
    window.location.href = '/login';
    throw new Error('Token refresh failed');
  }
  const data = await res.json();
  setTokens(data.access_token, data.refresh_token);
  return data.access_token;
}

export async function api(endpoint, options = {}) {
  const { method = 'GET', body, headers: extraHeaders = {} } = options;

  const headers = {
    'Content-Type': 'application/json',
    ...extraHeaders,
  };

  if (accessToken) {
    headers['Authorization'] = `Bearer ${accessToken}`;
  }

  const orgId = getOrgId();
  if (orgId) {
    headers['X-Organization-ID'] = orgId;
  }

  let res = await fetch(`${API_BASE}${endpoint}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });

  // If 401, try to refresh token
  if (res.status === 401 && refreshToken) {
    if (!isRefreshing) {
      isRefreshing = true;
      try {
        const newToken = await refreshAccessToken();
        isRefreshing = false;
        onRefreshed(newToken);
      } catch {
        isRefreshing = false;
        return res;
      }
    }

    // Wait for refresh to complete
    const retryToken = await new Promise(resolve => addRefreshSubscriber(resolve));
    headers['Authorization'] = `Bearer ${retryToken}`;
    res = await fetch(`${API_BASE}${endpoint}`, {
      method,
      headers,
      body: body ? JSON.stringify(body) : undefined,
    });
  }

  return res;
}

export async function apiJson(endpoint, options = {}) {
  const res = await api(endpoint, options);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: { message: res.statusText } }));
    throw new Error(err.error?.message || err.detail || res.statusText);
  }
  return res.json();
}

export default api;
