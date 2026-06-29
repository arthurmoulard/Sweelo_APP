/**
 * Profil public d'un utilisateur
 *
 * L'ID cible est passé via ?id=<uuid> dans l'URL.
 * Charge en parallèle le profil cible et la liste d'amis du connecté
 * pour afficher le bon bouton (Ajouter / Retirer) sans second appel.
 *
 * Routes API :
 *   GET    /users/:id           — profil public
 *   GET    /users/me/friends    — amis du connecté (état du bouton)
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

function initials(name) {
  return name ? name.slice(0, 2).toUpperCase() : '?';
}

function formatJoinDate(iso) {
  if (!iso) return '';
  return 'Membre depuis ' + new Date(iso).toLocaleDateString('fr-FR', {
    month: 'long', year: 'numeric',
  });
}

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
  } else {
    friendBtn.textContent = '+ Ajouter';
    friendBtn.className   = 'btn-friend add';
    friendBtn.onclick     = handleAddFriend;
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
