/**
 * [ARCHIVADO - CODIGO HISTORICO]
 * views.js: Renderizador seguro de vistas para Cajamarca Qhaway.
 * Retirado y archivado segun ADR 0008 (Adopcion de Arquitectura Multi-Pagina MPA).
 * Conservado exclusivamente como referencia historica de diseno.
 *
 * Restricciones:
 * - Antislop R-02: Cero rayas em-dash en todo el archivo.
 * - Antislop R-27: Tres estados obligatorios (loading, empty, error).
 * - Articulo 16: Prohibicion estricta de scoring a personas individuales.
 * - Articulo 17: Estado de reserva de DJI bajo Ley 29733.
 */

import {
  CANONICAL_INDICATORS,
  CAJAMARCA_PROVINCES,
  STANDARD_ALERT_DISCLAIMER
} from './config.js';
import { store } from './state.js';
import { escapeHtml, formatDateTime, openExplicabilidadModal, openRawPayloadModal, generateShareSummary } from './explicabilidad.js';
import { renderDenunciaView, setupDenunciaEvents } from './denuncias.js';
import {
  renderLoginView,
  setupLoginEvents,
  renderAdminRevisionView,
  renderAdminDenunciasView,
  renderAdminAuditoriaView,
  setupAdminEvents
} from './review-panel.js';
import {
  exportAlertsCsv,
  exportProcurementsCsv,
  exportBudgetExecutionsCsv,
  exportEntitiesCsv
} from './export-csv.js';

/**
 * 1. Estados Obligatorios de UI (Regla R-27 de Antislop)
 */
export function renderLoadingState(message = 'Cargando datos verificados...') {
  return `
    <div class="ui-state-loading text-center py-5" role="status" aria-live="polite">
      <div class="spinner-border text-primary mb-3" style="width: 2.5rem; height: 2.5rem;" role="status">
        <span class="visually-hidden">Cargando...</span>
      </div>
      <h2 class="h5 text-dark">${escapeHtml(message)}</h2>
      <p class="text-muted small">Consultando fuentes oficiales OCDS SEACE y MEF DataStore...</p>
    </div>
  `;
}

export function renderEmptyState(title, description, actionText = 'Restablecer filtros', actionHash = '#/inicio') {
  return `
    <div class="ui-state-empty card border-0 bg-body-subtle text-center p-5 my-4">
      <div class="mb-3">
        <span class="badge bg-secondary-subtle text-secondary-emphasis px-3 py-2 fs-6">Sin registros</span>
      </div>
      <h2 class="h5 text-dark mb-2">${escapeHtml(title)}</h2>
      <p class="text-secondary small max-w-600 mx-auto mb-4">${escapeHtml(description)}</p>
      <div>
        <a href="${escapeHtml(actionHash)}" class="btn btn-outline-primary btn-sm px-4 py-2" id="btn-empty-action">
          ${escapeHtml(actionText)}
        </a>
      </div>
    </div>
  `;
}

export function renderErrorState(title, message, retryActionText = 'Reintentar conexion') {
  return `
    <div class="ui-state-error card border-danger-subtle bg-danger-subtle text-center p-4 my-4" role="alert">
      <h2 class="h5 text-danger mb-2">${escapeHtml(title)}</h2>
      <p class="text-danger-emphasis small mb-3">${escapeHtml(message)}</p>
      <div>
        <button type="button" class="btn btn-danger btn-sm px-3" onclick="window.location.reload();">
          ${escapeHtml(retryActionText)}
        </button>
      </div>
    </div>
  `;
}

/**
 * 2. Vista Inicio (#/inicio)
 */
