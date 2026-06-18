const API_BASE = 'http://localhost:5000/api/v1';

/* ── Sélecteurs ── */
const form      = document.getElementById('login-form');   // id corrigé
const emailInput = document.getElementById('email');       // harmonisé avec l'HTML
const pwInput    = document.getElementById('password');
const submitBtn  = document.getElementById('submit-btn');
const alertEl    = document.getElementById('alert');
const alertMsg   = document.getElementById('alert-msg');
const alertIcon  = document.getElementById('alert-icon');
const btnLabel   = document.getElementById('btn-label');   // cible stable pour le texte

/* ── Afficher / masquer le mot de passe ── */
document.getElementById('toggle-pw').addEventListener('click', () => {
  const isHidden = pwInput.type === 'password';
  pwInput.type   = isHidden ? 'text' : 'password';

  document.getElementById('eye-icon').innerHTML = isHidden
    ? `<path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8
               a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4
               c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19
               m-6.72-1.07a3 3 0 1 1-4.24-4.24"/>
       <line x1="1" y1="1" x2="23" y2="23"/>`
    : `<path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
       <circle cx="12" cy="12" r="3"/>`;
});

/* ── Helpers état de champ ── */
function setFieldState(input, hintEl, valid, msg) {
  input.classList.toggle('error', valid === false);
  input.classList.toggle('valid', valid === true);
  if (hintEl) {
    hintEl.textContent = msg;
    hintEl.className   = valid === true  ? 'hint ok'
                       : valid === false ? 'hint err'
                       : 'hint';
  }
}

/* ── Validation email ── */
function validateEmail() {
  const hint = document.getElementById('email-hint');
  const val  = emailInput.value.trim();
  const re   = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

  if (!val)          { setFieldState(emailInput, hint, null,  '');                        return false; }
  if (!re.test(val)) { setFieldState(emailInput, hint, false, 'Adresse e-mail invalide'); return false; }
  setFieldState(emailInput, hint, true, '');
  return true;
}

/* ── Validation mot de passe (présence uniquement au login) ── */
function validatePassword() {
  const hint = document.getElementById('password-hint');
  const val  = pwInput.value;

  if (!val) { setFieldState(pwInput, hint, null, '');                       return false; }
  // On ne vérifie PAS la force au login — juste la présence
  setFieldState(pwInput, hint, true, '');
  return true;
}

/* ── Listeners de validation en temps réel ── */
emailInput.addEventListener('blur',  validateEmail);
emailInput.addEventListener('input', validateEmail);
pwInput.addEventListener('blur',     validatePassword);
pwInput.addEventListener('input',    validatePassword);

/* ── Alerte globale ── */
function showAlert(type, msg) {
  alertEl.className    = `alert show alert-${type}`;
  alertMsg.textContent = msg;
  alertIcon.innerHTML  = type === 'success'
    ? `<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
       <polyline points="22 4 12 14.01 9 11.01"/>`
    : `<circle cx="12" cy="12" r="10"/>
       <line x1="12" y1="8" x2="12" y2="12"/>
       <line x1="12" y1="16" x2="12.01" y2="16"/>`;
}

function hideAlert() {
  alertEl.className = 'alert';
}

/* ── Soumission du formulaire ── */
form.addEventListener('submit', async (e) => {
  e.preventDefault();
  hideAlert();

  // On utilise || pour court-circuiter proprement (pas de & bitwise)
  const emailOk = validateEmail();
  const pwOk    = validatePassword();
  if (!emailOk || !pwOk) return;

  // État chargement — on cible .btn-label, pas childNodes[0]
  submitBtn.disabled = true;
  submitBtn.classList.add('loading');
  document.querySelector('.btn-label').textContent = 'Connexion en cours…';

  try {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email:    emailInput.value.trim().toLowerCase(),
        password: pwInput.value,
        // ✅ username supprimé — inutile au login
      }),
    });

    const data = await res.json();

    if (res.status === 200) {
      // ✅ 200 OK pour le login (pas 201)
      localStorage.setItem('sweelo_access_token', data.data.access_token);

      // On décode le username depuis le token pour l'afficher
      let username = '';
      try {
        const payload = JSON.parse(atob(data.data.access_token.split('.')[1]));
        username = payload.username || payload.sub || '';
      } catch { /* token illisible, on affiche sans nom */ }

      showAlert('success', `Bienvenue${username ? ' ' + username : ''} ! 🎉 Redirection…`);
      setTimeout(() => { window.location.href = '../index.html'; }, 1800);

    } else if (res.status === 401) {
      showAlert('error', 'Email ou mot de passe incorrect.');

    } else if (res.status === 400) {
      const msg = data.errors
        ? Object.values(data.errors).flat().join(' ')
        : data.message || 'Données invalides.';
      showAlert('error', msg);

    } else if (res.status === 403) {
      showAlert('error', 'Ton compte a été suspendu. Contacte le support.');

    } else {
      showAlert('error', 'Une erreur est survenue. Réessaie plus tard.');
    }

  } catch {
    showAlert('error', 'Impossible de contacter le serveur. Vérifie ta connexion.');

  } finally {
    submitBtn.disabled = false;
    submitBtn.classList.remove('loading');
    document.querySelector('.btn-label').textContent = 'Se connecter';
  }
});