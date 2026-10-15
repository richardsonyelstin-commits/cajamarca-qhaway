/**
 * app.js: Controlador global de la plataforma Cajamarca Qhaway (Andean Civic Observatory)
 * Gestiona navegacion uniforme, tema oscuro, modo rural ligero, estado de sesion
 * de veedores acreditados, toasts, hidratacion dinamica de KPIs y exploradores en vivo.
 *
 * Politicas:
 * - Antislop R-02: Cero rayas em-dash en todo el archivo.
 * - WCAG 2.2 AA: Foco visible, targets >= 44px en controles interactivos, Escape para cerrar modales.
 * - Art. 14 Constitucion: Solo alertas published en vista publica.
 * - Art. 15 Constitucion: Explicabilidad algoritmica integral.
 */

import { dataEngine } from './data-engine.js';
import { CIVIC_DICTIONARY, CIVIC_DICTIONARY_MAP } from './dictionary-data.js';

const STORAGE_KEYS = {
  THEME: 'cajamarca_qhaway_theme',
  RURAL: 'cajamarca_qhaway_rural_lite',
  LANG_MODE: 'cq_lang_mode',
  TOKEN: 'cajamarca_veedor_token',
  PROFILE: 'cajamarca_veedor_profile'
};

// Notificacion no bloqueante tipo toast para entornos con iFrame
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

/**
 * Drawer / Modal Universal para Evidencia OCDS Cruda (Art. 10)
 */
let rawPayloadReturnFocus = null;
function closeRawPayloadDrawer() {
  document.getElementById('global-raw-payload-modal')?.classList.add('hidden');
  rawPayloadReturnFocus?.focus?.();
}

export function openRawPayloadDrawer(payloadObj, title = 'Evidencia Original OCDS (Art. 10)') {
  rawPayloadReturnFocus = document.activeElement;
  let modalEl = document.getElementById('global-raw-payload-modal');
  if (!modalEl) {
    modalEl = document.createElement('div');
    modalEl.id = 'global-raw-payload-modal';
    modalEl.className = 'fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 hidden';
    modalEl.setAttribute('role', 'dialog');
    modalEl.setAttribute('aria-modal', 'true');
    modalEl.setAttribute('aria-labelledby', 'global-raw-payload-title');
    modalEl.innerHTML = `
      <div class="bg-surface-container-lowest border border-slate-border rounded-lg shadow-2xl max-w-4xl w-full max-h-[90vh] flex flex-col overflow-hidden">
        <div class="p-4 border-b border-slate-border flex items-center justify-between bg-surface-container-low">
          <div class="flex items-center gap-2">
            <span class="material-symbols-outlined text-secondary text-[20px]">policy</span>
            <h3 id="global-raw-payload-title" class="font-serif font-bold text-base text-on-surface truncate"></h3>
          </div>
          <div class="flex items-center gap-2">
            <div class="inline-flex rounded border border-slate-border p-0.5 bg-surface text-xs">
              <button id="payload-tab-card" type="button" class="px-2.5 py-1 rounded bg-secondary text-white font-semibold cursor-pointer">Ficha Técnica</button>
              <button id="payload-tab-json" type="button" class="px-2.5 py-1 rounded text-on-surface-variant hover:text-on-surface font-semibold cursor-pointer">Microdatos JSON</button>
            </div>
            <button id="global-raw-payload-copy-btn" class="px-3 py-1.5 rounded bg-surface border border-slate-border hover:bg-surface-container text-xs font-semibold text-on-surface flex items-center gap-1 cursor-pointer transition-colors" title="Copiar JSON completo">
              <span class="material-symbols-outlined text-[15px]">content_copy</span> <span class="hidden sm:inline">Copiar</span>
            </button>
            <button id="global-raw-payload-close-btn" class="p-1.5 rounded hover:bg-surface-container text-on-surface-variant hover:text-on-surface cursor-pointer" aria-label="Cerrar modal">
              <span class="material-symbols-outlined text-[20px]">close</span>
            </button>
          </div>
        </div>

        <div id="payload-view-card" class="p-6 overflow-y-auto flex-1 bg-surface space-y-4">
          <div id="payload-card-content"></div>
        </div>

        <div id="payload-view-json" class="p-4 overflow-y-auto flex-1 bg-surface font-mono text-xs text-on-surface leading-relaxed hidden">
          <pre id="global-raw-payload-code" class="whitespace-pre-wrap break-all"></pre>
        </div>

        <div class="p-3 border-t border-slate-border bg-surface-container-low text-[11px] text-on-surface-variant flex items-center justify-between">
          <span>Fuente inmutable verificable: SEACE OCDS / MEF SIAF (Art. 10 y 14 de la Constitución)</span>
          <span class="font-semibold text-secondary">Veeduría Ciudadana Cajamarca</span>
        </div>
      </div>
    `;
    document.body.appendChild(modalEl);

    const btnTabCard = modalEl.querySelector('#payload-tab-card');
    const btnTabJson = modalEl.querySelector('#payload-tab-json');
    const viewCard = modalEl.querySelector('#payload-view-card');
    const viewJson = modalEl.querySelector('#payload-view-json');

    btnTabCard.addEventListener('click', () => {
      btnTabCard.className = 'px-2.5 py-1 rounded bg-secondary text-white font-semibold cursor-pointer';
      btnTabJson.className = 'px-2.5 py-1 rounded text-on-surface-variant hover:text-on-surface font-semibold cursor-pointer';
      viewCard.classList.remove('hidden');
      viewJson.classList.add('hidden');
    });

    btnTabJson.addEventListener('click', () => {
      btnTabJson.className = 'px-2.5 py-1 rounded bg-secondary text-white font-semibold cursor-pointer';
      btnTabCard.className = 'px-2.5 py-1 rounded text-on-surface-variant hover:text-on-surface font-semibold cursor-pointer';
      viewJson.classList.remove('hidden');
      viewCard.classList.add('hidden');
    });

    modalEl.querySelector('#global-raw-payload-close-btn').addEventListener('click', closeRawPayloadDrawer);
    modalEl.addEventListener('click', (e) => {
      if (e.target === modalEl) closeRawPayloadDrawer();
    });
    modalEl.querySelector('#global-raw-payload-copy-btn').addEventListener('click', () => {
      const code = modalEl.querySelector('#global-raw-payload-code').textContent;
      navigator.clipboard.writeText(code).then(() => {
        window.showToast('JSON copiado al portapapeles', 'success');
      });
    });
    window.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && !modalEl.classList.contains('hidden')) {
        closeRawPayloadDrawer();
      }
    });
  }

  const titleEl = modalEl.querySelector('#global-raw-payload-title');
  const codeEl = modalEl.querySelector('#global-raw-payload-code');
  const cardContentEl = modalEl.querySelector('#payload-card-content');

  if (titleEl) titleEl.textContent = title;
  if (codeEl) codeEl.textContent = JSON.stringify(payloadObj || {}, null, 2);

  if (cardContentEl) {
    cardContentEl.replaceChildren();
    const heading = document.createElement('h4');
    heading.textContent = 'Procedencia del registro';
    const note = document.createElement('p');
    note.textContent = payloadObj?.alerta?.status === 'published'
      ? 'El expediente incluye un dictamen publicado. Sus campos originales constan en Microdatos JSON.'
      : 'Registro oficial sin dictamen humano publicado asociado. Esta evidencia no es una alerta publicada.';
    const definition = document.createElement('dl');
    definition.className = 'qh-moments';
    for (const [key, value] of Object.entries(payloadObj || {})) {
      if (value == null || typeof value === 'object') continue;
      const row = document.createElement('div');
      const term = document.createElement('dt');
      const content = document.createElement('dd');
      term.textContent = key;
      content.textContent = String(value);
      row.append(term, content);
      definition.append(row);
    }
    const help = document.createElement('p');
    help.textContent = 'Microdatos JSON conserva las filas originales, fuentes y fechas de extraccion. Una senal tecnica requiere contexto y revision humana.';
    cardContentEl.append(heading, note, definition, help);
  }

  modalEl.classList.remove('hidden');
  modalEl.querySelector('#global-raw-payload-close-btn')?.focus();
  modalEl.onkeydown = event => {
    if (event.key !== 'Tab') return;
    const controls = [...modalEl.querySelectorAll('button,a[href],input,select,textarea,[tabindex="0"]')]
      .filter(element => element.getBoundingClientRect().height && !element.disabled);
    const first = controls[0], last = controls.at(-1);
    if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last?.focus(); }
    else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first?.focus(); }
  };
}

window.openRawPayloadModal = openRawPayloadDrawer;
window.openRawPayloadDrawer = openRawPayloadDrawer;

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
      const searchInput = document.querySelector('header input[type="text"], #entity-search, #index-procurement-search');
      if (searchInput) searchInput.focus();
    }
  });

  // 4. Menu Movil Desplegable Unificado
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

  // 6. Modo Ciudadano / Especialista (Pedagogia Civica)
  initLanguageMode();

  // 7. Micro-Tooltips Civicos Accesibles
  initCivicTooltips();

  // 8. Modal de Diccionario Civico Popular
  initCivicDictionaryModal();

  // 9. Hidratacion reactiva de datos reales (DataEngine)
  hydrateAllViews();
}