export function renderInicioView() {
  const { entities, procurements, budgetExecutions, alerts, ruralLiteMode } = store.getState();

  // Calculo de metricas macro
  const totalContratos = procurements.length;
  const montoContratadoTotal = procurements.reduce((acc, p) => acc + (Number(p.awarded_amount) || 0), 0);
  const totalAlertas = alerts.length;

  const pimTotal = budgetExecutions.reduce((acc, b) => acc + (Number(b.budgeted_amount) || 0), 0);
  const devengadoTotal = budgetExecutions.reduce((acc, b) => acc + (Number(b.executed_amount) || 0), 0);
  const pctDevengadoRegional = pimTotal > 0 ? ((devengadoTotal / pimTotal) * 100).toFixed(1) : '0.0';

  // Alertas recientes
  const recentAlerts = alerts.slice(0, 3);
  const alertsHtml = recentAlerts.length === 0 ? `
    <div class="p-3 bg-light rounded text-muted small text-center">
      No se han registrado alertas publicadas recientemente.
    </div>
  ` : recentAlerts.map(a => {
    const ent = entities.find(e => e.entity_id === a.entity_id);
    return `
      <div class="card mb-3 border-start border-4 border-warning shadow-sm">
        <div class="card-body p-3">
          <div class="d-flex justify-content-between align-items-center mb-1">
            <span class="badge bg-warning text-dark font-monospace">${escapeHtml(a.alert_id)}</span>
            <span class="small text-muted font-monospace">${escapeHtml(formatDateTime(a.published_at || a.reviewed_at))}</span>
          </div>
          <h3 class="h6 mb-1 text-primary">
            <a href="#/alerta?id=${escapeHtml(a.alert_id)}" class="text-decoration-none">
              ${escapeHtml(ent ? ent.official_name : 'Entidad Fiscalizada')}
            </a>
          </h3>
          <p class="small text-secondary mb-2 text-truncate">
            ${escapeHtml(a.review_notes || 'Revision humana conforme')}
          </p>
          <div class="d-flex justify-content-between align-items-center flex-wrap gap-2">
            <button type="button" class="btn btn-sm btn-outline-primary py-0 px-2 btn-open-explicabilidad" data-alert-id="${escapeHtml(a.alert_id)}">
              Explicabilidad Art. 15
            </button>
            <span class="small text-muted">Revisor: ${escapeHtml(a.reviewed_by)}</span>
          </div>
        </div>
      </div>
    `;
  }).join('');

  return `
    <div class="inicio-view">
      <!-- Seccion Hero de Bienvenida -->
      <section class="hero-section mb-4 p-4 rounded bg-body-subtle border">
        <div class="row align-items-center g-3">
          <div class="col-12 col-lg-8">
            <span class="badge bg-primary-subtle text-primary-emphasis border mb-2">Observatorio Civico Regional</span>
            <h1 class="h2 mb-2 text-dark">Fiscalizacion y Vigilancia del Gasto en Cajamarca</h1>
            <p class="text-secondary mb-3">
              Monitoreo independiente de contrataciones publicas SEACE y ejecucion presupuestal MEF en las 13 provincias de la region. Datos oficiales abiertos con trazabilidad criptografica y explicabilidad algoritmica.
            </p>
            <div class="d-flex gap-2 flex-wrap">
              <a href="#/alertas" class="btn btn-primary btn-sm px-3">Explorar Alertas Publicadas</a>
              <a href="#/entidades" class="btn btn-outline-secondary btn-sm px-3">14 Entidades Fiscalizadas</a>
              <a href="#/denuncia" class="btn btn-outline-warning btn-sm px-3 text-dark">Canal de Denuncia</a>
            </div>
          </div>
          <div class="col-12 col-lg-4 text-center">
            ${!ruralLiteMode ? `
              <img src="media/cajamarca-map.svg" alt="Mapa de Cajamarca" class="img-fluid" style="max-height: 160px;">
            ` : `
              <div class="p-3 border rounded bg-light text-muted small">Modo rural ligero: mapa vectorial optimizado.</div>
            `}
          </div>
        </div>
      </section>

      <!-- KPIs Macro Regionales -->
      <section class="kpis-section mb-4" aria-label="Indicadores macro regionales">
        <div class="row g-3">
          <div class="col-6 col-md-3">
            <div class="card h-100 border-0 bg-body-surface shadow-sm p-3">
              <span class="text-muted small">Entidades del Universo</span>
              <span class="display-6 fw-bold text-primary font-monospace">${entities.length}</span>
              <span class="small text-muted">1 GORE + 13 Provincias</span>
            </div>
          </div>
          <div class="col-6 col-md-3">
            <div class="card h-100 border-0 bg-body-surface shadow-sm p-3">
              <span class="text-muted small">Contratos SEACE OCDS</span>
              <span class="display-6 fw-bold text-dark font-monospace">${totalContratos}</span>
              <span class="small text-muted">S/ ${(montoContratadoTotal / 1000000).toFixed(1)}M adjudicados</span>
            </div>
          </div>
          <div class="col-6 col-md-3">
            <div class="card h-100 border-0 bg-body-surface shadow-sm p-3">
              <span class="text-muted small">Ejecucion Presupuestal MEF</span>
              <span class="display-6 fw-bold text-success font-monospace">${pctDevengadoRegional}%</span>
              <span class="small text-muted">Devengado sobre PIM</span>
            </div>
          </div>
          <div class="col-6 col-md-3">
            <div class="card h-100 border-0 bg-body-surface shadow-sm p-3">
              <span class="text-muted small">Alertas Publicadas (Art. 14)</span>
              <span class="display-6 fw-bold text-warning-emphasis font-monospace">${totalAlertas}</span>
              <span class="small text-muted">Revisadas nominalmente</span>
            </div>
          </div>
        </div>
      </section>

      <!-- Mapa y Ultimas Alertas -->
      <div class="row g-4 mb-4">
        <div class="col-12 col-lg-7">
          <div class="card border-0 shadow-sm bg-body-surface p-3 h-100">
            <div class="d-flex justify-content-between align-items-center mb-3">
              <h2 class="h5 mb-0">Directorio Territorial de Provincias</h2>
              <a href="#/entidades" class="small text-decoration-none">Ver todas &rarr;</a>
            </div>
            <p class="small text-muted mb-3">Seleccione una provincia para fiscalizar sus contrataciones:</p>
            <div class="row g-2">
              ${CAJAMARCA_PROVINCES.map(prov => `
                <div class="col-6 col-md-4">
                  <a href="#/entidades?province=${encodeURIComponent(prov)}" class="btn btn-outline-light text-dark border w-100 text-start py-2 px-3 small d-flex justify-content-between align-items-center">
                    <span>${escapeHtml(prov)}</span>
                    <span class="badge bg-secondary-subtle text-secondary small">&rarr;</span>
                  </a>
                </div>
              `).join('')}
            </div>
          </div>
        </div>

        <div class="col-12 col-lg-5">
          <div class="card border-0 shadow-sm bg-body-surface p-3 h-100">
            <div class="d-flex justify-content-between align-items-center mb-3">
              <h2 class="h5 mb-0">Alertas Publicadas Recientes</h2>
              <a href="#/alertas" class="small text-decoration-none">Ver todas &rarr;</a>
            </div>
            ${alertsHtml}
          </div>
        </div>
      </div>

      <!-- Casos de Uso Civicos (CU1 a CU5) -->
      <section class="card border-0 shadow-sm bg-body-surface p-4 mb-4" aria-label="Casos de uso del observatorio">
        <h2 class="h5 mb-3">Herramientas y Casos de Uso del Observatorio</h2>
        <div class="row g-3">
          <div class="col-12 col-md-4">
            <div class="p-3 border rounded bg-body-subtle h-100">
              <strong class="text-primary d-block mb-1">CU1: Exportacion CSV de Datos</strong>
              <p class="small text-secondary mb-2">Descarga masiva de contratos y alertas con calculo SHA-256 para investigacion en Excel.</p>
              <a href="#/transparencia" class="small fw-semibold text-decoration-none">Ir al centro de descargas &rarr;</a>
            </div>
          </div>
          <div class="col-12 col-md-4">
            <div class="p-3 border rounded bg-body-subtle h-100">
              <strong class="text-primary d-block mb-1">CU2 / CU4: Lenguaje Claro y Rural</strong>
              <p class="small text-secondary mb-2">Traduccion de terminos OCDS para comites de vigilancia y extractos listos para WhatsApp o SMS.</p>
              <a href="#/alertas" class="small fw-semibold text-decoration-none">Explorar fichas explicables &rarr;</a>
            </div>
          </div>
          <div class="col-12 col-md-4">
            <div class="p-3 border rounded bg-body-subtle h-100">
              <strong class="text-primary d-block mb-1">CU5: Revision Humana Nominal</strong>
              <p class="small text-secondary mb-2">Panel interno de evaluacion donde ningun algoritmo publica sin autor humano nominal (ADR 0005).</p>
              <a href="#/admin/revision" class="small fw-semibold text-decoration-none">Acceso al panel revisor &rarr;</a>
            </div>
          </div>
        </div>
      </section>
    </div>
  `;
}

/**
 * 3. Vista Directorio de 14 Entidades (#/entidades)
 */
