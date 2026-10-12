/**
 * denuncias.js: Controlador del Canal de Denuncia Ciudadana (006-denuncia-intake)
 * Ruta: #/denuncia
 *
 * Restricciones Constitucionales:
 * - Antislop R-02: Cero rayas em-dash en todo el archivo.
 * - Restriccion ineludible: legal_disclaimer_shown = true obligatorio (Ley 29733).
 * - Selector cerrado a las 14 entidades de Cajamarca (Art. 18).
 * - Generacion de codigo de seguimiento anonimo unico (cr-...).
 */

import { CITIZEN_REPORT_DISCLAIMER } from './config.js';
import { supabaseClient } from './supabase-client.js';
import { store } from './state.js';
import { escapeHtml } from './explicabilidad.js';

/**
 * Renderiza el formulario interactivo de denuncia ciudadana
 * @returns {string} HTML
 */
export function renderDenunciaView() {
  const { entities, ruralLiteMode } = store.getState();

  const entityOptions = entities.map(e => `
    <option value="${escapeHtml(e.entity_id)}">
      ${escapeHtml(e.official_name)} (${e.province ? escapeHtml(e.province) : 'Nivel Regional'}) - RUC ${escapeHtml(e.ruc)}
    </option>
  `).join('');

  return `
    <div class="denuncia-view max-w-800 mx-auto">
      <!-- Encabezado de la Seccion -->
      <div class="mb-4">
        <span class="badge bg-secondary-subtle text-secondary-emphasis border mb-2">Canal Civico Seguro (006-denuncia-intake)</span>
        <h1 class="h3 mb-2">Canal Ciudadano de Alertas y Denuncias de Cajamarca</h1>
        <p class="text-secondary">
          Espacio seguro e independiente para que pobladores, dirigentes comunales y comites de vigilancia ciudadana reporten presuntas anomalias en contrataciones publicas y obras de la Region Cajamarca.
        </p>
      </div>

      <!-- Contenedor de Resultado o Mensaje de Exito -->
      <div id="denuncia-feedback-container"></div>

      <!-- Formulario Principal -->
      <form id="form-denuncia-ciudadana" class="card shadow-sm border-0 bg-body-surface p-4" novalidate>
        <!-- Selector de Entidad (Universo cerrado de 14 entidades) -->
        <div class="mb-3">
          <label for="denuncia-entidad" class="form-label fw-semibold">
            Entidad Publica Involucrada <span class="text-muted fw-normal">(Opcional si es regional)</span>
          </label>
          <select class="form-select" id="denuncia-entidad" aria-describedby="denuncia-entidad-help">
            <option value="">Seleccione una de las 14 entidades de Cajamarca...</option>
            ${entityOptions}
          </select>
          <div id="denuncia-entidad-help" class="form-text small">
            Ambito restringido exclusivamente al Gobierno Regional de Cajamarca y las 13 Municipalidades Provinciales (Art. 18).
          </div>
        </div>

        <!-- Descripcion de los Hechos -->
        <div class="mb-3">
          <label for="denuncia-texto" class="form-label fw-semibold">
            Detalle de los Hechos o Anomalia Observada <span class="text-danger">*</span>
          </label>
          <textarea
            class="form-control"
            id="denuncia-texto"
            rows="${ruralLiteMode ? '4' : '6'}"
            placeholder="Describa con claridad que irregularidad presencio: obra paralizada, direccion ficticia del proveedor, sobrecosto notorio, falta de maquinaria o direccionamiento..."
            required
            aria-describedby="denuncia-texto-help"
          ></textarea>
          <div id="denuncia-texto-help" class="form-text small d-flex justify-content-between">
            <span>Proporcione datos objetivos verificables (nombres de calles, codigos de licitacion o fechas).</span>
            <span id="denuncia-char-counter" class="text-muted">0 caracteres</span>
          </div>
        </div>

        <!-- Referencia o Enlaces de Evidencia Adicional -->
        <div class="mb-3">
          <label for="denuncia-enlaces" class="form-label fw-semibold">
            Enlaces a Evidencias Publicas o Documentos <span class="text-muted fw-normal">(Opcional)</span>
          </label>
          <input
            type="text"
            class="form-control"
            id="denuncia-enlaces"
            placeholder="Ejemplo: enlace a video, acta comunal, publicacion SEACE o nota de prensa"
            aria-describedby="denuncia-enlaces-help"
          >
          <div id="denuncia-enlaces-help" class="form-text small">
            No incluya documentos con datos sensibles o privados de terceros no autorizados.
          </div>
        </div>

        <!-- Casilla Obligatoria Ineludible: Aviso Legal Ley 29733 (CA-304-01) -->
        <div class="p-3 rounded border border-warning-subtle bg-warning-subtle mb-4">
          <div class="form-check">
            <input class="form-check-input" type="checkbox" id="denuncia-disclaimer-check" required>
            <label class="form-check-label small text-dark" for="denuncia-disclaimer-check">
              <strong>Confirmacion Legal Obligatoria:</strong> He leido y acepto las condiciones de uso y advertencias legales:
            </label>
          </div>
          <div class="mt-2 text-secondary small" style="line-height: 1.45;">
            ${escapeHtml(CITIZEN_REPORT_DISCLAIMER)}
          </div>
        </div>

        <!-- Boton de Envio y Estado -->
        <div class="d-flex align-items-center justify-content-between flex-wrap gap-2">
          <button
            type="submit"
            id="btn-submit-denuncia"
            class="btn btn-primary px-4 py-2 fw-semibold"
            disabled
          >
            Registrar Denuncia Ciudadana
          </button>
          <span class="small text-muted" id="denuncia-submit-note">
            Marque la confirmacion legal para habilitar el envio.
          </span>
        </div>
      </form>

      <!-- Panel Informativo de Seguridad y Garantias Civicas -->
      <div class="mt-4 row g-3">
        <div class="col-12 col-md-6">
          <div class="p-3 border rounded bg-body-subtle h-100">
            <h2 class="h6 text-primary mb-1">Proteccion y Anonimato</h2>
            <p class="small text-muted mb-0">
              Esta plataforma no almacena direcciones IP fijas ni exige identificacion obligatoria del denunciante. Su reporte genera un codigo alfanumerico confidencial.
            </p>
          </div>
        </div>
        <div class="col-12 col-md-6">
          <div class="p-3 border rounded bg-body-subtle h-100">
            <h2 class="h6 text-primary mb-1">Proceso de Moderacion Humana (005)</h2>
            <p class="small text-muted mb-0">
              Todo reporte es revisado por el equipo humano del observatorio para contrastarlo con datos oficiales del SEACE y MEF antes de ser admitido como linea de investigacion.
            </p>
          </div>
        </div>
      </div>
    </div>
  `;
}