function applyTheme(theme) {
  const isDark = theme === 'dark';
  document.documentElement.dataset.tema = isDark ? 'noche' : 'dia';
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
        ? 'Modo Rural activado: Conectividad 2G / Consumo minimo de datos sin animaciones pesadas.'
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
        <span class="md:hidden font-semibold">Revision</span>
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

/**
 * ============================================================================
 * PEDAGOGIA CIVICA, LENGUAJE CLARO Y ACCESIBILIDAD COGNITIVA
 * Politica Antislop R-02: Cero guiones largos em-dash en todo el codigo.
 * WCAG 2.2 AA: Soporte completo de teclado, trampa de foco y contraste >= 4.5:1.
 * ============================================================================
 */

export function formatCitizenPocketMoney(percentage) {
  const numPct = typeof percentage === 'number' ? percentage : parseFloat(percentage) || 0;
  const solesPer100 = Math.round(numPct);
  const remaining = Math.max(0, 100 - solesPer100);

  let statusClass = 'civic-status-warning';
  let statusIcon = 'schedule';
  let statusLabel = 'Gasto lento';

  if (solesPer100 < 30) {
    statusClass = 'civic-status-critical';
    statusIcon = 'warning';
    statusLabel = 'Atención requerida';
  } else if (solesPer100 > 60) {
    statusClass = 'civic-status-good';
    statusIcon = 'check_circle';
    statusLabel = 'Gasto al día';
  }

  return {
    solesPer100,
    remaining,
    badge: `S/ ${solesPer100} de cada S/ 100`,
    narrative: `De cada S/ 100 del PIM elegido, S/ ${solesPer100} corresponden a gasto reconocido y S/ ${remaining} siguen sin devengar.`,
    statusClass,
    statusIcon,
    statusLabel
  };
}

export function formatCitizenPerCapita(montoTotal, poblacion = 1550000) {
  if (!montoTotal || isNaN(montoTotal)) return '';
  const porPersona = Math.round(montoTotal / poblacion);
  return `aprox. S/ ${porPersona.toLocaleString('es-PE')} por cada habitante de Cajamarca`;
}

export function initLanguageMode() {
  const savedMode = localStorage.getItem(STORAGE_KEYS.LANG_MODE) ||
                    localStorage.getItem('cq_lang_mode') ||
                    localStorage.getItem('cajamarca_qhaway_lang_mode') ||
                    'ciudadano';
  applyLanguageMode(savedMode, false);

  const toggleBtns = document.querySelectorAll('[data-action="toggle-lang-mode"], #lang-mode-toggle, .civic-mode-toggle');
  toggleBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const current = document.documentElement.getAttribute('data-lang-mode') || 'ciudadano';
      const nextMode = current === 'ciudadano' ? 'especialista' : 'ciudadano';
      applyLanguageMode(nextMode, true);
    });
  });
}

export function toggleLanguageMode() {
  const current = document.documentElement.getAttribute('data-lang-mode') || 'ciudadano';
  const nextMode = current === 'ciudadano' ? 'especialista' : 'ciudadano';
  applyLanguageMode(nextMode, true);
}

export function applyLanguageMode(mode, notify = false) {
  const isCitizen = mode === 'ciudadano';
  document.documentElement.setAttribute('data-lang-mode', mode);
  document.body.dataset.modo = mode;
  localStorage.setItem(STORAGE_KEYS.LANG_MODE, mode);
  localStorage.setItem('cq_lang_mode', mode);
  localStorage.setItem('cajamarca_qhaway_lang_mode', mode);

  // Actualizar botones de conmutacion en la interfaz
  const toggleBtns = document.querySelectorAll('[data-action="toggle-lang-mode"], #lang-mode-toggle, .civic-mode-toggle');
  toggleBtns.forEach(btn => {
    btn.setAttribute('aria-pressed', String(isCitizen));
    btn.setAttribute('aria-checked', String(isCitizen));
    const label = btn.querySelector('.lang-mode-label');
    const icon = btn.querySelector('.lang-mode-icon');
    if (isCitizen) {
      btn.title = 'Modo Ciudadano Activo: Lenguaje claro y explicaciones sencillas (clic para Modo Especialista)';
      if (label) label.textContent = 'Modo Ciudadano';
      if (icon) icon.textContent = 'groups';
      btn.classList.add('border-secondary', 'bg-secondary-container/20', 'text-secondary');
      btn.classList.remove('border-slate-border', 'text-on-surface-variant');
    } else {
      btn.title = 'Modo Especialista Activo: Siglas técnicas y fórmulas oficiales (clic para Modo Ciudadano)';
      if (label) label.textContent = 'Modo Especialista';
      if (icon) icon.textContent = 'analytics';
      btn.classList.remove('border-secondary', 'bg-secondary-container/20', 'text-secondary');
      btn.classList.add('border-slate-border', 'text-on-surface-variant');
    }
  });

  // Intercambio reactivo de textos marcados con .civic-text-swap
  document.querySelectorAll('.civic-text-swap').forEach(el => {
    const textCitizen = el.getAttribute('data-ciudadano') || el.getAttribute('data-citizen');
    const textExpert = el.getAttribute('data-especialista') || el.getAttribute('data-expert');
    if (isCitizen && textCitizen) {
      el.textContent = textCitizen;
    } else if (!isCitizen && textExpert) {
      el.textContent = textExpert;
    }
  });

  // Notificacion toast opcional
  if (notify) {
    window.showToast(
      isCitizen
        ? 'Modo Ciudadano activado: Explicaciones directas y dinero de bolsillo.'
        : 'Modo Especialista activado: Terminología técnica presupuestal y OCDS.',
      'info'
    );
  }

  // Despachar evento para sincronizacion de componentes
  window.dispatchEvent(new CustomEvent('cajamarca:lang-mode-change', { detail: { mode } }));
}

let activeTooltipPopover = null;
let activeTooltipTrigger = null;

export function initCivicTooltips() {
  // Delegacion de eventos para clics en botones de micro-tooltip
  document.addEventListener('click', (e) => {
    const btn = e.target.closest('.civic-tooltip-btn, .civic-tooltip-trigger');
    if (btn) {
      e.stopPropagation();
      e.preventDefault();
      toggleTooltipPopover(btn);
      return;
    }

    // Clic fuera cierra el tooltip si estuviera abierto
    if (activeTooltipPopover && !activeTooltipPopover.contains(e.target)) {
      closeActiveTooltip();
    }
  });

  // Soporte de teclado (Escape para cerrar, Enter/Espacio en botones)
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && activeTooltipPopover) {
      closeActiveTooltip();
    }
  });
}

function toggleTooltipPopover(triggerBtn) {
  if (activeTooltipTrigger === triggerBtn && activeTooltipPopover) {
    closeActiveTooltip();
    return;
  }

  const rawTerm = triggerBtn.dataset.term || triggerBtn.dataset.civicTerm || triggerBtn.getAttribute('data-term-id') || triggerBtn.getAttribute('data-civic-term') || '';
  const termId = String(rawTerm).trim().toLowerCase();
  let termData = termId ? CIVIC_DICTIONARY_MAP.get(termId) : null;
  if (!termData && termId) {
    termData = CIVIC_DICTIONARY.find(item => item.id.toLowerCase() === termId || item.id.replace(/-/g, '') === termId.replace(/-/g, '')) || null;
  }
  if (!termData) {
    openCivicDictionaryModal();
    return;
  }

  const popover = document.createElement('div');
  popover.id = 'civic-tooltip-bubble';
  popover.className = 'civic-tooltip-popover';
  popover.setAttribute('role', 'tooltip');
  popover.setAttribute('aria-live', 'polite');

  popover.innerHTML = `
    <div class="civic-tooltip-header">
      <div class="civic-tooltip-title">${termData.term}</div>
      <button type="button" class="civic-tooltip-close" aria-label="Cerrar explicación">
        <span class="material-symbols-outlined text-[15px]">close</span>
      </button>
    </div>
    <div class="font-semibold text-secondary text-xs mb-1">${termData.alias_ciudadano}</div>
    <p class="civic-card-def mb-2">${termData.definicion_simple}</p>
    <div class="civic-tooltip-pocket">
      <strong>En la vida diaria:</strong> ${termData.ejemplo_cotidiano}
    </div>
    <div class="flex items-center justify-between pt-1 border-t border-slate-border mt-2">
      <button type="button" class="civic-tooltip-more-btn" data-open-term="${termData.id}">
        <span>Ver en el Diccionario</span>
        <span class="material-symbols-outlined text-[13px]">open_in_new</span>
      </button>
      <span class="text-[10px] text-outline font-semibold uppercase">${termData.categoria}</span>
    </div>
  `;

  popover.querySelector('.civic-tooltip-close').addEventListener('click', (e) => {
    e.stopPropagation();
    closeActiveTooltip();
  });

  const moreBtn = popover.querySelector('.civic-tooltip-more-btn');
  if (moreBtn) {
    moreBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      closeActiveTooltip();
      openCivicDictionaryModal(termData.id);
    });
  }

  document.body.appendChild(popover);

  // Posicionamiento inteligente relativo al boton activador
  const rect = triggerBtn.getBoundingClientRect();
  const popoverWidth = 290;
  let left = rect.left + window.scrollX;
  let top = rect.bottom + window.scrollY + 6;

  // Ajuste si sobrepasa el borde derecho de la ventana
  if (left + popoverWidth > window.innerWidth - 16) {
    left = Math.max(16, window.innerWidth - popoverWidth - 16);
  }

  popover.style.left = `${left}px`;
  popover.style.top = `${top}px`;

  triggerBtn.setAttribute('aria-expanded', 'true');
  triggerBtn.setAttribute('aria-describedby', 'civic-tooltip-bubble');

  activeTooltipPopover = popover;
  activeTooltipTrigger = triggerBtn;
}

