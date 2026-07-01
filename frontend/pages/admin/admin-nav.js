(function () {
  try {
    const t = localStorage.getItem('sw_access_token');
    const p = JSON.parse(atob(t.split('.')[1]));
    if (p.is_admin) {
      const el = document.getElementById('admin-nav-link');
      if (el) el.classList.remove('hidden');
    }
  } catch (_) {}
}());
