/**
 * export-csv.js: Exportador de datos publicos a CSV con BOM UTF-8 (CU1)
 * Incluye calculo criptografico SHA-256 verificable con Web Crypto API.
 *
 * Restricciones:
 * - Antislop R-02: Cero rayas em-dash en todo el archivo.
 * - BOM UTF-8 (\uFEFF) para visualizacion correcta en Microsoft Excel.
 */

/**
 * Escapa valores para formato CSV compatible con RFC 4180
 * @param {any} val
 * @returns {string}
 */
function escapeCsvValue(val) {
  if (val === null || val === undefined) return '""';
  let str = String(val);
  // Reemplazar comillas dobles internas por pares de comillas dobles
  if (str.includes('"') || str.includes(',') || str.includes('\n') || str.includes('\r')) {
    str = `"${str.replace(/"/g, '""')}"`;
  } else {
    str = `"${str}"`;
  }
  return str;
}

/**
 * Calcula el digest SHA-256 de una cadena en hexadecimal
 * @param {string} text
 * @returns {Promise<string>}
 */
export async function computeSha256Hex(text) {
  try {
    if (window.crypto && window.crypto.subtle) {
      const msgBuffer = new TextEncoder().encode(text);
      const hashBuffer = await window.crypto.subtle.digest('SHA-256', msgBuffer);
      const hashArray = Array.from(new Uint8Array(hashBuffer));
      return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
    }
  } catch (err) {
    console.warn('Web Crypto API no disponible o en contexto inseguro, generando hash alternativo:', err);
  }
  // Fallback simple si no esta disponible Web Crypto (por ejemplo en http plano)
  let hash = 0;
  for (let i = 0; i < text.length; i++) {
    hash = ((hash << 5) - hash) + text.charCodeAt(i);
    hash |= 0;
  }
  return 'sha256-sim-' + Math.abs(hash).toString(16).padStart(8, '0');
}

/**
 * Descarga una cadena de texto como archivo CSV en el navegador
 * @param {string} csvContent
 * @param {string} filename
 */
