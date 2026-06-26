// ── Config ────────────────────────────────────────────────────────────────────
const API_BASE = 'http://localhost:5000/api/v1';

// Redirige vers l'accueil si pas de token
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
  // Token expiré → déconnexion automatique
  if (res.status === 401) {
    localStorage.removeItem('sw_access_token');
    localStorage.removeItem('sw_refresh_token');
    window.location.replace('../../index.html');
  }
  return res;
}

// ── Utilitaires ───────────────────────────────────────────────────────────────

function escapeHtml(str) {
  return String(str).replace(/[&<>"']/g, c =>
    ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c])
  );
}

// Génère les initiales pour l'avatar
function initials(name) {
  return name ? name.slice(0, 2).toUpperCase() : '?';
}

// ── État des amis ─────────────────────────────────────────────────────────────

// Set d'IDs pour vérifier instantanément si un user est ami
let friendIds = new Set();

// ── Chargement de la liste d'amis ─────────────────────────────────────────────

async function loadFriends() {
  const listEl   = document.getElementById('friends-list');
  const emptyEl  = document.getElementById('friends-empty');
  const loaderEl = document.getElementById('friends-loader');
  const countEl  = document.getElementById('friends-count');

  loaderEl.classList.remove('hidden');
  listEl.classList.add('hidden');
  emptyEl.classList.add('hidden');

  const res = await apiFetch('/users/me/friends');
  loaderEl.classList.add('hidden');

  if (!res.ok) {
    emptyEl.textContent = 'Impossible de charger la liste.';
    emptyEl.classList.remove('hidden');
    return;
  }

  const friends = await res.json();

  // Met à jour l'ensemble des IDs amis (utilisé par la recherche)
  friendIds = new Set(friends.map(f => f.id));

  // Affiche le compteur si au moins 1 ami
  if (friends.length) {
    countEl.textContent = friends.length;
    countEl.classList.remove('hidden');
  } else {
    countEl.classList.add('hidden');
  }

  if (!friends.length) {
    emptyEl.classList.remove('hidden');
    return;
  }

  listEl.innerHTML = friends.map(f => renderCard(f, true)).join('');
  listEl.classList.remove('hidden');

  // Lie les boutons "Retirer"
  listEl.querySelectorAll('.btn-remove').forEach(btn => {
    btn.addEventListener('click', () => removeFriend(btn.dataset.id, btn.dataset.username));
  });
}

// ── Rendu d'une carte utilisateur ────────────────────────────────────────────

function renderCard(user, isFriend) {
  const actionBtn = isFriend
    ? `<button class="btn-action btn-remove"
              data-id="${user.id}"
              data-username="${escapeHtml(user.username)}">
         Retirer
       </button>`
    : `<button class="btn-action btn-add"
              data-id="${user.id}"
              data-username="${escapeHtml(user.username)}">
         + Ajouter
       </button>`;

  return `
    <div class="user-card" id="user-card-${user.id}">
      <a href="../user/user.html?id=${user.id}" class="user-card-link">
        <div class="user-avatar">${initials(user.username)}</div>
        <span class="user-name">${escapeHtml(user.username)}</span>
      </a>
      ${actionBtn}
    </div>
  `;
}

// ── Recherche d'utilisateurs ──────────────────────────────────────────────────

const searchInput   = document.getElementById('search-input');
const searchResults = document.getElementById('search-results');
const searchEmpty   = document.getElementById('search-empty');
const searchLoader  = document.getElementById('search-loader');

let searchTimer = null;

searchInput.addEventListener('input', () => {
  clearTimeout(searchTimer);
  const q = searchInput.value.trim();

  // Cache les résultats si champ vide
  if (!q) {
    searchResults.classList.add('hidden');
    searchEmpty.classList.add('hidden');
    searchLoader.classList.add('hidden');
    return;
  }

  // Le backend exige au moins 2 caractères
  if (q.length < 2) return;

  searchLoader.classList.remove('hidden');
  searchResults.classList.add('hidden');
  searchEmpty.classList.add('hidden');

  // Debounce 350 ms pour limiter les appels API pendant la frappe
  searchTimer = setTimeout(() => doSearch(q), 350);
});

async function doSearch(q) {
  const res = await apiFetch(`/users/search?q=${encodeURIComponent(q)}`);
  searchLoader.classList.add('hidden');

  if (!res.ok) return;

  const users = await res.json();

  if (!users.length) {
    searchEmpty.classList.remove('hidden');
    return;
  }

  // Utilise friendIds pour afficher le bon bouton dès l'affichage
  searchResults.innerHTML = users.map(u => renderCard(u, friendIds.has(u.id))).join('');
  searchResults.classList.remove('hidden');

  // Lie les boutons de la grille de résultats
  searchResults.querySelectorAll('.btn-add').forEach(btn => {
    btn.addEventListener('click', () => addFriend(btn.dataset.id, btn.dataset.username));
  });
  searchResults.querySelectorAll('.btn-remove').forEach(btn => {
    btn.addEventListener('click', () => removeFriend(btn.dataset.id, btn.dataset.username));
  });
}

// ── Ajouter un ami ────────────────────────────────────────────────────────────

async function addFriend(id, username) {
  const res = await apiFetch(`/users/${id}/friend`, { method: 'POST' });
  if (!res.ok) return;

  friendIds.add(id);

  // Met à jour le bouton dans les résultats sans re-render complet
  const card = document.querySelector(`#search-results #user-card-${id}`);
  if (card) {
    const btn = card.querySelector('.btn-add');
    if (btn) {
      btn.className = 'btn-action btn-remove';
      btn.textContent = 'Retirer';
      btn.onclick = () => removeFriend(id, username);
    }
  }

  // Recharge la section "Mes amis" pour inclure le nouvel ami
  loadFriends();
}

// ── Retirer un ami ────────────────────────────────────────────────────────────

async function removeFriend(id, username) {
  const res = await apiFetch(`/users/${id}/friend`, { method: 'DELETE' });
  if (!res.ok) return;

  friendIds.delete(id);

  // Supprime la carte de la liste des amis immédiatement (pas d'attente de reload)
  const friendCard = document.querySelector(`#friends-list #user-card-${id}`);
  if (friendCard) friendCard.remove();

  // Met à jour le bouton dans les résultats de recherche si visibles
  const searchCard = document.querySelector(`#search-results #user-card-${id}`);
  if (searchCard) {
    const btn = searchCard.querySelector('.btn-remove');
    if (btn) {
      btn.className = 'btn-action btn-add';
      btn.textContent = '+ Ajouter';
      btn.onclick = () => addFriend(id, username);
    }
  }

  // Recharge pour mettre à jour le compteur et l'état vide
  loadFriends();
}

// ── Déconnexion ───────────────────────────────────────────────────────────────

document.getElementById('logout-btn').addEventListener('click', async () => {
  await apiFetch('/auth/logout', { method: 'POST' }).catch(() => {});
  localStorage.removeItem('sw_access_token');
  localStorage.removeItem('sw_refresh_token');
  window.location.replace('../../index.html');
});

// ── Init ──────────────────────────────────────────────────────────────────────

loadFriends();
