/* ============================================================
   SWEELO — admin.js
   Logique complète de la page d'administration.
   Endpoints utilisés :
     GET    /admin/reports
     PUT    /admin/reports/:id
     DELETE /admin/comments/:id
     DELETE /admin/posts/:id
     GET    /admin/users
     POST   /admin/users/:id/ban
     POST   /admin/users/:id/unban
   ============================================================ */

const API_BASE   = '/api/v1';
const TOKEN_KEY  = 'sw_access_token';

/* ============================================================
   1. UTILITAIRES AUTH
   ============================================================ */

function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

function decodeToken(token) {
  try {
    return JSON.parse(atob(token.split('.')[1]));
  } catch {
    return null;
  }
}

function isTokenExpired(token) {
  const payload = decodeToken(token);
  if (!payload) return true;
  return payload.exp * 1000 < Date.now();
}

/**
 * Vérifie au chargement que l'utilisateur est bien admin.
 * Redirige vers login si ce n'est pas le cas.
 */
function guardAdmin() {
  const token = getToken();

  if (!token || isTokenExpired(token)) {
    localStorage.removeItem(TOKEN_KEY);
    window.location.replace('../login/login.html');
    return false;
  }

  const payload = decodeToken(token);
  if (!payload?.is_admin) {
    window.location.replace('../feed/feed.html');
    return false;
  }

  return true;
}

/* ============================================================
   2. UTILITAIRES API
   ============================================================ */

/**
 * Wrapper fetch authentifié.
 * Gère automatiquement le header Authorization et le Content-Type.
 */
async function apiFetch(path, options = {}) {
  const token = getToken();

  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      'Content-Type':  'application/json',
      'Authorization': `Bearer ${token}`,
      ...options.headers,
    },
  });

  // Token expiré côté serveur → logout
  if (res.status === 401) {
    localStorage.removeItem(TOKEN_KEY);
    window.location.replace('../login/login.html');
    return null;
  }

  return res;
}

/* ============================================================
   3. UTILITAIRES UI
   ============================================================ */

function showAlert(type, msg) {
  const alertEl   = document.getElementById('alert');
  const alertMsg  = document.getElementById('alert-msg');
  const alertIcon = document.getElementById('alert-icon');

  alertEl.className    = `alert show alert-${type}`;
  alertMsg.textContent = msg;
  alertIcon.innerHTML  = type === 'success'
    ? `<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
       <polyline points="22 4 12 14.01 9 11.01"/>`
    : `<circle cx="12" cy="12" r="10"/>
       <line x1="12" y1="8" x2="12" y2="12"/>
       <line x1="12" y1="16" x2="12.01" y2="16"/>`;

  // Masquer automatiquement après 4s
  clearTimeout(showAlert._timer);
  showAlert._timer = setTimeout(() => {
    alertEl.className = 'alert';
  }, 4000);
}

function formatDate(isoString) {
  if (!isoString) return '—';
  return new Date(isoString).toLocaleDateString('fr-FR', {
    day:   '2-digit',
    month: 'short',
    year:  'numeric',
  });
}

function getInitial(username = '') {
  return username.charAt(0).toUpperCase() || '?';
}

/* ── Modale de confirmation ── */
let _modalCallback = null;

function openModal(title, body, onConfirm) {
  document.getElementById('modal-title').textContent = title;
  document.getElementById('modal-body').textContent  = body;
  document.getElementById('modal-overlay').classList.remove('hidden');
  _modalCallback = onConfirm;
}

function closeModal() {
  document.getElementById('modal-overlay').classList.add('hidden');
  _modalCallback = null;
}

document.getElementById('modal-cancel').addEventListener('click', closeModal);
document.getElementById('modal-confirm').addEventListener('click', () => {
  if (_modalCallback) _modalCallback();
  closeModal();
});

// Fermer en cliquant sur l'overlay
document.getElementById('modal-overlay').addEventListener('click', (e) => {
  if (e.target === e.currentTarget) closeModal();
});

/* ── Helpers show/hide ── */
function show(id) { document.getElementById(id)?.classList.remove('hidden'); }
function hide(id) { document.getElementById(id)?.classList.add('hidden'); }

/* ============================================================
   4. STATS GLOBALES
   ============================================================ */