function closeActiveTooltip() {
  if (activeTooltipPopover) {
    activeTooltipPopover.remove();
    activeTooltipPopover = null;
  }
  if (activeTooltipTrigger) {
    activeTooltipTrigger.setAttribute('aria-expanded', 'false');
    activeTooltipTrigger.removeAttribute('aria-describedby');
    activeTooltipTrigger.focus();
    activeTooltipTrigger = null;
  }
}

let civicModalEl = null;
let lastFocusedBeforeModal = null;

export function initCivicDictionaryModal() {
  ensureCivicDictionaryModal();

  // Escuchar botones globales que abren el diccionario
  document.addEventListener('click', (e) => {
    const openBtn = e.target.closest('[data-action="open-civic-dict"], #open-civic-dict-btn, .btn-open-civic-dict');
    if (openBtn) {
      e.preventDefault();
      const termId = openBtn.dataset.termId || openBtn.dataset.dictTerm || null;
      openCivicDictionaryModal(termId);
    }
  });
}

function ensureCivicDictionaryModal() {
  if (document.getElementById('civic-dictionary-modal')) return;

  const modal = document.createElement('div');
  modal.id = 'civic-dictionary-modal';
  modal.className = 'civic-modal-backdrop hidden';
  modal.setAttribute('role', 'dialog');
  modal.setAttribute('aria-modal', 'true');
  modal.setAttribute('aria-labelledby', 'civic-dict-title');

  modal.innerHTML = `
    <div class="civic-modal-window" role="document">
      <div class="civic-modal-header">
        <div class="flex items-center gap-2">
          <span class="material-symbols-outlined text-secondary text-[22px]">menu_book</span>
          <div>
            <h2 id="civic-dict-title" class="font-serif font-bold text-base text-on-surface">Diccionario Cívico Popular</h2>
            <p class="text-xs text-on-surface-variant">24 términos públicos explicados en fácil para Cajamarca</p>
          </div>
        </div>
        <button id="civic-dict-close-btn" type="button" class="p-1.5 rounded hover:bg-surface-container text-on-surface-variant hover:text-on-surface cursor-pointer" aria-label="Cerrar diccionario cívico">
          <span class="material-symbols-outlined text-[20px]">close</span>
        </button>
      </div>

      <div class="civic-dict-search-wrapper">
        <div class="relative">
          <span class="material-symbols-outlined absolute left-2.5 top-2.5 text-on-surface-variant text-[18px]">search</span>
          <input type="search" id="civic-dict-search-input" class="civic-dict-input" placeholder="Buscar por término, sigla (PIM, OCDS, HHI) o pregunta cotidiana..." aria-label="Buscar en el diccionario cívico">
        </div>
        <div class="civic-dict-categories" id="civic-dict-category-pills">
          <button type="button" class="civic-cat-pill active" data-cat="all">Todos (24)</button>
          <button type="button" class="civic-cat-pill" data-cat="presupuesto">Presupuesto</button>
          <button type="button" class="civic-cat-pill" data-cat="contratos">Contratos</button>
          <button type="button" class="civic-cat-pill" data-cat="alertas">Alertas</button>
          <button type="button" class="civic-cat-pill" data-cat="instituciones">Instituciones</button>
        </div>
      </div>

      <div class="civic-dict-body" id="civic-dict-cards-container">
        <!-- Tarjetas dinámicas inyectadas -->
      </div>

      <div class="p-3 border-t border-slate-border bg-surface-container-low text-[11px] text-on-surface-variant flex items-center justify-between">
        <span>Lenguaje Claro Cajamarca Qhaway · Ley Nº 27806 de Transparencia</span>
        <span class="font-semibold text-secondary">Veeduría Comunitaria</span>
      </div>
    </div>
  `;

  document.body.appendChild(modal);

  // Cerrar al hacer clic en backdrop o botón cerrar
  modal.querySelector('#civic-dict-close-btn').addEventListener('click', closeCivicDictionaryModal);
  modal.addEventListener('click', (e) => {
    if (e.target === modal) closeCivicDictionaryModal();
  });

  // Filtrado reactivo en búsqueda
  const searchInput = modal.querySelector('#civic-dict-search-input');
  searchInput.addEventListener('input', () => {
    filterCivicDictionary();
  });

  // Filtros de categoría
  modal.querySelectorAll('#civic-dict-category-pills .civic-cat-pill').forEach(pill => {
    pill.addEventListener('click', () => {
      modal.querySelectorAll('#civic-dict-category-pills .civic-cat-pill').forEach(p => p.classList.remove('active'));
      pill.classList.add('active');
      filterCivicDictionary();
    });
  });

  // Trampa de foco y Escape
  modal.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      closeCivicDictionaryModal();
      return;
    }

    if (e.key === 'Tab') {
      const focusables = modal.querySelectorAll('button, input, [tabindex="0"], a');
      if (focusables.length === 0) return;
      const first = focusables[0];
      const last = focusables[focusables.length - 1];

      if (e.shiftKey && document.activeElement === first) {
        e.preventDefault();
        last.focus();
      } else if (!e.shiftKey && document.activeElement === last) {
        e.preventDefault();
        first.focus();
      }
    }
  });

  civicModalEl = modal;
  renderCivicDictionaryCards(CIVIC_DICTIONARY);
}

function renderCivicDictionaryCards(items) {
  const container = document.getElementById('civic-dict-cards-container');
  if (!container) return;

  if (items.length === 0) {
    container.innerHTML = `
      <div class="col-span-full py-8 text-center text-on-surface-variant">
        <span class="material-symbols-outlined text-[36px] text-outline mb-2">search_off</span>
        <p class="text-sm font-semibold">No se encontraron términos para tu búsqueda.</p>
        <p class="text-xs text-outline mt-1">Prueba con siglas como PIM, Devengado, SEACE, OCDS o HHI.</p>
      </div>
    `;
    return;
  }

  container.innerHTML = items.map(item => `
    <article class="civic-dict-card" id="civic-card-${item.id}" data-term-id="${item.id}" data-cat="${item.categoria}">
      <div class="civic-card-header">
        <div>
          <div class="civic-card-term">${item.term}</div>
          <span class="civic-card-alias">${item.alias_ciudadano}</span>
        </div>
        <span class="text-[10px] uppercase font-bold px-1.5 py-0.5 rounded bg-surface-container text-on-surface-variant">${item.categoria}</span>
      </div>
      <p class="civic-card-def">${item.definicion_simple}</p>
      <div class="civic-card-pocket">
        <strong>En la vida diaria:</strong> ${item.ejemplo_cotidiano}
      </div>
      <div class="text-[11px] text-secondary font-medium">
        ${item.pregunta_clave}
      </div>
      ${item.explore_url ? `
        <div class="pt-1 mt-auto border-t border-slate-border text-right">
          <a href="${item.explore_url}" class="text-[11px] font-semibold text-secondary hover:underline inline-flex items-center gap-1">
            <span>Ver datos en la web</span>
            <span class="material-symbols-outlined text-[13px]">arrow_forward</span>
          </a>
        </div>
      ` : ''}
    </article>
  `).join('');
}

function filterCivicDictionary() {
  const modal = document.getElementById('civic-dictionary-modal');
  if (!modal) return;
  const search = (modal.querySelector('#civic-dict-search-input').value || '').toLowerCase().trim();
  const activePill = modal.querySelector('#civic-dict-category-pills .civic-cat-pill.active');
  const cat = activePill ? activePill.dataset.cat : 'all';

  const filtered = CIVIC_DICTIONARY.filter(item => {
    const matchesCat = (cat === 'all') || (item.categoria === cat);
    if (!matchesCat) return false;
    if (!search) return true;

    const termText = (item.term || '').toLowerCase();
    const aliasText = (item.alias_ciudadano || '').toLowerCase();
    const defText = (item.definicion_simple || '').toLowerCase();
    const ejText = (item.ejemplo_cotidiano || '').toLowerCase();
    const qText = (item.pregunta_clave || '').toLowerCase();

    return termText.includes(search) ||
           aliasText.includes(search) ||
           defText.includes(search) ||
           ejText.includes(search) ||
           qText.includes(search);
  });

  renderCivicDictionaryCards(filtered);
}

