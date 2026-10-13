/**
 * app.js: Controlador global de la plataforma Cajamarca Qhaway (Andean Civic Observatory)
 * Gestiona navegación uniforme, tema oscuro, modo rural ligero con icono representativo,
 * estado de sesión de veedores acreditados, toasts y accesibilidad.
 */

const STORAGE_KEYS = {
  THEME: 'cajamarca_qhaway_theme',
  RURAL: 'cajamarca_qhaway_rural_lite',
  TOKEN: 'cajamarca_veedor_token',
  PROFILE: 'cajamarca_veedor_profile'
};

// Notificación no bloqueante tipo toast para entornos con iFrame
window.showToast = function(message, type = 'warning') {
  let container = document.getElementById('app-toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'app-toast-container';
    container.className = 'fixed bottom-5 right-5 z-50 flex flex-col gap-2 max-w-sm';
    document.body.appendChild(container);
  }

  const toastEl = document.createElement('div');
  const bgColors = {
    error: 'bg-alert-rose text-white',
    warning: 'bg-alert-amber text-white',
    success: 'bg-civic-emerald text-white',
    info: 'bg-primary text-white'
  };
  const colorClass = bgColors[type] || 'bg-on-surface text-on-primary';

  toastEl.className = `p-3.5 rounded shadow-xl text-body-sm font-label-sm ${colorClass} flex items-center justify-between gap-3 transition-all duration-300 transform translate-y-0`;
  toastEl.setAttribute('role', 'alert');
  toastEl.innerHTML = `
    <div class="flex items-center gap-2.5">
      <span class="material-symbols-outlined text-[20px] shrink-0">${type === 'success' ? 'check_circle' : type === 'error' ? 'report' : 'info'}</span>
      <span class="leading-snug">${message}</span>
    </div>
    <button type="button" class="text-white/80 hover:text-white transition-opacity shrink-0 ml-2 cursor-pointer" aria-label="Cerrar">
      <span class="material-symbols-outlined text-[16px]">close</span>
    </button>
  `;

  const closeBtn = toastEl.querySelector('button');
  if (closeBtn) {
    closeBtn.addEventListener('click', () => toastEl.remove());
  }

  container.appendChild(toastEl);
  setTimeout(() => {
    if (toastEl.parentNode) {
      toastEl.classList.add('opacity-0', 'translate-y-2');
      setTimeout(() => toastEl.remove(), 300);
    }
  }, 4500);
};

// Reemplazo seguro de window.alert para no colgar el iFrame
window.alert = function(msg) {
  window.showToast(msg, 'warning');
};

export function initGlobalControls() {
  // 1. Tema Claro / Oscuro
  const savedTheme = localStorage.getItem(STORAGE_KEYS.THEME) || 'light';
  applyTheme(savedTheme);

  const themeToggleBtns = document.querySelectorAll('[data-action="toggle-theme"], #theme-toggle, #btn-theme-toggle');
  themeToggleBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const current = document.documentElement.classList.contains('dark') ? 'dark' : 'light';
      const nextTheme = current === 'dark' ? 'light' : 'dark';
      applyTheme(nextTheme);
      localStorage.setItem(STORAGE_KEYS.THEME, nextTheme);
    });
  });

  // 2. Modo Rural Ligero (Ahorro de datos / 2G / Sin animaciones)
  const savedRural = localStorage.getItem(STORAGE_KEYS.RURAL) === 'true';
  applyRuralMode(savedRural, false);

  const ruralBtns = document.querySelectorAll('[data-action="toggle-rural"], #rural-toggle, #btn-rural-mode');
  ruralBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const isRural = document.body.classList.contains('mode-rural-lite');
      const nextRural = !isRural;
      applyRuralMode(nextRural, true);
      localStorage.setItem(STORAGE_KEYS.RURAL, String(nextRural));
    });
  });

  // 3. Atajo global Cmd+K / Ctrl+K para buscar
  window.addEventListener('keydown', (e) => {
    if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
      e.preventDefault();
      const searchInput = document.querySelector('header input[type="text"], #entity-search');
      if (searchInput) searchInput.focus();
    }
  });

  // 4. Menú Móvil Desplegable Unificado
  const mobileBtn = document.getElementById('mobile-menu-btn') || document.getElementById('btn-mobile-nav');
  const mobileMenu = document.getElementById('mobile-menu') || document.getElementById('mobile-nav-drawer');
  if (mobileBtn && mobileMenu) {
    mobileBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      const isOpen = !mobileMenu.classList.contains('hidden');
      if (isOpen) {
        mobileMenu.classList.add('hidden');
        mobileBtn.setAttribute('aria-expanded', 'false');
      } else {
        mobileMenu.classList.remove('hidden');
        mobileBtn.setAttribute('aria-expanded', 'true');
      }
    });

    document.addEventListener('click', (e) => {
      if (!mobileMenu.contains(e.target) && !mobileBtn.contains(e.target)) {
        mobileMenu.classList.add('hidden');
        mobileBtn.setAttribute('aria-expanded', 'false');
      }
    });
  }

  // 5. Estado de Veedor Acreditado en el Encabezado
  updateVeedorHeaderStatus();
}