export function renderEntidadesView() {
  const { entities, filters, procurements, alerts } = store.getState();
  const selectedProvince = filters.province;

  let filteredEntities = entities;
  if (selectedProvince) {
    filteredEntities = entities.filter(e => (e.province || 'REGIONAL').toUpperCase() === selectedProvince.toUpperCase());
  }

  const itemsHtml = filteredEntities.map(e => {
    const entProcs = procurements.filter(p => p.entity_id === e.entity_id);
    const entAlerts = alerts.filter(a => a.entity_id === e.entity_id);
    const totalAwarded = entProcs.reduce((acc, p) => acc + (Number(p.awarded_amount) || 0), 0);

    return `
      <div class="col-12 col-md-6 col-lg-4">
        <div class="card h-100 border shadow-sm">
          <div class="card-header bg-body-tertiary d-flex justify-content-between align-items-center">
            <span class="badge ${e.entity_level === 'regional' ? 'bg-primary' : 'bg-secondary'}">
              ${e.entity_level === 'regional' ? 'Regional' : 'Provincial'}
            </span>
            <span class="small font-monospace text-muted">RUC: ${escapeHtml(e.ruc)}</span>
          </div>
          <div class="card-body">
            <h3 class="h6 card-title mb-2">
              <a href="#/entidad?id=${escapeHtml(e.entity_id)}" class="text-decoration-none text-dark fw-bold">
                ${escapeHtml(e.official_name)}
              </a>
            </h3>
            <p class="small text-muted mb-2">
              Provincia: <strong>${escapeHtml(e.province || 'Cajamarca (Sede Regional)')}</strong>
            </p>
            <div class="small text-secondary mb-3">
              <div>Contratos registrados: <strong>${entProcs.length}</strong></div>
              <div>Monto total contratado: <strong>S/ ${totalAwarded.toLocaleString('es-PE', { minimumFractionDigits: 2 })}</strong></div>
              <div>Alertas publicadas: <strong class="${entAlerts.length > 0 ? 'text-warning-emphasis' : 'text-success'}">${entAlerts.length}</strong></div>
            </div>
            <a href="#/entidad?id=${escapeHtml(e.entity_id)}" class="btn btn-outline-primary btn-sm w-100">
              Ver Ficha Detallada
            </a>
          </div>
        </div>
      </div>
    `;
  }).join('');

  return `
    <div class="entidades-view">
      <div class="d-flex justify-content-between align-items-center flex-wrap gap-2 mb-3">
        <div>
          <h1 class="h3 mb-1">Directorio de las 14 Entidades Fiscalizadas</h1>
          <p class="text-secondary small mb-0">Universo cerrado de la Region Cajamarca: Gobierno Regional y 13 Municipalidades Provinciales (Art. 18).</p>
        </div>
        <button type="button" class="btn btn-outline-secondary btn-sm" id="btn-export-entities-csv">
          Descargar Directorio CSV (CU1)
        </button>
      </div>

      <!-- Filtro por Provincia -->
      <div class="card bg-body-subtle border-0 p-3 mb-4">
        <div class="row align-items-center g-2">
          <div class="col-12 col-md-4">
            <label for="filter-provincia-select" class="form-label small fw-semibold mb-1">Filtrar por Provincia:</label>
            <select class="form-select form-select-sm" id="filter-provincia-select">
              <option value="">Todas las provincias (14 entidades)</option>
              ${CAJAMARCA_PROVINCES.map(p => `
                <option value="${escapeHtml(p)}" ${selectedProvince === p ? 'selected' : ''}>${escapeHtml(p)}</option>
              `).join('')}
            </select>
          </div>
          <div class="col-12 col-md-8 text-md-end pt-md-3">
            <span class="small text-muted">Mostrando <strong>${filteredEntities.length}</strong> de <strong>14</strong> entidades</span>
          </div>
        </div>
      </div>

      ${filteredEntities.length === 0 ? renderEmptyState('No se encontraron entidades', 'No hay coincidencias con la provincia seleccionada.', 'Ver todas', '#/entidades') : `
        <div class="row g-3">
          ${itemsHtml}
        </div>
      `}
    </div>
  `;
}

/**
 * 4. Vista Ficha de Entidad (#/entidad?id=...)
 */
