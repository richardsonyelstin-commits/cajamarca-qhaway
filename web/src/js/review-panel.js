/**
 * review-panel.js: Panel Interno de Revision Humana y Moderacion (005-review-panel + ADR 0005)
 * Rutas: /login, /admin/revision, /admin/revision, /admin/revision
 *
 * Restricciones:
 * - Antislop R-02: Cero rayas em-dash en todo el archivo.
 * - Prohibicion estricta de revisores genericos (admin, system, root, bot, etc.).
 * - Justificacion obligatoria al descartar banderas (CA-005-04 / CA-304-05).
 * - Proteccion de rutas no autenticadas con redireccion a /login (CA-304-03).
 */

import { GENERIC_REVIEWERS, CANONICAL_INDICATORS } from './config.js';
import { supabaseClient } from './supabase-client.js';
import { store } from './state.js';
import { closeReviewerSession } from './veedor-auth.js';
import { escapeHtml, formatDateTime } from './explicabilidad.js';

/**
 * Verifica si el usuario actual posee sesion activa de revisor humano nominal
 */
export function isAuthenticatedReviewer() {
  const session = store.getState().reviewerSession;
  if (!session || !session.email) return false;
  const norm = session.email.trim().toLowerCase();
  if (GENERIC_REVIEWERS.includes(norm)) return false;
  return true;
}

/**
 * Renderiza la pantalla de inicio de sesion (ADR 0005 Google OAuth & Sesion Nominal)
 */
export function renderLoginView() {
  return '<p>El acceso requiere una identidad acreditada.</p><a href="/login">Ingresar con Google</a>';
}

export function setupLoginEvents() {
  // La autenticacion se realiza exclusivamente en /login mediante Supabase Auth.
}

/**
 * Renderiza la barra superior de navegacion interna del panel
 */
function renderAdminSubnav(activeTab = 'revision') {
  const session = store.getState().reviewerSession;
  return `
    <div class="d-flex justify-content-between align-items-center flex-wrap gap-2 pb-3 mb-4 border-bottom">
      <div>
        <h1 class="h4 mb-0 text-dark">Panel de Revision Humana (CU5)</h1>
        <div class="small text-muted">
          Revisor activo: <strong>${escapeHtml(session?.name || 'Revisor')}</strong>
          (<code>${escapeHtml(session?.email || '')}</code> - ${escapeHtml(session?.organization || '')})
        </div>
      </div>

      <div class="d-flex align-items-center gap-2">
        <div class="btn-group btn-group-sm" role="group" aria-label="Navegacion de administracion">
          <a href="/admin/revision" class="btn ${activeTab === 'revision' ? 'btn-primary' : 'btn-outline-secondary'}">
            Banderas Rojas Pendientes
          </a>
          <a href="/admin/revision" class="btn ${activeTab === 'denuncias' ? 'btn-primary' : 'btn-outline-secondary'}">
            Moderacion de Denuncias
          </a>
          <a href="/admin/revision" class="btn ${activeTab === 'auditoria' ? 'btn-primary' : 'btn-outline-secondary'}">
            Bitacora de Auditoria
          </a>
        </div>
        <button type="button" class="btn btn-sm btn-outline-danger" id="btn-logout-reviewer">
          Cerrar Sesion
        </button>
      </div>
    </div>
  `;
}

/**
 * Renderiza la bandeja de revision de banderas rojas (/admin/revision)
 */
