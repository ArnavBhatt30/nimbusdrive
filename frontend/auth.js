// ============ NIMBUSDRIVE AUTH HELPER ============

// Auto-detect API URL — works locally and on Render
const API = window.location.origin;

function getToken() {
  return localStorage.getItem('nimbus_token');
}

function getUsername() {
  return localStorage.getItem('nimbus_username') || 'User';
}

function logout() {
  localStorage.removeItem('nimbus_token');
  localStorage.removeItem('nimbus_username');
  localStorage.removeItem('nimbus_email');
  window.location.href = '/login.html';
}

function requireAuth() {
  if (!getToken()) {
    window.location.href = '/login.html';
    return false;
  }
  return true;
}

// Authenticated fetch — automatically adds Bearer token
async function authFetch(url, options = {}) {
  const token = getToken();
  const headers = {
    ...(options.headers || {}),
    'Authorization': `Bearer ${token}`
  };
  const res = await fetch(url, { ...options, headers });

  if (res.status === 401) {
    logout();
    return null;
  }
  return res;
}