export function renderEntidadDetalleView(entityId) {
  const { entities, procurements, budgetExecutions, alerts } = store.getState();
  const entity = entities.find(e => e.entity_id === entityId);

  if (!entity) {
    return renderEmptyState('Entidad no encontrada', `No existe una entidad registrada con identificador ${entityId}.`, 'Volver al directorio', '#/entidades');
  }

  const entProcs = procurements.filter(p => p.entity_id === entity.entity_id);
  const entAlerts = alerts.filter(a => a.entity_id === entity.entity_id);
  const entBudgets = budgetExecutions.filter(b => b.entity_id === entity.entity_id);

  const budgetRows = entBudgets.map(b => {
    const pim = Number(b.budgeted_amount || 0);
    const dev = Number(b.executed_amount || 0);
    const pct = pim > 0 ? ((dev / pim) * 100).toFixed(1) : '0.0';
    return `
      <tr>
        <td class="font-monospace">${b.fiscal_year}</td>
        <td>${escapeHtml(b.budget_category || 'Gasto General')}</td>
        <td class="font-monospace text-end">S/ ${pim.toLocaleString('es-PE', { minimumFractionDigits: 2 })}</td>
        <td class="font-monospace text-end">S/ ${dev.toLocaleString('es-PE', { minimumFractionDigits: 2 })}</td>
        <td class="font-monospace text-end fw-bold ${Number(pct) > 70 ? 'text-success' : 'text-warning-emphasis'}">${pct}%</td>
      </tr>
    `;
  }).join('');

  const procRows = entProcs.map(p => `
    <tr>
      <td class="font-monospace small"><code>${escapeHtml(p.ocid)}</code></td>
      <td class="small">${escapeHtml(p.title)}</td>
      <td class="small">${escapeHtml(p.procurement_method || '-')}</td>
      <td class="font-monospace small text-end">S/ ${Number(p.awarded_amount || 0).toLocaleString('es-PE', { minimumFractionDigits: 2 })}</td>
      <td class="small text-truncate" style="max-width: 180px;">${escapeHtml(p.supplier_name || 'No consignado')}</td>
      <td>
        <button type="button" class="btn btn-sm btn-outline-secondary py-0 px-2 btn-open-raw-payload" data-proc-id="${escapeHtml(p.procurement_id)}">
          JSON
        </button>
      </td>
    </tr>
  `).join('');

  return `
    <div class="entidad-detalle-view">
      <!-- Migas de Pan -->
      <nav aria-label="breadcrumb" class="mb-3">
        <ol class="breadcrumb small">
          <li class="breadcrumb-item"><a href="#/inicio">Inicio</a></li>
          <li class="breadcrumb-item"><a href="#/entidades">Entidades</a></li>
          <li class="breadcrumb-item active" aria-current="page">${escapeHtml(entity.official_name)}</li>
        </ol>
      </nav>

      <!-- Ficha Institucional -->
      <div class="card border-0 shadow-sm bg-body-surface p-4 mb-4">
        <div class="d-flex justify-content-between align-items-center flex-wrap gap-2 mb-2">
          <span class="badge ${entity.entity_level === 'regional' ? 'bg-primary' : 'bg-secondary'} px-3 py-1">
            ${entity.entity_level === 'regional' ? 'Gobierno Regional' : 'Municipalidad Provincial'}
          </span>
          <span class="font-monospace text-muted">ID: <code>${escapeHtml(entity.entity_id)}</code></span>
        </div>
        <h1 class="h3 mb-2 text-dark">${escapeHtml(entity.official_name)}</h1>
        <div class="row g-2 small text-muted mt-2">
          <div class="col-6 col-md-3">RUC Oficial: <strong class="text-dark font-monospace">${escapeHtml(entity.ruc)}</strong></div>
          <div class="col-6 col-md-3">Provincia: <strong class="text-dark">${escapeHtml(entity.province || 'Regional')}</strong></div>
          <div class="col-6 col-md-3">Departamento: <strong class="text-dark">${escapeHtml(entity.department)}</strong></div>
          <div class="col-6 col-md-3">Verificado: <strong class="text-dark font-monospace">${escapeHtml(formatDateTime(entity.verified_at))}</strong></div>
        </div>
      </div>

      <!-- Alertas Publicadas de esta Entidad -->
      <div class="card border-0 shadow-sm bg-body-surface p-4 mb-4">
        <h2 class="h5 mb-3">Alertas Civicas Publicadas (${entAlerts.length})</h2>
        ${entAlerts.length === 0 ? `
          <div class="alert alert-success py-2 px-3 mb-0 small">
            No se registran alertas civicas publicadas para esta entidad en el periodo fiscal activo.
          </div>
        ` : `
          <div class="row g-3">
            ${entAlerts.map(a => `
              <div class="col-12 col-md-6">
                <div class="card border-start border-4 border-warning h-100">
                  <div class="card-body p-3">
                    <span class="badge bg-warning text-dark font-monospace mb-2">${escapeHtml(a.alert_id)}</span>
                    <p class="small text-secondary mb-2">${escapeHtml(a.review_notes || 'Alerta validada por revisor humano')}</p>
                    <button type="button" class="btn btn-sm btn-outline-primary btn-open-explicabilidad" data-alert-id="${escapeHtml(a.alert_id)}">
                      Ver Explicabilidad Art. 15
                    </button>
                  </div>
                </div>
              </div>
            `).join('')}
          </div>
        `}
      </div>

      <!-- Ejecucion Presupuestal MEF (PIM vs Devengado) -->
      <div class="card border-0 shadow-sm bg-body-surface p-4 mb-4">
        <h2 class="h5 mb-3">Ejecucion Presupuestal MEF CKAN DataStore</h2>
        <div class="table-responsive">
          <table class="table table-sm table-bordered align-middle mb-0">
            <thead class="table-light small">
              <tr>
                <th scope="col">Ano Fiscal</th>
                <th scope="col">Categoria Presupuestal</th>
                <th scope="col" class="text-end">PIM (Presupuesto Modificado)</th>
                <th scope="col" class="text-end">Devengado (Ejecutado)</th>
                <th scope="col" class="text-end">% Avance</th>
              </tr>
            </thead>
            <tbody>
              ${budgetRows || '<tr><td colspan="5" class="text-center text-muted py-3">Sin registros presupuestales MEF sincronizados aun.</td></tr>'}
            </tbody>
          </table>
        </div>
      </div>

      <!-- Contrataciones SEACE OCDS -->
      <div class="card border-0 shadow-sm bg-body-surface p-4">
        <h2 class="h5 mb-3">Contrataciones Publicas SEACE OCDS (${entProcs.length})</h2>
        <div class="table-responsive">
          <table class="table table-sm table-hover align-middle mb-0">
            <thead class="table-light small">
              <tr>
                <th scope="col">OCID</th>
                <th scope="col">Objeto del Contrato</th>
                <th scope="col">Modalidad</th>
                <th scope="col" class="text-end">Monto Adjudicado</th>
                <th scope="col">Proveedor Adjudicado</th>
                <th scope="col">Evidencia</th>
              </tr>
            </thead>
            <tbody>
              ${procRows || '<tr><td colspan="6" class="text-center text-muted py-3">Sin contrataciones SEACE registradas para esta entidad.</td></tr>'}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  `;
}

/**
 * 5. Vista Explorador de Alertas Publicadas (#/alertas)
 */
export function renderAlertasView() {
  const { alerts, entities, filters, plainLanguageMode } = store.getState();

  const entityMap = new Map(entities.map(e => [e.entity_id, e]));

  const alertsList = alerts.map(a => {
    const ent = entityMap.get(a.entity_id);
    return `
      <div class="card mb-3 border shadow-sm" id="alert-card-${escapeHtml(a.alert_id)}">
        <div class="card-body p-4">
          <div class="d-flex justify-content-between align-items-center flex-wrap gap-2 mb-2">
            <div>
              <span class="badge bg-warning text-dark font-monospace me-2">${escapeHtml(a.alert_id)}</span>
              <span class="badge bg-success">Revision Humana Aprobada (Art. 14)</span>
            </div>
            <span class="small text-muted font-monospace">${escapeHtml(formatDateTime(a.published_at || a.reviewed_at))}</span>
          </div>

          <h2 class="h5 text-primary mb-1">
            <a href="#/alerta?id=${escapeHtml(a.alert_id)}" class="text-decoration-none">
              ${escapeHtml(ent ? ent.official_name : 'Entidad Fiscalizada')}
            </a>
          </h2>

          <div class="small text-muted mb-3">
            Provincia: <strong>${escapeHtml(ent ? (ent.province || 'Regional') : '-')}</strong> |
            RUC: <code class="font-monospace">${escapeHtml(ent ? ent.ruc : '-')}</code>
          </div>

          <div class="p-3 border rounded bg-body-subtle mb-3">
            <span class="small fw-bold text-secondary d-block mb-1">Hallazgo Verificado por Revisor Humano:</span>
            <p class="small text-dark mb-0">${escapeHtml(a.review_notes || 'Hallazgo corroborado con datos de contrataciones SEACE y MEF.')}</p>
          </div>

          <div class="d-flex justify-content-between align-items-center flex-wrap gap-2">
            <div class="d-flex gap-2">
              <button type="button" class="btn btn-sm btn-primary btn-open-explicabilidad" data-alert-id="${escapeHtml(a.alert_id)}">
                Ficha de Explicabilidad (Art. 15)
              </button>
              <a href="#/alerta?id=${escapeHtml(a.alert_id)}" class="btn btn-sm btn-outline-secondary">
                Ver Ficha Individual
              </a>
            </div>
            <span class="small text-muted">Revisado nominalmente por: <code>${escapeHtml(a.reviewed_by)}</code></span>
          </div>
        </div>
      </div>
    `;
  }).join('');

  return `
    <div class="alertas-view">
      <div class="d-flex justify-content-between align-items-center flex-wrap gap-2 mb-3">
        <div>
          <h1 class="h3 mb-1">Explorador de Alertas Civicas Publicadas</h1>
          <p class="text-secondary small mb-0">Solo se muestran alertas evaluadas y aprobadas por un revisor humano nominal (Art. 14 de la Constitucion SDD).</p>
        </div>
        <div class="d-flex gap-2">
          <button type="button" class="btn btn-outline-success btn-sm" id="btn-export-alerts-csv">
            Exportar Alertas a CSV (CU1)
          </button>
          <button type="button" class="btn btn-outline-secondary btn-sm" id="btn-toggle-plain-lang">
            ${plainLanguageMode ? 'Modo Tecnico' : 'Modo Lenguaje Claro (CU4)'}
          </button>
        </div>
      </div>

      <!-- Descargo Legal General -->
      <div class="alert alert-secondary py-2 px-3 mb-4 small border">
        <strong>Aviso Legal Obligatorio:</strong> ${escapeHtml(STANDARD_ALERT_DISCLAIMER)}
      </div>

      ${alerts.length === 0 ? renderEmptyState('No hay alertas publicadas', 'Todas las anomalias se encuentran en proceso de evaluacion o fueron desestimadas.', 'Ver contrataciones', '#/contrataciones') : alertsList}
    </div>
  `;
}

