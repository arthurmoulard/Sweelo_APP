/**
 * Profil public d'un utilisateur
 *
 * L'ID cible est passé via ?id=<uuid> dans l'URL.
 * Charge en parallèle le profil cible et la liste d'amis du connecté
 * pour afficher le bon bouton (Ajouter / Retirer) sans second appel.
 * Si les deux utilisateurs sont amis, les activités postées sont affichées.
 *
 * Routes API :
 *   GET    /users/:id           — profil public
 *   GET    /users/me/friends    — amis du connecté (état du bouton)
 *   GET    /users/:id/posts     — posts du feed (amis seulement)
 *   POST   /users/:id/friend    — ajouter
 *   DELETE /users/:id/friend    — retirer
 */

// ── Config ────────────────────────────────────────────────────────────────────
const API_BASE = '/api/v1';

// Redirige si pas connecté
if (!localStorage.getItem('sw_access_token')) {
  window.location.replace('../../index.html');
}

// Récupère l'ID de l'utilisateur depuis ?id=<uuid> dans l'URL
const userId = new URLSearchParams(location.search).get('id');
if (!userId) {
  window.location.replace('../feed/feed.html');
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

// ── Utilitaires ───────────────────────────────────────────────────────────────

const currentUserId = (() => {
  try {
    const token = localStorage.getItem('sw_access_token');
    return JSON.parse(atob(token.split('.')[1])).sub;
  } catch { return null; }
})();

function initials(name) {
  return name ? name.slice(0, 2).toUpperCase() : '?';
}

function formatJoinDate(iso) {
  if (!iso) return '';
  return 'Membre depuis ' + new Date(iso).toLocaleDateString('fr-FR', {
    month: 'long', year: 'numeric',
  });
}

function escapeHtml(str) {
  return String(str).replace(/[&<>"']/g, c =>
    ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c])
  );
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

// ── Chargement du profil public ───────────────────────────────────────────────

async function loadProfile() {
  // Charge en parallèle le profil et la liste d'amis du connecté
  const [profileRes, friendsRes] = await Promise.all([
    apiFetch(`/users/${userId}`),
    apiFetch('/users/me/friends'),
  ]);

  if (!profileRes.ok) {
    document.getElementById('profile-card').classList.add('hidden');
    document.getElementById('stats-row')?.classList.add('hidden');
    document.getElementById('error-state').classList.remove('hidden');
    return;
  }

  const profile = await profileRes.json();
  const friends = friendsRes.ok ? await friendsRes.json() : [];

  // Vérifie si l'utilisateur vu est déjà ami avec le connecté
  const isFriend = friends.some(f => f.id === userId);

  // Renseigne le titre de l'onglet avec le pseudo
  document.title = `Sweelo — ${profile.username}`;

  // Remplit la carte de profil
  const avatarEl = document.getElementById('avatar');
  if (profile.avatar_url) {
    avatarEl.innerHTML = `<img src="${profile.avatar_url}" alt="${initials(profile.username)}" style="width:100%;height:100%;object-fit:cover;border-radius:50%;" />`;
  } else {
    avatarEl.textContent = initials(profile.username);
  }
  document.getElementById('username').textContent  = profile.username;
  document.getElementById('join-date').textContent = formatJoinDate(profile.created_at);

  // Remplit les statistiques
  document.getElementById('stat-activities').textContent = profile.activities_count ?? 0;
  document.getElementById('stat-friends').textContent    = profile.friends_count ?? 0;

  // Configure le bouton ami
  const friendBtn = document.getElementById('friend-btn');
  friendBtn.classList.remove('hidden');

  if (isFriend) {
    friendBtn.textContent = 'Retirer des amis';
    friendBtn.className   = 'btn-friend remove';
    friendBtn.onclick     = handleRemoveFriend;
    loadUserPosts(userId);
  } else {
    friendBtn.textContent = '+ Ajouter';
    friendBtn.className   = 'btn-friend add';
    friendBtn.onclick     = handleAddFriend;
  }
}

// ── Posts de l'utilisateur (amis seulement) ──────────────────────────────────

let postsPage = 1;
let postsHasNext = false;
let postsLoading = false;

function renderActivityStats(activity) {
  const parts = [];
  if (activity.distance_km != null) {
    parts.push(`<span class="stat-pill">${activity.distance_km.toFixed(1)} km</span>`);
  }
  if (activity.duration_min) {
    const h = Math.floor(activity.duration_min / 60);
    const m = activity.duration_min % 60;
    parts.push(`<span class="stat-pill">${h > 0 ? `${h}h${m > 0 ? m + 'min' : ''}` : `${m} min`}</span>`);
  }
  return parts.join('');
}

function renderPost(post) {
  const act        = post.activity || {};
  const badgeLabel = ACTIVITY_LABELS[act.type] || act.type || '';
  const notesHtml  = act.notes ? `<p class="post-notes">${escapeHtml(act.notes)}</p>` : '';
  const photoHtml  = post.photo_url
    ? `<img class="post-photo" src="${escapeHtml(post.photo_url)}" alt="Photo de l'activité" loading="lazy" />`
    : '';
  const avatarContent = post.author_avatar_url
    ? `<img src="${escapeHtml(post.author_avatar_url)}" alt="${initials(post.username)}" />`
    : initials(post.username);

  const article = document.createElement('article');
  article.className    = 'post-card';
  article.dataset.postId = post.id;
  article.innerHTML = `
    <div class="post-header">
      <div class="post-avatar">${avatarContent}</div>
      <div class="post-meta">
        <span class="post-author">${escapeHtml(post.username || '—')}</span>
        <span class="post-time">${timeAgo(post.created_at)}</span>
      </div>
    </div>
    <div class="post-activity">
      <span class="activity-badge ${act.type || ''}">${badgeLabel}</span>
      <div class="activity-stats">${renderActivityStats(act)}</div>
    </div>
    ${notesHtml}
    ${photoHtml}
    <div class="post-actions">
      <button class="btn-action btn-like ${post.user_has_liked ? 'liked' : ''}" data-post-id="${post.id}">
        <span class="like-icon">🏋️</span>
        <span class="likes-count">${post.likes_count}</span>
      </button>
    </div>
  `;

  article.querySelector('.btn-like').addEventListener('click', () => toggleLikeOnProfile(post.id));
  return article;
}

async function toggleLikeOnProfile(postId) {
  const postsContainer = document.getElementById('user-posts-container');
  const card    = postsContainer.querySelector(`[data-post-id="${postId}"]`);
  const btn     = card.querySelector('.btn-like');
  const countEl = btn.querySelector('.likes-count');
  const wasLiked = btn.classList.contains('liked');

  btn.classList.toggle('liked', !wasLiked);
  countEl.textContent = parseInt(countEl.textContent) + (wasLiked ? -1 : 1);

  const res = await apiFetch(`/feed/${postId}/like`, { method: 'POST' });
  if (res.ok) {
    const data = await res.json();
    countEl.textContent = data.likes_count;
    btn.classList.toggle('liked', data.liked);
  } else {
    btn.classList.toggle('liked', wasLiked);
    countEl.textContent = parseInt(countEl.textContent) + (wasLiked ? 1 : -1);
  }
}

async function loadUserPosts(targetId, page = 1) {
  if (postsLoading) return;
  postsLoading = true;

  const section   = document.getElementById('user-posts-section');
  const container = document.getElementById('user-posts-container');
  const loader    = document.getElementById('user-posts-loader');
  const emptyEl   = document.getElementById('user-posts-empty');
  const moreBtn   = document.getElementById('user-posts-more');

  section.classList.remove('hidden');
  loader.classList.remove('hidden');
  moreBtn.classList.add('hidden');

  const res = await apiFetch(`/users/${targetId}/posts?page=${page}`);
  loader.classList.add('hidden');
  postsLoading = false;

  if (!res.ok) return;

  const data = await res.json();
  const posts = data.posts || [];

  if (page === 1 && !posts.length) {
    emptyEl.classList.remove('hidden');
    return;
  }

  posts.forEach(post => container.appendChild(renderPost(post)));

  postsHasNext = data.has_next;
  postsPage    = data.page;

  if (postsHasNext) {
    moreBtn.classList.remove('hidden');
    moreBtn.onclick = () => loadUserPosts(targetId, postsPage + 1);
  }
}

// ── Actions ami ───────────────────────────────────────────────────────────────

async function handleAddFriend() {
  const btn = document.getElementById('friend-btn');
  btn.disabled = true;

  const res = await apiFetch(`/users/${userId}/friend`, { method: 'POST' });

  btn.disabled = false;

  if (res.ok) {
    btn.textContent = 'Retirer des amis';
    btn.className   = 'btn-friend remove';
    btn.onclick     = handleRemoveFriend;

    // Met à jour le compteur d'amis affiché
    const statEl = document.getElementById('stat-friends');
    statEl.textContent = parseInt(statEl.textContent || '0') + 1;
  }
}

async function handleRemoveFriend() {
  const btn = document.getElementById('friend-btn');
  btn.disabled = true;

  const res = await apiFetch(`/users/${userId}/friend`, { method: 'DELETE' });

  btn.disabled = false;

  if (res.ok) {
    btn.textContent = '+ Ajouter';
    btn.className   = 'btn-friend add';
    btn.onclick     = handleAddFriend;

    const statEl = document.getElementById('stat-friends');
    statEl.textContent = Math.max(0, parseInt(statEl.textContent || '0') - 1);
  }
}

// ── Bouton retour ─────────────────────────────────────────────────────────────

// Retourne à la page précédente dans l'historique, ou au feed par défaut
document.getElementById('back-btn').addEventListener('click', () => {
  if (history.length > 1) {
    history.back();
  } else {
    window.location.replace('../feed/feed.html');
  }
});

// ── Déconnexion ───────────────────────────────────────────────────────────────

document.getElementById('logout-btn').addEventListener('click', async () => {
  await apiFetch('/auth/logout', { method: 'POST' }).catch(() => {});
  localStorage.removeItem('sw_access_token');
  localStorage.removeItem('sw_refresh_token');
  window.location.replace('../../index.html');
});

// ── Init ──────────────────────────────────────────────────────────────────────

loadProfile();
