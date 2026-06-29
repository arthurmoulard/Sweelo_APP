/**
 * Page d'inscription
 *
 * Validation en temps réel : email, username (3–30 chars, alphanumeric + _-),
 * force du mot de passe (score 1–5), confirmation.
 *
 * Le backend renvoie les tokens directement dans la réponse 201,
 * ce qui évite un second appel de login post-inscription.
 * Redirige vers feed.html après 1,5 s.
 *
 * Route API : POST /auth/register
 */

const API_BASE = '/api/v1';

const form       = document.getElementById('register-form');
const emailInput = document.getElementById('email');
const userInput  = document.getElementById('username');
const pwInput    = document.getElementById('password');
const cpwInput   = document.getElementById('confirm-password');
const submitBtn  = document.getElementById('submit-btn');
const alertEl    = document.getElementById('alert');
const alertMsg   = document.getElementById('alert-msg');
const alertIcon  = document.getElementById('alert-icon');

document.getElementById('toggle-pw').addEventListener('click', () => {
  const isHidden = pwInput.type === 'password';
  pwInput.type   = isHidden ? 'text' : 'password';
  document.getElementById('eye-icon').innerHTML = isHidden
    ? `<path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/>`
    : `<path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/>`;
});

const STRENGTH_COLORS = ['', '#ff4d6a', '#ff8c42', '#ffd166', '#a8e063', '#4ecdc4'];
const STRENGTH_LABELS = ['', 'Très faible', 'Faible', 'Moyen', 'Fort', 'Excellent'];

function getStrength(pw) {
  let score = 0;
  if (pw.length >= 8)          score++;
  if (pw.length >= 12)         score++;
  if (/[A-Z]/.test(pw))        score++;
  if (/[0-9]/.test(pw))        score++;
  if (/[^A-Za-z0-9]/.test(pw)) score++;
  return score;
}

pwInput.addEventListener('input', () => {
  const s    = getStrength(pwInput.value);
  const fill = document.getElementById('strength-fill');
  const hint = document.getElementById('password-hint');
  fill.style.width      = pwInput.value ? `${s * 20}%` : '0%';
  fill.style.background = STRENGTH_COLORS[s] || 'transparent';
  if (pwInput.value) {
    hint.textContent = STRENGTH_LABELS[s];
    hint.className   = s >= 3 ? 'hint ok' : 'hint err';
  } else {
    hint.textContent = '';
    hint.className   = 'hint';
  }
  validateConfirm();
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

function validateUsername() {
  const hint = document.getElementById('username-hint');
  const val  = userInput.value.trim();
  const re   = /^[a-zA-Z0-9_\-]+$/;
  if (!val)            { setFieldState(userInput, hint, null,  '3–30 caractères, lettres, chiffres, _ ou -'); return false; }
  if (val.length < 3)  { setFieldState(userInput, hint, false, 'Minimum 3 caractères');                       return false; }
  if (val.length > 30) { setFieldState(userInput, hint, false, 'Maximum 30 caractères');                      return false; }
  if (!re.test(val))   { setFieldState(userInput, hint, false, 'Uniquement lettres, chiffres, _ ou -');        return false; }
  setFieldState(userInput, hint, true, '');
  return true;
}

function validatePassword() {
  if (pwInput.value.length > 0 && pwInput.value.length < 8) {
    setFieldState(pwInput, null, false, '');
    return false;
  }
  return pwInput.value.length >= 8;
}

function validateConfirm() {
  const hint = document.getElementById('confirm-hint');
  const val  = cpwInput.value;
  if (!val)                  { setFieldState(cpwInput, hint, null,  '');                                       return false; }
  if (val !== pwInput.value) { setFieldState(cpwInput, hint, false, 'Les mots de passe ne correspondent pas'); return false; }
  setFieldState(cpwInput, hint, true, 'Les mots de passe correspondent');
  return true;
}

emailInput.addEventListener('blur',  validateEmail);
emailInput.addEventListener('input', validateEmail);
userInput.addEventListener('blur',   validateUsername);
userInput.addEventListener('input',  validateUsername);
cpwInput.addEventListener('input',   validateConfirm);
cpwInput.addEventListener('blur',    validateConfirm);

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

  const ok = validateEmail() & validateUsername() & validatePassword() & validateConfirm();
  if (!ok) return;

  submitBtn.disabled = true;
  submitBtn.classList.add('loading');
  submitBtn.childNodes[0].textContent = 'Création en cours…';

  try {
    const res = await fetch(`${API_BASE}/auth/register`, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({
        email:    emailInput.value.trim().toLowerCase(),
        username: userInput.value.trim(),
        password: pwInput.value,
      }),
    });

    const data = await res.json();

    if (res.status === 201) {
      localStorage.setItem('sw_access_token',  data.access_token);
      localStorage.setItem('sw_refresh_token', data.refresh_token);
      showAlert('success', `Compte créé ! Bienvenue, ${data.username} 🎉 Redirection…`);
      form.reset();
      document.getElementById('strength-fill').style.width = '0%';
      setTimeout(() => { window.location.href = '../feed/feed.html'; }, 1500);
    } else if (res.status === 409) {
      showAlert('error', data.message || 'Cet e-mail ou ce pseudo est déjà utilisé.');
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
    submitBtn.childNodes[0].textContent = 'Créer mon compte';
  }
});