async function loadStats() {
  try {
    const [reportsRes, usersRes] = await Promise.all([
      apiFetch('/admin/reports?status=pending'),
      apiFetch('/admin/users'),
    ]);

    if (reportsRes?.ok) {
      const data = await reportsRes.json();
      const reports = data.data ?? data;
      document.getElementById('stat-reports').textContent = reports.length ?? '—';
      // Mettre à jour le compteur de l'onglet
      const countEl = document.getElementById('tab-reports-count');
      if (reports.length > 0) {
        countEl.textContent = reports.length;
        countEl.style.display = '';
      } else {
        countEl.style.display = 'none';
      }
    }

    if (usersRes?.ok) {
      const data = await usersRes.json();
      const users  = data.data ?? data;
      const active = users.filter(u => !u.is_banned).length;
      const banned = users.filter(u =>  u.is_banned).length;
      document.getElementById('stat-users').textContent  = active;
      document.getElementById('stat-banned').textContent = banned;
    }

  } catch (err) {
    console.error('Erreur chargement stats :', err);
  }
}

/* ============================================================
   5. PANEL SIGNALEMENTS
   ============================================================ */

let _allReports = [];

async function loadReports() {
  const status = document.getElementById('filter-status').value;
  const type   = document.getElementById('filter-type').value;

  show('reports-loading');
  hide('reports-list');
  hide('reports-empty');

  try {
    const params = new URLSearchParams({ status });
    if (type) params.set('type', type);

    const res = await apiFetch(`/admin/reports?${params}`);
    if (!res?.ok) throw new Error('Erreur serveur');

    const data = await res.json();
    _allReports = data.data ?? data;

    hide('reports-loading');

    if (_allReports.length === 0) {
      show('reports-empty');
      return;
    }

    renderReports(_allReports);
    show('reports-list');

  } catch (err) {
    hide('reports-loading');
    showAlert('error', 'Impossible de charger les signalements.');
    console.error(err);
  }
}

function renderReports(reports) {
  const list = document.getElementById('reports-list');
  list.innerHTML = '';

  reports.forEach(report => {
    const card = document.createElement('div');
    card.className = `report-card report-card--${report.status}`;
    card.dataset.id = report.id;

    const isPending = report.status === 'pending';

    card.innerHTML = `
      <div class="report-card__header">
        <div class="report-card__meta">
          <span class="badge badge--${report.target_type}">
            ${report.target_type === 'post' ? 'Post' : 'Commentaire'}
          </span>
          <span class="badge badge--${report.status}">
            ${{ pending: 'En attente', reviewed: 'Traité', dismissed: 'Rejeté' }[report.status] ?? report.status}
          </span>
          <span class="text-muted" style="font-size:.78rem">
            Signalé par <strong style="color:var(--text)">${report.reporter_username ?? '—'}</strong>
          </span>
        </div>
        <span class="report-card__date">${formatDate(report.created_at)}</span>
      </div>

      <div class="report-card__content">
        <div class="report-card__content-label">Contenu signalé</div>
        ${report.target_content ?? '<em style="color:var(--muted)">Contenu supprimé ou indisponible</em>'}
      </div>

      <div class="report-card__reason">
        <strong>Raison :</strong> ${report.reason ?? '—'}
      </div>

      ${isPending ? `
      <div class="report-card__actions">
        <button class="btn btn--danger btn--sm" data-action="delete-content" data-report-id="${report.id}" data-target-type="${report.target_type}" data-target-id="${report.target_id}">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14H6L5 6"/><path d="M10 11v6"/><path d="M14 11v6"/><path d="M9 6V4h6v2"/>
          </svg>
          Supprimer le contenu
        </button>
        <button class="btn btn--success btn--sm" data-action="dismiss" data-report-id="${report.id}">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="20 6 9 17 4 12"/>
          </svg>
          Rejeter le signalement
        </button>
      </div>
      ` : ''}
    `;

    list.appendChild(card);
  });

  // Délégation d'événements sur la liste
  list.onclick = handleReportAction;
}

