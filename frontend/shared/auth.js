/**
 * Sweelo — Authentification partagée
 *
 * Le JWT (access + refresh) est posé par le serveur dans des cookies httpOnly :
 * le JS ne peut plus le lire (contrairement à l'ancien localStorage), ce qui
 * ferme l'exfiltration de session via une faille XSS.
 *
 * Contrepartie : les cookies sont vulnérables au CSRF. Flask-JWT-Extended
 * pose donc en plus un cookie NON-httpOnly `csrf_access_token`, lisible par
 * ce script, à renvoyer en en-tête `X-CSRF-TOKEN` sur toute requête qui
 * modifie des données (POST/PUT/PATCH/DELETE).
 */

const API_BASE = '/api/v1';

function getCookie(name) {
  const match = document.cookie.match(`(?:^|; )${name}=([^;]*)`);
  return match ? decodeURIComponent(match[1]) : null;
}

const MUTATING_METHODS = new Set(['POST', 'PUT', 'PATCH', 'DELETE']);

async function apiFetch(path, options = {}) {
  const method  = (options.method || 'GET').toUpperCase();
  const headers = { 'Content-Type': 'application/json', ...(options.headers || {}) };

  if (MUTATING_METHODS.has(method)) {
    const csrf = getCookie('csrf_access_token');
    if (csrf) headers['X-CSRF-TOKEN'] = csrf;
  }

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers, credentials: 'include' });

  if (res.status === 401) {
    window.location.replace('/pages/login/login.html');
  }

  return res;
}

async function requireAuth() {
  const res = await apiFetch('/users/me');
  if (!res.ok) {
    window.location.replace('/pages/login/login.html');
    return null;
  }
  return res.json();
}

async function logout() {
  await apiFetch('/auth/logout', { method: 'POST' }).catch(() => {});
  window.location.replace('/pages/login/login.html');
}
