import { dataEngine } from './data-engine.js';
import { openRawPayloadDrawer } from './app.js';

export const escapeHTML = value => String(value ?? '').replace(/[&<>"']/g,
  character => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[character]);

function officialURL(value) {
  try {
    const url = new URL(value);
    return url.protocol === 'https:' && ['conosce.osce.gob.pe', 'bi.seace.gob.pe', 'prod2.seace.gob.pe'].includes(url.hostname) ? url.href : null;
  } catch { return null; }
}

export function renderProcurementEvidence(record) {
  const evidence = record.source_evidence || [];
  const sources = [...new Map(evidence.map(item => [item.source_url, item])).values()];
  const cuis = [...new Set(evidence.map(item => item.cui).filter(Boolean))];
  return `<div class="qh-source-evidence"><span class="qh-source-tag">SEACE OCDS: registro original</span>
    ${sources.map(item => {
      const url = officialURL(item.source_url);
      return url ? `<a class="qh-source-tag" href="${escapeHTML(url)}" target="_blank" rel="noopener">${item.source_system === 'oece_pentaho_bi' ? 'OECE Datos Abiertos' : 'SEACE Buscador'}: ${escapeHTML(item.dataset)} ${item.fiscal_year}</a>` : '';
    }).join('')}
    ${evidence.length ? `<span>${evidence.length} filas oficiales vinculadas</span>` : '<span>Sin evidencia adicional vinculada en este corte</span>'}
    ${cuis.length === 1 ? `<span>CUI documentado: ${escapeHTML(cuis[0])}</span>` : ''}
    <a href="https://prod2.seace.gob.pe/seacebus-uiwd-pub/buscadorPublico/buscadorPublico.xhtml" target="_blank" rel="noopener">Consultar SEACE (verificacion manual con CAPTCHA)</a>
    <button type="button" data-procurement-evidence="${escapeHTML(record.procurement_id)}">Ver procedencia y filas originales</button></div>`;
}

export async function initProcurementEvidence() {
  if (document.querySelector('#qh-contract-evidence')) {
    const id = new URLSearchParams(location.search).get('id');
    const record = await dataEngine.getProcurementByOcid(id);
    const host = document.querySelector('#qh-contract-evidence');
    if (record && host) host.innerHTML = renderProcurementEvidence(record);
  }
  document.addEventListener('click', async event => {
    const control = event.target.closest('[data-procurement-evidence]');
    if (!control) return;
    const record = await dataEngine.getProcurementByOcid(control.dataset.procurementEvidence);
    if (!record) return;
    openRawPayloadDrawer({ procurement_id: record.procurement_id, ocid: record.ocid,
      source: record.source, retrieved_at: record.retrieved_at, raw_payload: record.raw_payload,
      official_source_evidence: record.source_evidence || [] }, 'Procedencia oficial de la contratacion');
  });
}
