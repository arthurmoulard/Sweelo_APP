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

// ── Sport config ──────────────────────────────────────────────────────────────

const SPORTS = [
  { key: 'run',       label: 'Course',       icon: '🏃', cat: 'endurance' },
  { key: 'bike',      label: 'Vélo',         icon: '🚴', cat: 'endurance' },
  { key: 'swim',      label: 'Natation',     icon: '🏊', cat: 'endurance' },
  { key: 'walk',      label: 'Marche',       icon: '🚶', cat: 'endurance' },
  { key: 'trail',     label: 'Trail',        icon: '⛰️',  cat: 'endurance' },
  { key: 'triathlon', label: 'Triathlon',    icon: '🏅', cat: 'endurance' },
  { key: 'hyrox',     label: 'Hyrox',        icon: '⚡', cat: 'endurance' },
  { key: 'muscu',     label: 'Muscu',        icon: '🏋️', cat: 'gym'      },
  { key: 'basket',    label: 'Basket',       icon: '🏀', cat: 'team'     },
  { key: 'foot',      label: 'Football',     icon: '⚽', cat: 'team'     },
  { key: 'hand',      label: 'Handball',     icon: '🤾', cat: 'team'     },
  { key: 'volley',    label: 'Volley',       icon: '🏐', cat: 'team'     },
  { key: 'combat',    label: 'Combat',       icon: '🥋', cat: 'combat'   },
];

const NO_DISTANCE = new Set(['muscu', 'basket', 'foot', 'hand', 'volley', 'combat']);

const sportByKey = Object.fromEntries(SPORTS.map(s => [s.key, s]));

// ── Utilities ─────────────────────────────────────────────────────────────────

function escapeHtml(str) {
  return String(str).replace(/[&<>"']/g, c =>
    ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c])
  );
}

function formatDate(iso) {
  return new Date(iso + 'T00:00:00').toLocaleDateString('fr-FR', {
    day: 'numeric', month: 'long', year: 'numeric',
  });
}

function formatDuration(min) {
  const h = Math.floor(min / 60);
  const m = min % 60;
  if (h === 0) return `${m} min`;
  if (m === 0) return `${h}h`;
  return `${h}h ${m}min`;
}

function todayISO() {
  return new Date().toISOString().slice(0, 10);
}

// ── List state ────────────────────────────────────────────────────────────────

let currentPage = 1;
let hasNext     = false;
let loading     = false;

const container  = document.getElementById('activities-container');
const emptyState = document.getElementById('empty-state');
const loader     = document.getElementById('loader');
const loadMoreBtn = document.getElementById('load-more');
const listEnd    = document.getElementById('list-end');

// ── Render activity card ──────────────────────────────────────────────────────

function renderCard(activity) {
  const sport = sportByKey[activity.type] || { label: activity.type, icon: '🏃', cat: 'endurance' };

  const stats = [];
  if (activity.distance_km != null) {
    stats.push(`<span class="stat-pill">${activity.distance_km.toFixed(1)} km</span>`);
  }
  stats.push(`<span class="stat-pill">${formatDuration(activity.duration_min)}</span>`);

  const notesHtml = activity.notes
    ? `<p class="activity-notes">${escapeHtml(activity.notes)}</p>`
    : '';

  const photoBadge = activity.photo_url
    ? `<span class="activity-photo-badge" title="Contient une photo">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
             stroke-linecap="round" stroke-linejoin="round" width="14" height="14">
          <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"/>
          <circle cx="12" cy="13" r="4"/>
        </svg>
      </span>`
    : '';

  const div = document.createElement('div');
  div.className = 'activity-card';
  div.dataset.activityId = activity.id;
  div.innerHTML = `
    <div class="activity-icon ${sport.cat}">${sport.icon}</div>
    <div class="activity-body">
      <div class="activity-top">
        <span class="activity-label">${sport.label}</span>
        ${photoBadge}
        <span class="activity-date">${formatDate(activity.date)}</span>
      </div>
      <div class="activity-stats">${stats.join('')}</div>
      ${notesHtml}
    </div>
    <div class="activity-actions">
      <button class="btn-icon btn-edit" title="Modifier" data-id="${activity.id}">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
          <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
        </svg>
      </button>
      <button class="btn-icon btn-icon danger btn-delete" title="Supprimer" data-id="${activity.id}">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <polyline points="3 6 5 6 21 6"/>
          <path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/>
          <path d="M10 11v6"/><path d="M14 11v6"/>
          <path d="M9 6V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2"/>
        </svg>
      </button>
    </div>
  `;

  div.querySelector('.btn-edit').addEventListener('click', () => openModal(activity));
  div.querySelector('.btn-delete').addEventListener('click', () => openConfirm(activity.id));

  return div;
}