export function openCivicDictionaryModal(termId = null) {
  ensureCivicDictionaryModal();
  const modal = document.getElementById('civic-dictionary-modal');
  if (!modal) return;

  lastFocusedBeforeModal = document.activeElement;
  modal.classList.remove('hidden');

  const searchInput = modal.querySelector('#civic-dict-search-input');
  if (termId) {
    const item = CIVIC_DICTIONARY_MAP.get(termId);
    if (item && searchInput) {
      searchInput.value = item.id;
      filterCivicDictionary();
      const card = document.getElementById(`civic-card-${item.id}`);
      if (card) {
        card.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        card.classList.add('ring-2', 'ring-secondary');
        setTimeout(() => card.classList.remove('ring-2', 'ring-secondary'), 2500);
      }
    }
  } else {
    if (searchInput) {
      searchInput.value = '';
      filterCivicDictionary();
    }
  }

  if (searchInput) searchInput.focus();
}

export function closeCivicDictionaryModal() {
  const modal = document.getElementById('civic-dictionary-modal');
  if (!modal) return;
  modal.classList.add('hidden');
  if (lastFocusedBeforeModal && typeof lastFocusedBeforeModal.focus === 'function') {
    lastFocusedBeforeModal.focus();
    lastFocusedBeforeModal = null;
  }
}

/**
 * Hidratacion integral de KPIs y Vistas Dinamicas
 */
async function hydrateAllViews() {
  try {
    const kpis = await dataEngine.getMacroKPIs();
    hydrateGlobalKPIElements(kpis);

    // 1. Vista index.html
    if (document.getElementById('explorador-contrataciones-sec') || document.getElementById('territorial-cards-grid')) {
      await hydrateIndexPage(kpis);
    }

    // 2. Vista entidades.html
    if (document.getElementById('cards-container') || document.getElementById('table-container')) {
      await hydrateEntidadesPage(kpis);
    }

    // 3. Vista alertas.html
    if (document.getElementById('alert-search-input') || document.querySelector('.alert-card')) {
      await hydrateAlertasPage(kpis);
    }
  } catch (err) {
    console.warn('Error durante hidratacion dinamica de datos:', err);
  }
}

/**
 * Actualiza reactivamente el velocimetro SVG con calculo geometrico y animacion fluida
 * @param {number|string} rate - Porcentaje de ejecucion presupuestal
 */
export function updateSpeedometer(rate) {
  const arc = document.getElementById('speedo-meter-arc');
  const text = document.getElementById('speedo-text-pct');
  const dot = document.getElementById('speedo-indicator-dot');
  const pct = Math.max(0, Math.min(100, Number(rate) || 0));

  if (text) text.textContent = `${pct.toFixed(1)}%`;

  // Longitud de semicirculo para R=75: pi * 75 = 235.62
  const totalLength = 235.62;
  const offset = totalLength * (1 - pct / 100);

  if (arc) {
    arc.style.strokeDashoffset = `${offset.toFixed(2)}`;
    arc.style.transition = 'stroke-dashoffset 0.8s cubic-bezier(0.4, 0, 0.2, 1), stroke 0.5s ease';
    arc.classList.remove('text-alert-rose', 'text-alert-amber', 'text-secondary', 'text-civic-emerald');
    if (pct >= 45) {
      arc.classList.add('text-secondary');
    } else if (pct >= 30) {
      arc.classList.add('text-alert-amber');
    } else {
      arc.classList.add('text-alert-rose');
    }
  }

  if (dot) {
    // Calculo trigonometrico exacto:
    // Arco inicia en x=25 (180 deg) y va a x=175 (0 deg)
    const angleRad = Math.PI * (pct / 100);
    const cx = (100 - 75 * Math.cos(angleRad)).toFixed(2);
    const cy = (100 - 75 * Math.sin(angleRad)).toFixed(2);
    dot.setAttribute('cx', cx);
    dot.setAttribute('cy', cy);
    const colorClass = pct >= 45 ? 'fill-secondary' : pct >= 30 ? 'fill-alert-amber' : 'fill-alert-rose';
    dot.setAttribute('class', `${colorClass} stroke-surface stroke-2 transition-all duration-700`);
  }
}

export function hydrateGlobalKPIElements(kpis) {
  // Atributos genericos data-kpi
  document.querySelectorAll('[data-kpi="pim-total"]').forEach(el => el.textContent = dataEngine.formatBudgetAmount(kpis.totalPim));
  document.querySelectorAll('[data-kpi="devengado-total"]').forEach(el => el.textContent = dataEngine.formatBudgetAmount(kpis.totalDevengado));
  document.querySelectorAll('[data-kpi="execution-rate"]').forEach(el => el.textContent = `${kpis.executionRate}%`);
  document.querySelectorAll('[data-kpi="procurements-total"]').forEach(el => el.textContent = `${kpis.totalProcurements.toLocaleString('es-PE')} Procesos`);
  document.querySelectorAll('[data-kpi="alerts-total"]').forEach(el => el.textContent = `${kpis.totalAlerts}`);
  document.querySelectorAll('[data-kpi="flags-total"]').forEach(el => el.textContent = `${kpis.totalRedFlags}`);
  document.querySelectorAll('[data-kpi="entities-total"]').forEach(el => el.textContent = `${kpis.entitiesCount}`);

  // IDs conocidos de index.html
  const heroPim = document.getElementById('hero-total-pim');
  if (heroPim) heroPim.textContent = dataEngine.formatBudgetAmount(kpis.totalPim);

  const heroAlertsBtn = document.getElementById('hero-alerts-btn');
  if (heroAlertsBtn) heroAlertsBtn.textContent = `Ver Alertas Activas (${kpis.totalAlerts} Publicadas)`;

  const heroDevPct = document.getElementById('hero-devengado-pct');
  if (heroDevPct) heroDevPct.textContent = `${kpis.executionRate}%`;

  const heroDevMonto = document.getElementById('hero-devengado-monto');
  if (heroDevMonto) heroDevMonto.textContent = dataEngine.formatBudgetAmount(kpis.totalDevengado);

  const kpiPim = document.getElementById('kpi-pim-total');
  if (kpiPim) kpiPim.textContent = dataEngine.formatBudgetAmount(kpis.totalPim);

  const kpiDevPct = document.getElementById('kpi-devengado-pct');
  if (kpiDevPct) kpiDevPct.textContent = `${kpis.executionRate}%`;

  const kpiDevBar = document.getElementById('kpi-devengado-bar');
  if (kpiDevBar) {
    kpiDevBar.style.width = `${Math.min(100, kpis.executionRate)}%`;
    kpiDevBar.style.transition = 'width 0.8s ease-out';
    kpiDevBar.className = kpis.executionRate >= 45
      ? 'bg-secondary h-full rounded-full transition-all duration-700 ease-out'
      : kpis.executionRate >= 30
      ? 'bg-alert-amber h-full rounded-full transition-all duration-700 ease-out'
      : 'bg-alert-rose h-full rounded-full transition-all duration-700 ease-out';
  }

  // Actualizar velocimetro SVG con semantica y animacion
  updateSpeedometer(kpis.executionRate);

  const kpiProcTotal = document.getElementById('kpi-procurements-total');
  if (kpiProcTotal) kpiProcTotal.textContent = `${kpis.totalProcurements.toLocaleString('es-PE')} Procesos`;

  const kpiProcSub = document.getElementById('kpi-procurements-sub');
  if (kpiProcSub) kpiProcSub.innerHTML = `${dataEngine.formatMillions(kpis.totalAwarded)} adjudicados en SEACE OCDS`;

  const kpiAlertsTotal = document.getElementById('kpi-alerts-total');
  if (kpiAlertsTotal) kpiAlertsTotal.textContent = `${kpis.totalAlerts} Alertas Publicadas`;

  const speedoRisk = document.getElementById('speedo-risk-budget');
  if (speedoRisk) {
    const riskAmount = Math.max(0, kpis.totalPim - kpis.totalDevengado);
    speedoRisk.textContent = dataEngine.formatMillions(riskAmount);
  }

  const speedoProv = document.getElementById('speedo-alert-provinces');
  if (speedoProv) {
    speedoProv.textContent = `${kpis.totalAlerts} de 13 Provincias`;
  }

  // IDs conocidos de entidades.html
  const entPim = document.getElementById('entidades-kpi-pim');
  if (entPim) entPim.textContent = dataEngine.formatBudgetAmount(kpis.totalPim);

  const entDev = document.getElementById('entidades-kpi-devengado');
  if (entDev) entDev.textContent = dataEngine.formatBudgetAmount(kpis.totalDevengado);

  const entExec = document.getElementById('entidades-kpi-ejecucion');
  if (entExec) entExec.textContent = `${kpis.executionRate}%`;

  const entProc = document.getElementById('entidades-kpi-contratos');
  if (entProc) entProc.textContent = `${kpis.totalProcurements.toLocaleString('es-PE')}`;

  const entBar = document.getElementById('entidades-kpi-bar');
  if (entBar) {
    entBar.style.width = `${Math.min(100, kpis.executionRate)}%`;
    entBar.className = kpis.executionRate >= 45
      ? 'bg-secondary h-full rounded-full transition-all duration-700 ease-out'
      : kpis.executionRate >= 30
      ? 'bg-alert-amber h-full rounded-full transition-all duration-700 ease-out'
      : 'bg-alert-rose h-full rounded-full transition-all duration-700 ease-out';
  }

  const entAlertasSub = document.getElementById('entidades-kpi-alertas-sub');
  if (entAlertasSub) {
    entAlertasSub.innerHTML = `
      <span>Alertas de riesgo</span>
      <span class="text-secondary font-semibold flex items-center gap-0.5">
        <span class="w-1.5 h-1.5 rounded-full bg-secondary"></span> ${kpis.totalAlerts} Alertas · ${kpis.totalRedFlags} Banderas
      </span>
    `;
  }

  // Equivalencia cotidiana y dinero de bolsillo pedagogico (Pilar 3)
  const pocket = formatCitizenPocketMoney(kpis.executionRate);
  document.querySelectorAll('[data-pocket="execution-rate"]').forEach(el => {
    el.textContent = pocket.badge;
  });

  const heroPocket = document.getElementById('hero-pocket-badge');
  if (heroPocket) {
    heroPocket.textContent = pocket.badge;
    heroPocket.className = `civic-pocket-badge ${pocket.statusClass}`;
  }

  const speedoPocket = document.getElementById('speedo-pocket-badge');
  if (speedoPocket) {
    speedoPocket.innerHTML = `
      <span class="civic-status-badge ${pocket.statusClass}">
        <span class="material-symbols-outlined text-[14px]">${pocket.statusIcon}</span>
        <span>${pocket.badge} · ${pocket.statusLabel}</span>
      </span>
    `;
  }

  const kpiDevPocket = document.getElementById('kpi-devengado-pocket');
  if (kpiDevPocket) {
    kpiDevPocket.textContent = pocket.badge;
  }

  const kpiDevNarrative = document.getElementById('kpi-devengado-narrative');
  if (kpiDevNarrative) {
    kpiDevNarrative.textContent = pocket.narrative;
  }
}