export function renderAdminRevisionView() {
  if (!isAuthenticatedReviewer()) {
    return `<div class="p-4 text-center">Redirigiendo a inicio de sesion...</div>`;
  }

  const { redFlags, alerts, entities, procurements } = store.getState();

  // Filtrar banderas rojas que no estan asociadas a alertas publicadas o descartadas
  const reviewedFlagIds = new Set();
  alerts.forEach(a => {
    (a.red_flag_ids || []).forEach(id => reviewedFlagIds.add(id));
  });

  const pendingFlags = redFlags.filter(rf => !reviewedFlagIds.has(rf.red_flag_id));

  const itemsHtml = pendingFlags.length === 0 ? `
    <div class="card border-0 bg-light p-4 text-center">
      <h3 class="h6 text-muted mb-1">Bandeja al dia: No hay banderas rojas pendientes</h3>
      <p class="small text-secondary mb-0">Todas las anomalias algoritmicas han sido evaluadas por los revisores humanos.</p>
    </div>
  ` : pendingFlags.map((rf, idx) => {
    const indMeta = CANONICAL_INDICATORS[rf.indicator_code] || {
      name: rf.indicator_code,
      formula_description: rf.formula_description,
      default_threshold: rf.threshold,
      unit: ''
    };

    // Identificar contrataciones
    const matchedProcs = procurements.filter(p => (rf.procurement_ids || []).includes(p.procurement_id));
    const firstProc = matchedProcs[0];
    const ent = firstProc ? entities.find(e => e.entity_id === firstProc.entity_id) : null;

    return `
      <div class="card mb-4 border shadow-sm" id="card-flag-${escapeHtml(rf.red_flag_id)}">
        <div class="card-header bg-warning-subtle text-warning-emphasis d-flex justify-content-between align-items-center flex-wrap gap-2">
          <div>
            <span class="badge bg-dark font-monospace me-2">Bandera ${idx + 1}: ${escapeHtml(rf.red_flag_id)}</span>
            <strong>${escapeHtml(indMeta.name)}</strong>
          </div>
          <span class="small font-monospace">Fuente: ${escapeHtml(rf.evidence_source)}</span>
        </div>
        <div class="card-body">
          ${ent ? `
            <div class="mb-3 p-2 border rounded bg-body-subtle">
              <strong class="text-primary">${escapeHtml(ent.official_name)}</strong>
              <div class="small text-muted">
                Provincia: ${escapeHtml(ent.province || 'Regional')} | RUC: <code>${escapeHtml(ent.ruc)}</code>
              </div>
            </div>
          ` : ''}

          <div class="row g-2 mb-3 small">
            <div class="col-12 col-md-6">
              <span class="text-muted d-block">Formula Algoritmica:</span>
              <code class="text-break">${escapeHtml(rf.formula_description)}</code>
            </div>
            <div class="col-6 col-md-3">
              <span class="text-muted d-block">Umbral:</span>
              <strong class="font-monospace">${escapeHtml(String(rf.threshold))} ${escapeHtml(indMeta.unit || '')}</strong>
            </div>
            <div class="col-6 col-md-3">
              <span class="text-muted d-block">Valor Observado:</span>
              <strong class="font-monospace text-danger">${escapeHtml(String(rf.observed_value))} ${escapeHtml(indMeta.unit || '')}</strong>
            </div>
          </div>

          ${matchedProcs.length > 0 ? `
            <div class="p-2 border rounded bg-light mb-3">
              <span class="small text-muted fw-bold d-block mb-1">Contrato OCDS Asociado:</span>
              <div class="small font-monospace">${escapeHtml(firstProc.ocid)} - ${escapeHtml(firstProc.title)}</div>
              <div class="small mt-1">
                Proveedor: <strong>${escapeHtml(firstProc.supplier_name || 'No consignado')}</strong> (RUC: ${escapeHtml(firstProc.supplier_ruc || '-')})
              </div>
            </div>
          ` : ''}

          <!-- Formulario de Decision Humana (Art. 14, CA-304-04, CA-304-05) -->
          <div class="border-top pt-3 mt-3">
            <h6 class="small fw-bold text-uppercase text-secondary mb-2">Decision Humana Explicita (Articulo 14):</h6>

            <div class="mb-3">
              <label for="notes-${escapeHtml(rf.red_flag_id)}" class="form-label small fw-semibold">
                Nota Tecnica de Justificacion <span class="text-danger">* (Obligatoria si descarta)</span>
              </label>
              <textarea
                class="form-control form-control-sm review-notes-input"
                id="notes-${escapeHtml(rf.red_flag_id)}"
                rows="2"
                placeholder="Indique los hallazgos verificados o el motivo tecnico por el cual descarta el candidato (minimo 15 caracteres para descarte)..."
              ></textarea>
            </div>

            <div class="d-flex gap-2 flex-wrap">
              <button
                type="button"
                class="btn btn-sm btn-success btn-approve-alert"
                data-flag-id="${escapeHtml(rf.red_flag_id)}"
                data-entity-id="${escapeHtml(ent ? ent.entity_id : 'ce-f5f5d8fc32518855')}"
              >
                Publicar Alerta Civica (Aprobar)
              </button>
              <button
                type="button"
                class="btn btn-sm btn-outline-danger btn-discard-flag"
                data-flag-id="${escapeHtml(rf.red_flag_id)}"
                data-entity-id="${escapeHtml(ent ? ent.entity_id : 'ce-f5f5d8fc32518855')}"
              >
                Descartar Candidato (Falso Positivo)
              </button>
            </div>
          </div>
        </div>
      </div>
    `;
  }).join('');

  return `
    <div class="admin-revision-view">
      ${renderAdminSubnav('revision')}
      <div class="row">
        <div class="col-12 col-lg-8">
          <div class="d-flex justify-content-between align-items-center mb-3">
            <h2 class="h5 mb-0">Banderas Rojas Pendientes de Triage (${pendingFlags.length})</h2>
            <span class="small text-muted">Las banderas rojas no son publicas hasta su aprobacion</span>
          </div>
          <div id="revision-feedback-container"></div>
          ${itemsHtml}
        </div>
        <div class="col-12 col-lg-4">
          <div class="card border-0 bg-body-subtle p-3 mb-3">
            <h3 class="h6 text-primary mb-2">Protocolo de Evaluacion</h3>
            <ul class="small text-secondary ps-3 mb-0">
              <li class="mb-2"><strong>Regla Art. 14:</strong> Toda alerta ciudadana exige firma humana nominal del revisor.</li>
              <li class="mb-2"><strong>Regla Art. 15:</strong> La alerta hereda los 6 elementos de explicabilidad.</li>
              <li class="mb-2"><strong>Regla Art. 16:</strong> Queda prohibido imputar delitos o calificar personas por nombre propio.</li>
              <li><strong>CA-005-04:</strong> Todo descarte exige justificacion tecnica documentada.</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  `;
}