// ── Load activities ───────────────────────────────────────────────────────────

async function loadActivities(page = 1) {
  if (loading) return;
  loading = true;
  loader.classList.remove('hidden');
  loadMoreBtn.classList.add('hidden');

  const res = await apiFetch(`/activities/?page=${page}`);
  loader.classList.add('hidden');
  loading = false;

  if (!res.ok) return;

  const data       = await res.json();
  const activities = data.items || [];

  if (page === 1 && !activities.length) {
    emptyState.classList.remove('hidden');
    return;
  }

  activities.forEach(a => container.appendChild(renderCard(a)));

  hasNext     = data.has_next;
  currentPage = data.page;

  if (hasNext) {
    loadMoreBtn.classList.remove('hidden');
  } else if (page > 1) {
    listEnd.classList.remove('hidden');
  }
}

loadMoreBtn.addEventListener('click', () => loadActivities(currentPage + 1));

// ── Modal state ───────────────────────────────────────────────────────────────

const modal      = document.getElementById('modal');
const modalTitle = document.getElementById('modal-title');
const modalAlert = document.getElementById('modal-alert');
const saveBtn    = document.getElementById('save-btn');
const deleteBtn  = document.getElementById('delete-btn');

let editingId    = null;
let selectedType = null;

// ── Build sport grid ──────────────────────────────────────────────────────────

const sportGrid = document.getElementById('sport-grid');

SPORTS.forEach(sport => {
  const btn = document.createElement('button');
  btn.type      = 'button';
  btn.className = 'sport-btn';
  btn.dataset.key = sport.key;
  btn.innerHTML = `${sport.icon}<br>${sport.label}`;
  btn.addEventListener('click', () => selectSport(sport.key));
  sportGrid.appendChild(btn);
});

function selectSport(key) {
  selectedType = key;
  sportGrid.querySelectorAll('.sport-btn').forEach(b => {
    b.classList.toggle('selected', b.dataset.key === key);
  });
  document.getElementById('err-type').textContent = '';
  // Toggle distance field
  document.getElementById('distance-field').style.display =
    NO_DISTANCE.has(key) ? 'none' : '';
}

// ── Gestion de la photo ───────────────────────────────────────────────────────

// stocke l'ID du post lié à l'activité en cours d'édition (pour l'upload)
let currentPostId   = null;
// indique si l'utilisateur veut supprimer la photo existante
let pendingRemovePhoto = false;

const photoInput   = document.getElementById('f-photo');
const photoDrop    = document.getElementById('photo-drop');
const photoLabel   = document.getElementById('photo-label');
const photoFilename = document.getElementById('photo-filename');
const photoCurrent = document.getElementById('photo-current');
const photoPreview = document.getElementById('photo-preview');
const photoRemove  = document.getElementById('photo-remove');

// Met à jour le label quand l'utilisateur sélectionne un fichier
photoInput.addEventListener('change', () => {
  if (photoInput.files[0]) {
    photoFilename.textContent = photoInput.files[0].name;
    photoFilename.classList.remove('hidden');
    photoLabel.textContent = 'Changer la photo';
  }
});

// Drag & drop sur la zone de sélection
photoDrop.addEventListener('dragover', e => { e.preventDefault(); photoDrop.classList.add('drag-over'); });
photoDrop.addEventListener('dragleave', () => photoDrop.classList.remove('drag-over'));
photoDrop.addEventListener('drop', e => {
  e.preventDefault();
  photoDrop.classList.remove('drag-over');
  const file = e.dataTransfer.files[0];
  if (file && file.type.startsWith('image/')) {
    // Injecte le fichier dans l'input natif
    const dt = new DataTransfer();
    dt.items.add(file);
    photoInput.files = dt.files;
    photoFilename.textContent = file.name;
    photoFilename.classList.remove('hidden');
    photoLabel.textContent = 'Changer la photo';
  }
});