/**
 * Hidratacion de index.html: Radar territorial y Explorador en vivo
 */
async function hydrateIndexPage(kpis) {
  const [entities, procurements, budgets] = await Promise.all([
    dataEngine.getEntities(),
    dataEngine.getProcurements(),
    dataEngine.getBudgetRecords()
  ]);

  const entitiesMap = new Map();
  entities.forEach(e => entitiesMap.set(e.entity_id, e));

  // Actualizar Foco departamental / Speedometer reactivo
  updateSpeedometer(kpis.executionRate);

  // Actualizar Radar territorial con datos reales y animacion de barras
  const radarCards = document.querySelectorAll('.radar-card');
  for (const card of radarCards) {
    const eid = card.dataset.entityId;
    if (!eid) continue;
    const stats = await dataEngine.getEntityBudgetStats(eid);
    const pimEl = card.querySelector('[data-radar-pim]');
    const rateEl = card.querySelector('[data-radar-rate]');
    const barEl = card.querySelector('[data-radar-bar]');
    if (pimEl) pimEl.textContent = dataEngine.formatMillions(stats.pim);
    if (rateEl) {
      rateEl.textContent = `${stats.rate}%`;
      rateEl.className = stats.rate >= 45
        ? 'font-semibold font-mono text-secondary'
        : stats.rate >= 30
        ? 'font-semibold font-mono text-alert-amber'
        : 'font-semibold font-mono text-alert-rose';
    }
    if (barEl) {
      barEl.style.width = `${Math.min(100, stats.rate)}%`;
      barEl.style.transition = 'width 0.8s ease-out';
      barEl.className = stats.rate >= 45
        ? 'bg-secondary h-full rounded-full transition-all duration-700 ease-out'
        : stats.rate >= 30
        ? 'bg-alert-amber h-full rounded-full transition-all duration-700 ease-out'
        : 'bg-alert-rose h-full rounded-full transition-all duration-700 ease-out';
    }
  }

  // Explorador de Contrataciones OCDS en index.html
  const tbody = document.getElementById('index-procurements-tbody');
  const counterEl = document.getElementById('index-procurement-counter');
  const searchInput = document.getElementById('index-procurement-search');
  const prevBtn = document.getElementById('index-page-prev');
  const nextBtn = document.getElementById('index-page-next');
  const pageInfo = document.getElementById('index-page-info');
  const yearBtns = document.querySelectorAll('.index-year-btn');
  const badgeTotal = document.getElementById('index-total-procurements-badge');

  if (badgeTotal) badgeTotal.textContent = procurements.length;

  if (tbody && counterEl) {
    let currentYear = 'all';
    let currentSearch = '';
    let currentPage = 1;
    const pageSize = 10;

    function getFilteredList() {
      return procurements.filter(p => {
        const title = (p.title || '').toLowerCase();
        const ocid = (p.ocid || '').toLowerCase();
        const supName = (p.supplier_name || '').toLowerCase();
        const supRuc = String(p.supplier_ruc || '');
        const ent = entitiesMap.get(p.entity_id);
        const entName = ent ? ent.official_name.toLowerCase() : '';

        const matchesSearch = !currentSearch ||
          title.includes(currentSearch) ||
          ocid.includes(currentSearch) ||
          supName.includes(currentSearch) ||
          supRuc.includes(currentSearch) ||
          entName.includes(currentSearch);

        let matchesYear = true;
        if (currentYear !== 'all') {
          const dateStr = p.retrieved_at || p.date || (p.raw_payload && p.raw_payload.date) || '';
          matchesYear = dateStr.includes(currentYear) || ocid.includes(currentYear);
        }

        return matchesSearch && matchesYear;
      });
    }

    function renderTable() {
      const filtered = getFilteredList();
      const totalPages = Math.max(1, Math.ceil(filtered.length / pageSize));
      currentPage = Math.min(currentPage, totalPages);

      counterEl.textContent = `Mostrando ${filtered.length} de ${procurements.length} contrataciones verificadas OCDS`;
      if (pageInfo) pageInfo.textContent = `Pagina ${currentPage} de ${totalPages}`;
      if (prevBtn) prevBtn.disabled = currentPage <= 1;
      if (nextBtn) nextBtn.disabled = currentPage >= totalPages;

      if (filtered.length === 0) {
        tbody.innerHTML = `
          <tr>
            <td colspan="5" class="py-8 text-center text-outline">
              No se encontraron contrataciones con los filtros seleccionados.
            </td>
          </tr>
        `;
        return;
      }

      const startIdx = (currentPage - 1) * pageSize;
      const pageSlice = filtered.slice(startIdx, startIdx + pageSize);

      tbody.innerHTML = pageSlice.map(p => {
        const ent = entitiesMap.get(p.entity_id);
        const entName = ent ? ent.official_name : 'Entidad Cajamarca';
        const amount = p.awarded_amount ? dataEngine.formatCurrency(p.awarded_amount) : 'Sin monto fijado';
        const supName = p.supplier_name || 'Sin proveedor adjudicado';
        const supRuc = p.supplier_ruc || '';
        const isRuc = /^[12]\d{10}$/.test(supRuc);

        return `
          <tr class="hover:bg-surface-container-low/70 transition-colors">
            <td class="py-3 px-4">
              <div class="font-mono text-[11px] text-secondary font-semibold">${p.ocid || p.procurement_id}</div>
              <div class="font-medium text-on-surface line-clamp-1 max-w-xs" title="${p.title || ''}">${p.title || 'Proceso OCDS'}</div>
            </td>
            <td class="py-3 px-4">
              <span class="text-on-surface line-clamp-1 max-w-xs font-medium" title="${entName}">${entName}</span>
            </td>
            <td class="py-3 px-4">
              <div class="text-on-surface line-clamp-1 max-w-xs font-medium">${supName}</div>
              <div class="flex items-center gap-1.5 mt-0.5">
                ${supRuc ? `<span class="font-mono text-[10px] text-outline">${supRuc}</span>` : ''}
                ${isRuc ? `<span class="badge-sunat-activo">ACTIVO</span><span class="badge-sunat-habido">HABIDO</span>` : ''}
              </div>
            </td>
            <td class="py-3 px-4 text-right font-mono font-semibold text-on-surface whitespace-nowrap">
              ${amount}
            </td>
            <td class="py-3 px-4 text-center whitespace-nowrap">
              <button type="button" class="btn-inspect-ocds px-2.5 py-1 rounded bg-surface border border-slate-border hover:bg-surface-container text-secondary text-xs font-semibold inline-flex items-center gap-1 cursor-pointer transition-colors" data-ocid="${p.ocid}">
                <span class="material-symbols-outlined text-[15px]">data_object</span>
                <span>JSON OCDS</span>
              </button>
            </td>
          </tr>
        `;
      }).join('');

      // Adjuntar eventos a botones de JSON
      tbody.querySelectorAll('.btn-inspect-ocds').forEach(btn => {
        btn.addEventListener('click', () => {
          const ocid = btn.dataset.ocid;
          const proc = procurements.find(p => p.ocid === ocid);
          if (proc) {
            openRawPayloadDrawer(proc.raw_payload || proc, `Contratacion SEACE OCDS: ${proc.ocid}`);
          }
        });
      });
    }

    if (searchInput) {
      searchInput.addEventListener('input', (e) => {
        currentSearch = e.target.value.toLowerCase().trim();
        currentPage = 1;
        renderTable();
      });
    }

    yearBtns.forEach(btn => {
      btn.addEventListener('click', () => {
        yearBtns.forEach(b => {
          b.className = 'index-year-btn px-3 py-1.5 rounded bg-surface border border-slate-border text-on-surface-variant hover:text-on-surface whitespace-nowrap cursor-pointer transition-colors';
        });
        btn.className = 'index-year-btn px-3 py-1.5 rounded bg-primary text-on-primary whitespace-nowrap cursor-pointer transition-colors';
        currentYear = btn.dataset.year;
        currentPage = 1;
        renderTable();
      });
    });

    if (prevBtn) {
      prevBtn.addEventListener('click', () => {
        if (currentPage > 1) {
          currentPage--;
          renderTable();
        }
      });
    }

    if (nextBtn) {
      nextBtn.addEventListener('click', () => {
        const filtered = getFilteredList();
        const totalPages = Math.ceil(filtered.length / pageSize);
        if (currentPage < totalPages) {
          currentPage++;
          renderTable();
        }
      });
    }

    renderTable();
  }
}

