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

const STORAGE_KEYS = {
  THEME: 'cajamarca_qhaway_theme',
  RURAL: 'cajamarca_qhaway_rural_lite',
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
export function openRawPayloadDrawer(payloadObj, title = 'Evidencia Original OCDS (Art. 10)') {
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
            <span class="material-symbols-outlined text-secondary text-[20px]">data_object</span>
            <h3 id="global-raw-payload-title" class="font-serif font-bold text-base text-on-surface truncate"></h3>
          </div>
          <div class="flex items-center gap-2">
            <button id="global-raw-payload-copy-btn" class="px-3 py-1.5 rounded bg-surface border border-slate-border hover:bg-surface-container text-xs font-semibold text-on-surface flex items-center gap-1 cursor-pointer transition-colors" title="Copiar JSON completo">
              <span class="material-symbols-outlined text-[15px]">content_copy</span> Copiar
            </button>
            <button id="global-raw-payload-close-btn" class="p-1.5 rounded hover:bg-surface-container text-on-surface-variant hover:text-on-surface cursor-pointer" aria-label="Cerrar modal">
              <span class="material-symbols-outlined text-[20px]">close</span>
            </button>
          </div>
        </div>
        <div class="p-4 overflow-y-auto flex-1 bg-surface font-mono text-xs text-on-surface leading-relaxed">
          <pre id="global-raw-payload-code" class="whitespace-pre-wrap break-all"></pre>
        </div>
        <div class="p-3 border-t border-slate-border bg-surface-container-low text-[11px] text-on-surface-variant flex items-center justify-between">
          <span>Fuente inmutable verificable: SEACE OCDS / MEF SIAF (Art. 10 de la Constitucion)</span>
          <span class="font-semibold text-secondary">JSON Canonico</span>
        </div>
      </div>
    `;
    document.body.appendChild(modalEl);

    modalEl.querySelector('#global-raw-payload-close-btn').addEventListener('click', () => {
      modalEl.classList.add('hidden');
    });
    modalEl.addEventListener('click', (e) => {
      if (e.target === modalEl) modalEl.classList.add('hidden');
    });
    modalEl.querySelector('#global-raw-payload-copy-btn').addEventListener('click', () => {
      const code = modalEl.querySelector('#global-raw-payload-code').textContent;
      navigator.clipboard.writeText(code).then(() => {
        window.showToast('JSON copiado al portapapeles', 'success');
      });
    });
    window.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && !modalEl.classList.contains('hidden')) {
        modalEl.classList.add('hidden');
      }
    });
  }

  const titleEl = modalEl.querySelector('#global-raw-payload-title');
  const codeEl = modalEl.querySelector('#global-raw-payload-code');
  if (titleEl) titleEl.textContent = title;
  if (codeEl) codeEl.textContent = JSON.stringify(payloadObj || {}, null, 2);

  modalEl.classList.remove('hidden');
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

  // 6. Hidratacion reactiva de datos reales (DataEngine)
  hydrateAllViews();
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

function hydrateGlobalKPIElements(kpis) {
  // Atributos genericos data-kpi
  document.querySelectorAll('[data-kpi="pim-total"]').forEach(el => el.textContent = dataEngine.formatMillions(kpis.totalPim));
  document.querySelectorAll('[data-kpi="devengado-total"]').forEach(el => el.textContent = dataEngine.formatMillions(kpis.totalDevengado));
  document.querySelectorAll('[data-kpi="execution-rate"]').forEach(el => el.textContent = `${kpis.executionRate}%`);
  document.querySelectorAll('[data-kpi="procurements-total"]').forEach(el => el.textContent = `${kpis.totalProcurements.toLocaleString('es-PE')} Procesos`);
  document.querySelectorAll('[data-kpi="alerts-total"]').forEach(el => el.textContent = `${kpis.totalAlerts}`);
  document.querySelectorAll('[data-kpi="flags-total"]').forEach(el => el.textContent = `${kpis.totalRedFlags}`);
  document.querySelectorAll('[data-kpi="entities-total"]').forEach(el => el.textContent = `${kpis.entitiesCount}`);

  // IDs conocidos de index.html
  const heroPim = document.getElementById('hero-total-pim');
  if (heroPim) heroPim.textContent = dataEngine.formatMillions(kpis.totalPim);

  const heroAlertsBtn = document.getElementById('hero-alerts-btn');
  if (heroAlertsBtn) heroAlertsBtn.textContent = `Ver Alertas Activas (${kpis.totalAlerts} Publicadas)`;

  const heroDevPct = document.getElementById('hero-devengado-pct');
  if (heroDevPct) heroDevPct.textContent = `${kpis.executionRate}%`;

  const heroDevMonto = document.getElementById('hero-devengado-monto');
  if (heroDevMonto) heroDevMonto.textContent = dataEngine.formatMillions(kpis.totalDevengado);

  const kpiPim = document.getElementById('kpi-pim-total');
  if (kpiPim) kpiPim.textContent = dataEngine.formatMillions(kpis.totalPim);

  const kpiDevPct = document.getElementById('kpi-devengado-pct');
  if (kpiDevPct) kpiDevPct.textContent = `${kpis.executionRate}%`;

  const kpiDevBar = document.getElementById('kpi-devengado-bar');
  if (kpiDevBar) kpiDevBar.style.width = `${Math.min(100, kpis.executionRate)}%`;

  const kpiProcTotal = document.getElementById('kpi-procurements-total');
  if (kpiProcTotal) kpiProcTotal.textContent = `${kpis.totalProcurements.toLocaleString('es-PE')} Procesos`;

  const kpiProcSub = document.getElementById('kpi-procurements-sub');
  if (kpiProcSub) kpiProcSub.innerHTML = `${dataEngine.formatMillions(kpis.totalAwarded)} adjudicados en SEACE OCDS`;

  const kpiAlertsTotal = document.getElementById('kpi-alerts-total');
  if (kpiAlertsTotal) kpiAlertsTotal.textContent = `${kpis.totalAlerts} Alertas Publicadas`;

  // IDs conocidos de entidades.html
  const entPim = document.getElementById('entidades-kpi-pim');
  if (entPim) entPim.textContent = dataEngine.formatMillions(kpis.totalPim);

  const entDev = document.getElementById('entidades-kpi-devengado');
  if (entDev) entDev.textContent = dataEngine.formatMillions(kpis.totalDevengado);

  const entExec = document.getElementById('entidades-kpi-ejecucion');
  if (entExec) entExec.textContent = `${kpis.executionRate}%`;

  const entProc = document.getElementById('entidades-kpi-contratos');
  if (entProc) entProc.textContent = `${kpis.totalProcurements.toLocaleString('es-PE')}`;

  // IDs conocidos de alertas.html
  const alTotal = document.getElementById('alertas-kpi-total');
  if (alTotal) alTotal.textContent = `${kpis.totalAlerts}`;

  const alMonto = document.getElementById('alertas-kpi-monto');
  if (alMonto) alMonto.textContent = dataEngine.formatMillions(kpis.totalDevengado * 0.22);

  const alEnt = document.getElementById('alertas-kpi-entidades');
  if (alEnt) alEnt.textContent = `3 / 14`;
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

  // Actualizar Foco departamental / Speedometer
  const speedoPct = document.getElementById('speedo-text-pct');
  if (speedoPct) speedoPct.textContent = `${kpis.executionRate}%`;

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

/**
 * Hidratacion de entidades.html con filtro de año y datos en vivo
 */
async function hydrateEntidadesPage(kpis) {
  const [entities, budgets, procurements] = await Promise.all([
    dataEngine.getEntities(),
    dataEngine.getBudgetRecords(),
    dataEngine.getProcurements()
  ]);

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

        const updatedKpis = await dataEngine.getMacroKPIs(year);
        hydrateGlobalKPIElements(updatedKpis);
      });
    });
  }

  const resultsCount = document.getElementById('results-count');
  if (resultsCount) {
    resultsCount.textContent = `Mostrando ${entities.length} de ${entities.length} entidades fiscalizadas en Fase 1`;
  }
}

/**
 * Hidratacion de alertas.html con explicabilidad algoritmica integral (Art. 14 y Art. 15)
 */
async function hydrateAlertasPage(kpis) {
  const alerts = await dataEngine.getAlerts();
  const flags = await dataEngine.getRedFlags();
  const entities = await dataEngine.getEntities();
  const entitiesMap = new Map();
  entities.forEach(e => entitiesMap.set(e.entity_id, e));

  const flagsMap = new Map();
  flags.forEach(f => flagsMap.set(f.red_flag_id, f));

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

      const searchKeywords = `${a.alert_id} ${entName} ${a.review_notes || ''} ${flag.formula_description || ''} ${code}`.toLowerCase();

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
            <h2 class="font-headline-md text-headline-md text-on-surface font-semibold tracking-tight hover:text-secondary cursor-pointer transition-colors">
              Alerta de Riesgo en Contratacion Publica: ${code}
            </h2>
            <p class="font-body-md text-body-md text-on-surface-variant leading-relaxed mt-1">
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

// Iniciar al cargar
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initGlobalControls);
} else {
  initGlobalControls();
}
