/**
 * Page de connexion
 *
 * Validation côté client (format email, champ non vide).
 * Si l'utilisateur est déjà connecté (token présent), redirige vers index.html.
 * Après succès (200), les tokens sont stockés dans localStorage :
 *   sw_access_token  — JWT court (utilisé dans Authorization: Bearer)
 *   sw_refresh_token — JWT long (non utilisé côté client pour l'instant)
 *
 * Route API : POST /auth/login
 */

const API_BASE = '/api/v1';

const form       = document.getElementById('login-form');
const emailInput = document.getElementById('email');
const pwInput    = document.getElementById('password');
const submitBtn  = document.getElementById('submit-btn');
const alertEl    = document.getElementById('alert');
const alertMsg   = document.getElementById('alert-msg');
const alertIcon  = document.getElementById('alert-icon');

if (localStorage.getItem('sw_access_token')) {
  window.location.replace('../../index.html');
}

document.getElementById('toggle-pw').addEventListener('click', () => {
  const isHidden = pwInput.type === 'password';
  pwInput.type   = isHidden ? 'text' : 'password';
  document.getElementById('eye-icon').innerHTML = isHidden
    ? `<path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/>`
    : `<path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/>`;
});

function setFieldState(input, hint, valid, msg) {
  input.classList.toggle('error', valid === false);
  input.classList.toggle('valid', valid === true);
  if (hint) {
    hint.textContent = msg;
    hint.className   = valid === true ? 'hint ok' : valid === false ? 'hint err' : 'hint';
  }
}

function validateEmail() {
  const hint = document.getElementById('email-hint');
  const val  = emailInput.value.trim();
  const re   = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!val)          { setFieldState(emailInput, hint, null,  '');                        return false; }
  if (!re.test(val)) { setFieldState(emailInput, hint, false, 'Adresse e-mail invalide'); return false; }
  setFieldState(emailInput, hint, true, '');
  return true;
}

function validatePassword() {
  const hint = document.getElementById('password-hint');
  const val  = pwInput.value;
  if (!val) { setFieldState(pwInput, hint, null, ''); return false; }
  setFieldState(pwInput, hint, true, '');
  return true;
}

emailInput.addEventListener('blur',  validateEmail);
emailInput.addEventListener('input', validateEmail);
pwInput.addEventListener('input',    validatePassword);

function showAlert(type, msg) {
  alertEl.className    = `alert show alert-${type}`;
  alertMsg.textContent = msg;
  alertIcon.innerHTML  = type === 'success'
    ? `<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/>`
    : `<circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>`;
}

function hideAlert() { alertEl.className = 'alert'; }

form.addEventListener('submit', async (e) => {
  e.preventDefault();
  hideAlert();

  const ok = validateEmail() & validatePassword();
  if (!ok) return;

  submitBtn.disabled = true;
  submitBtn.classList.add('loading');
  submitBtn.childNodes[0].textContent = 'Connexion…';

  try {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({
        email:    emailInput.value.trim().toLowerCase(),
        password: pwInput.value,
      }),
    });

    const data = await res.json();

    if (res.status === 200) {
      localStorage.setItem('sw_access_token',  data.access_token);
      localStorage.setItem('sw_refresh_token', data.refresh_token);
      showAlert('success', 'Connexion réussie ! Redirection…');
      setTimeout(() => { window.location.replace('../../index.html'); }, 1000);
    } else if (res.status === 401) {
      showAlert('error', data.message || 'Identifiants incorrects ou compte banni.');
    } else if (res.status === 400) {
      const msg = data.errors
        ? Object.values(data.errors).flat().join(' ')
        : data.message || 'Données invalides.';
      showAlert('error', msg);
    } else {
      showAlert('error', 'Une erreur est survenue. Réessaie plus tard.');
    }
  } catch {
    showAlert('error', 'Impossible de contacter le serveur. Vérifie ta connexion.');
  } finally {
    submitBtn.disabled = false;
    submitBtn.classList.remove('loading');
    submitBtn.childNodes[0].textContent = 'Se connecter';
  }
});