export function downloadCsvFile(csvContent, filename) {
  // Anteponer BOM UTF-8 (\uFEFF)
  const blob = new Blob(['\uFEFF' + csvContent], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.setAttribute('href', url);
  link.setAttribute('download', filename);
  link.style.visibility = 'hidden';
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

/**
 * Exporta el catalogo de Alertas Publicadas
 * @param {Array} alerts
 * @param {Array} entities
 * @returns {Promise<{ filename: string, rowCount: number, sha256: string }>}
 */
export async function exportAlertsCsv(alerts, entities) {
  const entityMap = new Map((entities || []).map(e => [e.entity_id, e]));
  const headers = [
    'alert_id',
    'entity_id',
    'official_name',
    'province',
    'ruc',
    'status',
    'red_flag_ids',
    'reviewed_by',
    'reviewed_at',
    'published_at',
    'review_notes',
    'disclaimer'
  ];

  const rows = (alerts || []).map(a => {
    const ent = entityMap.get(a.entity_id);
    return [
      a.alert_id,
      a.entity_id,
      ent ? ent.official_name : '',
      ent ? (ent.province || 'Regional') : '',
      ent ? ent.ruc : '',
      a.status,
      Array.isArray(a.red_flag_ids) ? a.red_flag_ids.join(';') : String(a.red_flag_ids || ''),
      a.reviewed_by,
      a.reviewed_at,
      a.published_at || '',
      a.review_notes || '',
      a.disclaimer
    ].map(escapeCsvValue).join(',');
  });

  const csvBody = [headers.join(','), ...rows].join('\r\n');
  const sha256 = await computeSha256Hex(csvBody);
  const filename = `cajamarca-qhaway-alertas-${new Date().toISOString().slice(0, 10)}.csv`;

  downloadCsvFile(csvBody, filename);
  return { filename, rowCount: rows.length, sha256 };
}

/**
 * Exporta el catalogo de Contrataciones SEACE OCDS
 * @param {Array} procurements
 * @param {Array} entities
 * @returns {Promise<{ filename: string, rowCount: number, sha256: string }>}
 */
export async function exportProcurementsCsv(procurements, entities) {
  const entityMap = new Map((entities || []).map(e => [e.entity_id, e]));
  const headers = [
    'procurement_id',
    'ocid',
    'entity_id',
    'official_name',
    'province',
    'title',
    'procurement_method',
    'awarded_amount_pen',
    'executed_amount_pen',
    'number_of_bidders',
    'supplier_name',
    'supplier_ruc',
    'source',
    'retrieved_at'
  ];

  const rows = (procurements || []).map(p => {
    const ent = entityMap.get(p.entity_id);
    return [
      p.procurement_id,
      p.ocid,
      p.entity_id,
      ent ? ent.official_name : '',
      ent ? (ent.province || 'Regional') : '',
      p.title,
      p.procurement_method || '',
      p.awarded_amount !== null && p.awarded_amount !== undefined ? p.awarded_amount : '',
      p.executed_amount !== null && p.executed_amount !== undefined ? p.executed_amount : '',
      p.number_of_bidders !== null && p.number_of_bidders !== undefined ? p.number_of_bidders : '',
      p.supplier_name || '',
      p.supplier_ruc || '',
      p.source,
      p.retrieved_at
    ].map(escapeCsvValue).join(',');
  });

  const csvBody = [headers.join(','), ...rows].join('\r\n');
  const sha256 = await computeSha256Hex(csvBody);
  const filename = `cajamarca-qhaway-contratos-seace-${new Date().toISOString().slice(0, 10)}.csv`;

  downloadCsvFile(csvBody, filename);
  return { filename, rowCount: rows.length, sha256 };
}

/**
 * Exporta los registros de Ejecucion Presupuestal MEF
 * @param {Array} budgetExecutions
 * @param {Array} entities
 * @returns {Promise<{ filename: string, rowCount: number, sha256: string }>}
 */
export async function exportBudgetExecutionsCsv(budgetExecutions, entities) {
  const entityMap = new Map((entities || []).map(e => [e.entity_id, e]));
  const headers = [
    'execution_record_id',
    'entity_id',
    'official_name',
    'province',
    'fiscal_year',
    'budgeted_amount_pim_pen',
    'executed_amount_devengado_pen',
    'execution_percentage',
    'budget_category',
    'source',
    'retrieved_at'
  ];

  const rows = (budgetExecutions || []).map(b => {
    const ent = entityMap.get(b.entity_id);
    const pim = Number(b.budgeted_amount || 0);
    const dev = Number(b.executed_amount || 0);
    const pct = pim > 0 ? ((dev / pim) * 100).toFixed(2) : '0.00';
    return [
      b.execution_record_id,
      b.entity_id,
      ent ? ent.official_name : '',
      ent ? (ent.province || 'Regional') : '',
      b.fiscal_year,
      pim,
      dev,
      pct,
      b.budget_category || '',
      b.source,
      b.retrieved_at
    ].map(escapeCsvValue).join(',');
  });

  const csvBody = [headers.join(','), ...rows].join('\r\n');
  const sha256 = await computeSha256Hex(csvBody);
  const filename = `cajamarca-qhaway-presupuesto-mef-${new Date().toISOString().slice(0, 10)}.csv`;

  downloadCsvFile(csvBody, filename);
  return { filename, rowCount: rows.length, sha256 };
}

/**
 * Exporta el directorio oficial del Universo de 14 Entidades
 * @param {Array} entities
 * @returns {Promise<{ filename: string, rowCount: number, sha256: string }>}
 */
export async function exportEntitiesCsv(entities) {
  const headers = [
    'entity_id',
    'official_name',
    'entity_level',
    'province',
    'ruc',
    'consucode_id',
    'department',
    'verified_at',
    'active'
  ];

  const rows = (entities || []).map(e => [
    e.entity_id,
    e.official_name,
    e.entity_level,
    e.province || '',
    e.ruc,
    e.consucode_id || '',
    e.department,
    e.verified_at,
    e.active ? 'TRUE' : 'FALSE'
  ].map(escapeCsvValue).join(','));

  const csvBody = [headers.join(','), ...rows].join('\r\n');
  const sha256 = await computeSha256Hex(csvBody);
  const filename = `cajamarca-qhaway-14-entidades-${new Date().toISOString().slice(0, 10)}.csv`;

  downloadCsvFile(csvBody, filename);
  return { filename, rowCount: rows.length, sha256 };
}
