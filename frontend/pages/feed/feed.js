const API_BASE = 'http://localhost:5000/api/v1';

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

const currentUserId = (() => {
  try {
    const token = localStorage.getItem('sw_access_token');
    return JSON.parse(atob(token.split('.')[1])).sub;
  } catch { return null; }
})();

function initials(name) {
  return name ? name.slice(0, 2).toUpperCase() : '?';
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
  const d = Math.floor(h / 24);
  return `il y a ${d}j`;
}

const ACTIVITY_LABELS = {
  run:        'Course',
  bike:       'Vélo',
  swim:       'Natation',
  walk:       'Marche',
  trail:      'Trail',
  triathlon:  'Triathlon',
  hyrox:      'Hyrox',
  muscu:      'Musculation',
  basket:     'Basketball',
  foot:       'Football',
  hand:       'Handball',
  volley:     'Volleyball',
  combat:     'Combat',
};

// ── Feed state ────────────────────────────────────────────────────────────────

let currentPage = 1;
let hasNext     = false;
let loading     = false;

const feedContainer = document.getElementById('feed-container');
const emptyState    = document.getElementById('empty-state');
const loader        = document.getElementById('loader');
const loadMoreBtn   = document.getElementById('load-more');
const feedEnd       = document.getElementById('feed-end');

// ── Render helpers ────────────────────────────────────────────────────────────

function renderActivityStats(activity) {
  const parts = [];
  if (activity.distance_km != null) {
    parts.push(`<span class="stat-pill">${activity.distance_km.toFixed(1)} km</span>`);
  }
  if (activity.duration_min) {
    const h = Math.floor(activity.duration_min / 60);
    const m = activity.duration_min % 60;
    const label = h > 0 ? `${h}h${m > 0 ? m + 'min' : ''}` : `${m} min`;
    parts.push(`<span class="stat-pill">${label}</span>`);
  }
  return parts.join('');
}

function renderPost(post) {
  const act = post.activity || {};
  const badgeClass = act.type || '';
  const badgeLabel = ACTIVITY_LABELS[act.type] || act.type || '';
  const notesHtml  = act.notes
    ? `<p class="post-notes">${escapeHtml(act.notes)}</p>`
    : '';
  const photoHtml  = post.photo_url
    ? `<img class="post-photo" src="${escapeHtml(post.photo_url)}" alt="Photo de l'activité" loading="lazy" />`
    : '';

  const heartFill = post.user_has_liked ? 'currentColor' : 'none';

  const article = document.createElement('article');
  article.className = 'post-card';
  article.dataset.postId = post.id;
  article.innerHTML = `
    <div class="post-header">
      <div class="post-avatar">${initials(post.username)}</div>
      <div class="post-meta">
        <span class="post-author">${escapeHtml(post.username || '—')}</span>
        <span class="post-time">${timeAgo(post.created_at)}</span>
      </div>
    </div>

    <div class="post-activity">
      <span class="activity-badge ${badgeClass}">${badgeLabel}</span>
      <div class="activity-stats">${renderActivityStats(act)}</div>
    </div>

    ${notesHtml}
    ${photoHtml}

    <div class="post-actions">
      <button class="btn-action btn-like ${post.user_has_liked ? 'liked' : ''}" data-post-id="${post.id}">
        <svg viewBox="0 0 24 24" fill="${heartFill}" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>
        </svg>
        <span class="likes-count">${post.likes_count}</span>
      </button>

      <button class="btn-action btn-comments" data-post-id="${post.id}">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
        </svg>
        <span class="comments-count">${post.comments_count}</span>
      </button>
    </div>

    <div class="comments-section hidden" id="comments-section-${post.id}">
      <div class="comments-list" id="comments-list-${post.id}">
        <p class="comment-placeholder">Chargement…</p>
      </div>
      ${post.user_id !== currentUserId ? `
      <form class="comment-form" id="comment-form-${post.id}">
        <input
          type="text"
          class="comment-input"
          placeholder="Ajouter un commentaire…"
          maxlength="500"
          autocomplete="off"
        />
        <button type="submit" class="btn-send" disabled>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <line x1="22" y1="2" x2="11" y2="13"/>
            <polygon points="22 2 15 22 11 13 2 9 22 2"/>
          </svg>
        </button>
      </form>` : ''}
    </div>
  `;

  bindPostEvents(article, post.id);
  return article;
}