async function handleReportAction(e) {
  const btn = e.target.closest('[data-action]');
  if (!btn) return;

  const action     = btn.dataset.action;
  const reportId   = btn.dataset.reportId;
  const targetType = btn.dataset.targetType;
  const targetId   = btn.dataset.targetId;

  if (action === 'delete-content') {
    openModal(
      'Supprimer le contenu',
      `Tu vas supprimer définitivement ce ${targetType === 'post' ? 'post' : 'commentaire'} et marquer le signalement comme traité. Cette action est irréversible.`,
      () => deleteContent(reportId, targetType, targetId)
    );
  }

  if (action === 'dismiss') {
    openModal(
      'Rejeter le signalement',
      'Le contenu sera conservé et le signalement marqué comme rejeté.',
      () => updateReportStatus(reportId, 'dismissed')
    );
  }
}

async function deleteContent(reportId, targetType, targetId) {
  try {
    // 1. Supprimer le contenu
    const deleteRoute = targetType === 'comment'
      ? `/admin/comments/${targetId}`
      : `/admin/posts/${targetId}`;

    const deleteRes = await apiFetch(deleteRoute, { method: 'DELETE' });

    if (!deleteRes?.ok && deleteRes?.status !== 404) {
      showAlert('error', 'Erreur lors de la suppression du contenu.');
      return;
    }

    // 2. Marquer le signalement comme traité
    await updateReportStatus(reportId, 'reviewed', false);

    showAlert('success', 'Contenu supprimé et signalement traité.');
    await loadReports();
    await loadStats();

  } catch (err) {
    showAlert('error', 'Une erreur est survenue.');
    console.error(err);
  }
}

async function updateReportStatus(reportId, status, withFeedback = true) {
  try {
    const res = await apiFetch(`/admin/reports/${reportId}`, {
      method: 'PUT',
      body:   JSON.stringify({ action: status }),
    });

    if (!res?.ok) {
      if (withFeedback) showAlert('error', 'Erreur lors de la mise à jour du signalement.');
      return;
    }

    if (withFeedback) {
      showAlert('success', status === 'dismissed'
        ? 'Signalement rejeté.'
        : 'Signalement marqué comme traité.'
      );
      await loadReports();
      await loadStats();
    }

  } catch (err) {
    if (withFeedback) showAlert('error', 'Une erreur est survenue.');
    console.error(err);
  }
}

/* ── Filtres ── */
document.getElementById('filter-status').addEventListener('change', loadReports);
document.getElementById('filter-type').addEventListener('change', loadReports);

/* ============================================================
   6. PANEL UTILISATEURS
   ============================================================ */

let _allUsers   = [];
let _searchTimer = null;

async function loadUsers() {
  show('users-loading');
  hide('users-table-wrap');
  hide('users-empty');

  try {
    const res = await apiFetch('/admin/users');
    if (!res?.ok) throw new Error('Erreur serveur');

    const data = await res.json();
    _allUsers = data.items ?? data.data ?? data;

    hide('users-loading');
    renderUsers(_allUsers);

  } catch (err) {
    hide('users-loading');
    showAlert('error', 'Impossible de charger les utilisateurs.');
    console.error(err);
  }
}

function renderUsers(users) {
  const tbody = document.getElementById('users-tbody');
  tbody.innerHTML = '';

  if (users.length === 0) {
    hide('users-table-wrap');
    show('users-empty');
    return;
  }

  hide('users-empty');
  show('users-table-wrap');

  users.forEach(user => {
    const tr = document.createElement('tr');
    tr.dataset.userId = user.id;

    tr.innerHTML = `
      <td>
        <div class="user-cell">
          <div class="user-avatar">${getInitial(user.username)}</div>
          <span class="user-username">${user.username}</span>
        </div>
      </td>
      <td class="user-email">${user.email}</td>
      <td>${formatDate(user.created_at)}</td>
      <td>
        <span class="${user.is_banned ? 'status-banned' : 'status-active'}">
          ${user.is_banned ? '🚫 Banni' : '✅ Actif'}
        </span>
      </td>
      <td>
        <button
          class="btn btn--sm ${user.is_banned ? 'btn--secondary' : 'btn--danger'}"
          data-action="${user.is_banned ? 'unban' : 'ban'}"
          data-user-id="${user.id}"
          data-username="${user.username}"
          ${user.is_admin ? 'disabled title="Impossible de bannir un admin"' : ''}
        >
          ${user.is_banned ? 'Débannir' : 'Bannir'}
        </button>
      </td>
    `;

    tbody.appendChild(tr);
  });

  tbody.onclick = handleUserAction;
}