/**
 * 6. Vista Detalle de Alerta Individual (#/alerta?id=...)
 */
export function renderAlertaDetalleView(alertId) {
  const { alerts, entities, redFlags, procurements } = store.getState();
  const alert = alerts.find(a => a.alert_id === alertId);

  if (!alert) {
    return renderEmptyState('Alerta no encontrada', `No se encontro la alerta con identificador ${alertId}.`, 'Volver al explorador', '#/alertas');
  }

  const entity = entities.find(e => e.entity_id === alert.entity_id);
  const flags = redFlags.filter(rf => (alert.red_flag_ids || []).includes(rf.red_flag_id));

  return `
    <div class="alerta-detalle-view">
      <nav aria-label="breadcrumb" class="mb-3">
        <ol class="breadcrumb small">
          <li class="breadcrumb-item"><a href="#/inicio">Inicio</a></li>
          <li class="breadcrumb-item"><a href="#/alertas">Alertas</a></li>
          <li class="breadcrumb-item active" aria-current="page">${escapeHtml(alert.alert_id)}</li>
        </ol>
      </nav>

      <!-- Boton de apertura de modal completo -->
      <div class="d-flex justify-content-between align-items-center mb-3">
        <h1 class="h4 mb-0">Ficha Explicable de Alerta Civica</h1>
        <button type="button" class="btn btn-sm btn-outline-primary btn-open-explicabilidad" data-alert-id="${escapeHtml(alert.alert_id)}">
          Abrir en Ventana Modal Completa
        </button>
      </div>

      <!-- Contenido incrustado directo -->
      <div class="card border-0 shadow-sm bg-body-surface p-4">
        ${renderAlertaDetalleInline(alert, entity, flags, procurements)}
      </div>
    </div>
  `;
}

function renderAlertaDetalleInline(alert, entity, redFlags, procurements) {
  // Desglose de los 6 elementos del Articulo 15
  return `
    <div class="alert-inline-detail">
      <div class="bg-body-subtle p-3 rounded mb-4">
        <div class="d-flex justify-content-between align-items-center flex-wrap gap-2 mb-2">
          <span class="badge bg-warning text-dark font-monospace px-3 py-2 fs-6">${escapeHtml(alert.alert_id)}</span>
          <span class="small text-muted">Publicado: ${escapeHtml(formatDateTime(alert.published_at || alert.reviewed_at))}</span>
        </div>
        <h2 class="h5 mb-1">${escapeHtml(entity ? entity.official_name : 'Entidad Fiscalizada')}</h2>
        <div class="small text-muted">
          Provincia: <strong>${escapeHtml(entity ? (entity.province || 'Regional') : '-')}</strong> |
          RUC: <code class="font-monospace">${escapeHtml(entity ? entity.ruc : '-')}</code>
        </div>
      </div>

      <!-- Revisor Humano Nominal -->
      <div class="card border-info mb-4">
        <div class="card-header bg-info-subtle text-info-emphasis py-2">
          <strong class="small">Trazabilidad Humana Nominal (Articulo 14 y 15)</strong>
        </div>
        <div class="card-body py-3">
          <div class="row g-2 small">
            <div class="col-12 col-md-6">
              <span class="text-muted">Revisor Nominal Verificado:</span>
              <div class="fw-bold text-dark font-monospace">${escapeHtml(alert.reviewed_by)}</div>
            </div>
            <div class="col-12 col-md-6">
              <span class="text-muted">Fecha y Hora de Evaluacion:</span>
              <div class="fw-bold text-dark font-monospace">${escapeHtml(formatDateTime(alert.reviewed_at))}</div>
            </div>
            ${alert.review_notes ? `
              <div class="col-12 mt-2 pt-2 border-top">
                <span class="text-muted d-block">Nota de Justificacion del Revisor:</span>
                <p class="mb-0 text-dark fst-italic">"${escapeHtml(alert.review_notes)}"</p>
              </div>
            ` : ''}
          </div>
        </div>
      </div>

      <!-- Banderas y Formulas -->
      <h3 class="h6 text-uppercase text-muted fw-bold mb-3">Banderas Tecnicas Vinculadas (${redFlags.length})</h3>
      ${redFlags.map((rf, idx) => {
        const ind = CANONICAL_INDICATORS[rf.indicator_code] || {
          name: rf.indicator_code,
          formula_description: rf.formula_description,
          default_threshold: rf.threshold,
          unit: ''
        };
        return `
          <div class="card mb-3 border-start border-4 border-warning">
            <div class="card-body p-3">
              <div class="d-flex justify-content-between align-items-center mb-2">
                <span class="badge bg-secondary font-monospace">Bandera ${idx + 1}: ${escapeHtml(rf.red_flag_id)}</span>
                <span class="small text-muted font-monospace">Fuente: ${escapeHtml(rf.evidence_source)}</span>
              </div>
              <h4 class="h6 text-primary mb-2">${escapeHtml(ind.name)}</h4>
              <div class="row g-2 mb-2 small">
                <div class="col-12 col-md-6">
                  <span class="text-muted d-block">1. Formula Algoritmica:</span>
                  <code class="text-break">${escapeHtml(rf.formula_description)}</code>
                </div>
                <div class="col-6 col-md-3">
                  <span class="text-muted d-block">2. Umbral:</span>
                  <strong class="font-monospace">${escapeHtml(String(rf.threshold))} ${escapeHtml(ind.unit || '')}</strong>
                </div>
                <div class="col-6 col-md-3">
                  <span class="text-muted d-block">3. Valor Observado:</span>
                  <strong class="font-monospace text-danger">${escapeHtml(String(rf.observed_value))} ${escapeHtml(ind.unit || '')}</strong>
                </div>
              </div>
              <div class="small text-muted">
                Fecha corte de evidencia: <strong class="font-monospace">${escapeHtml(formatDateTime(rf.evidence_retrieved_at))}</strong>
              </div>
            </div>
          </div>
        `;
      }).join('')}

      <div class="alert alert-secondary py-2 px-3 small border mt-4">
        <strong>Descargo Legal Constitucional Obligatorio:</strong> ${escapeHtml(alert.disclaimer || STANDARD_ALERT_DISCLAIMER)}
      </div>
    </div>
  `;
}

