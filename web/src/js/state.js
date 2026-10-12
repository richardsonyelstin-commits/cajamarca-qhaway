/**
 * state.js: Almacen de estado reactivo y gestion de filtros para Cajamarca Qhaway
 *
 * Restricciones:
 * - Antislop R-02: Cero rayas em-dash en todo el archivo.
 * - Soporte para los 3 modos: normal, ruralLiteMode, plainLanguageMode.
 */

const STORAGE_KEYS = {
  THEME: 'cajamarca_qhaway_theme',
  RURAL_MODE: 'cajamarca_qhaway_rural_lite',
  PLAIN_LANGUAGE: 'cajamarca_qhaway_plain_lang',
  REVIEWER: 'cajamarca_qhaway_reviewer_session'
};

class StateStore {
  constructor() {
    this.listeners = new Set();

    // Cargar configuraciones guardadas
    const savedTheme = localStorage.getItem(STORAGE_KEYS.THEME) || 'light';
    const savedRural = localStorage.getItem(STORAGE_KEYS.RURAL_MODE) === 'true';
    const savedPlain = localStorage.getItem(STORAGE_KEYS.PLAIN_LANGUAGE) === 'true';

    let savedReviewer = null;
    try {
      const rawReviewer = localStorage.getItem(STORAGE_KEYS.REVIEWER);
      savedReviewer = rawReviewer ? JSON.parse(rawReviewer) : null;
    } catch {
      savedReviewer = null;
    }

    this.state = {
      // Datos cargados desde Supabase / snapshot
      entities: [],
      procurements: [],
      budgetExecutions: [],
      alerts: [],
      redFlags: [],
      citizenReports: [],
      auditLog: [],
      sourceMode: 'online', // 'online', 'snapshot', 'local-fallback'
      isLoading: true,
      loadError: null,

      // Filtros globales y exploracion
      filters: {
        province: '',
        entityId: '',
        indicatorCode: '',
        searchQuery: '',
        fiscalYear: 2026,
        procurementMethod: '',
        minAmount: 0,
        maxAmount: Infinity
      },

      // Modalidades de visualizacion y accesibilidad
      theme: savedTheme,
      ruralLiteMode: savedRural,
      plainLanguageMode: savedPlain,

      // Sesion de revisor humano (005-review-panel / ADR 0005)
      reviewerSession: savedReviewer,

      // Modal activo
      activeModal: null, // { type: 'explicabilidad' | 'raw_payload', data: any }
      rawPayloadModalData: null
    };
  }

  /**
   * Suscribe un callback a cualquier actualizacion de estado
   * @param {Function} listener
   * @returns {Function} Funcion para desuscribirse
   */
  subscribe(listener) {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  /**
   * Notifica a todos los oyentes registrados
   */
  notify() {
    for (const listener of this.listeners) {
      try {
        listener(this.state);
      } catch (err) {
        console.error('Error en listener de estado:', err);
      }
    }
  }

  /**
   * Obtiene copia inmutable superficial del estado actual
   */
  getState() {
    return { ...this.state };
  }

  /**
   * Actualiza el estado combinando propiedades
   * @param {object} updates
   */
  setState(updates) {
    this.state = {
      ...this.state,
      ...updates
    };
    this.notify();
  }

  /**
   * Establece un filtro especifico
   */
  setFilter(key, value) {
    this.state = {
      ...this.state,
      filters: {
        ...this.state.filters,
        [key]: value
      }
    };
    this.notify();
  }

  /**
   * Restablece todos los filtros de busqueda a sus valores iniciales
   */
  resetFilters() {
    this.state = {
      ...this.state,
      filters: {
        province: '',
        entityId: '',
        indicatorCode: '',
        searchQuery: '',
        fiscalYear: 2026,
        procurementMethod: '',
        minAmount: 0,
        maxAmount: Infinity
      }
    };
    this.notify();
  }

  /**
   * Alterna entre tema claro y oscuro (R-34)
   */
  toggleTheme() {
    const nextTheme = this.state.theme === 'dark' ? 'light' : 'dark';
    localStorage.setItem(STORAGE_KEYS.THEME, nextTheme);
    document.documentElement.setAttribute('data-bs-theme', nextTheme);
    this.setState({ theme: nextTheme });
  }

  /**
   * Alterna el modo rural ligero (CU2)
   */
  toggleRuralLiteMode() {
    const next = !this.state.ruralLiteMode;
    localStorage.setItem(STORAGE_KEYS.RURAL_MODE, String(next));
    if (next) {
      document.body.classList.add('mode-rural-lite');
    } else {
      document.body.classList.remove('mode-rural-lite');
    }
    this.setState({ ruralLiteMode: next });
  }

  /**
   * Alterna el modo de lenguaje claro ciudadano (CU4)
   */
  togglePlainLanguageMode() {
    const next = !this.state.plainLanguageMode;
    localStorage.setItem(STORAGE_KEYS.PLAIN_LANGUAGE, String(next));
    this.setState({ plainLanguageMode: next });
  }

  /**
   * Establece la sesion autenticada de un revisor humano nominal
   */
  setReviewerSession(sessionData) {
    localStorage.setItem(STORAGE_KEYS.REVIEWER, JSON.stringify(sessionData));
    this.setState({ reviewerSession: sessionData });
  }

  /**
   * Cierra la sesion del revisor humano
   */
  clearReviewerSession() {
    localStorage.removeItem(STORAGE_KEYS.REVIEWER);
    this.setState({ reviewerSession: null });
  }
}

export const store = new StateStore();