async function handleUserAction(e) {
  const btn = e.target.closest('[data-action]');
  if (!btn || btn.disabled) return;

  const action   = btn.dataset.action;
  const userId   = btn.dataset.userId;
  const username = btn.dataset.username;

  if (action === 'ban') {
    openModal(
      'Bannir l\'utilisateur',
      `Tu vas bannir @${username}. Il ne pourra plus se connecter. Tu pourras le débannir plus tard.`,
      () => toggleBan(userId, true)
    );
  }

  if (action === 'unban') {
    openModal(
      'Débannir l\'utilisateur',
      `Tu vas débannir @${username}. Il pourra à nouveau accéder à l'application.`,
      () => toggleBan(userId, false)
    );
  }
}

async function toggleBan(userId, ban) {
  try {
    const route = ban
      ? `/admin/users/${userId}/ban`
      : `/admin/users/${userId}/unban`;

    const res = await apiFetch(route, { method: 'POST' });

    if (!res?.ok) {
      showAlert('error', `Erreur lors du ${ban ? 'bannissement' : 'débannissement'}.`);
      return;
    }

    showAlert('success', ban
      ? 'Utilisateur banni avec succès.'
      : 'Utilisateur débanni avec succès.'
    );

    await loadUsers();
    await loadStats();

  } catch (err) {
    showAlert('error', 'Une erreur est survenue.');
    console.error(err);
  }
}

/* ── Recherche utilisateurs avec debounce ── */
document.getElementById('user-search').addEventListener('input', (e) => {
  clearTimeout(_searchTimer);
  _searchTimer = setTimeout(() => {
    const q = e.target.value.trim().toLowerCase();
    if (!q) {
      renderUsers(_allUsers);
      return;
    }
    const filtered = _allUsers.filter(u =>
      u.username.toLowerCase().includes(q) ||
      u.email.toLowerCase().includes(q)
    );
    renderUsers(filtered);
  }, 300);
});

/* ============================================================
   7. ONGLETS
   ============================================================ */

/* ============================================================
   7b. PANEL UTILISATEURS & ACTIVITÉS
   ============================================================ */

const ACTIVITY_LABELS_OV = {
  run: 'Course', bike: 'Vélo', swim: 'Natation', walk: 'Marche',
  trail: 'Trail', triathlon: 'Triathlon', hyrox: 'Hyrox',
  muscu: 'Musculation', basket: 'Basketball', foot: 'Football',
  hand: 'Handball', volley: 'Volleyball', combat: 'Combat',
};

let _overviewUsers   = [];
let _overviewTimer   = null;
let _expandedUsers   = new Set();

async function loadOverview() {
  show('overview-loading');
  hide('overview-list');
  hide('overview-empty');

  try {
    const res = await apiFetch('/admin/users');
    if (!res?.ok) throw new Error();
    const data = await res.json();
    _overviewUsers = data.data ?? data.items ?? data;
    hide('overview-loading');
    renderOverview(_overviewUsers);
  } catch {
    hide('overview-loading');
    showAlert('error', 'Impossible de charger les utilisateurs.');
  }
}