// ── Event binding ─────────────────────────────────────────────────────────────

function bindPostEvents(article, postId) {
  // Like
  article.querySelector('.btn-like').addEventListener('click', () => toggleLike(postId));

  // Comments toggle
  article.querySelector('.btn-comments').addEventListener('click', () => toggleComments(postId));

  // Comment form (absent on own posts)
  const form = article.querySelector(`#comment-form-${postId}`);
  if (form) {
    const input = form.querySelector('.comment-input');
    const send  = form.querySelector('.btn-send');

    input.addEventListener('input', () => {
      send.disabled = !input.value.trim();
    });

    form.addEventListener('submit', async e => {
      e.preventDefault();
      const content = input.value.trim();
      if (!content) return;
      send.disabled = true;
      await submitComment(postId, content);
      input.value = '';
      send.disabled = true;
    });
  }
}

// ── Like ──────────────────────────────────────────────────────────────────────

async function toggleLike(postId) {
  const card      = feedContainer.querySelector(`[data-post-id="${postId}"]`);
  const btn       = card.querySelector('.btn-like');
  const countEl   = btn.querySelector('.likes-count');
  const svg       = btn.querySelector('svg');
  const wasLiked  = btn.classList.contains('liked');

  // Optimistic update
  btn.classList.toggle('liked', !wasLiked);
  svg.setAttribute('fill', wasLiked ? 'none' : 'currentColor');
  countEl.textContent = parseInt(countEl.textContent) + (wasLiked ? -1 : 1);

  const res = await apiFetch(`/feed/${postId}/like`, { method: 'POST' });
  if (res.ok) {
    const data = await res.json();
    countEl.textContent = data.likes_count;
    btn.classList.toggle('liked', data.liked);
    svg.setAttribute('fill', data.liked ? 'currentColor' : 'none');
  } else {
    // Revert on error
    btn.classList.toggle('liked', wasLiked);
    svg.setAttribute('fill', wasLiked ? 'currentColor' : 'none');
    countEl.textContent = parseInt(countEl.textContent) + (wasLiked ? 1 : -1);
  }
}

// ── Comments ──────────────────────────────────────────────────────────────────

const loadedComments = new Set();

async function toggleComments(postId) {
  const section = document.getElementById(`comments-section-${postId}`);
  const isOpen  = !section.classList.contains('hidden');

  if (isOpen) {
    section.classList.add('hidden');
    return;
  }

  section.classList.remove('hidden');

  if (!loadedComments.has(postId)) {
    await loadComments(postId);
  }
}

async function loadComments(postId) {
  const list = document.getElementById(`comments-list-${postId}`);
  const res  = await apiFetch(`/feed/${postId}/comments`);

  if (!res.ok) {
    list.innerHTML = '<p class="comment-placeholder">Impossible de charger les commentaires.</p>';
    return;
  }

  const data     = await res.json();
  const comments = data.items || [];
  loadedComments.add(postId);
  renderComments(postId, comments);
}

function renderComments(postId, comments) {
  const list = document.getElementById(`comments-list-${postId}`);

  if (!comments.length) {
    list.innerHTML = '<p class="comment-placeholder">Aucun commentaire. Sois le premier !</p>';
    return;
  }

  list.innerHTML = comments.map(c => {
    const isOwn    = c.user_id === currentUserId;
    const deleteBtn = isOwn
      ? `<button class="btn-delete-comment" data-comment-id="${c.id}" data-post-id="${postId}" title="Supprimer">✕</button>`
      : '';
    return `
      <div class="comment-item" id="comment-${c.id}">
        <div class="comment-avatar">${initials(c.username)}</div>
        <div class="comment-body">
          <div class="comment-header">
            <span class="comment-author">${escapeHtml(c.username || '—')}</span>
            <span class="comment-time">${timeAgo(c.created_at)}</span>
          </div>
          <p class="comment-text">${escapeHtml(c.content)}</p>
        </div>
        ${deleteBtn}
      </div>
    `;
  }).join('');

  list.querySelectorAll('.btn-delete-comment').forEach(btn => {
    btn.addEventListener('click', () => deleteComment(btn.dataset.commentId, btn.dataset.postId));
  });
}