/**
 * 7. Vista Buscador de Contratos OCDS SEACE (#/contrataciones)
 */
export function renderContratacionesView() {
  const { procurements, entities, filters } = store.getState();

  const entityMap = new Map(entities.map(e => [e.entity_id, e]));

  const rows = procurements.map(p => {
    const ent = entityMap.get(p.entity_id);
    return `
      <tr>
        <td class="font-monospace small">
          <a href="#/contrato?id=${encodeURIComponent(p.ocid)}" class="text-decoration-none">
            <code>${escapeHtml(p.ocid)}</code>
          </a>
        </td>
        <td class="small">
          <strong>${escapeHtml(ent ? ent.official_name : 'Entidad')}</strong>
          <div class="text-muted">${escapeHtml(ent ? (ent.province || 'Regional') : '-')}</div>
        </td>
        <td class="small text-break" style="max-width: 280px;">${escapeHtml(p.title)}</td>
        <td class="small">${escapeHtml(p.procurement_method || '-')}</td>
        <td class="font-monospace small text-end fw-bold">S/ ${Number(p.awarded_amount || 0).toLocaleString('es-PE', { minimumFractionDigits: 2 })}</td>
        <td class="small text-truncate" style="max-width: 180px;">
          ${escapeHtml(p.supplier_name || 'No consignado')}
          ${p.supplier_ruc ? `<div class="text-muted font-monospace">RUC: ${escapeHtml(p.supplier_ruc)}</div>` : ''}
        </td>
        <td class="text-center">
          <button type="button" class="btn btn-sm btn-outline-secondary py-0 px-2 btn-open-raw-payload" data-proc-id="${escapeHtml(p.procurement_id)}">
            JSON
          </button>
        </td>
      </tr>
    `;
  }).join('');

  return `
    <div class="contrataciones-view">
      <div class="d-flex justify-content-between align-items-center flex-wrap gap-2 mb-3">
        <div>
          <h1 class="h3 mb-1">Explorador de Contrataciones SEACE OCDS</h1>
          <p class="text-secondary small mb-0">Procesos de contratacion publica capturados bajo el Open Contracting Data Standard (Art. 10).</p>
        </div>
        <button type="button" class="btn btn-outline-success btn-sm" id="btn-export-procurements-csv">
          Exportar Contratos a CSV (CU1)
        </button>
      </div>

      <!-- Buscador y Tabla -->
      <div class="card border-0 shadow-sm bg-body-surface mb-4">
        <div class="table-responsive">
          <table class="table table-hover table-striped align-middle mb-0">
            <thead class="table-dark small">
              <tr>
                <th scope="col">OCID</th>
                <th scope="col">Entidad Compradora</th>
                <th scope="col">Objeto del Contrato</th>
                <th scope="col">Modalidad</th>
                <th scope="col" class="text-end">Monto Adjudicado</th>
                <th scope="col">Proveedor</th>
                <th scope="col" class="text-center">Payload Crudo</th>
              </tr>
            </thead>
            <tbody>
              ${rows.length > 0 ? rows : '<tr><td colspan="7" class="text-center py-4 text-muted">No se encontraron contrataciones registradas.</td></tr>'}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  `;
}

/**
 * 8. Vista Ficha Individual de Contrato (#/contrato?id=...)
 */
export function renderContratoDetalleView(ocid) {
  const { procurements, entities, alerts } = store.getState();
  const proc = procurements.find(p => p.ocid === ocid || p.procurement_id === ocid);

  if (!proc) {
    return renderEmptyState('Contrato no encontrado', `No se encontro el contrato con OCID ${ocid}.`, 'Ver contrataciones', '#/contrataciones');
  }

  const ent = entities.find(e => e.entity_id === proc.entity_id);

  return `
    <div class="contrato-detalle-view">
      <nav aria-label="breadcrumb" class="mb-3">
        <ol class="breadcrumb small">
          <li class="breadcrumb-item"><a href="#/inicio">Inicio</a></li>
          <li class="breadcrumb-item"><a href="#/contrataciones">Contrataciones</a></li>
          <li class="breadcrumb-item active" aria-current="page">${escapeHtml(proc.ocid)}</li>
        </ol>
      </nav>

      <div class="card border-0 shadow-sm bg-body-surface p-4 mb-4">
        <div class="d-flex justify-content-between align-items-center flex-wrap gap-2 mb-2">
          <span class="badge bg-secondary font-monospace px-3 py-1">OCID: ${escapeHtml(proc.ocid)}</span>
          <button type="button" class="btn btn-sm btn-outline-primary btn-open-raw-payload" data-proc-id="${escapeHtml(proc.procurement_id)}">
            Ver Registro JSON Original (Art. 10)
          </button>
        </div>
        <h1 class="h4 mb-2">${escapeHtml(proc.title)}</h1>
        <p class="text-secondary mb-3">Entidad: <strong>${escapeHtml(ent ? ent.official_name : 'Entidad')}</strong></p>

        <div class="row g-3 p-3 border rounded bg-body-subtle small mb-3">
          <div class="col-6 col-md-3">
            <span class="text-muted d-block">Modalidad de Seleccion:</span>
            <strong>${escapeHtml(proc.procurement_method || 'No especificada')}</strong>
          </div>
          <div class="col-6 col-md-3">
            <span class="text-muted d-block">Monto Adjudicado:</span>
            <strong class="font-monospace">S/ ${Number(proc.awarded_amount || 0).toLocaleString('es-PE', { minimumFractionDigits: 2 })}</strong>
          </div>
          <div class="col-6 col-md-3">
            <span class="text-muted d-block">Monto Ejecutado / Liquidado:</span>
            <strong class="font-monospace">S/ ${Number(proc.executed_amount || proc.awarded_amount || 0).toLocaleString('es-PE', { minimumFractionDigits: 2 })}</strong>
          </div>
          <div class="col-6 col-md-3">
            <span class="text-muted d-block">Numero de Postores:</span>
            <strong class="font-monospace">${escapeHtml(String(proc.number_of_bidders || '-'))}</strong>
          </div>
          <div class="col-12 col-md-6">
            <span class="text-muted d-block">Proveedor Adjudicado:</span>
            <strong>${escapeHtml(proc.supplier_name || 'No consignado')}</strong>
            ${proc.supplier_ruc ? `(RUC: <code class="font-monospace">${escapeHtml(proc.supplier_ruc)}</code>)` : ''}
          </div>
          <div class="col-12 col-md-6">
            <span class="text-muted d-block">Fecha y Hora de Extraccion (SEACE):</span>
            <strong class="font-monospace">${escapeHtml(formatDateTime(proc.retrieved_at))}</strong>
          </div>
        </div>
      </div>
    </div>
  `;
}