/**
 * Renderiza la bandeja de moderacion de denuncias (/admin/revision)
 */
export function renderAdminDenunciasView() {
  if (!isAuthenticatedReviewer()) {
    return `<div class="p-4 text-center">Redirigiendo a inicio de sesion...</div>`;
  }

  const { citizenReports, entities } = store.getState();
  const entityMap = new Map(entities.map(e => [e.entity_id, e]));

  const reportsList = (citizenReports || []).map(r => {
    const ent = r.related_entity_id ? entityMap.get(r.related_entity_id) : null;
    let badgeClass = 'bg-warning text-dark';
    let statusLabel = 'Pendiente de Evaluacion';

    if (r.moderation_status === 'accepted_as_lead') {
      badgeClass = 'bg-success';
      statusLabel = 'Aceptada como Linea de Investigacion';
    } else if (r.moderation_status === 'rejected') {
      badgeClass = 'bg-secondary';
      statusLabel = 'Descartada';
    }

    return `
      <div class="card mb-3 border shadow-sm" id="card-report-${escapeHtml(r.report_id)}">
        <div class="card-header bg-light d-flex justify-content-between align-items-center flex-wrap gap-2 py-2">
          <div>
            <span class="badge bg-secondary font-monospace">${escapeHtml(r.report_id)}</span>
            <span class="badge ${badgeClass} ms-2">${escapeHtml(statusLabel)}</span>
          </div>
          <span class="small text-muted">${escapeHtml(formatDateTime(r.submitted_at))}</span>
        </div>
        <div class="card-body">
          <div class="mb-2">
            <span class="small text-muted">Entidad involucrada:</span>
            <strong class="text-dark ms-1">${escapeHtml(ent ? ent.official_name : 'No especificada')}</strong>
          </div>
          <p class="card-text small text-dark p-2 border rounded bg-body-subtle mb-3">
            ${escapeHtml(r.raw_text)}
          </p>

          ${r.moderation_status !== 'pending' ? `
            <div class="small text-muted">
              Moderado por: <strong>${escapeHtml(r.moderated_by || '')}</strong> el ${escapeHtml(formatDateTime(r.moderated_at))}
            </div>
          ` : `
            <div class="d-flex gap-2">
              <button
                type="button"
                class="btn btn-sm btn-success btn-moderate-report"
                data-report-id="${escapeHtml(r.report_id)}"
                data-target-status="accepted_as_lead"
              >
                Admitir como Linea Investigativa
              </button>
              <button
                type="button"
                class="btn btn-sm btn-outline-danger btn-moderate-report"
                data-report-id="${escapeHtml(r.report_id)}"
                data-target-status="rejected"
              >
                Descartar Reporte
              </button>
            </div>
          `}
        </div>
      </div>
    `;
  }).join('');

  return `
    <div class="admin-denuncias-view">
      ${renderAdminSubnav('denuncias')}
      <div class="d-flex justify-content-between align-items-center mb-3">
        <h2 class="h5 mb-0">Bandeja de Denuncias Ciudadanas Recibidas (${citizenReports.length})</h2>
      </div>
      <div id="denuncias-mod-feedback"></div>
      ${citizenReports.length === 0 ? '<p class="text-muted">No hay denuncias registradas.</p>' : reportsList}
    </div>
  `;
}

