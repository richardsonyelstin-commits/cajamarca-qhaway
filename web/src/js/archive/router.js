/**
 * [ARCHIVADO - CODIGO HISTORICO]
 * router.js: Enrutador SPA basado en Hash (#) para Cajamarca Qhaway.
 * Retirado y archivado segun ADR 0008 (Adopcion de Arquitectura Multi-Pagina MPA).
 * Conservado exclusivamente como referencia historica de diseno.
 *
 * Restricciones:
 * - Antislop R-02: Cero rayas em-dash en todo el archivo.
 * - Antislop R-24: Cero rutas rotas; fallback 404 limpio y accesible.
 */

import { store } from './state.js';
import {
  renderLoadingState,
  renderEmptyState,
  renderInicioView,
  renderEntidadesView,
  renderEntidadDetalleView,
  renderAlertasView,
  renderAlertaDetalleView,
  renderContratacionesView,
  renderContratoDetalleView,
  renderPresupuestoView,
  renderTransparenciaView,
  renderAcercaView,
  setupViewEvents
} from './views.js';
import { renderDenunciaView, setupDenunciaEvents } from './denuncias.js';
import {
  isAuthenticatedReviewer,
  renderLoginView,
  setupLoginEvents,
  renderAdminRevisionView,
  renderAdminDenunciasView,
  renderAdminAuditoriaView,
  setupAdminEvents
} from './review-panel.js';

export class Router {
  constructor(appContainerId = 'app-view-container') {
    this.container = document.getElementById(appContainerId);
    this.currentRoute = '';
    this.currentParams = {};
  }

  /**
   * Parsea la ruta y los parametros desde window.location.hash
   */
  parseLocation() {
    const rawHash = window.location.hash.slice(1) || '/inicio';
    const [pathPart, queryPart] = rawHash.split('?');
    const path = pathPart.startsWith('/') ? pathPart : `/${pathPart}`;

    const params = {};
    if (queryPart) {
      const searchParams = new URLSearchParams(queryPart);
      for (const [key, value] of searchParams.entries()) {
        params[key] = value;
      }
    }

    return { path, params };
  }

  /**
   * Actualiza la clase activa en los enlaces de navegacion
   */
  updateActiveNavLinks(path) {
    const navLinks = document.querySelectorAll('.nav-link, .navbar-brand');
    navLinks.forEach(link => {
      const route = link.getAttribute('data-route') || link.getAttribute('href');
      if (route && (route === `#${path}` || (path.startsWith('/entidad') && route.includes('entidades')) || (path.startsWith('/alerta') && route.includes('alertas')) || (path.startsWith('/contrato') && route.includes('contrataciones')))) {
        link.classList.add('active');
        link.setAttribute('aria-current', 'page');
      } else {
        link.classList.remove('active');
        link.removeAttribute('aria-current');
      }
    });
  }

  /**
   * Renderiza la ruta correspondiente en el contenedor principal
   */
  route() {
    if (!this.container) {
      this.container = document.getElementById('app-view-container');
      if (!this.container) return;
    }

    const { path, params } = this.parseLocation();
    this.currentRoute = path;
    this.currentParams = params;

    // Si los datos todavia estan cargando
    const { isLoading, loadError } = store.getState();
    if (isLoading) {
      this.container.innerHTML = renderLoadingState();
      return;
    }

    if (loadError) {
      this.container.innerHTML = renderEmptyState(
        'Error al conectar con fuentes de datos',
        loadError,
        'Reintentar carga',
        '#/inicio'
      );
      return;
    }

    // Rutas protegidas del Panel Humano (CU5 / ADR 0005)
    if (path.startsWith('/admin/') && path !== '/admin/login') {
      if (!isAuthenticatedReviewer()) {
        window.location.hash = '#/admin/login';
        return;
      }
    }

    // Sincronizar navegacion
    this.updateActiveNavLinks(path);

    // Mapeo exhaustivo de rutas del Sitemap 004
    switch (path) {
      case '/inicio':
        this.container.innerHTML = renderInicioView();
        setupViewEvents();
        break;

      case '/entidades':
        if (params.province) {
          store.setFilter('province', params.province);
        }
        this.container.innerHTML = renderEntidadesView();
        setupViewEvents();
        break;

      case '/entidad':
        this.container.innerHTML = renderEntidadDetalleView(params.id || '');
        setupViewEvents();
        break;

      case '/alertas':
        this.container.innerHTML = renderAlertasView();
        setupViewEvents();
        break;

      case '/alerta':
        this.container.innerHTML = renderAlertaDetalleView(params.id || '');
        setupViewEvents();
        break;

      case '/contrataciones':
        this.container.innerHTML = renderContratacionesView();
        setupViewEvents();
        break;

      case '/contrato':
        this.container.innerHTML = renderContratoDetalleView(params.id || '');
        setupViewEvents();
        break;

      case '/presupuesto':
        this.container.innerHTML = renderPresupuestoView();
        setupViewEvents();
        break;

      case '/denuncia':
        this.container.innerHTML = renderDenunciaView();
        setupDenunciaEvents();
        break;

      case '/transparencia':
        this.container.innerHTML = renderTransparenciaView();
        setupViewEvents();
        break;

      case '/acerca':
        this.container.innerHTML = renderAcercaView();
        break;

      case '/admin/login':
        this.container.innerHTML = renderLoginView();
        setupLoginEvents();
        break;

      case '/admin/revision':
        this.container.innerHTML = renderAdminRevisionView();
        setupAdminEvents();
        break;

      case '/admin/denuncias':
        this.container.innerHTML = renderAdminDenunciasView();
        setupAdminEvents();
        break;

      case '/admin/auditoria':
        this.container.innerHTML = renderAdminAuditoriaView();
        setupAdminEvents();
        break;

      default:
        // Manejo 404 limpio (R-24)
        this.container.innerHTML = renderEmptyState(
          'Pagina no encontrada (Error 404)',
          `La seccion "${path}" no existe en la plataforma de Cajamarca Qhaway.`,
          'Ir a la pagina de Inicio',
          '#/inicio'
        );
        break;
    }

    // Desplazamiento al inicio de la pagina
    window.scrollTo({ top: 0, behavior: 'instant' });
    this.container.removeAttribute('aria-busy');
  }

  /**
   * Inicia el enrutador y escucha eventos de navegacion
   */
  init() {
    window.addEventListener('hashchange', () => this.route());

    // Reaccionar a cambios en el estado que afecten la vista actual
    store.subscribe((state) => {
      if (!state.isLoading) {
        this.route();
      }
    });

    // Primera ejecucion
    if (!window.location.hash) {
      window.location.hash = '#/inicio';
    } else {
      this.route();
    }
  }
}
