(async function () {
  try {
    const me = await apiFetch('/users/me');
    if (me.ok) {
      const data = await me.json();
      if (data.is_admin) {
        const el = document.getElementById('admin-nav-link');
        if (el) el.classList.remove('hidden');
      }
    }
  } catch (_) {}
}());