// Bouton de suppression de la photo existante
photoRemove.addEventListener('click', () => {
  pendingRemovePhoto = true;
  photoCurrent.classList.add('hidden');
  photoPreview.src = '';
  photoLabel.textContent = 'Cliquer ou glisser une photo ici';
  photoFilename.classList.add('hidden');
  photoInput.value = '';
});

function resetPhotoField() {
  pendingRemovePhoto = false;
  currentPostId      = null;
  photoInput.value   = '';
  photoFilename.textContent = '';
  photoFilename.classList.add('hidden');
  photoCurrent.classList.add('hidden');
  photoPreview.src = '';
  photoLabel.textContent = 'Cliquer ou glisser une photo ici';
}

// Upload la photo sélectionnée vers le backend, retourne la photo_url ou null
async function uploadPhoto(postId) {
  if (!photoInput.files[0]) return null;
  const fd = new FormData();
  fd.append('photo', photoInput.files[0]);
  // On n'utilise pas apiFetch car on envoie multipart (pas JSON)
  const res = await fetch(`${API_BASE}/feed/${postId}/photo`, {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${localStorage.getItem('sw_access_token')}` },
    body: fd,
  });
  if (res.ok) {
    const data = await res.json();
    return data.photo_url || null;
  }
  return null;
}

// Supprime la photo via l'API
async function deletePhoto(postId) {
  await apiFetch(`/feed/${postId}/photo`, { method: 'DELETE' });
}

// ── Open / close modal ────────────────────────────────────────────────────────

function openModal(activity = null) {
  editingId    = activity ? activity.id : null;
  selectedType = null;

  modalTitle.textContent = activity ? 'Modifier l\'activité' : 'Nouvelle activité';
  deleteBtn.classList.toggle('hidden', !activity);
  clearAlert();
  clearErrors();
  resetPhotoField();

  // Reset sport grid
  sportGrid.querySelectorAll('.sport-btn').forEach(b => b.classList.remove('selected'));
  document.getElementById('distance-field').style.display = '';

  // Fill fields
  document.getElementById('f-date').value     = activity ? activity.date : todayISO();
  document.getElementById('f-duration').value = activity ? activity.duration_min : '';
  document.getElementById('f-distance').value = activity ? (activity.distance_km ?? '') : '';
  document.getElementById('f-notes').value    = activity ? (activity.notes ?? '') : '';
  updateCharCount();

  if (activity) {
    selectSport(activity.type);
    currentPostId = activity.post_id || null;

    // Affiche la photo existante si présente
    if (activity.photo_url) {
      photoPreview.src = activity.photo_url;
      photoCurrent.classList.remove('hidden');
      photoLabel.textContent = 'Remplacer la photo';
    }
  }

  modal.classList.remove('hidden');
  document.getElementById('f-date').focus();
}

function closeModal() {
  modal.classList.add('hidden');
  editingId = null;
  selectedType = null;
  resetPhotoField();
}

document.getElementById('modal-close').addEventListener('click', closeModal);
document.getElementById('cancel-btn').addEventListener('click', closeModal);
modal.addEventListener('click', e => { if (e.target === modal) closeModal(); });
document.addEventListener('keydown', e => {
  if (e.key === 'Escape') { closeModal(); closeConfirm(); }
});

// ── Char count ────────────────────────────────────────────────────────────────

function updateCharCount() {
  const len = document.getElementById('f-notes').value.length;
  document.getElementById('char-count').textContent = `${len} / 500`;
}
document.getElementById('f-notes').addEventListener('input', updateCharCount);

// ── Validation ────────────────────────────────────────────────────────────────

function showAlert(msg, type = 'error') {
  modalAlert.textContent = msg;
  modalAlert.className   = `alert ${type}`;
}
function clearAlert() {
  modalAlert.className   = 'alert hidden';
  modalAlert.textContent = '';
}

function setErr(id, msg) {
  document.getElementById(id).textContent = msg;
  const inputId = id.replace('err-', 'f-');
  document.getElementById(inputId)?.classList.toggle('error', !!msg);
  return !msg;
}
function clearErrors() {
  ['err-type', 'err-date', 'err-duration', 'err-distance'].forEach(id => setErr(id, ''));
}

function validate() {
  let ok = true;
  if (!selectedType)                                         { setErr('err-type',     'Choisis un sport');       ok = false; }
  const date = document.getElementById('f-date').value;
  if (!date)                                                 { setErr('err-date',     'Requis');                  ok = false; }
  else if (date > todayISO())                                { setErr('err-date',     'Pas dans le futur');       ok = false; }
  const dur = parseInt(document.getElementById('f-duration').value);
  if (!dur || dur < 1)                                       { setErr('err-duration', 'Au moins 1 minute');       ok = false; }
  if (selectedType && !NO_DISTANCE.has(selectedType)) {
    const dist = parseFloat(document.getElementById('f-distance').value);
    if (!dist || dist <= 0)                                  { setErr('err-distance', 'Distance requise');        ok = false; }
  }
  return ok;
}

// ── Save ──────────────────────────────────────────────────────────────────────

saveBtn.addEventListener('click', async () => {
  clearAlert();
  if (!validate()) return;

  const notes = document.getElementById('f-notes').value.trim();
  const body = {
    type:         selectedType,
    date:         document.getElementById('f-date').value,
    duration_min: parseInt(document.getElementById('f-duration').value),
  };
  if (notes) body.notes = notes;

  if (!NO_DISTANCE.has(selectedType)) {
    body.distance_km = parseFloat(document.getElementById('f-distance').value);
  }

  saveBtn.disabled = true;
  saveBtn.classList.add('loading');

  const isEdit = !!editingId;
  const res = await apiFetch(
    isEdit ? `/activities/${editingId}` : '/activities/',
    { method: isEdit ? 'PUT' : 'POST', body: JSON.stringify(body) }
  );

  saveBtn.disabled = false;
  saveBtn.classList.remove('loading');

  if (res.ok) {
    let activity = await res.json();

    // Gestion photo après la sauvegarde de l'activité
    const postId = isEdit ? currentPostId : activity.post_id;
    if (postId) {
      if (pendingRemovePhoto) {
        await deletePhoto(postId);
        activity = { ...activity, photo_url: null };
      } else if (photoInput.files[0]) {
        const url = await uploadPhoto(postId);
        if (url) activity = { ...activity, photo_url: url };
      }
    }

    if (isEdit) {
      // Replace card in list
      const old = container.querySelector(`[data-activity-id="${editingId}"]`);
      if (old) old.replaceWith(renderCard(activity));
    } else {
      // Prepend new card, hide empty state
      emptyState.classList.add('hidden');
      container.prepend(renderCard(activity));
    }
    closeModal();
  } else {
    const err = await res.json().catch(() => ({}));
    showAlert(err.message || err.msg || 'Une erreur est survenue.', 'error');
  }
});

// ── Delete confirm ────────────────────────────────────────────────────────────

const confirmModal  = document.getElementById('confirm-modal');
const confirmDelete = document.getElementById('confirm-delete');
let deletingId      = null;

function openConfirm(id) {
  deletingId = id;
  confirmModal.classList.remove('hidden');
}
function closeConfirm() {
  confirmModal.classList.add('hidden');
  deletingId = null;
}

document.getElementById('confirm-cancel').addEventListener('click', closeConfirm);
confirmModal.addEventListener('click', e => { if (e.target === confirmModal) closeConfirm(); });

confirmDelete.addEventListener('click', async () => {
  if (!deletingId) return;
  confirmDelete.disabled = true;
  confirmDelete.classList.add('loading');

  const res = await apiFetch(`/activities/${deletingId}`, { method: 'DELETE' });

  confirmDelete.disabled = false;
  confirmDelete.classList.remove('loading');

  if (res.status === 204) {
    container.querySelector(`[data-activity-id="${deletingId}"]`)?.remove();
    closeConfirm();
    closeModal();

    if (!container.children.length) {
      emptyState.classList.remove('hidden');
    }
  }
});

// Modal's own delete button opens the confirm
deleteBtn.addEventListener('click', () => {
  if (editingId) openConfirm(editingId);
});

// ── New buttons ───────────────────────────────────────────────────────────────

document.getElementById('new-btn').addEventListener('click', () => openModal());
document.getElementById('new-btn-empty').addEventListener('click', () => openModal());

// ── Logout ────────────────────────────────────────────────────────────────────

document.getElementById('logout-btn').addEventListener('click', async () => {
  await apiFetch('/auth/logout', { method: 'POST' }).catch(() => {});
  localStorage.removeItem('sw_access_token');
  localStorage.removeItem('sw_refresh_token');
  window.location.replace('../../index.html');
});

// ── Init ──────────────────────────────────────────────────────────────────────

loadActivities(1);