/**
 * Renderiza la bitacora inmutable de auditoria (/admin/revision)
 */
export function renderAdminAuditoriaView() {
  if (!isAuthenticatedReviewer()) {
    return `<div class="p-4 text-center">Redirigiendo a inicio de sesion...</div>`;
  }

  const { alerts } = store.getState();
  const rawAudit = localStorage.getItem('cajamarca_qhaway_auditLog');
  let auditLogs = [];
  try {
    auditLogs = rawAudit ? JSON.parse(rawAudit) : [];
  } catch {
    auditLogs = [];
  }

  const rows = alerts.map(a => `
    <tr>
      <td class="font-monospace small"><code>${escapeHtml(a.alert_id)}</code></td>
      <td>
        <span class="badge ${a.status === 'published' ? 'bg-success' : 'bg-secondary'}">
          ${escapeHtml(a.status)}
        </span>
      </td>
      <td class="font-monospace small">${escapeHtml(a.reviewed_by)}</td>
      <td class="small">${escapeHtml(formatDateTime(a.reviewed_at))}</td>
      <td class="small text-truncate" style="max-width: 250px;">
        ${escapeHtml(a.review_notes || 'Sin notas adicionales')}
      </td>
    </tr>
  `).join('');

  return `
    <div class="admin-auditoria-view">
      ${renderAdminSubnav('auditoria')}
      <h2 class="h5 mb-3">Registro de Trazabilidad y Decisiones Humanas (Art. 14)</h2>
      <p class="small text-secondary">
        Bitacora inmutable que acredita quien reviso y publico o descarto cada candidato. Cero decisiones automatizadas.
      </p>

      <div class="table-responsive card border-0 shadow-sm">
        <table class="table table-hover table-striped mb-0 align-middle">
          <thead class="table-dark">
            <tr>
              <th scope="col">Identificador</th>
              <th scope="col">Estado</th>
              <th scope="col">Revisor Humano</th>
              <th scope="col">Fecha Revision</th>
              <th scope="col">Notas / Justificacion</th>
            </tr>
          </thead>
          <tbody>
            ${rows.length > 0 ? rows : '<tr><td colspan="5" class="text-center py-4 text-muted">Sin registros de auditoria aun.</td></tr>'}
          </tbody>
        </table>
      </div>
    </div>
  `;
}

/**
 * Configura los eventos del panel de administracion
 */
