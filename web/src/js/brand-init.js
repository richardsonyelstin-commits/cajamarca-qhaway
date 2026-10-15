(() => {
  const root = document.documentElement;
  const preferred = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  let theme = preferred;
  try {
    theme = localStorage.getItem('cajamarca_qhaway_theme') || preferred;
  } catch {
    theme = preferred;
  }
  root.dataset.tema = theme === 'dark' ? 'noche' : 'dia';
  root.dataset.bsTheme = theme;
  root.classList.toggle('dark', theme === 'dark');
})();