/**
 * 9. Vista Monitor Presupuestal MEF (#/presupuesto)
 */
export function renderPresupuestoView() {
  const { budgetExecutions, entities } = store.getState();
  const entityMap = new Map(entities.map(e => [e.entity_id, e]));

  const rows = budgetExecutions.map(b => {
    const ent = entityMap.get(b.entity_id);
    const pim = Number(b.budgeted_amount || 0);
    const dev = Number(b.executed_amount || 0);
    const pct = pim > 0 ? ((dev / pim) * 100).toFixed(1) : '0.0';

    return `
      <tr>
        <td class="font-monospace small"><strong>${b.fiscal_year}</strong></td>
        <td class="small">
          <a href="#/entidad?id=${escapeHtml(b.entity_id)}" class="text-decoration-none">
            <strong>${escapeHtml(ent ? ent.official_name : 'Entidad')}</strong>
          </a>
          <div class="text-muted small">${escapeHtml(ent ? (ent.province || 'Regional') : '-')}</div>
        </td>
        <td class="small">${escapeHtml(b.budget_category || 'Gasto General')}</td>
        <td class="font-monospace small text-end">S/ ${pim.toLocaleString('es-PE', { minimumFractionDigits: 2 })}</td>
        <td class="font-monospace small text-end">S/ ${dev.toLocaleString('es-PE', { minimumFractionDigits: 2 })}</td>
        <td class="font-monospace small text-end fw-bold ${Number(pct) > 70 ? 'text-success' : 'text-warning-emphasis'}">
          ${pct}%
        </td>
      </tr>
    `;
  }).join('');

  return `
    <div class="presupuesto-view">
      <div class="d-flex justify-content-between align-items-center flex-wrap gap-2 mb-3">
        <div>
          <h1 class="h3 mb-1">Monitor de Ejecucion Presupuestal MEF</h1>
          <p class="text-secondary small mb-0">Seguimiento PIM vs. Devengado desde el Portal de Datos Abiertos MEF CKAN DataStore (Art. 10).</p>
        </div>
        <button type="button" class="btn btn-outline-success btn-sm" id="btn-export-budget-csv">
          Exportar Presupuesto a CSV (CU1)
        </button>
      </div>

      <div class="card border-0 shadow-sm bg-body-surface mb-4">
        <div class="table-responsive">
          <table class="table table-hover table-striped align-middle mb-0">
            <thead class="table-dark small">
              <tr>
                <th scope="col">Ano</th>
                <th scope="col">Entidad</th>
                <th scope="col">Categoria Presupuestal</th>
                <th scope="col" class="text-end">PIM (Asignado)</th>
                <th scope="col" class="text-end">Devengado (Ejecutado)</th>
                <th scope="col" class="text-end">% Avance</th>
              </tr>
            </thead>
            <tbody>
              ${rows.length > 0 ? rows : '<tr><td colspan="6" class="text-center py-4 text-muted">No se registran datos presupuestales.</td></tr>'}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  `;
}

/**
 * 10. Vista Transparencia y Metodologia (#/transparencia)
 */
export function renderTransparenciaView() {
  const indicatorsList = Object.values(CANONICAL_INDICATORS).map(ind => `
    <div class="card mb-3 border-start border-4 border-primary">
      <div class="card-body p-3">
        <h3 class="h6 text-primary mb-1">${escapeHtml(ind.name)} (<code>${escapeHtml(ind.code)}</code>)</h3>
        <p class="small text-secondary mb-2">${escapeHtml(ind.plain_description)}</p>
        <div class="small text-muted">
          Formula oficial: <code>${escapeHtml(ind.formula_description)}</code> |
          Umbral de corte: <strong>${escapeHtml(String(ind.default_threshold))} ${escapeHtml(ind.unit)}</strong>
        </div>
      </div>
    </div>
  `).join('');

  return `
    <div class="transparencia-view max-w-900 mx-auto">
      <div class="mb-4">
        <span class="badge bg-primary-subtle text-primary-emphasis border mb-2">Transparencia Activa y Metodologia</span>
        <h1 class="h3 mb-2">Constitucion Tecnica y Etica del Observatorio</h1>
        <p class="text-secondary">
          Cajamarca Qhaway opera bajo los 19 articulos de la Constitucion SDD, garantizando verificabilidad, explicabilidad completa y proteccion de derechos ciudadanos.
        </p>
      </div>

      <!-- Diagrama de Flujo de Arquitectura -->
      <div class="card border-0 shadow-sm bg-body-surface p-4 mb-4 text-center">
        <h2 class="h5 mb-3 text-start">Arquitectura de Datos y Separacion de Deteccion / Publicacion</h2>
        <img src="media/architecture-flow.svg" alt="Diagrama de flujo de datos Cajamarca Qhaway" class="img-fluid mx-auto" style="max-height: 280px;">
        <p class="small text-muted mt-2 mb-0">Flujo inmutable: Fuentes oficiales &rarr; Deteccion tecnica interna (RedFlag) &rarr; Evaluacion humana (Art. 14) &rarr; Alerta publica explicable (Art. 15).</p>
      </div>

      <!-- Catalogo de los 5 Indicadores Canonicos -->
      <div class="card border-0 shadow-sm bg-body-surface p-4 mb-4">
        <h2 class="h5 mb-3">Catalogo Oficial de los 5 Indicadores Algoritmicos (Fase 1)</h2>
        ${indicatorsList}
      </div>

      <!-- Estado Reservado de Declaraciones Juradas de Intereses (Articulo 17) -->
      <div class="card border-warning mb-4 shadow-sm">
        <div class="card-header bg-warning-subtle text-warning-emphasis py-2">
          <strong class="h6 mb-0">Articulo 17: Estado de las Declaraciones Juradas de Intereses (DJI)</strong>
        </div>
        <div class="card-body p-3">
          <p class="small text-dark mb-2">
            Conforme a la Constitucion del Proyecto y el principio de legalidad bajo la Ley 29733 (Ley de Proteccion de Datos Personales):
          </p>
          <ul class="small text-secondary ps-3 mb-2">
            <li>La fuente de Declaraciones Juradas de Intereses se mantiene en <strong>ESTADO RESERVADO / EN EVALUACION LEGAL ESTRICTA</strong> durante la Fase 1.</li>
            <li>No se realiza ningun cruce automatizado sobre personas naturales ni funcionarios publicos por nombre propio.</li>
            <li>Queda expresamente vetado cualquier indice, ranking o scoring de reputacion individual (Articulo 16).</li>
          </ul>
        </div>
      </div>

      <!-- Centro de Descargas Masivas (CU1) -->
      <div class="card border-0 shadow-sm bg-body-surface p-4">
        <h2 class="h5 mb-3">Centro de Descarga Masiva de Datos Verificados (CU1)</h2>
        <p class="small text-muted mb-3">Archivos con codificacion UTF-8 con BOM y suma de comprobacion SHA-256 calculada al momento de la descarga:</p>
        <div class="d-flex gap-2 flex-wrap">
          <button type="button" class="btn btn-outline-primary btn-sm" id="btn-dl-entities-csv">Descargar 14 Entidades (CSV)</button>
          <button type="button" class="btn btn-outline-primary btn-sm" id="btn-dl-procurements-csv">Descargar Contratos SEACE (CSV)</button>
          <button type="button" class="btn btn-outline-primary btn-sm" id="btn-dl-budget-csv">Descargar Presupuesto MEF (CSV)</button>
          <button type="button" class="btn btn-outline-primary btn-sm" id="btn-dl-alerts-csv">Descargar Alertas Publicadas (CSV)</button>
        </div>
      </div>
    </div>
  `;
}