function renderEntityCard(ent, stats, flagsCount, procsCount, year) {
  const isGore = ent.entity_level === 'regional';
  const prov = ent.province || '';
  const provUpper = prov.toUpperCase();
  const zone = isGore ? 'gore' : ['JAEN', 'SAN IGNACIO', 'CUTERVO'].includes(provUpper) ? 'norte' : 'centrosur';
  const levelText = isGore ? 'Sede Regional · Nivel GORE' : `Provincia de ${prov} · Local`;
  const nameShort = isGore ? 'Gobierno Regional de Cajamarca' : `M. P. de ${prov}`;
  const rate = stats.rate;
  const color = rate >= 35 ? 'secondary' : rate >= 30 ? 'alert-amber' : 'alert-rose';
  const statusLabel = rate >= 35 ? 'Avance (>=35%)' : rate >= 30 ? 'Moderado (30-35%)' : 'Subejecucion (<30%)';
  const flagBadgeClass = flagsCount > 0 ? (flagsCount >= 4 ? 'bg-error-container text-on-error-container' : 'bg-alert-amber/10 text-alert-amber') : 'bg-surface-container text-on-surface-variant';
  const flagText = flagsCount > 0 ? `${flagsCount} Banderas` : 'Sin Banderas';
  const yearLabel = year && year !== 'all' ? year : 'Consolidado';
  const observation = rate >= 35
    ? 'Avance del gasto sobre el presupuesto autorizado del ejercicio.'
    : rate >= 30
    ? 'Avance moderado de gasto con seguimiento en devengados de obras.'
    : 'Devengado inferior al 30% del presupuesto autorizado del ejercicio.';

  return `
    <article class="entity-card bg-surface-container-lowest border border-slate-border rounded flex flex-col justify-between hover:shadow-md transition-shadow"
             data-alerts="${flagsCount}"
             data-entity-id="${ent.entity_id}"
             data-exec="${rate}"
             data-name="${ent.official_name}"
             data-pim="${stats.pim}"
             data-ruc="${ent.ruc}"
             data-zone="${zone}">
      <div class="p-6 space-y-4">
        <div class="flex items-start justify-between gap-2 border-b border-slate-border pb-2">
          <div>
            <span class="px-2 py-0.5 rounded bg-surface-container text-on-surface-variant font-caption text-caption uppercase tracking-wider font-semibold">
              ${levelText}
            </span>
            <h2 class="font-headline-sm text-headline-sm text-on-surface font-semibold mt-1 leading-snug">
              ${nameShort}
            </h2>
          </div>
          <span class="inline-flex items-center gap-1 px-2 py-0.5 rounded ${flagBadgeClass} font-label-sm text-label-sm shrink-0 font-semibold" title="${flagsCount} senales de alerta">
            <span class="material-symbols-outlined text-[14px]">flag</span> ${flagText}
          </span>
        </div>
        <div class="flex items-center justify-between text-body-sm font-body-sm text-on-surface-variant">
          <span>RUC: <strong class="text-on-surface font-mono">${ent.ruc}</strong></span>
          <button class="inline-flex items-center gap-1 text-secondary hover:text-on-surface font-label-sm text-label-sm cursor-pointer" onclick="copyRuc('${ent.ruc}', this)">
            <span class="material-symbols-outlined text-[15px]">content_copy</span> Copiar
          </button>
        </div>
        <div class="grid grid-cols-2 gap-2 bg-slate-surface p-3 rounded border border-slate-border">
          <div>
            <span class="block text-caption font-caption text-on-surface-variant uppercase">PIM ${yearLabel}</span>
            <span data-card-pim class="font-headline-sm text-headline-sm text-on-surface font-semibold">${dataEngine.formatBudgetAmount(stats.pim)}</span>
          </div>
          <div>
            <span class="block text-caption font-caption text-on-surface-variant uppercase">Devengado (% / S/.)</span>
            <span data-card-rate class="font-headline-sm text-headline-sm text-${color} font-semibold">${rate}%</span>
            <span data-card-dev class="block font-caption text-caption text-on-surface-variant">${dataEngine.formatBudgetAmount(stats.devengado)}</span>
          </div>
        </div>
        <div>
          <div class="flex justify-between items-center text-caption font-caption mb-1">
            <span class="text-on-surface-variant">Nivel de ejecucion presupuestal</span>
            <span class="text-${color} font-semibold">${statusLabel}</span>
          </div>
          <div class="w-full bg-surface-container rounded-full h-2 overflow-hidden">
            <div data-card-bar class="bg-${color} h-full rounded-full transition-all duration-700 ease-out" style="width: ${Math.min(100, rate)}%"></div>
          </div>
        </div>
        <div class="space-y-1 text-body-sm font-body-sm pt-1">
          <div class="text-caption font-caption text-on-surface-variant bg-surface-container-low p-2 rounded border border-slate-border">
            <strong class="text-on-surface font-semibold">Diagnostico:</strong> ${observation}
          </div>
        </div>
        <div class="border-t border-slate-border pt-2 flex items-center justify-between text-body-sm font-body-sm text-on-surface-variant">
          <span>SEACE OCDS: <strong class="text-on-surface">${procsCount} Contratos</strong></span>
          <span class="text-secondary font-medium font-mono text-caption">RUC ${ent.ruc}</span>
        </div>
      </div>
      <div class="px-6 py-3 bg-surface-container-low border-t border-slate-border flex items-center justify-between">
        <span class="text-caption font-caption text-on-surface-variant font-mono">ID: ${ent.entity_id.slice(0, 8)}</span>
        <a class="inline-flex items-center gap-1 font-label-md text-label-md text-secondary hover:underline font-semibold" href="/entidad?id=${ent.entity_id}">
          Ver Ficha de Auditoria <span class="material-symbols-outlined text-[16px]">arrow_forward</span>
        </a>
      </div>
    </article>
  `;
}

function renderEntityTableRow(ent, stats, flagsCount, procsCount, year) {
  const isGore = ent.entity_level === 'regional';
  const prov = ent.province || '';
  const levelText = isGore ? 'Nivel Regional (GORE)' : `Provincia de ${prov}`;
  const rate = stats.rate;
  const color = rate >= 35 ? 'bg-secondary text-white' : rate >= 30 ? 'bg-alert-amber/20 text-alert-amber' : 'bg-error-container text-on-error-container';

  return `
    <tr class="hover:bg-slate-surface">
      <td class="px-4 py-3 font-semibold text-on-surface">${ent.official_name}<br/><span class="font-normal font-mono text-caption text-on-surface-variant">RUC: ${ent.ruc}</span></td>
      <td class="px-4 py-3 text-on-surface-variant">${levelText}</td>
      <td class="px-4 py-3 text-right font-medium text-on-surface">${dataEngine.formatBudgetAmount(stats.pim)}</td>
      <td class="px-4 py-3 text-right text-on-surface font-medium">${dataEngine.formatBudgetAmount(stats.devengado)}</td>
      <td class="px-4 py-3 text-center"><span class="px-2 py-0.5 rounded ${color} font-semibold">${rate}%</span></td>
      <td class="px-4 py-3 text-center font-mono">${procsCount}</td>
      <td class="px-4 py-3 text-center"><span class="${flagsCount > 0 ? 'text-alert-rose font-semibold' : 'text-on-surface-variant'}">${flagsCount > 0 ? `${flagsCount} Banderas` : '0'}</span></td>
      <td class="px-4 py-3 text-right"><a class="text-secondary hover:underline font-label-sm font-semibold" href="/entidad?id=${ent.entity_id}">Ver Ficha</a></td>
    </tr>
  `;
}

