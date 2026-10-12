/**
 * explicabilidad.js: Ficha de Explicabilidad Algoritmica (Articulo 15)
 * y Traductor a Lenguaje Claro Ciudadano (CU4, CU2, Art. 10)
 *
 * Restricciones:
 * - Antislop R-02: Cero rayas em-dash en todo el archivo.
 * - Desglose de los 6 elementos del Articulo 15.
 * - Sin calificar ni crear rankings de personas por nombre propio (Art. 16).
 */

import { CANONICAL_INDICATORS, STANDARD_ALERT_DISCLAIMER } from './config.js';
import { store } from './state.js';

/**
 * Escapa cadenas para prevenir XSS
 */
export function escapeHtml(str) {
  if (str === null || str === undefined) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

/**
 * Formatea fechas a formato legible UTC / Peru
 */
export function formatDateTime(isoString) {
  if (!isoString) return 'No registrado';
  try {
    const d = new Date(isoString);
    if (isNaN(d.getTime())) return String(isoString);
    return d.toLocaleString('es-PE', {
      year: 'numeric',
      month: 'short',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      timeZone: 'UTC'
    }) + ' UTC';
  } catch {
    return String(isoString);
  }
}

/**
 * Traduce un indicador a explicacion en Lenguaje Claro Ciudadano (CU4)
 */
export function translateToPlainLanguage(indicatorCode, observedValue, threshold) {
  const meta = CANONICAL_INDICATORS[indicatorCode] || {
    plain_title: 'Hallazgo de riesgo detectado',
    plain_description: 'El algoritmo identifico una variacion inusual en los registros oficiales.',
    recommendation: 'Revisar la documentacion de sustento en las fuentes oficiales.'
  };

  let specificNote = '';
  if (indicatorCode === 'single-bidder') {
    specificNote = `La contratacion se entrego con solo ${observedValue} postor participante, cuando el estandar exige competencia entre multiples ofertas.`;
  } else if (indicatorCode === 'execution-overrun' || indicatorCode === 'cost-overrun') {
    const pct = ((Number(observedValue) - 1) * 100).toFixed(1);
    specificNote = `El costo final o devengado aumento en un ${pct}% sobre el presupuesto pactado (el umbral de tolerancia es de 10%).`;
  } else if (indicatorCode === 'short-tender-window' || indicatorCode === 'short-bidding-window') {
    specificNote = `Se dio solo ${observedValue} dias para postular, por debajo de los 5 dias recomendados para que haya transparencia.`;
  } else if (indicatorCode === 'contract-concentration' || indicatorCode === 'high-concentration-supplier') {
    const pct = (Number(observedValue) * 100).toFixed(1);
    specificNote = `Este proveedor concentra el ${pct}% de los contratos de la entidad, superando el limite del 40%.`;
  } else if (indicatorCode === 'direct-award-threshold') {
    specificNote = `El monto adjudicado directamente fue de S/ ${Number(observedValue).toLocaleString('es-PE')}, bordeando el umbral de S/ ${Number(threshold).toLocaleString('es-PE')}.`;
  } else if (indicatorCode === 'direct-administration-equipment-rent') {
    specificNote = `Se detectaron ${observedValue} ocurrencia(s) de cobro o facturacion cruzada de maquinaria en administracion directa.`;
  } else if (indicatorCode === 'contract-splitting-orders') {
    specificNote = `Se emitieron ${observedValue} ordenes consecutivas menores a 8 UIT al mismo proveedor (umbral: ${threshold} ordenes).`;
  }

  return {
    title: meta.plain_title,
    summary: meta.plain_description,
    specificNote,
    recommendation: meta.recommendation
  };
}

/**
 * Genera texto breve para compartir por SMS o WhatsApp (CU2)
 */
export function generateShareSummary(alert, entity, redFlags) {
  const entityName = entity ? entity.official_name : 'Entidad de Cajamarca';
  const url = `${window.location.origin}${window.location.pathname}#/alerta?id=${alert.alert_id}`;
  const flagsCount = redFlags.length;
  const firstFlag = redFlags[0];
  const flagCode = firstFlag ? (CANONICAL_INDICATORS[firstFlag.indicator_code]?.name || firstFlag.indicator_code) : 'Riesgo detectado';

  return `*Cajamarca Qhaway | Alerta Civica*
Entidad: ${entityName}
Indicador principal: ${flagCode}
Banderas tecnicas asociadas: ${flagsCount}
Fecha revision humana: ${formatDateTime(alert.reviewed_at)}
Revisado por: ${alert.reviewed_by}
Enlace verificado: ${url}

Aviso: ${STANDARD_ALERT_DISCLAIMER}`;
}

/**
 * Renderiza el desglose completo de una Alerta y sus Banderas Rojas (Articulo 15)
 */
export function renderExplicabilidadModalContent(alert, entity, redFlags, procurements) {
  const flagsHtml = redFlags.map((rf, idx) => {
    const indMeta = CANONICAL_INDICATORS[rf.indicator_code] || {
      name: rf.indicator_code,
      formula_description: rf.formula_description,
      default_threshold: rf.threshold,
      unit: 'unidad'
    };

    const plain = translateToPlainLanguage(rf.indicator_code, rf.observed_value, rf.threshold);

    // Buscar contratos vinculados a esta bandera
    const matchedProcs = procurements.filter(p => (rf.procurement_ids || []).includes(p.procurement_id));
    const procsList = matchedProcs.map(p => `
      <div class="procurement-ref-item p-2 mb-2 border rounded bg-light">
        <div class="d-flex justify-content-between align-items-center">
          <strong class="small font-monospace">${escapeHtml(p.ocid)}</strong>
          <button type="button" class="btn btn-sm btn-outline-secondary py-0 px-2 btn-open-raw-payload" data-proc-id="${escapeHtml(p.procurement_id)}">
            Ver JSON crudo (Art. 10)
          </button>
        </div>
        <div class="small text-muted text-truncate mt-1">${escapeHtml(p.title)}</div>
        <div class="small mt-1">
          <span>Adjudicado: <strong>S/ ${Number(p.awarded_amount || 0).toLocaleString('es-PE', { minimumFractionDigits: 2 })}</strong></span>
          ${p.executed_amount ? `<span class="ms-3">Ejecutado: <strong>S/ ${Number(p.executed_amount).toLocaleString('es-PE', { minimumFractionDigits: 2 })}</strong></span>` : ''}
        </div>
      </div>
    `).join('');

    return `
      <div class="card mb-3 border-start border-4 border-warning shadow-sm">
        <div class="card-header bg-body-tertiary d-flex justify-content-between align-items-center">
          <span class="badge bg-warning text-dark font-monospace">Bandera ${idx + 1}: ${escapeHtml(rf.red_flag_id)}</span>
          <span class="small text-muted">Fuente: <code>${escapeHtml(rf.evidence_source)}</code></span>
        </div>
        <div class="card-body">
          <h5 class="h6 text-primary mb-2">${escapeHtml(indMeta.name)}</h5>

          <!-- Desglose de los 6 elementos del Articulo 15 -->
          <div class="row g-2 mb-3">
            <div class="col-12 col-md-6">
              <div class="p-2 border rounded bg-body-subtle h-100">
                <span class="text-muted d-block small">1. Formula Algoritmica:</span>
                <code class="small text-break">${escapeHtml(rf.formula_description || indMeta.formula_description)}</code>
              </div>
            </div>
            <div class="col-6 col-md-3">
              <div class="p-2 border rounded bg-body-subtle h-100">
                <span class="text-muted d-block small">2. Umbral de Corte:</span>
                <strong class="font-monospace">${escapeHtml(String(rf.threshold))} ${escapeHtml(indMeta.unit || '')}</strong>
              </div>
            </div>
            <div class="col-6 col-md-3">
              <div class="p-2 border rounded bg-body-subtle h-100">
                <span class="text-muted d-block small">3. Valor Observado:</span>
                <strong class="font-monospace text-danger">${escapeHtml(String(rf.observed_value))} ${escapeHtml(indMeta.unit || '')}</strong>
              </div>
            </div>
          </div>

          <!-- Traduccion en Lenguaje Claro Ciudadano (CU4) -->
          <div class="alert alert-light border border-info-subtle py-2 px-3 mb-3">
            <div class="d-flex align-items-center gap-2 mb-1">
              <span class="badge bg-info text-dark">Lenguaje Claro Ciudadano</span>
              <strong class="small text-dark">${escapeHtml(plain.title)}</strong>
            </div>
            <p class="small text-secondary mb-1">${escapeHtml(plain.summary)}</p>
            <p class="small text-dark fw-medium mb-1">${escapeHtml(plain.specificNote)}</p>
            <p class="small text-muted mb-0"><strong>Recomendacion civica:</strong> ${escapeHtml(plain.recommendation)}</p>
          </div>

          <!-- Metadatos de evidencia oficial -->
          <div class="row g-2 small text-muted mb-2">
            <div class="col-12 col-md-6">
              <span>Fecha de corte de evidencia:</span>
              <strong class="text-dark font-monospace">${escapeHtml(formatDateTime(rf.evidence_retrieved_at))}</strong>
            </div>
            <div class="col-12 col-md-6">
              <span>Generacion de bandera tecnica:</span>
              <strong class="text-dark font-monospace">${escapeHtml(formatDateTime(rf.generated_at))}</strong>
            </div>
          </div>

          ${matchedProcs.length > 0 ? `
            <div class="mt-3">
              <h6 class="small text-uppercase text-muted fw-bold mb-2">Evidencias Contractuales SEACE Asociadas:</h6>
              ${procsList}
            </div>
          ` : ''}
        </div>
      </div>
    `;
  }).join('');

  return `
    <div class="explicabilidad-container">
      <!-- Encabezado de la Alerta -->
      <div class="bg-body-secondary p-3 rounded mb-3">
        <div class="d-flex justify-content-between align-items-center flex-wrap gap-2 mb-2">
          <span class="badge bg-primary px-3 py-2 font-monospace">Alerta ID: ${escapeHtml(alert.alert_id)}</span>
          <span class="badge bg-success">Revision Humana Aprobada (Art. 14)</span>
        </div>
        <h4 class="h5 mb-1">${escapeHtml(entity ? entity.official_name : 'Entidad Fiscalizada')}</h4>
        <div class="small text-muted">
          ${entity && entity.province ? `Provincia: <strong>${escapeHtml(entity.province)}</strong> | ` : ''}
          RUC: <code class="font-monospace">${escapeHtml(entity ? entity.ruc : 'No especificado')}</code>
        </div>
      </div>

      <!-- Trazabilidad del Revisor Humano Nominal (ADR 0005) -->
      <div class="card mb-3 border-info shadow-sm">
        <div class="card-header bg-info-subtle text-info-emphasis py-2">
          <strong class="small">Trazabilidad Humana Nominal (Articulo 14 y 15)</strong>
        </div>
        <div class="card-body py-2">
          <div class="row g-2 small">
            <div class="col-12 col-md-6">
              <span class="text-muted">Revisor Nominal Verificado:</span>
              <div class="fw-bold text-dark font-monospace">${escapeHtml(alert.reviewed_by)}</div>
            </div>
            <div class="col-12 col-md-6">
              <span class="text-muted">Fecha y Hora de Revision:</span>
              <div class="fw-bold text-dark font-monospace">${escapeHtml(formatDateTime(alert.reviewed_at))}</div>
            </div>
            ${alert.published_at ? `
              <div class="col-12">
                <span class="text-muted">Publicacion Efectiva en Plataforma:</span>
                <span class="fw-bold text-dark font-monospace ms-2">${escapeHtml(formatDateTime(alert.published_at))}</span>
              </div>
            ` : ''}
            ${alert.review_notes ? `
              <div class="col-12 mt-2 pt-2 border-top">
                <span class="text-muted d-block">Nota de Justificacion del Revisor Humano:</span>
                <p class="mb-0 text-secondary fst-italic">"${escapeHtml(alert.review_notes)}"</p>
              </div>
            ` : ''}
          </div>
        </div>
      </div>

      <!-- Listado de Banderas Rojas y Formulas -->
      <h5 class="h6 text-uppercase text-muted fw-bold mb-3">
        Banderas Rojas Evaluadas (${redFlags.length}):
      </h5>
      ${flagsHtml}

      <!-- Acciones de Difusion Comunitaria (CU2) -->
      <div class="d-flex justify-content-between align-items-center flex-wrap gap-2 p-3 border rounded bg-light mb-3">
        <div>
          <strong class="small d-block">Difusion Civica para Zonas Rurales (CU2)</strong>
          <span class="text-muted small">Genera un extracto ligero optimizado para SMS o WhatsApp.</span>
        </div>
        <button type="button" class="btn btn-outline-success btn-sm btn-copy-share-summary" id="btn-copy-summary">
          Copiar Resumen para WhatsApp / SMS
        </button>
      </div>

      <!-- Descargo Legal Constitucional Obligatorio -->
      <div class="alert alert-secondary py-2 px-3 mb-0 small border" role="note">
        <strong>Descargo Legal Obligatorio:</strong> ${escapeHtml(alert.disclaimer || STANDARD_ALERT_DISCLAIMER)}
      </div>
    </div>
  `;
}

/**
 * Abre el modal de explicabilidad algoritmica
 */
export function openExplicabilidadModal(alertId) {
  const st = store.getState();
  const alert = st.alerts.find(a => a.alert_id === alertId);
  if (!alert) {
    alert(`No se encontro la alerta con identificador ${alertId}`);
    return;
  }

  const entity = st.entities.find(e => e.entity_id === alert.entity_id);
  const redFlags = st.redFlags.filter(rf => (alert.red_flag_ids || []).includes(rf.red_flag_id));

  const modalBody = document.getElementById('modal-explicabilidad-body');
  if (modalBody) {
    modalBody.innerHTML = renderExplicabilidadModalContent(alert, entity, redFlags, st.procurements);

    // Configurar listener para boton de copiar resumen
    const btnCopySummary = modalBody.querySelector('#btn-copy-summary');
    if (btnCopySummary) {
      btnCopySummary.addEventListener('click', async () => {
        const text = generateShareSummary(alert, entity, redFlags);
        try {
          await navigator.clipboard.writeText(text);
          btnCopySummary.textContent = 'Copiado al Portapapeles!';
          setTimeout(() => {
            btnCopySummary.textContent = 'Copiar Resumen para WhatsApp / SMS';
          }, 2500);
        } catch {
          prompt('Copia manualmente este resumen:', text);
        }
      });
    }

    // Configurar listeners para ver JSON crudo de contrataciones
    const btnRawList = modalBody.querySelectorAll('.btn-open-raw-payload');
    btnRawList.forEach(btn => {
      btn.addEventListener('click', (e) => {
        const procId = e.currentTarget.getAttribute('data-proc-id');
        const proc = st.procurements.find(p => p.procurement_id === procId);
        if (proc) {
          openRawPayloadModal(proc.raw_payload || proc, `Contrato SEACE OCDS: ${proc.ocid}`);
        }
      });
    });
  }

  const modalEl = document.getElementById('modal-explicabilidad');
  if (modalEl && window.bootstrap && window.bootstrap.Modal) {
    const modalInstance = window.bootstrap.Modal.getOrCreateInstance(modalEl);
    modalInstance.show();
  }
}

/**
 * Abre el modal con el JSON crudo original (Articulo 10)
 */
export function openRawPayloadModal(payloadObj, title = 'Evidencia Original JSON') {
  const codeEl = document.getElementById('modal-raw-payload-code');
  const titleEl = document.getElementById('modal-raw-payload-title');

  if (titleEl) {
    titleEl.textContent = title;
  }

  const jsonString = JSON.stringify(payloadObj || {}, null, 2);
  if (codeEl) {
    codeEl.textContent = jsonString;
  }

  // Guardar en estado para el boton de copia global
  store.setState({ rawPayloadModalData: jsonString });

  const modalEl = document.getElementById('modal-raw-payload');
  if (modalEl && window.bootstrap && window.bootstrap.Modal) {
    const modalInstance = window.bootstrap.Modal.getOrCreateInstance(modalEl);
    modalInstance.show();
  }
}
