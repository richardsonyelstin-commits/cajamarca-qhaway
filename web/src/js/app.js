/**
 * app.js: Inicializador principal de Cajamarca Qhaway
 * Punto de entrada del modulo ES6 (<script type="module" src="src/js/app.js">)
 *
 * Restricciones:
 * - Antislop R-02: Cero rayas em-dash en todo el archivo.
 * - Antislop R-26: Todo control interactivo funcional.
 * - Antislop R-27: Tres estados obligatorios.
 */

import { supabaseClient } from './supabase-client.js';
import { store } from './state.js';
import { Router } from './router.js';

/**
 * Actualiza el indicador visual de conexion en la barra superior
 */
function updateConnectionBadge(sourceMode) {
  const badgeText = document.getElementById('connection-status-text');
  const badgeContainer = document.getElementById('connection-status-badge');

  if (!badgeText || !badgeContainer) return;

  if (sourceMode === 'online') {
    badgeText.textContent = 'Conectado a Red Oficial Supabase';
    badgeContainer.className = 'badge-connection badge-connection-online';
  } else if (sourceMode === 'snapshot') {
    badgeText.textContent = 'Modo Respaldo: Instantanea Verificada';
    badgeContainer.className = 'badge-connection badge-connection-snapshot';
  } else {
    badgeText.textContent = 'Modo Contingencia: Semilla Canónica Local';
    badgeContainer.className = 'badge-connection badge-connection-local';
  }
}

/**
 * Sincroniza el estado del boton de tema claro/oscuro
 */
function syncThemeButton() {
  const label = document.getElementById('theme-toggle-label');
  const currentTheme = store.getState().theme;
  document.documentElement.setAttribute('data-bs-theme', currentTheme);

  if (label) {
    label.textContent = currentTheme === 'dark' ? 'Tema Claro' : 'Tema Oscuro';
  }
}

/**
 * Configura los controles interactivos globales de la aplicacion
 */
function setupGlobalControls() {
  // 1. Conmutador de Tema Claro / Oscuro (R-34)
  const btnThemeToggle = document.getElementById('btn-theme-toggle');
  if (btnThemeToggle) {
    btnThemeToggle.addEventListener('click', () => {
      store.toggleTheme();
      syncThemeButton();
    });
  }

  // 2. Conmutador de Modo Rural Ligero (CU2)
  const btnRuralMode = document.getElementById('btn-rural-mode');
  if (btnRuralMode) {
    // Sincronizar estado inicial
    const isRural = store.getState().ruralLiteMode;
    btnRuralMode.setAttribute('aria-pressed', String(isRural));
    if (isRural) {
      document.body.classList.add('mode-rural-lite');
      btnRuralMode.classList.add('active');
    }

    btnRuralMode.addEventListener('click', () => {
      store.toggleRuralLiteMode();
      const current = store.getState().ruralLiteMode;
      btnRuralMode.setAttribute('aria-pressed', String(current));
      if (current) {
        btnRuralMode.classList.add('active');
      } else {
        btnRuralMode.classList.remove('active');
      }
    });
  }

  // 3. Buscador Global Rapido (buscar por RUC, nombre de entidad o contrato)
  const searchForm = document.getElementById('global-search-form');
  const searchInput = document.getElementById('global-search-input');
  if (searchForm && searchInput) {
    searchForm.addEventListener('submit', (e) => {
      e.preventDefault();
      const query = searchInput.value.trim().toLowerCase();
      if (!query) return;

      const { entities, procurements } = store.getState();

      // Buscar coincidencia en entidades (por RUC o nombre)
      const foundEntity = entities.find(ent =>
        ent.ruc.includes(query) || ent.official_name.toLowerCase().includes(query)
      );

      if (foundEntity) {
        window.location.hash = `#/entidad?id=${foundEntity.entity_id}`;
        return;
      }

      // Buscar coincidencia en contratos (por OCID o titulo)
      const foundProc = procurements.find(p =>
        p.ocid.toLowerCase().includes(query) || p.title.toLowerCase().includes(query)
      );

      if (foundProc) {
        window.location.hash = `#/contrato?id=${encodeURIComponent(foundProc.ocid)}`;
        return;
      }

      // Si no es exacto, ir a directorio con busqueda
      window.location.hash = `#/entidades?q=${encodeURIComponent(query)}`;
    });
  }

  // 4. Boton para copiar payload JSON en modal accesible (Art. 10)
  const btnCopyPayload = document.getElementById('btn-copy-payload');
  if (btnCopyPayload) {
    btnCopyPayload.addEventListener('click', async () => {
      const payloadData = store.getState().rawPayloadModalData;
      if (!payloadData) return;

      try {
        await navigator.clipboard.writeText(payloadData);
        const originalText = btnCopyPayload.textContent;
        btnCopyPayload.textContent = 'JSON Copiado!';
        setTimeout(() => {
          btnCopyPayload.textContent = originalText;
        }, 2000);
      } catch (err) {
        prompt('Copie manualmente el contenido JSON:', payloadData);
      }
    });
  }

  // 5. Cierre accesible con tecla Escape para modales
  window.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      const openModals = document.querySelectorAll('.modal.show');
      openModals.forEach(modalEl => {
        if (window.bootstrap && window.bootstrap.Modal) {
          const instance = window.bootstrap.Modal.getInstance(modalEl);
          if (instance) instance.hide();
        }
      });
    }
  });
}

/**
 * Inicializacion de la aplicacion
 */
async function initializeApp() {
  syncThemeButton();
  setupGlobalControls();

  const router = new Router('app-view-container');
  router.init();

  try {
    // Carga de datos con fallback resiliente
    const dataset = await supabaseClient.fetchInitialDataset();

    store.setState({
      entities: dataset.entities,
      procurements: dataset.procurements,
      budgetExecutions: dataset.budgetExecutions,
      alerts: dataset.alerts,
      redFlags: dataset.redFlags,
      citizenReports: dataset.citizenReports,
      sourceMode: dataset.sourceMode,
      isLoading: false,
      loadError: null
    });

    updateConnectionBadge(dataset.sourceMode);
  } catch (err) {
    console.error('Error critico en la inicializacion de datos:', err);
    store.setState({
      isLoading: false,
      loadError: `Fallo de inicializacion: ${err.message}. Verifique la conectividad de red.`
    });
    updateConnectionBadge('local-fallback');
  }
}

// Iniciar al cargar el DOM
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initializeApp);
} else {
  initializeApp();
}