function renderOverview(users) {
  const listEl = document.getElementById('overview-list');
  listEl.innerHTML = '';

  if (!users.length) { hide('overview-list'); show('overview-empty'); return; }
  hide('overview-empty'); show('overview-list');

  users.forEach(user => {
    const card = document.createElement('div');
    card.className = 'ov-card';
    card.id = `ov-user-${user.id}`;

    const isExpanded = _expandedUsers.has(user.id);
    const statusHtml = user.is_banned
      ? `<span class="status-banned">🚫 Banni</span>`
      : `<span class="status-active">✅ Actif</span>`;
    const banBtnHtml = user.is_admin ? '' : `
      <button class="btn btn--sm ${user.is_banned ? 'btn--secondary' : 'btn--danger'}"
              data-action="${user.is_banned ? 'ov-unban' : 'ov-ban'}"
              data-user-id="${user.id}" data-username="${escapeHtmlOv(user.username)}">
        ${user.is_banned ? 'Débannir' : 'Bannir'}
      </button>`;

    card.innerHTML = `
      <div class="ov-header">
        <div class="user-cell">
          <div class="user-avatar">${getInitial(user.username)}</div>
          <div>
            <span class="user-username">${escapeHtmlOv(user.username)}</span>
            <span class="ov-email">${escapeHtmlOv(user.email)}</span>
          </div>
        </div>
        <div class="ov-actions">
          ${statusHtml}
          ${banBtnHtml}
          <button class="btn btn--sm btn--ghost ov-expand-btn"
                  data-user-id="${user.id}">
            ${isExpanded ? '▲ Masquer' : '▼ Activités'}
          </button>
        </div>
      </div>
      <div class="ov-activities ${isExpanded ? '' : 'hidden'}" id="ov-acts-${user.id}">
        <div class="ov-acts-loader">
          <div class="spinner spinner--sm"></div>
          <span class="text-muted" style="font-size:.8rem">Chargement…</span>
        </div>
      </div>`;

    listEl.appendChild(card);

    if (isExpanded) fetchUserActivities(user.id);
  });

  listEl.onclick = handleOverviewAction;
}

function escapeHtmlOv(str) {
  return String(str ?? '').replace(/[&<>"']/g, c =>
    ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c])
  );
}

async function handleOverviewAction(e) {
  const btn = e.target.closest('[data-action], .ov-expand-btn');
  if (!btn) return;

  const action   = btn.dataset.action;
  const userId   = btn.dataset.userId;
  const username = btn.dataset.username;

  if (btn.classList.contains('ov-expand-btn')) {
    toggleExpand(userId);
    return;
  }

  if (action === 'ov-ban') {
    openModal('Bannir l\'utilisateur',
      `Tu vas bannir @${username}. Il ne pourra plus se connecter.`,
      () => toggleBanOv(userId, true, username));
  }
  if (action === 'ov-unban') {
    openModal('Débannir l\'utilisateur',
      `Tu vas débannir @${username}. Il pourra à nouveau accéder à l'application.`,
      () => toggleBanOv(userId, false, username));
  }
  if (action === 'delete-activity') {
    const actId   = btn.dataset.activityId;
    const actType = btn.dataset.activityType;
    openModal('Supprimer l\'activité',
      `Supprimer définitivement cette activité "${ACTIVITY_LABELS_OV[actType] || actType}" de @${username} ?`,
      () => deleteActivityOv(actId, userId));
  }
}

async function toggleBanOv(userId, ban, username) {
  const route = ban
    ? `/admin/users/${userId}/ban`
    : `/admin/users/${userId}/unban`;
  const res = await apiFetch(route, { method: 'POST' });
  if (!res?.ok) { showAlert('error', 'Erreur.'); return; }
  showAlert('success', ban ? `@${username} banni.` : `@${username} débanni.`);
  await loadOverview();
  await loadStats();
}

async function toggleExpand(userId) {
  const actsEl   = document.getElementById(`ov-acts-${userId}`);
  const expandBtn = document.querySelector(`#ov-user-${userId} .ov-expand-btn`);
  if (!actsEl) return;

  if (_expandedUsers.has(userId)) {
    _expandedUsers.delete(userId);
    actsEl.classList.add('hidden');
    if (expandBtn) expandBtn.textContent = '▼ Activités';
  } else {
    _expandedUsers.add(userId);
    actsEl.classList.remove('hidden');
    if (expandBtn) expandBtn.textContent = '▲ Masquer';
    fetchUserActivities(userId);
  }
}