async function submitComment(postId, content) {
  const res = await apiFetch(`/feed/${postId}/comments`, {
    method: 'POST',
    body: JSON.stringify({ content }),
  });

  if (!res.ok) return;

  const comment = await res.json();
  const list    = document.getElementById(`comments-list-${postId}`);

  // Clear "no comments" placeholder if present
  const placeholder = list.querySelector('.comment-placeholder');
  if (placeholder) placeholder.remove();

  const item = document.createElement('div');
  item.className = 'comment-item';
  item.id        = `comment-${comment.id}`;
  item.innerHTML = `
    <div class="comment-avatar">${initials(comment.username)}</div>
    <div class="comment-body">
      <div class="comment-header">
        <span class="comment-author">${escapeHtml(comment.username || '—')}</span>
        <span class="comment-time">à l'instant</span>
      </div>
      <p class="comment-text">${escapeHtml(comment.content)}</p>
    </div>
    <button class="btn-delete-comment" data-comment-id="${comment.id}" data-post-id="${postId}" title="Supprimer">✕</button>
  `;
  item.querySelector('.btn-delete-comment').addEventListener('click', () =>
    deleteComment(comment.id, postId)
  );
  list.appendChild(item);

  // Update comment count
  const card     = feedContainer.querySelector(`[data-post-id="${postId}"]`);
  const countEl  = card.querySelector('.comments-count');
  countEl.textContent = parseInt(countEl.textContent) + 1;

  list.scrollTop = list.scrollHeight;
}

async function deleteComment(commentId, postId) {
  const res = await apiFetch(`/feed/comments/${commentId}`, { method: 'DELETE' });
  if (res.status !== 204) return;

  document.getElementById(`comment-${commentId}`)?.remove();

  const card    = feedContainer.querySelector(`[data-post-id="${postId}"]`);
  const countEl = card.querySelector('.comments-count');
  const newCount = Math.max(0, parseInt(countEl.textContent) - 1);
  countEl.textContent = newCount;

  const list = document.getElementById(`comments-list-${postId}`);
  if (!list.querySelector('.comment-item')) {
    list.innerHTML = '<p class="comment-placeholder">Aucun commentaire. Sois le premier !</p>';
  }
}

// ── Feed loading ──────────────────────────────────────────────────────────────

async function loadFeed(page = 1) {
  if (loading) return;
  loading = true;
  loader.classList.remove('hidden');
  loadMoreBtn.classList.add('hidden');

  const res = await apiFetch(`/feed/?page=${page}`);
  loader.classList.add('hidden');
  loading = false;

  if (!res.ok) return;

  const data  = await res.json();
  const posts = data.items || [];

  if (page === 1 && !posts.length) {
    emptyState.classList.remove('hidden');
    return;
  }

  posts.forEach(post => feedContainer.appendChild(renderPost(post)));

  hasNext     = data.has_next;
  currentPage = data.page;

  if (hasNext) {
    loadMoreBtn.classList.remove('hidden');
  } else if (page > 1) {
    feedEnd.classList.remove('hidden');
  }
}

// ── Logout ────────────────────────────────────────────────────────────────────

document.getElementById('logout-btn').addEventListener('click', async () => {
  await apiFetch('/auth/logout', { method: 'POST' }).catch(() => {});
  localStorage.removeItem('sw_access_token');
  localStorage.removeItem('sw_refresh_token');
  window.location.replace('../../index.html');
});

// ── Load more ─────────────────────────────────────────────────────────────────

loadMoreBtn.addEventListener('click', () => loadFeed(currentPage + 1));

// ── Init ──────────────────────────────────────────────────────────────────────

loadFeed(1);
