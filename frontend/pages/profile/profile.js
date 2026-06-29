/**
 * Profil — page personnelle de l'utilisateur connecté
 *
 * Affiche et permet d'éditer son profil (username, email, mot de passe).
 * L'avatar se change au clic (upload multipart, sans passer par apiFetch
 * car Content-Type est multipart/form-data et non JSON).
 *
 * Routes API :
 *   GET  /users/me          — données du profil
 *   PUT  /users/me          — modifier profil
 *   GET  /users/me/stats    — km totaux, heures totales
 *   GET  /users/me/friends  — liste des amis
 *   POST /users/me/avatar   — upload avatar (multipart/form-data)
 */

// ── Config ────────────────────────────────────────────────────────────────────
const API_BASE = '/api/v1';

if (!localStorage.getItem('sw_access_token')) {
  window.location.replace('../../index.html');
}

// ── API helper ────────────────────────────────────────────────────────────────

async function apiFetch(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${localStorage.getItem('sw_access_token')}`,
      ...(options.headers || {}),
    },
  });
  if (res.status === 401) {
    localStorage.removeItem('sw_access_token');
    localStorage.removeItem('sw_refresh_token');
    window.location.replace('../../index.html');
  }
  return res;
}

function initials(name) {
  if (!name) return '?';
  return name.slice(0, 2).toUpperCase();
}

function formatJoinDate(iso) {
  if (!iso) return '';
  return 'Membre depuis ' + new Date(iso).toLocaleDateString('fr-FR', { month: 'long', year: 'numeric' });
}

// ── Load profile ──────────────────────────────────────────────────────────────

function setAvatar(avatarUrl, username) {
  const avatarEl = document.getElementById('avatar');
  if (avatarUrl) {
    avatarEl.innerHTML = `<img src="${avatarUrl}" alt="${initials(username)}" />`;
  } else {
    avatarEl.textContent = initials(username);
  }
}

async function loadProfile() {
  const res = await apiFetch('/users/me');
  if (!res.ok) return;
  const data = await res.json();

  setAvatar(data.avatar_url, data.username);
  document.getElementById('username').textContent  = data.username;
  document.getElementById('email').textContent     = data.email;
  document.getElementById('join-date').textContent = formatJoinDate(data.created_at);

  document.getElementById('stat-activities').textContent = data.activities_count ?? 0;
  document.getElementById('stat-friends').textContent    = data.friends_count ?? 0;

  document.getElementById('edit-username').value = data.username;
  document.getElementById('edit-email').value    = data.email;
}

// ── Avatar upload ─────────────────────────────────────────────────────────────

const avatarWrapper = document.getElementById('avatar-wrapper');
const avatarInput   = document.getElementById('avatar-input');

avatarWrapper.addEventListener('click', () => avatarInput.click());

avatarInput.addEventListener('change', async () => {
  const file = avatarInput.files[0];
  if (!file) return;

  const wrapper = document.getElementById('avatar-wrapper');
  wrapper.classList.add('avatar-uploading');

  const fd = new FormData();
  fd.append('avatar', file);

  const res = await fetch(`${API_BASE}/users/me/avatar`, {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${localStorage.getItem('sw_access_token')}` },
    body: fd,
  });

  wrapper.classList.remove('avatar-uploading');
  avatarInput.value = '';

  if (res.ok) {
    const data = await res.json();
    setAvatar(data.avatar_url, document.getElementById('username').textContent);
  }
});

// ── Load stats ────────────────────────────────────────────────────────────────

async function loadStats() {
  const res = await apiFetch('/users/me/stats');
  if (!res.ok) return;
  const data = await res.json();

  const km    = Math.round(data.total_km ?? 0);
  const hours = data.total_min ? (data.total_min / 60).toFixed(1) : 0;

  document.getElementById('stat-km').textContent    = km;
  document.getElementById('stat-hours').textContent = hours;
}

// ── Load friends ──────────────────────────────────────────────────────────────

async function loadFriends() {
  const container = document.getElementById('friends-list');
  const res = await apiFetch('/users/me/friends');

  if (!res.ok) {
    container.innerHTML = '<p class="placeholder">Impossible de charger les amis.</p>';
    return;
  }

  const friends = await res.json();

  if (!friends.length) {
    container.innerHTML = '<p class="placeholder">Tu n\'as pas encore d\'amis. Recherche des sportifs pour te connecter !</p>';
    return;
  }

  container.innerHTML = friends.map(f => `
    <div class="friend-chip">
      <div class="friend-avatar">${initials(f.username)}</div>
      <span class="friend-name">${escapeHtml(f.username)}</span>
    </div>
  `).join('');
}