function renderRankingObras(rankingItems) {
  const container = document.getElementById('ranking-obras-container');
  if (!container) return;

  container.innerHTML = rankingItems.slice(0, 7).map((item, idx) => {
    const bgClass = item.rate >= 35 ? 'bg-secondary' : item.rate >= 30 ? 'bg-alert-amber' : 'bg-alert-rose';
    const textClass = item.rate >= 35 ? 'text-secondary' : item.rate >= 30 ? 'text-alert-amber' : 'text-alert-rose';
    const name = item.isGore ? 'Gobierno Regional Cajamarca (Sede Central)' : `M. P. ${item.province || item.name}`;

    return `
      <div>
        <div class="flex justify-between font-label-sm text-label-sm mb-1">
          <span class="text-on-surface">${idx + 1}. ${name}</span>
          <span class="font-semibold ${textClass}">${item.rate}% de avance</span>
        </div>
        <div class="w-full bg-surface-container rounded-full h-2.5 overflow-hidden">
          <div class="${bgClass} h-full rounded-full transition-all duration-700 ease-out" style="width: ${Math.min(100, item.rate)}%"></div>
        </div>
      </div>
    `;
  }).join('');

  const brechaEl = document.getElementById('ranking-brecha-text');
  if (brechaEl && rankingItems.length > 0) {
    const gap = (rankingItems[0].rate - rankingItems[rankingItems.length - 1].rate).toFixed(1);
    brechaEl.textContent = `Brecha de ejecucion: ${gap} puntos porcentuales entre 1° y ${rankingItems.length}°`;
  }
}

/**
 * Hidratacion de entidades.html con filtro de ano y datos en vivo
 */
async function hydrateEntidadesPage(kpis) {
  const [entities, budgets, procurements] = await Promise.all([
    dataEngine.getEntities(),
    dataEngine.getBudgetRecords(),
    dataEngine.getProcurements()
  ]);

  // Actualizar Donut Chart SVG de fuentes de financiamiento
  const funding = dataEngine.getFundingComposition();
  const sliceCanon = document.getElementById('donut-slice-canon');
  const sliceRo = document.getElementById('donut-slice-ro');
  const sliceFoncomun = document.getElementById('donut-slice-foncomun');
  const donutText = document.getElementById('donut-pct-text');
  if (funding && sliceCanon && sliceRo && sliceFoncomun) {
    sliceCanon.style.transition = 'stroke-dasharray 0.8s ease-out, stroke-dashoffset 0.8s ease-out';
    sliceRo.style.transition = 'stroke-dasharray 0.8s ease-out, stroke-dashoffset 0.8s ease-out';
    sliceFoncomun.style.transition = 'stroke-dasharray 0.8s ease-out, stroke-dashoffset 0.8s ease-out';
    sliceCanon.setAttribute('stroke-dasharray', `${funding.canon.pct}, 100`);
    sliceRo.setAttribute('stroke-dasharray', `${funding.recursosOrdinarios.pct}, 100`);
    sliceRo.setAttribute('stroke-dashoffset', `-${funding.canon.pct}`);
    sliceFoncomun.setAttribute('stroke-dasharray', `${funding.foncomun.pct}, 100`);
    sliceFoncomun.setAttribute('stroke-dashoffset', `-${(funding.canon.pct + funding.recursosOrdinarios.pct).toFixed(1)}`);
  }
  if (donutText) donutText.textContent = funding ? `${Math.round(funding.canon.pct)}%` : 'Sin datos';

  async function updateEntitiesView(year = null) {
    const updatedKpis = await dataEngine.getMacroKPIs(year);
    hydrateGlobalKPIElements(updatedKpis);

    const cardsContainer = document.getElementById('cards-container');
    const tableBody = document.querySelector('#table-container tbody');
    const cardsHtml = [];
    const tableRowsHtml = [];
    const rankingItems = [];
    const displayedYear = year || budgets[0]?.fiscal_year;

    for (const ent of entities) {
      const stats = await dataEngine.getEntityBudgetStats(ent.entity_id, year);
      const procs = await dataEngine.getProcurements(ent.entity_id, year);
      const flags = await dataEngine.getRedFlags(ent.entity_id);

      cardsHtml.push(renderEntityCard(ent, stats, flags.length, procs.length, displayedYear));
      tableRowsHtml.push(renderEntityTableRow(ent, stats, flags.length, procs.length, displayedYear));
      rankingItems.push({
        id: ent.entity_id,
        name: ent.official_name,
        province: ent.province,
        isGore: ent.entity_level === 'regional',
        rate: stats.rate
      });
    }

    if (cardsContainer) cardsContainer.innerHTML = cardsHtml.join('');
    if (tableBody) tableBody.innerHTML = tableRowsHtml.join('');

    // Ordenar ranking por tasa descendente
    rankingItems.sort((a, b) => b.rate - a.rate);
    renderRankingObras(rankingItems);

    const resultsCount = document.getElementById('results-count');
    if (resultsCount) {
      resultsCount.textContent = `Mostrando ${entities.length} de ${entities.length} entidades fiscalizadas en Fase 1`;
    }

    if (typeof window.applyFiltersAndSearch === 'function') {
      window.applyFiltersAndSearch();
    }
  }

  // Render inicial
  await updateEntitiesView();
  document.addEventListener('qh-budget-view-change', () => updateEntitiesView(dataEngine.budgetView.year));

  const yearFilterContainer = document.getElementById('entidades-year-filter');
  if (yearFilterContainer) {
    const yearBtns = yearFilterContainer.querySelectorAll('.year-pill');
    yearBtns.forEach(btn => {
      btn.addEventListener('click', async () => {
        yearBtns.forEach(b => {
          b.className = 'year-pill px-3 py-1 rounded bg-surface text-on-surface-variant hover:text-on-surface border border-slate-border whitespace-nowrap cursor-pointer transition-colors';
        });
        btn.className = 'year-pill px-3 py-1 rounded bg-on-surface text-on-primary whitespace-nowrap cursor-pointer transition-colors';
        const year = btn.dataset.year;
        if (year === 'all' || year === 'Todos') {
          document.dispatchEvent(new CustomEvent('qh-budget-compare-request'));
          return;
        }
        dataEngine.budgetView.year = Number(year);
        await updateEntitiesView(year);
        document.dispatchEvent(new CustomEvent('qh-budget-controls-change'));
      });
    });
  }
}

/**
 * Hidratacion de alertas.html con explicabilidad algoritmica integral (Art. 14 y Art. 15)
 */