function applyTheme(theme) {
  const isDark = theme === 'dark';
  if (isDark) {
    document.documentElement.classList.add('dark');
    document.documentElement.setAttribute('data-bs-theme', 'dark');
  } else {
    document.documentElement.classList.remove('dark');
    document.documentElement.setAttribute('data-bs-theme', 'light');
  }

  const themeIcons = document.querySelectorAll('#theme-toggle .material-symbols-outlined, [data-action="toggle-theme"] .material-symbols-outlined');
  themeIcons.forEach(icon => {
    icon.textContent = isDark ? 'light_mode' : 'dark_mode';
  });

  const themeBtns = document.querySelectorAll('#theme-toggle, [data-action="toggle-theme"]');
  themeBtns.forEach(btn => {
    btn.title = isDark ? 'Cambiar a Tema Claro' : 'Cambiar a Tema Oscuro';
  });
}

function applyRuralMode(isRural, notify = false) {
  if (isRural) {
    document.body.classList.add('mode-rural-lite');
  } else {
    document.body.classList.remove('mode-rural-lite');
  }

  const ruralBtns = document.querySelectorAll('[data-action="toggle-rural"], #rural-toggle, #btn-rural-mode');
  ruralBtns.forEach(btn => {
    btn.setAttribute('aria-pressed', String(isRural));
    const badge = btn.querySelector('.rural-badge');
    const label = btn.querySelector('.rural-label');
    const icon = btn.querySelector('.rural-signal-icon');

    if (isRural) {
      btn.classList.add('border-civic-emerald', 'bg-civic-emerald/10', 'text-civic-emerald');
      btn.classList.remove('border-slate-border', 'text-on-surface-variant');
      btn.title = 'Modo Rural Activo: Optimizado para baja cobertura 2G (clic para desactivar)';
      if (badge) badge.classList.remove('hidden');
      if (label) label.textContent = 'Rural (2G)';
      if (icon) {
        icon.classList.add('text-civic-emerald');
        icon.classList.remove('text-on-surface-variant');
      }
    } else {
      btn.classList.remove('border-civic-emerald', 'bg-civic-emerald/10', 'text-civic-emerald');
      btn.classList.add('border-slate-border', 'text-on-surface-variant');
      btn.title = 'Modo Rural: Optimizado para baja cobertura (2G/3G), ahorra datos y elimina animaciones';
      if (badge) badge.classList.add('hidden');
      if (label) label.textContent = 'Rural';
      if (icon) {
        icon.classList.remove('text-civic-emerald');
        icon.classList.add('text-on-surface-variant');
      }
    }
  });

  if (notify) {
    window.showToast(
      isRural
        ? 'Modo Rural activado: Conectividad 2G / Consumo mínimo de datos sin animaciones pesadas.'
        : 'Modo Rural desactivado: Experiencia visual completa restaurada.',
      'info'
    );
  }
}

export function updateVeedorHeaderStatus() {
  const token = sessionStorage.getItem(STORAGE_KEYS.TOKEN);
  const profileRaw = sessionStorage.getItem(STORAGE_KEYS.PROFILE);
  const veedorBtn = document.getElementById('header-veedor-btn');

  if (!veedorBtn) return;

  if (token && profileRaw) {
    try {
      const profile = JSON.parse(profileRaw);
      veedorBtn.href = '/admin/revision';
      veedorBtn.classList.add('border-civic-emerald/50', 'text-civic-emerald', 'bg-civic-emerald/10');
      veedorBtn.classList.remove('bg-surface-container-high', 'text-on-surface');
      veedorBtn.title = `Veedor Acreditado: ${profile.name} (${profile.organization})`;
      veedorBtn.innerHTML = `
        <span class="w-2 h-2 rounded-full bg-civic-emerald animate-pulse shrink-0"></span>
        <span class="hidden md:inline font-semibold">Panel Revisor</span>
        <span class="md:hidden font-semibold">Revisión</span>
      `;
    } catch {
      // Ignorar error de parsing
    }
  } else {
    veedorBtn.href = '/login';
    veedorBtn.classList.remove('border-civic-emerald/50', 'text-civic-emerald', 'bg-civic-emerald/10');
    veedorBtn.classList.add('bg-surface-container-high', 'text-on-surface');
    veedorBtn.title = 'Acceso seguro para veedores acreditados';
    veedorBtn.innerHTML = `
      <span class="material-symbols-outlined text-[16px] text-secondary shrink-0">verified_user</span>
      <span class="hidden md:inline">Veedores</span>
    `;
  }
}

// Iniciar al cargar
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initGlobalControls);
} else {
  initGlobalControls();
}