export function setupAdminEvents() {
  const btnLogout = document.getElementById('btn-logout-reviewer');
  if (btnLogout) {
    btnLogout.addEventListener('click', async () => {
      try {
        const token = sessionStorage.getItem('cajamarca_veedor_token') || '';
        await closeReviewerSession(token);
        store.clearReviewerSession();
        window.location.assign('/login');
      } catch (error) { window.showToast(error.message, 'error'); }
    });
  }

  // Botones de aprobacion de alertas
  const approveButtons = document.querySelectorAll('.btn-approve-alert');
  approveButtons.forEach(btn => {
    btn.addEventListener('click', async (e) => {
      const flagId = e.currentTarget.getAttribute('data-flag-id');
      const entityId = e.currentTarget.getAttribute('data-entity-id');
      const notesEl = document.getElementById(`notes-${flagId}`);
      const notes = notesEl ? notesEl.value.trim() : '';

      const session = store.getState().reviewerSession;
      if (!session || !isAuthenticatedReviewer()) return;
      if (!notes) {
        if (notesEl) {
          notesEl.setAttribute('aria-invalid', 'true');
          notesEl.setCustomValidity('Escribe el fundamento real del dictamen antes de publicar.');
          notesEl.reportValidity();
          notesEl.focus();
        }
        return;
      }
      notesEl?.removeAttribute('aria-invalid');
      notesEl?.setCustomValidity('');

      btn.disabled = true;
      btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Publicando...';

      try {
        const res = await supabaseClient.submitHumanReviewDecision({
          red_flag_ids: [flagId],
          entity_id: entityId,
          status: 'published',
          reviewed_by: session.email,
          review_notes: notes
        });

        // Actualizar estado
        const st = store.getState();
        store.setState({
          alerts: [res.alert, ...st.alerts]
        });

        const card = document.getElementById(`card-flag-${flagId}`);
        if (card) {
          card.innerHTML = `
            <div class="card-body bg-success-subtle text-success-emphasis p-3 text-center">
              <strong>Alerta Publicada con Exito (ID: ${escapeHtml(res.alert.alert_id)})</strong>
              <div class="small mt-1">Ya es visible en el explorador ciudadano (/alertas).</div>
            </div>
          `;
        }
      } catch (err) {
        btn.disabled = false;
        btn.textContent = 'Publicar Alerta Civica (Aprobar)';
        alert(`Error al publicar alerta: ${err.message}`);
      }
    });
  });

  // Botones de descarte de candidatos (exige justificacion)
  const discardButtons = document.querySelectorAll('.btn-discard-flag');
  discardButtons.forEach(btn => {
    btn.addEventListener('click', async (e) => {
      const flagId = e.currentTarget.getAttribute('data-flag-id');
      const entityId = e.currentTarget.getAttribute('data-entity-id');
      const notesEl = document.getElementById(`notes-${flagId}`);
      const notes = notesEl ? notesEl.value.trim() : '';

      if (!notes || notes.length < 15) {
        alert('CA-005-04: Para descartar un candidato es obligatorio redactar una justificacion tecnica de al menos 15 caracteres.');
        if (notesEl) notesEl.focus();
        return;
      }

      const session = store.getState().reviewerSession;
      if (!session) return;

      btn.disabled = true;
      btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Descartando...';

      try {
        const res = await supabaseClient.submitHumanReviewDecision({
          red_flag_ids: [flagId],
          entity_id: entityId,
          status: 'discarded',
          reviewed_by: session.email,
          review_notes: notes
        });

        const card = document.getElementById(`card-flag-${flagId}`);
        if (card) {
          card.innerHTML = `
            <div class="card-body bg-secondary-subtle text-secondary-emphasis p-3 text-center">
              <strong>Candidato Descartado y Documentado (ID: ${escapeHtml(res.alert.alert_id)})</strong>
              <div class="small mt-1">Justificacion registrada en bitacora de auditoria.</div>
            </div>
          `;
        }
      } catch (err) {
        btn.disabled = false;
        btn.textContent = 'Descartar Candidato (Falso Positivo)';
        alert(`Error al descartar candidato: ${err.message}`);
      }
    });
  });

  // Botones de moderacion de denuncias
  const modButtons = document.querySelectorAll('.btn-moderate-report');
  modButtons.forEach(btn => {
    btn.addEventListener('click', async (e) => {
      const reportId = e.currentTarget.getAttribute('data-report-id');
      const targetStatus = e.currentTarget.getAttribute('data-target-status');
      const session = store.getState().reviewerSession;
      if (!session) return;

      try {
        await supabaseClient.moderateCitizenReport({
          report_id: reportId,
          moderation_status: targetStatus,
          moderated_by: session.email
        });

        // Actualizar vista local
        const st = store.getState();
        const updated = st.citizenReports.map(r => {
          if (r.report_id === reportId) {
            return {
              ...r,
              moderation_status: targetStatus,
              moderated_by: session.email,
              moderated_at: new Date().toISOString()
            };
          }
          return r;
        });
        store.setState({ citizenReports: updated });

        const card = document.getElementById(`card-report-${reportId}`);
        if (card) {
          card.classList.add(targetStatus === 'accepted_as_lead' ? 'border-success' : 'border-secondary');
        }
        window.location.assign('/admin/revision');
      } catch (err) {
        alert(`Error en moderacion: ${err.message}`);
      }
    });
  });
}