async function hydrateAlertasPage(kpis) {
  const alerts = await dataEngine.getAlerts();
  const flags = await dataEngine.getRedFlags();
  const entities = await dataEngine.getEntities();
  const stats = await dataEngine.getPublishedAlertsStats();

  const entitiesMap = new Map();
  entities.forEach(e => entitiesMap.set(e.entity_id, e));

  const flagsMap = new Map();
  flags.forEach(f => flagsMap.set(f.red_flag_id, f));

  // Actualizar top KPI cards de alertas.html con valores reales
  const alTotal = document.getElementById('alertas-kpi-total');
  if (alTotal) alTotal.textContent = `${stats.total}`;

  const alSevSub = document.getElementById('alertas-kpi-severity-sub');
  if (alSevSub) alSevSub.innerHTML = `<span class="text-alert-rose font-semibold">${stats.critCount} Criticas</span> · ${stats.highCount} Altas · ${stats.medCount} Medias`;

  const alMonto = document.getElementById('alertas-kpi-monto');
  if (alMonto) alMonto.textContent = dataEngine.formatMillions(stats.flaggedAmount);

  const alMontoSub = document.getElementById('alertas-kpi-monto-sub');
  if (alMontoSub) alMontoSub.textContent = 'En expedientes auditados con dictamen activo';

  const alEnt = document.getElementById('alertas-kpi-entidades');
  if (alEnt) alEnt.textContent = `${stats.distinctEntitiesCount} / ${entities.length}`;

  const alEntSub = document.getElementById('alertas-kpi-entidades-sub');
  if (alEntSub) alEntSub.textContent = 'Pliegos con alertas formalmente validadas';

  // Actualizar botones de severidad
  const btnAll = document.getElementById('alert-btn-all');
  if (btnAll) btnAll.textContent = `Todas (${stats.total})`;

  const btnCrit = document.getElementById('alert-btn-critica');
  if (btnCrit) btnCrit.innerHTML = `<span class="w-2 h-2 rounded-full bg-alert-rose"></span> Critica (${stats.critCount})`;

  const btnAlta = document.getElementById('alert-btn-alta');
  if (btnAlta) btnAlta.innerHTML = `<span class="w-2 h-2 rounded-full bg-alert-amber"></span> Alta (${stats.highCount})`;

  const btnMedia = document.getElementById('alert-btn-media');
  if (btnMedia) btnMedia.innerHTML = `<span class="w-2 h-2 rounded-full bg-civic-teal"></span> Media (${stats.medCount})`;

  const container = document.getElementById('alertas-dinamicas-container');
  if (container && alerts.length > 0) {
    container.innerHTML = alerts.map(a => {
      const ent = entitiesMap.get(a.entity_id);
      const entName = ent ? ent.official_name : 'Entidad Fiscalizada';
      const flagId = (a.red_flag_ids && a.red_flag_ids[0]) || '';
      const flag = flagsMap.get(flagId) || {};

      const code = flag.indicator_code || 'riesgo-ocds';
      const isCrit = code === 'single-bidder' || code === 'mef-underspending' || code === 'recurrent-direct-award';
      const severity = isCrit ? 'critica' : 'alta';
      const badgeClass = isCrit
        ? 'bg-error-container text-on-error-container'
        : 'bg-surface-container-highest text-alert-amber';
      const badgeIcon = isCrit ? 'error' : 'warning';
      const badgeLabel = isCrit ? 'SEVERIDAD CRITICA' : 'SEVERIDAD ALTA';

      const INDICATOR_LABELS = {
        'short-tender-window': 'Ventana anormalmente corta de licitacion publica',
        'single-bidder': 'Licitacion publica adjudicada a postor unico',
        'execution-overrun': 'Sobrecosto y desvio del presupuesto modificado',
        'contract-concentration': 'Concentracion contractual en un solo proveedor',
        'direct-award-threshold': 'Adjudicacion directa en el umbral limite legal',
        'direct-administration-equipment-rent': 'Alquiler irregular de maquinaria en administracion directa',
        'contract-splitting-orders': 'Fraccionamiento de compras en ordenes menores a 8 UIT',
        'mef-underspending': 'Subejecucion presupuestal critica en proyectos de inversion',
        'recurrent-direct-award': 'Contrataciones directas recurrentes a la misma empresa',
        'hhi-concentration': 'Alta concentracion de mercado de proveedores (Indice HHI)'
      };
      const humanIndicatorName = INDICATOR_LABELS[code] || flag.name || flag.formula_description || `Alerta Tecnica: ${code}`;

      const searchKeywords = `${a.alert_id} ${entName} ${humanIndicatorName} ${a.review_notes || ''} ${flag.formula_description || ''} ${code}`.toLowerCase();

      return `
        <article class="alert-card bg-surface-container-lowest rounded border border-slate-border shadow-sm p-6 flex flex-col gap-4" data-severity="${severity}" data-text="${searchKeywords}">
          <div class="flex flex-wrap items-center justify-between gap-2 border-b border-slate-border pb-3">
            <div class="flex items-center gap-2 flex-wrap">
              <span class="px-2.5 py-1 rounded ${badgeClass} font-label-sm text-label-sm font-bold flex items-center gap-1.5 shadow-sm">
                <span class="material-symbols-outlined text-[16px]">${badgeIcon}</span>
                ${badgeLabel}
              </span>
              <span class="font-mono text-label-sm font-bold text-on-surface px-2 py-0.5 rounded bg-surface-container-highest">
                ${a.alert_id}
              </span>
              <span class="text-caption font-label-sm uppercase tracking-wide text-on-surface-variant flex items-center gap-1 font-semibold">
                <span class="material-symbols-outlined text-[15px]">apartment</span>
                ${entName}
              </span>
            </div>
            <div class="text-caption font-label-sm text-civic-emerald font-semibold flex items-center gap-1">
              <span class="material-symbols-outlined text-[15px]">verified</span>
              Validada por Revisor Humano (Art. 14)
            </div>
          </div>

          <div>
            <div class="flex items-center gap-2 mb-1 text-xs">
              <span class="font-mono text-caption text-secondary font-semibold uppercase">Alerta Preventiva</span>
              <span class="text-outline">·</span>
              <span class="font-mono text-caption text-outline">Regla: ${code}</span>
            </div>
            <h2 class="font-headline-md text-headline-md text-on-surface font-semibold tracking-tight hover:text-secondary cursor-pointer transition-colors leading-snug">
              ${humanIndicatorName}
            </h2>
            <p class="font-body-md text-body-md text-on-surface-variant leading-relaxed mt-1.5">
              ${a.review_notes || 'Revision colegiada formal completada conforme a los Articulos 14 y 15.'}
            </p>
          </div>

          <!-- Cuadro de Explicabilidad Algoritmica (Art. 15) -->
          <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2 py-2 bg-surface-container-low px-4 rounded border border-slate-border text-xs">
            <div class="flex flex-col">
              <span class="text-caption font-label-sm uppercase text-on-surface-variant">Indicador Algoritmico</span>
              <span class="font-body-sm text-body-sm font-mono text-secondary font-semibold">${code}</span>
            </div>
            <div class="flex flex-col">
              <span class="text-caption font-label-sm uppercase text-on-surface-variant">Umbral vs Observado</span>
              <span class="font-body-sm text-body-sm font-mono text-on-surface font-semibold">Umbral: ${flag.threshold ?? 1} / Obs: ${flag.observed_value ?? 1}</span>
            </div>
            <div class="flex flex-col">
              <span class="text-caption font-label-sm uppercase text-on-surface-variant">Fuente Evidencia</span>
              <span class="font-body-sm text-body-sm font-mono text-on-surface font-semibold">${flag.evidence_source || 'seace-ocds'}</span>
            </div>
            <div class="flex flex-col">
              <span class="text-caption font-label-sm uppercase text-on-surface-variant">Revisor Nominal</span>
              <span class="font-body-sm text-body-sm text-on-surface font-semibold truncate" title="${a.reviewed_by}">${a.reviewed_by}</span>
            </div>
          </div>

          <div class="p-3 bg-surface-container rounded border border-slate-border text-xs space-y-1">
            <div class="text-secondary font-semibold">Formula Matematica Auditada:</div>
            <div class="font-mono text-on-surface text-[11px] leading-relaxed">${flag.formula_description || 'Algoritmo determinista de deteccion de anomalias.'}</div>
            <div class="text-[11px] text-outline pt-1 border-t border-slate-border mt-1 font-sans">${a.disclaimer}</div>
          </div>

          <div class="flex flex-wrap items-center justify-between gap-2 pt-2 border-t border-slate-border">
            <button type="button" class="btn-inspect-alert-evidence px-3.5 py-1.5 rounded bg-primary text-on-primary font-label-sm text-label-sm hover:opacity-90 transition-opacity flex items-center gap-1.5 shadow-sm font-semibold cursor-pointer" data-alert-id="${a.alert_id}">
              <span class="material-symbols-outlined text-[16px]">visibility</span>
              Inspeccionar Evidencia OCDS / SIAF
            </button>
            <a class="inline-flex items-center gap-1 text-label-sm font-label-sm text-secondary hover:underline font-semibold" href="/entidad?id=${a.entity_id}">
              Inspeccionar Ficha de Entidad <span class="material-symbols-outlined text-[15px]">arrow_forward</span>
            </a>
          </div>
        </article>
      `;
    }).join('');

    // Eventos para botones de evidencia
    container.querySelectorAll('.btn-inspect-alert-evidence').forEach(btn => {
      btn.addEventListener('click', () => {
        const alertId = btn.dataset.alertId;
        const alertObj = alerts.find(x => x.alert_id === alertId);
        if (alertObj) {
          const flag = flagsMap.get((alertObj.red_flag_ids && alertObj.red_flag_ids[0]) || '') || {};
          openRawPayloadDrawer({
            alerta: alertObj,
            bandera_roja: flag,
            marco_legal: 'Art. 14 y Art. 15 Constitucion Cajamarca Qhaway'
          }, `Evidencia de Alerta: ${alertObj.alert_id}`);
        }
      });
    });
  }
}

// Exponer funciones civicas globalmente
window.initLanguageMode = initLanguageMode;
window.applyLanguageMode = applyLanguageMode;
window.toggleLanguageMode = toggleLanguageMode;
window.initCivicTooltips = initCivicTooltips;
window.initCivicDictionaryModal = initCivicDictionaryModal;
window.openCivicDictionaryModal = openCivicDictionaryModal;
window.closeCivicDictionaryModal = closeCivicDictionaryModal;
window.formatCitizenPocketMoney = formatCitizenPocketMoney;
window.updateSpeedometer = updateSpeedometer;
window.formatCitizenPerCapita = formatCitizenPerCapita;

// Iniciar al cargar
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initGlobalControls);
} else {
  initGlobalControls();
}