/**
 * Inicializa los eventos y validaciones del formulario de denuncia
 */
export function setupDenunciaEvents() {
  const form = document.getElementById('form-denuncia-ciudadana');
  if (!form) return;

  const disclaimerCheck = document.getElementById('denuncia-disclaimer-check');
  const btnSubmit = document.getElementById('btn-submit-denuncia');
  const submitNote = document.getElementById('denuncia-submit-note');
  const textarea = document.getElementById('denuncia-texto');
  const charCounter = document.getElementById('denuncia-char-counter');
  const feedbackContainer = document.getElementById('denuncia-feedback-container');

  // Control dinamico del checkbox obligatorio (CA-304-01)
  function updateButtonState() {
    const isChecked = disclaimerCheck && disclaimerCheck.checked;
    const hasText = textarea && textarea.value.trim().length >= 10;

    if (btnSubmit) {
      btnSubmit.disabled = !(isChecked && hasText);
    }

    if (submitNote) {
      if (!isChecked) {
        submitNote.textContent = 'Debe marcar la confirmacion legal obligatoria.';
        submitNote.className = 'small text-warning-emphasis fw-medium';
      } else if (!hasText) {
        submitNote.textContent = 'Ingrese al menos 10 caracteres describiendo los hechos.';
        submitNote.className = 'small text-muted';
      } else {
        submitNote.textContent = 'Formulario listo para enviar.';
        submitNote.className = 'small text-success fw-medium';
      }
    }
  }

  if (disclaimerCheck) {
    disclaimerCheck.addEventListener('change', updateButtonState);
  }

  if (textarea) {
    textarea.addEventListener('input', () => {
      const len = textarea.value.length;
      if (charCounter) {
        charCounter.textContent = `${len} caracteres`;
      }
      updateButtonState();
    });
  }

  // Manejador del envio
  form.addEventListener('submit', async (e) => {
    e.preventDefault();

    if (!disclaimerCheck || !disclaimerCheck.checked) {
      alert('Error: Debe marcar la casilla del aviso legal obligatorio para proceder.');
      return;
    }

    const rawText = textarea.value.trim();
    if (rawText.length < 10) {
      alert('Error: La descripcion de los hechos debe contener al menos 10 caracteres.');
      return;
    }

    const entitySelect = document.getElementById('denuncia-entidad');
    const relatedEntityId = entitySelect ? entitySelect.value || null : null;
    const extraLinks = document.getElementById('denuncia-enlaces')?.value?.trim();

    let fullDescription = rawText;
    if (extraLinks) {
      fullDescription += `\n\n[Evidencias referenciales adjuntas: ${extraLinks}]`;
    }

    // Deshabilitar boton durante envio
    btnSubmit.disabled = true;
    btnSubmit.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Registrando denuncia...';

    try {
      const result = await supabaseClient.submitCitizenReport({
        raw_text: fullDescription,
        related_entity_id: relatedEntityId,
        channel: 'web',
        legal_disclaimer_shown: true
      });

      // Actualizar estado global
      const st = store.getState();
      const updatedReports = [
        {
          report_id: result.report_id,
          submitted_at: result.submitted_at,
          channel: 'web',
          raw_text: fullDescription,
          related_entity_id: relatedEntityId,
          moderation_status: 'pending',
          moderated_by: null,
          moderated_at: null,
          legal_disclaimer_shown: true
        },
        ...st.citizenReports
      ];
      store.setState({ citizenReports: updatedReports });

      // Mostrar confirmacion con el codigo de seguimiento unico (CA-304-02)
      form.style.display = 'none';
      if (feedbackContainer) {
        feedbackContainer.innerHTML = `
          <div class="card border-success shadow-sm mb-4">
            <div class="card-header bg-success text-white py-3">
              <h2 class="h5 mb-0">Denuncia Registrada con Exito</h2>
            </div>
            <div class="card-body p-4">
              <p class="lead text-dark">
                Su reporte ciudadano ha sido recibido satisfactoriamente por el observatorio.
              </p>
              <div class="p-3 border rounded bg-body-subtle my-3 text-center">
                <span class="text-muted d-block small mb-1">Codigo de Seguimiento Anonimo:</span>
                <strong class="display-6 font-monospace text-primary text-break">${escapeHtml(result.report_id)}</strong>
              </div>
              <p class="small text-muted mb-2">
                Guarde este codigo para consultas futuras. Su reporte ha ingresado a la bandeja interna de evaluacion humana (estado: <code>pending</code>).
              </p>
              <p class="small text-secondary mb-3">
                ${result.remote_synced ? 'Sincronizado con base de datos central en la nube.' : 'Guardado en sesion local con sincronizacion diferida por contingencia.'}
              </p>
              <div class="d-flex gap-2 flex-wrap">
                <button type="button" class="btn btn-outline-primary" id="btn-nueva-denuncia">
                  Registrar Otra Denuncia
                </button>
                <a href="#/inicio" class="btn btn-secondary">
                  Volver al Inicio
                </a>
              </div>
            </div>
          </div>
        `;

        const btnNueva = feedbackContainer.querySelector('#btn-nueva-denuncia');
        if (btnNueva) {
          btnNueva.addEventListener('click', () => {
            form.reset();
            form.style.display = 'block';
            feedbackContainer.innerHTML = '';
            updateButtonState();
          });
        }
      }
    } catch (err) {
      btnSubmit.disabled = false;
      btnSubmit.textContent = 'Registrar Denuncia Ciudadana';
      alert(`No se pudo registrar la denuncia: ${err.message}`);
    }
  });

  updateButtonState();
}