async function fetchUserActivities(userId) {
  const actsEl = document.getElementById(`ov-acts-${userId}`);
  if (!actsEl) return;

  const res = await apiFetch(`/admin/users/${userId}/activities`);
  if (!res?.ok) {
    actsEl.innerHTML = '<p style="color:var(--error);font-size:.82rem;padding:8px">Impossible de charger les activités.</p>';
    return;
  }
  const data = await res.json();
  const items = data.items ?? data;

  const username = document.querySelector(`#ov-user-${userId} .user-username`)?.textContent ?? '';

  if (!items.length) {
    actsEl.innerHTML = '<p style="color:var(--muted);font-size:.82rem;padding:8px 0">Aucune activité enregistrée.</p>';
    return;
  }

  actsEl.innerHTML = `
    <table class="acts-table">
      <thead>
        <tr>
          <th>Sport</th>
          <th>Date</th>
          <th>Durée</th>
          <th>Distance</th>
          <th>Notes</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        ${items.map(act => {
          const h = Math.floor(act.duration_min / 60);
          const m = act.duration_min % 60;
          const dur = h > 0 ? `${h}h${m > 0 ? m + 'min' : ''}` : `${m} min`;
          const dist = act.distance_km != null ? `${act.distance_km.toFixed(1)} km` : '—';
          const notes = act.notes
            ? `<span title="${escapeHtmlOv(act.notes)}">${escapeHtmlOv(act.notes.slice(0, 40))}${act.notes.length > 40 ? '…' : ''}</span>`
            : '<span style="color:var(--muted)">—</span>';
          return `
            <tr>
              <td><span class="act-badge act-badge--${escapeHtmlOv(act.type)}">${ACTIVITY_LABELS_OV[act.type] || act.type}</span></td>
              <td style="white-space:nowrap">${formatDate(act.date)}</td>
              <td style="white-space:nowrap">${dur}</td>
              <td style="white-space:nowrap">${dist}</td>
              <td class="notes-cell">${notes}</td>
              <td>
                <button class="btn btn--sm btn--danger"
                        data-action="delete-activity"
                        data-activity-id="${act.id}"
                        data-activity-type="${escapeHtmlOv(act.type)}"
                        data-user-id="${userId}"
                        data-username="${escapeHtmlOv(username)}">
                  Supprimer
                </button>
              </td>
            </tr>`;
        }).join('')}
      </tbody>
    </table>`;
}

async function deleteActivityOv(activityId, userId) {
  const res = await apiFetch(`/admin/activities/${activityId}`, { method: 'DELETE' });
  if (!res?.ok) { showAlert('error', 'Erreur lors de la suppression.'); return; }
  showAlert('success', 'Activité supprimée.');
  fetchUserActivities(userId);
  loadStats();
}

/* ── Filtrage overview ── */
document.getElementById('overview-search').addEventListener('input', e => {
  clearTimeout(_overviewTimer);
  _overviewTimer = setTimeout(() => {
    const q = e.target.value.trim().toLowerCase();
    const filtered = q
      ? _overviewUsers.filter(u =>
          u.username.toLowerCase().includes(q) || u.email.toLowerCase().includes(q))
      : _overviewUsers;
    renderOverview(filtered);
  }, 250);
});

const TABS = [
  { tabId: 'tab-reports',  panelId: 'panel-reports',  loader: loadReports  },
  { tabId: 'tab-users',    panelId: 'panel-users',     loader: loadUsers    },
  { tabId: 'tab-overview', panelId: 'panel-overview',  loader: loadOverview },
];

function switchTab(activeTabId) {
  TABS.forEach(({ tabId, panelId }) => {
    const tab   = document.getElementById(tabId);
    const panel = document.getElementById(panelId);
    const isActive = tabId === activeTabId;

    tab.classList.toggle('tab--active', isActive);
    tab.setAttribute('aria-selected', isActive);
    panel.classList.toggle('hidden', !isActive);
  });

  // Charger les données de l'onglet actif
  const activeTab = TABS.find(t => t.tabId === activeTabId);
  activeTab?.loader();
}

document.getElementById('tab-reports').addEventListener('click',  () => switchTab('tab-reports'));
document.getElementById('tab-users').addEventListener('click',    () => switchTab('tab-users'));
document.getElementById('tab-overview').addEventListener('click', () => switchTab('tab-overview'));

/* ============================================================
   8. DÉCONNEXION
   ============================================================ */

document.getElementById('logout-btn').addEventListener('click', () => {
  openModal(
    'Déconnexion',
    'Tu vas être déconnecté de l\'interface d\'administration.',
    () => {
      localStorage.removeItem(TOKEN_KEY);
      window.location.replace('../login/login.html');
    }
  );
});

/* ============================================================
   9. INIT
   ============================================================ */

(function init() {
  if (!guardAdmin()) return;

  // Chargement initial : stats + onglet signalements
  loadStats();
  switchTab('tab-reports');
})();