function escapeHtml(str) {
  return str.replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
}

// ── Logout ────────────────────────────────────────────────────────────────────

document.getElementById('logout-btn').addEventListener('click', async () => {
  await apiFetch('/auth/logout', { method: 'POST' }).catch(() => {});
  localStorage.removeItem('sw_access_token');
  localStorage.removeItem('sw_refresh_token');
  window.location.replace('../../index.html');
});

// ── Edit modal ────────────────────────────────────────────────────────────────

const modal   = document.getElementById('edit-modal');
const alertEl = document.getElementById('modal-alert');
const saveBtn = document.getElementById('save-btn');

document.getElementById('edit-btn').addEventListener('click', () => {
  clearAlert();
  modal.classList.remove('hidden');
});

document.getElementById('cancel-btn').addEventListener('click', closeModal);

modal.addEventListener('click', e => { if (e.target === modal) closeModal(); });

document.addEventListener('keydown', e => { if (e.key === 'Escape') closeModal(); });

function closeModal() {
  modal.classList.add('hidden');
  clearAlert();
  clearErrors();
}

function showAlert(msg, type = 'error') {
  alertEl.textContent = msg;
  alertEl.className = `alert ${type}`;
}

function clearAlert() {
  alertEl.className = 'alert hidden';
  alertEl.textContent = '';
}

// ── Field validation ──────────────────────────────────────────────────────────

function setError(id, msg) {
  const el = document.getElementById(id);
  const input = document.getElementById(id.replace('err-', 'edit-'));
  el.textContent = msg;
  if (input) input.classList.toggle('error', !!msg);
  return !msg;
}

function clearErrors() {
  ['err-username', 'err-email', 'err-password'].forEach(id => setError(id, ''));
}

function validateUsername() {
  const val = document.getElementById('edit-username').value.trim();
  if (!val)                              return setError('err-username', 'Requis');
  if (val.length < 3 || val.length > 30) return setError('err-username', '3 à 30 caractères');
  if (!/^[a-zA-Z0-9_-]+$/.test(val))    return setError('err-username', 'Lettres, chiffres, _ et - uniquement');
  return setError('err-username', '');
}

function validateEmail() {
  const val = document.getElementById('edit-email').value.trim();
  if (!val)                                          return setError('err-email', 'Requis');
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(val))      return setError('err-email', 'Adresse e-mail invalide');
  return setError('err-email', '');
}

function validatePassword() {
  const val = document.getElementById('edit-password').value;
  if (val && val.length < 8) return setError('err-password', '8 caractères minimum');
  return setError('err-password', '');
}

document.getElementById('edit-username').addEventListener('input', validateUsername);
document.getElementById('edit-email').addEventListener('input', validateEmail);
document.getElementById('edit-password').addEventListener('input', validatePassword);

// ── Save profile ──────────────────────────────────────────────────────────────

saveBtn.addEventListener('click', async () => {
  clearAlert();
  const okU = validateUsername();
  const okE = validateEmail();
  const okP = validatePassword();
  if (!okU || !okE || !okP) return;

  const body = {
    username: document.getElementById('edit-username').value.trim(),
    email:    document.getElementById('edit-email').value.trim(),
  };
  const pw = document.getElementById('edit-password').value;
  if (pw) body.password = pw;

  saveBtn.disabled = true;
  saveBtn.classList.add('loading');

  const res = await apiFetch('/users/me', { method: 'PUT', body: JSON.stringify(body) });

  saveBtn.disabled = false;
  saveBtn.classList.remove('loading');

  if (res.ok) {
    showAlert('Profil mis à jour !', 'success');
    document.getElementById('edit-password').value = '';
    await loadProfile();
    setTimeout(closeModal, 1200);
  } else {
    const err = await res.json().catch(() => ({}));
    showAlert(err.message || err.msg || 'Une erreur est survenue.', 'error');
  }
});

// ── Init ──────────────────────────────────────────────────────────────────────

loadProfile();
loadStats();
loadFriends();
