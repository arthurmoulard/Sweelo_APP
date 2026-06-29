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

// ── Utilities ─────────────────────────────────────────────────────────────────

function escapeHtml(str) {
  return String(str).replace(/[&<>"']/g, c =>
    ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c])
  );
}

function initials(name) {
  return name ? name.slice(0, 2).toUpperCase() : '?';
}

function timeAgo(iso) {
  const diff = Date.now() - new Date(iso).getTime();
  const min  = Math.floor(diff / 60000);
  if (min < 1)  return "à l'instant";
  if (min < 60) return `il y a ${min} min`;
  const h = Math.floor(min / 60);
  if (h < 24)   return `il y a ${h}h`;
  return `il y a ${Math.floor(h / 24)}j`;
}

const ACTIVITY_LABELS = {
  run: 'Course', bike: 'Vélo', swim: 'Natation', walk: 'Marche',
  trail: 'Trail', triathlon: 'Triathlon', hyrox: 'Hyrox',
  muscu: 'Musculation', basket: 'Basketball', foot: 'Football',
  hand: 'Handball', volley: 'Volleyball', combat: 'Combat',
};

const ACTIVITY_EMOJIS = {
  run: '🏃', bike: '🚴', swim: '🏊', walk: '🚶', trail: '⛰️',
  triathlon: '🏅', hyrox: '💪', muscu: '🏋️', basket: '🏀',
  foot: '⚽', hand: '🤾', volley: '🏐', combat: '🥊',
};

// ── Tabs ──────────────────────────────────────────────────────────────────────

document.querySelectorAll('.tab-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-panel').forEach(p => p.classList.add('hidden'));
    btn.classList.add('active');
    document.getElementById(`tab-${btn.dataset.tab}`).classList.remove('hidden');
  });
});

// ── Logout ────────────────────────────────────────────────────────────────────

document.getElementById('logout-btn').addEventListener('click', async () => {
  await apiFetch('/auth/logout', { method: 'POST' }).catch(() => {});
  localStorage.removeItem('sw_access_token');
  localStorage.removeItem('sw_refresh_token');
  window.location.replace('../../index.html');
});

// ═══════════════════════════════════════════════════════════════════════════════
// ONGLET UTILISATEURS
// ═══════════════════════════════════════════════════════════════════════════════

let friendIds = new Set();

function renderUserCard(user, isFriend) {
  const btn = isFriend
    ? `<button class="btn-action btn-remove" data-id="${user.id}" data-username="${escapeHtml(user.username)}">Retirer</button>`
    : `<button class="btn-action btn-add"    data-id="${user.id}" data-username="${escapeHtml(user.username)}">+ Ajouter</button>`;
  return `
    <div class="user-card" id="user-card-${user.id}">
      <a href="../user/user.html?id=${user.id}" class="user-card-link">
        <div class="user-avatar">${initials(user.username)}</div>
        <span class="user-name">${escapeHtml(user.username)}</span>
      </a>
      ${btn}
    </div>`;
}

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
  if (!res.ok) { emptyEl.textContent = 'Impossible de charger la liste.'; emptyEl.classList.remove('hidden'); return; }

  const friends = await res.json();
  friendIds = new Set(friends.map(f => f.id));

  if (friends.length) {
    countEl.textContent = friends.length;
    countEl.classList.remove('hidden');
  } else {
    countEl.classList.add('hidden');
  }

  if (!friends.length) { emptyEl.classList.remove('hidden'); return; }

  listEl.innerHTML = friends.map(f => renderUserCard(f, true)).join('');
  listEl.classList.remove('hidden');
  listEl.querySelectorAll('.btn-remove').forEach(btn => {
    btn.addEventListener('click', () => removeFriend(btn.dataset.id, btn.dataset.username));
  });
}

const userSearchInput   = document.getElementById('user-search-input');
const userSearchResults = document.getElementById('user-search-results');
const userSearchEmpty   = document.getElementById('user-search-empty');
const userSearchLoader  = document.getElementById('user-search-loader');

let userSearchTimer = null;

userSearchInput.addEventListener('input', () => {
  clearTimeout(userSearchTimer);
  const q = userSearchInput.value.trim();
  if (!q) {
    userSearchResults.classList.add('hidden');
    userSearchEmpty.classList.add('hidden');
    userSearchLoader.classList.add('hidden');
    return;
  }
  if (q.length < 2) return;
  userSearchLoader.classList.remove('hidden');
  userSearchResults.classList.add('hidden');
  userSearchEmpty.classList.add('hidden');
  userSearchTimer = setTimeout(() => doUserSearch(q), 350);
});

async function doUserSearch(q) {
  const res = await apiFetch(`/users/search?q=${encodeURIComponent(q)}`);
  userSearchLoader.classList.add('hidden');
  if (!res.ok) return;
  const users = await res.json();
  if (!users.length) { userSearchEmpty.classList.remove('hidden'); return; }
  userSearchResults.innerHTML = users.map(u => renderUserCard(u, friendIds.has(u.id))).join('');
  userSearchResults.classList.remove('hidden');
  userSearchResults.querySelectorAll('.btn-add').forEach(btn => {
    btn.addEventListener('click', () => addFriend(btn.dataset.id, btn.dataset.username));
  });
  userSearchResults.querySelectorAll('.btn-remove').forEach(btn => {
    btn.addEventListener('click', () => removeFriend(btn.dataset.id, btn.dataset.username));
  });
}