/**
 * 11. Vista Acerca del Observatorio (#/acerca)
 */
export function renderAcercaView() {
  return `
    <div class="acerca-view max-w-800 mx-auto">
      <div class="card border-0 shadow-sm bg-body-surface p-4 mb-4">
        <h1 class="h3 mb-3 text-dark">Acerca de Cajamarca Qhaway</h1>
        <p class="lead text-secondary">
          "Qhaway" es una voz quechua que significa observar, cuidar y vigilar con atencion y respeto.
        </p>
        <p class="small text-secondary">
          Cajamarca Qhaway nacio como una iniciativa civica de tecnologia ciudadana y periodismo de datos para cerrar la brecha de informacion publica en el departamento de Cajamarca, articulando esfuerzos con organizaciones de la sociedad civil local como Proetica, el Grupo Propuesta Ciudadana, GRUFIDES y redes de comunicacion radial rural (RCR).
        </p>
        <h2 class="h5 text-primary mt-4 mb-2">Nuestros Pilares Innegociables</h2>
        <ul class="small text-secondary ps-3 mb-4">
          <li class="mb-2"><strong>Fuentes Primarias y Verificables:</strong> Datos crudos de SEACE OCDS y MEF CKAN DataStore.</li>
          <li class="mb-2"><strong>Cero Juicios Automatizados:</strong> Ningun algoritmo condena a nadie; la tecnologia solo alerta desvios estadisticos para que los ciudadanos y la prensa contrasten los hechos.</li>
          <li class="mb-2"><strong>Acceso Inclusivo Rural:</strong> Optimizacion para telefonos basicos y conexiones lentas (2G/3G) en comunidades altoandinas.</li>
        </ul>
        <div class="alert alert-light border py-2 px-3 small text-muted">
          Contacto institucional e investigacion civica: <code>observatorio@cajamarca-qhaway.pe</code>
        </div>
      </div>
    </div>
  `;
}

/**
 * Configura los eventos interactivos de las vistas públicas
 */
export function setupViewEvents() {
  const { alerts, entities, procurements, budgetExecutions } = store.getState();

  // Exportadores CSV (CU1)
  const btnExportAlerts = document.getElementById('btn-export-alerts-csv') || document.getElementById('btn-dl-alerts-csv');
  if (btnExportAlerts) {
    btnExportAlerts.addEventListener('click', async () => {
      await exportAlertsCsv(alerts, entities);
    });
  }

  const btnExportProc = document.getElementById('btn-export-procurements-csv') || document.getElementById('btn-dl-procurements-csv');
  if (btnExportProc) {
    btnExportProc.addEventListener('click', async () => {
      await exportProcurementsCsv(procurements, entities);
    });
  }

  const btnExportBudg = document.getElementById('btn-export-budget-csv') || document.getElementById('btn-dl-budget-csv');
  if (btnExportBudg) {
    btnExportBudg.addEventListener('click', async () => {
      await exportBudgetExecutionsCsv(budgetExecutions, entities);
    });
  }

  const btnExportEnt = document.getElementById('btn-export-entities-csv') || document.getElementById('btn-dl-entities-csv');
  if (btnExportEnt) {
    btnExportEnt.addEventListener('click', async () => {
      await exportEntitiesCsv(entities);
    });
  }

  // Selector de provincia en directorio de entidades
  const provSelect = document.getElementById('filter-provincia-select');
  if (provSelect) {
    provSelect.addEventListener('change', (e) => {
      store.setFilter('province', e.target.value);
    });
  }

  // Boton toggle Lenguaje Claro (CU4)
  const btnPlainLang = document.getElementById('btn-toggle-plain-lang');
  if (btnPlainLang) {
    btnPlainLang.addEventListener('click', () => {
      store.togglePlainLanguageMode();
    });
  }

  // Modales de explicabilidad (Art. 15)
  const expButtons = document.querySelectorAll('.btn-open-explicabilidad');
  expButtons.forEach(btn => {
    btn.addEventListener('click', (e) => {
      const alertId = e.currentTarget.getAttribute('data-alert-id');
      if (alertId) {
        openExplicabilidadModal(alertId);
      }
    });
  });

  // Modales de payload JSON (Art. 10)
  const rawButtons = document.querySelectorAll('.btn-open-raw-payload');
  rawButtons.forEach(btn => {
    btn.addEventListener('click', (e) => {
      const procId = e.currentTarget.getAttribute('data-proc-id');
      const proc = procurements.find(p => p.procurement_id === procId);
      if (proc) {
        openRawPayloadModal(proc.raw_payload || proc, `Contratacion SEACE: ${proc.ocid}`);
      }
    });
  });
}