async function addFriend(id, username) {
  const res = await apiFetch(`/users/${id}/friend`, { method: 'POST' });
  if (!res.ok) return;
  friendIds.add(id);
  const card = document.querySelector(`#user-search-results #user-card-${id}`);
  if (card) {
    const btn = card.querySelector('.btn-add');
    if (btn) { btn.className = 'btn-action btn-remove'; btn.textContent = 'Retirer'; btn.onclick = () => removeFriend(id, username); }
  }
  loadFriends();
}

async function removeFriend(id, username) {
  const res = await apiFetch(`/users/${id}/friend`, { method: 'DELETE' });
  if (!res.ok) return;
  friendIds.delete(id);
  const friendCard = document.querySelector(`#friends-list #user-card-${id}`);
  if (friendCard) friendCard.remove();
  const searchCard = document.querySelector(`#user-search-results #user-card-${id}`);
  if (searchCard) {
    const btn = searchCard.querySelector('.btn-remove');
    if (btn) { btn.className = 'btn-action btn-add'; btn.textContent = '+ Ajouter'; btn.onclick = () => addFriend(id, username); }
  }
  loadFriends();
}

// ═══════════════════════════════════════════════════════════════════════════════
// ONGLET ACTIVITÉS
// ═══════════════════════════════════════════════════════════════════════════════

const ACTIVITY_TYPES = ['run','bike','swim','walk','trail','triathlon','hyrox','muscu','basket','foot','hand','volley','combat'];

let selectedType    = null;
let activityPage    = 1;
let activityHasNext = false;
let activityLoading = false;

function buildSportChips() {
  const container = document.getElementById('sport-chips');
  container.innerHTML = ACTIVITY_TYPES.map(type => `
    <button class="sport-chip" data-type="${type}">
      <span class="chip-emoji">${ACTIVITY_EMOJIS[type]}</span>
      ${ACTIVITY_LABELS[type]}
    </button>
  `).join('');

  container.querySelectorAll('.sport-chip').forEach(chip => {
    chip.addEventListener('click', () => {
      container.querySelectorAll('.sport-chip').forEach(c => c.classList.remove('active'));
      chip.classList.add('active');
      selectedType    = chip.dataset.type;
      activityPage    = 1;
      activityHasNext = false;
      document.getElementById('activity-results').innerHTML = '';
      document.getElementById('activity-load-more').classList.add('hidden');
      loadActivities();
    });
  });
}

function renderActivityStats(act) {
  const parts = [];
  if (act.distance_km != null) parts.push(`<span class="stat-pill">${act.distance_km.toFixed(1)} km</span>`);
  if (act.duration_min) {
    const h = Math.floor(act.duration_min / 60);
    const m = act.duration_min % 60;
    parts.push(`<span class="stat-pill">${h > 0 ? h + 'h' + (m > 0 ? m + 'min' : '') : m + ' min'}</span>`);
  }
  return parts.join('');
}

function renderActivityPost(post) {
  const act   = post.activity || {};
  const notes = act.notes ? `<p class="post-notes">${escapeHtml(act.notes)}</p>` : '';
  const photo = post.photo_url
    ? `<img class="post-photo" src="${escapeHtml(post.photo_url)}" alt="Photo" loading="lazy" />`
    : '';
  const avatarContent = post.author_avatar_url
    ? `<img src="${escapeHtml(post.author_avatar_url)}" alt="${initials(post.username)}" />`
    : initials(post.username);
  return `
    <article class="post-card">
      <div class="post-header">
        <div class="post-avatar">${avatarContent}</div>
        <div class="post-meta">
          <a href="../user/user.html?id=${post.user_id}" class="post-author">${escapeHtml(post.username || '—')}</a>
          <span class="post-time">${timeAgo(post.created_at)}</span>
        </div>
      </div>
      <div class="post-activity">
        <span class="activity-badge ${escapeHtml(act.type || '')}">${ACTIVITY_LABELS[act.type] || act.type || ''}</span>
        <div class="activity-stats">${renderActivityStats(act)}</div>
      </div>
      ${notes}
      ${photo}
      <div class="post-footer">
        <span class="post-stat">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>
          </svg>
          ${post.likes_count}
        </span>
        <span class="post-stat">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
          </svg>
          ${post.comments_count}
        </span>
      </div>
    </article>`;
}

async function loadActivities(append = false) {
  if (!selectedType || activityLoading) return;
  activityLoading = true;

  const loaderEl   = document.getElementById('activity-loader');
  const emptyEl    = document.getElementById('activity-empty');
  const resultsEl  = document.getElementById('activity-results');
  const loadMoreEl = document.getElementById('activity-load-more');

  loaderEl.classList.remove('hidden');
  emptyEl.classList.add('hidden');
  loadMoreEl.classList.add('hidden');

  const res = await apiFetch(`/feed/search?type=${encodeURIComponent(selectedType)}&page=${activityPage}`);
  loaderEl.classList.add('hidden');
  activityLoading = false;

  if (!res.ok) return;
  const data = await res.json();

  if (!append && !data.posts.length) { emptyEl.classList.remove('hidden'); return; }

  resultsEl.insertAdjacentHTML('beforeend', data.posts.map(renderActivityPost).join(''));
  activityHasNext = data.has_next;

  if (activityHasNext) {
    loadMoreEl.classList.remove('hidden');
    loadMoreEl.onclick = () => { activityPage++; loadActivities(true); };
  }
}

// ── Init ──────────────────────────────────────────────────────────────────────

buildSportChips();
loadFriends();
