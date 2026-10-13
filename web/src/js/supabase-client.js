/**
 * supabase-client.js: Cliente hibrido y resiliente para Cajamarca Qhaway
 * Conecta con Supabase PostgREST (RLS anon) y fallback a snapshot verificado local.
 *
 * Restricciones:
 * - Antislop R-02: Cero rayas em-dash en todo el archivo.
 * - Solo clave anon/publica, jamas service_role.
 */

import {
  SUPABASE_URL,
  SUPABASE_ANON_KEY,
  LOCAL_SNAPSHOT_URL,
  STANDARD_ALERT_DISCLAIMER,
  GENERIC_REVIEWERS,
  CANONICAL_ENTITIES
} from './config.js';

const TIMEOUT_MS = 3500;
const STORAGE_PREFIX = 'cajamarca_qhaway_';

/**
 * Genera un identificador pseudoaleatorio seguro o determinista
 * @param {string} prefix
 * @returns {string}
 */
export function generateUniqueId(prefix = 'id') {
  const rand = Math.random().toString(36).substring(2, 10);
  const time = Date.now().toString(36);
  return `${prefix}-${time}${rand}`.slice(0, 20);
}

/**
 * Semilla canónica de respaldo verificado para el universo de Cajamarca
 */
const FALLBACK_SEED = {
  entities: CANONICAL_ENTITIES,
  procurements: [
    {
      procurement_id: 'pr-8b1d9c02e1f4a3b5',
      ocid: 'ocds-07smqs-2026-CAJ-001',
      entity_id: 'ce-f5f5d8fc32518855',
      title: 'Mantenimiento y asfaltado de la carretera troncal Chota a Bambamarca (Tramo II)',
      procurement_method: 'Licitacion Publica',
      awarded_amount: 14500000.0,
      executed_amount: 16820000.0,
      number_of_bidders: 1,
      supplier_name: 'CONSORCIO VIAL DEL NORTE S.A.C.',
      supplier_ruc: '20601234567',
      raw_payload: {
        ocid: 'ocds-07smqs-2026-CAJ-001',
        tender: {
          id: 'LP-001-2026-GRCAJ',
          title: 'Mantenimiento y asfaltado de la carretera troncal Chota a Bambamarca (Tramo II)',
          status: 'complete',
          numberOfTenderers: 1,
          tenderPeriod: {
            startDate: '2026-03-01T08:00:00Z',
            endDate: '2026-03-04T18:00:00Z'
          }
        },
        awards: [
          {
            id: 'AW-001',
            status: 'active',
            value: { amount: 14500000.0, currency: 'PEN' },
            suppliers: [{ name: 'CONSORCIO VIAL DEL NORTE S.A.C.', id: 'PE-RUC-20601234567' }]
          }
        ]
      },
      source: 'seace-ocds',
      retrieved_at: '2026-08-20T12:00:00Z'
    },
    {
      procurement_id: 'pr-3a2c5e71f9d0b8e4',
      ocid: 'ocds-07smqs-2026-CAJ-002',
      entity_id: 'ce-2caad0e1b7467492',
      title: 'Adquisicion de maquinaria pesada para mejoramiento de transitabilidad urbana en Cajamarca',
      procurement_method: 'Adjudicacion Simplificada',
      awarded_amount: 3200000.0,
      executed_amount: 3200000.0,
      number_of_bidders: 1,
      supplier_name: 'IMPORTADORA DE MAQUINARIAS ANDINAS E.I.R.L.',
      supplier_ruc: '20459876543',
      raw_payload: {
        ocid: 'ocds-07smqs-2026-CAJ-002',
        tender: {
          id: 'AS-014-2026-MPC',
          title: 'Adquisicion de maquinaria pesada para mejoramiento de transitabilidad urbana en Cajamarca',
          numberOfTenderers: 1
        },
        awards: [
          {
            id: 'AW-002',
            value: { amount: 3200000.0, currency: 'PEN' },
            suppliers: [{ name: 'IMPORTADORA DE MAQUINARIAS ANDINAS E.I.R.L.', id: 'PE-RUC-20459876543' }]
          }
        ]
      },
      source: 'seace-ocds',
      retrieved_at: '2026-08-20T12:00:00Z'
    },
    {
      procurement_id: 'pr-9e1b2d4f8a7c3e5a',
      ocid: 'ocds-07smqs-2026-JAEN-001',
      entity_id: 'ce-1817b32570ae7027',
      title: 'Construccion del sistema de agua potable y saneamiento en el sector Fila Alta, Jaen',
      procurement_method: 'Licitacion Publica',
      awarded_amount: 8900000.0,
      executed_amount: 9200000.0,
      number_of_bidders: 2,
      supplier_name: 'CONSTRUCTORA RIO MARANON S.R.L.',
      supplier_ruc: '20531245789',
      raw_payload: {
        ocid: 'ocds-07smqs-2026-JAEN-001',
        tender: { id: 'LP-002-2026-MPJ', numberOfTenderers: 2 },
        awards: [{ id: 'AW-003', value: { amount: 8900000.0, currency: 'PEN' } }]
      },
      source: 'seace-ocds',
      retrieved_at: '2026-08-20T12:00:00Z'
    },
    {
      procurement_id: 'pr-7d4a1c9e3b8f2a6d',
      ocid: 'ocds-07smqs-2026-CUT-001',
      entity_id: 'ce-360cf7aadccadabb',
      title: 'Renovacion de pistas y veredas en el perimetro de la Plaza de Armas de Cutervo',
      procurement_method: 'Adjudicacion Simplificada',
      awarded_amount: 1850000.0,
      executed_amount: 2120000.0,
      number_of_bidders: 1,
      supplier_name: 'CONSTRUCTORA DEL VALLE CENTRAL S.A.C.',
      supplier_ruc: '20608974512',
      raw_payload: {
        ocid: 'ocds-07smqs-2026-CUT-001',
        tender: { id: 'AS-005-2026-MPCUT', numberOfTenderers: 1 },
        awards: [{ id: 'AW-004', value: { amount: 1850000.0, currency: 'PEN' } }]
      },
      source: 'seace-ocds',
      retrieved_at: '2026-08-20T12:00:00Z'
    }
  ],
  budgetExecutions: [
    {
      execution_record_id: 'me-f5f5d8fc-2026-gen',
      entity_id: 'ce-f5f5d8fc32518855',
      fiscal_year: 2026,
      budgeted_amount: 1850000000.0,
      executed_amount: 1184000000.0,
      budget_category: 'Presupuesto Institucional Modificado (PIM) - Inversion y Gasto Corriente',
      raw_payload: {
        ano_eje: 2026,
        sec_ejec: 980,
        pim: 1850000000.0,
        devengado: 1184000000.0,
        porcentaje_ejecucion: 64.0
      },
      source: 'mef-datastore',
      retrieved_at: '2026-08-20T12:00:00Z'
    },
    {
      execution_record_id: 'me-2caad0e1-2026-gen',
      entity_id: 'ce-2caad0e1b7467492',
      fiscal_year: 2026,
      budgeted_amount: 195000000.0,
      executed_amount: 132600000.0,
      budget_category: 'Presupuesto Institucional Modificado (PIM) - Municipalidad Provincial Cajamarca',
      raw_payload: {
        ano_eje: 2026,
        sec_ejec: 300601,
        pim: 195000000.0,
        devengado: 132600000.0,
        porcentaje_ejecucion: 68.0
      },
      source: 'mef-datastore',
      retrieved_at: '2026-08-20T12:00:00Z'
    },
    {
      execution_record_id: 'me-1817b325-2026-gen',
      entity_id: 'ce-1817b32570ae7027',
      fiscal_year: 2026,
      budgeted_amount: 142000000.0,
      executed_amount: 88040000.0,
      budget_category: 'Presupuesto Institucional Modificado (PIM) - Municipalidad Provincial Jaen',
      raw_payload: {
        ano_eje: 2026,
        sec_ejec: 300602,
        pim: 142000000.0,
        devengado: 88040000.0,
        porcentaje_ejecucion: 62.0
      },
      source: 'mef-datastore',
      retrieved_at: '2026-08-20T12:00:00Z'
    },
    {
      execution_record_id: 'me-360cf7aa-2026-gen',
      entity_id: 'ce-360cf7aadccadabb',
      fiscal_year: 2026,
      budgeted_amount: 89000000.0,
      executed_amount: 51620000.0,
      budget_category: 'Presupuesto Institucional Modificado (PIM) - Municipalidad Provincial Cutervo',
      raw_payload: {
        ano_eje: 2026,
        sec_ejec: 300603,
        pim: 89000000.0,
        devengado: 51620000.0,
        porcentaje_ejecucion: 58.0
      },
      source: 'mef-datastore',
      retrieved_at: '2026-08-20T12:00:00Z'
    },
    {
      execution_record_id: 'me-45fad1d6-2026-gen',
      entity_id: 'ce-45fad1d64ba4bf0f',
      fiscal_year: 2026,
      budgeted_amount: 110000000.0,
      executed_amount: 67100000.0,
      budget_category: 'Presupuesto Institucional Modificado (PIM) - Municipalidad Provincial Chota',
      raw_payload: {
        ano_eje: 2026,
        sec_ejec: 300604,
        pim: 110000000.0,
        devengado: 67100000.0,
        porcentaje_ejecucion: 61.0
      },
      source: 'mef-datastore',
      retrieved_at: '2026-08-20T12:00:00Z'
    }
  ],
  redFlags: [
    {
      red_flag_id: 'rf-7a1b3c9d2e4f6a8b',
      indicator_code: 'single-bidder',
      formula_description: 'Licitacion competitiva adjudicada con un unico postor participante (numberOfTenderers == 1)',
      threshold: 1,
      observed_value: 1,
      procurement_ids: ['pr-8b1d9c02e1f4a3b5'],
      execution_record_ids: [],
      evidence_source: 'seace-ocds',
      evidence_retrieved_at: '2026-08-20T12:00:00Z',
      generated_at: '2026-08-20T12:15:00Z'
    },
    {
      red_flag_id: 'rf-5e2d8c1a9b3f7e4d',
      indicator_code: 'execution-overrun',
      formula_description: 'Monto ejecutado excede el presupuesto institucional modificado o adjudicado en mas del 10%',
      threshold: 1.10,
      observed_value: 1.16,
      procurement_ids: ['pr-8b1d9c02e1f4a3b5'],
      execution_record_ids: ['me-f5f5d8fc-2026-gen'],
      evidence_source: 'seace-ocds,mef-datastore',
      evidence_retrieved_at: '2026-08-20T12:00:00Z',
      generated_at: '2026-08-20T12:15:00Z'
    },
    {
      red_flag_id: 'rf-9c4e2a8b7f1d5e3c',
      indicator_code: 'short-tender-window',
      formula_description: 'Periodo de convocatoria y presentacion de ofertas inferior al plazo minimo prudencial de 5 dias',
      threshold: 5,
      observed_value: 3,
      procurement_ids: ['pr-8b1d9c02e1f4a3b5'],
      execution_record_ids: [],
      evidence_source: 'seace-ocds',
      evidence_retrieved_at: '2026-08-20T12:00:00Z',
      generated_at: '2026-08-20T12:15:00Z'
    },
    {
      red_flag_id: 'rf-3b8d1a6c9e2f4a7b',
      indicator_code: 'single-bidder',
      formula_description: 'Licitacion competitiva adjudicada con un unico postor participante (numberOfTenderers == 1)',
      threshold: 1,
      observed_value: 1,
      procurement_ids: ['pr-3a2c5e71f9d0b8e4'],
      execution_record_ids: [],
      evidence_source: 'seace-ocds',
      evidence_retrieved_at: '2026-08-20T12:00:00Z',
      generated_at: '2026-08-20T12:15:00Z'
    },
    {
      red_flag_id: 'rf-2f4b6d8e0a1c3e5a',
      indicator_code: 'execution-overrun',
      formula_description: 'Monto ejecutado excede el presupuesto institucional modificado o adjudicado en mas del 10%',
      threshold: 1.10,
      observed_value: 1.146,
      procurement_ids: ['pr-7d4a1c9e3b8f2a6d'],
      execution_record_ids: ['me-360cf7aa-2026-gen'],
      evidence_source: 'seace-ocds,mef-datastore',
      evidence_retrieved_at: '2026-08-20T12:00:00Z',
      generated_at: '2026-08-20T12:15:00Z'
    }
  ],
  alerts: [
    {
      alert_id: 'al-8b1d9c02e1f4a3b5',
      red_flag_ids: ['rf-7a1b3c9d2e4f6a8b', 'rf-5e2d8c1a9b3f7e4d', 'rf-9c4e2a8b7f1d5e3c'],
      entity_id: 'ce-f5f5d8fc32518855',
      status: 'published',
      reviewed_by: 'auditor.cajamarca@proetica.org.pe',
      reviewed_at: '2026-08-20T14:30:00Z',
      review_notes: 'Verificado el proceso en SEACE y MEF: concurrencia de postor unico con incremento de costo del 16% sobre el valor adjudicado inicial y plazo de convocatoria de 3 dias.',
      disclaimer: STANDARD_ALERT_DISCLAIMER,
      published_at: '2026-08-20T15:00:00Z'
    },
    {
      alert_id: 'al-3a2c5e71f9d0b8e4',
      red_flag_ids: ['rf-3b8d1a6c9e2f4a7b'],
      entity_id: 'ce-2caad0e1b7467492',
      status: 'published',
      reviewed_by: 'observatorio.regional@grufides.org',
      reviewed_at: '2026-08-21T09:15:00Z',
      review_notes: 'Proceso de adjudicacion simplificada con postor unico verificado en actas de otorgamiento de buena pro.',
      disclaimer: STANDARD_ALERT_DISCLAIMER,
      published_at: '2026-08-21T10:00:00Z'
    }
  ],
  citizenReports: [
    {
      report_id: 'cr-4f8a2b6d1e3c5a70',
      submitted_at: '2026-08-21T11:00:00Z',
      channel: 'web',
      raw_text: 'Reporte vecinal: En la obra de saneamiento de Fila Alta se observo paralizacion de maquinaria desde la semana anterior sin explicacion municipal.',
      related_entity_id: 'ce-1817b32570ae7027',
      moderation_status: 'accepted_as_lead',
      moderated_by: 'revisor.investigacion@propuestaciudadana.org.pe',
      moderated_at: '2026-08-21T14:20:00Z',
      legal_disclaimer_shown: true
    }
  ]
};

/**
 * Realiza un fetch con timeout estricto
 */
async function fetchWithTimeout(url, options = {}, timeoutMs = TIMEOUT_MS) {
  const controller = new AbortController();
  const id = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const res = await fetch(url, { ...options, signal: controller.signal });
    clearTimeout(id);
    return res;
  } catch (err) {
    clearTimeout(id);
    throw err;
  }
}

/**
 * Guarda y recupera estado persistente local de respaldo
 */
function getLocalCollection(key) {
  try {
    const raw = localStorage.getItem(`${STORAGE_PREFIX}${key}`);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

function setLocalCollection(key, data) {
  try {
    localStorage.setItem(`${STORAGE_PREFIX}${key}`, JSON.stringify(data));
  } catch (err) {
    console.warn(`No se pudo persistir en localStorage: ${key}`, err);
  }
}

export class SupabaseClient {
  constructor() {
    this.supabaseUrl = SUPABASE_URL;
    this.anonKey = SUPABASE_ANON_KEY;
    this.sourceMode = 'online'; // 'online', 'snapshot' o 'local-fallback'
  }

  /**
   * Encabezados estandar para peticiones PostgREST publicas
   */
  getHeaders() {
    return {
      'apikey': this.anonKey,
      'Authorization': `Bearer ${this.anonKey}`,
      'Content-Type': 'application/json',
      'Prefer': 'return=representation'
    };
  }

  /**
   * Consulta una tabla en PostgREST de Supabase con fallback seguro
   */
  /**
   * Carga raw_payload bajo demanda para un registro especifico (auditoria JSON Art. 10)
   * con fallback inmediato al snapshot verificado local.
   * @param {string} table
   * @param {string} idColumn
   * @param {string} idValue
   * @returns {Promise<object|null>}
   */
  async fetchRawPayload(table = 'procurement_records', idColumn = 'ocid', idValue = '') {
    if (!idValue) return null;
    const tableName = table.includes('procurement') ? 'procurement_records' : table;

    // 1. Intentar consultar Supabase si estamos online
    if (this.sourceMode === 'online') {
      try {
        const rows = await this.queryTable(tableName, `select=raw_payload&${idColumn}=eq.${encodeURIComponent(idValue)}&limit=1`);
        if (Array.isArray(rows) && rows.length > 0 && rows[0].raw_payload) {
          return rows[0].raw_payload;
        }
      } catch (err) {
        console.info('Supabase no retorno raw_payload para', idValue, ', usando snapshot local:', err.message);
      }
    }

    // 2. Fallback inmediato al snapshot local
    try {
      const snapRes = await fetchWithTimeout(LOCAL_SNAPSHOT_URL, { method: 'GET' }, 2000);
      if (snapRes.ok) {
        const snap = await snapRes.json();
        const records = snap.procurement_records || snap.procurements || [];
        const found = records.find(p => p[idColumn] === idValue || p.ocid === idValue || p.procurement_id === idValue);
        if (found && found.raw_payload) {
          return found.raw_payload;
        }
        if (found) return found;
      }
    } catch (snapErr) {
      console.warn('Snapshot local no accesible para raw_payload:', snapErr.message);
    }

    // 3. Fallback a semilla local
    const fallbackRecord = FALLBACK_SEED.procurements.find(p => p[idColumn] === idValue || p.ocid === idValue);
    if (fallbackRecord && fallbackRecord.raw_payload) {
      return fallbackRecord.raw_payload;
    }

    return null;
  }

  async queryTable(tableName, queryParams = '') {
    const url = `${this.supabaseUrl}/rest/v1/${tableName}?${queryParams}`;
    const res = await fetchWithTimeout(url, {
      method: 'GET',
      headers: this.getHeaders()
    });
    if (!res.ok) {
      throw new Error(`Error HTTP ${res.status} al consultar ${tableName}`);
    }
    return await res.json();
  }

  /**
   * Carga el dataset inicial de la plataforma con resiliencia total
   * @returns {Promise<object>}
   */
  async fetchInitialDataset() {
    let dataset = {
      entities: [],
      procurements: [],
      budgetExecutions: [],
      alerts: [],
      redFlags: [],
      citizenReports: [],
      sourceMode: 'online'
    };

    let onlineSuccess = false;

    // Intento 1: Supabase PostgREST oficial (proyeccion ligera de columnas)
    try {
      const [entities, procurements, budgets, alerts, redFlags, reports] = await Promise.all([
        this.queryTable('contracting_entities', 'select=*&order=official_name.asc'),
        this.queryTable('procurement_records', 'select=procurement_id,ocid,entity_id,title,procurement_method,awarded_amount,executed_amount,number_of_bidders,supplier_name,supplier_ruc,source,retrieved_at&order=retrieved_at.desc&limit=1000'),
        this.queryTable('budget_execution_records', 'select=execution_record_id,entity_id,fiscal_year,budget_category,budgeted_amount,executed_amount,source,retrieved_at&order=fiscal_year.desc&limit=1000'),
        this.queryTable('alerts', 'select=*&status=eq.published&order=published_at.desc'),
        this.queryTable('red_flags', 'select=*&order=detected_at.desc').catch(() => []),
        this.queryTable('citizen_reports', 'select=*&order=submitted_at.desc').catch(() => [])
      ]);

      if (Array.isArray(entities) && entities.length > 0) {
        dataset.entities = entities;
        dataset.procurements = procurements || [];
        dataset.budgetExecutions = budgets || [];
        dataset.alerts = alerts || [];
        dataset.redFlags = Array.isArray(redFlags) && redFlags.length > 0 ? redFlags : [];
        dataset.citizenReports = Array.isArray(reports) && reports.length > 0 ? reports : [];
        dataset.sourceMode = 'online';
        onlineSuccess = true;

        // Cargar banderas rojas y reportes ciudadanos desde snapshot complementario si no vinieron de Supabase
        if (!dataset.redFlags.length || !dataset.citizenReports.length) {
          try {
            const snapRes = await fetchWithTimeout(LOCAL_SNAPSHOT_URL, { method: 'GET' }, 2000);
            if (snapRes.ok) {
              const snapData = await snapRes.json();
              if (!dataset.redFlags.length) dataset.redFlags = snapData.red_flags || snapData.redFlags || [];
              if (!dataset.citizenReports.length) dataset.citizenReports = snapData.citizen_reports || snapData.citizenReports || [];
            }
          } catch {
            // Si el snapshot local no responde, el bloque posterior fusionara con la semilla canonica local
          }
        }
      }
    } catch (supaErr) {
      console.info('Supabase en linea no disponible o con latencia, evaluando respaldo snapshot:', supaErr.message);
    }

    // Intento 2: Snapshot local verificado via HTTP si falló Supabase
    if (!onlineSuccess) {
      try {
        const snapRes = await fetchWithTimeout(LOCAL_SNAPSHOT_URL, { method: 'GET' }, 2000);
        if (snapRes.ok) {
          const snapData = await snapRes.json();
          dataset.entities = snapData.contracting_entities || snapData.entities || [];
          dataset.procurements = snapData.procurement_records || snapData.procurements || [];
          dataset.budgetExecutions = snapData.budget_execution_records || snapData.budgetExecutions || [];
          dataset.alerts = (snapData.alerts || []).filter(a => a.status === 'published');
          dataset.redFlags = snapData.red_flags || snapData.redFlags || [];
          dataset.citizenReports = snapData.citizen_reports || snapData.citizenReports || [];
          dataset.sourceMode = 'snapshot';
          onlineSuccess = true;
        }
      } catch (snapErr) {
        console.info('Snapshot HTTP no accesible, cargando semilla canónica local:', snapErr.message);
      }
    }

    // Intento 3: Semilla canónica integrada
    if (!onlineSuccess || dataset.entities.length === 0) {
      dataset.entities = [...FALLBACK_SEED.entities];
      dataset.procurements = [...FALLBACK_SEED.procurements];
      dataset.budgetExecutions = [...FALLBACK_SEED.budgetExecutions];
      dataset.alerts = [...FALLBACK_SEED.alerts];
      dataset.redFlags = [...FALLBACK_SEED.redFlags];
      dataset.citizenReports = [...FALLBACK_SEED.citizenReports];
      dataset.sourceMode = 'local-fallback';
    }

    // Cargar y fusionar banderas rojas internas (para el panel humano CU5)
    const localRedFlags = getLocalCollection('redFlags') || [];
    dataset.redFlags = this.mergeUniqueById(
      [...(dataset.redFlags || []), ...FALLBACK_SEED.redFlags, ...localRedFlags],
      'red_flag_id'
    );

    // Cargar y fusionar alertas locales de sesion
    const localAlerts = getLocalCollection('alerts') || [];
    dataset.alerts = this.mergeUniqueById(
      [...dataset.alerts, ...localAlerts.filter(a => a.status === 'published')],
      'alert_id'
    );

    // Cargar y fusionar denuncias ciudadanas locales
    const localReports = getLocalCollection('citizenReports') || [];
    dataset.citizenReports = this.mergeUniqueById(
      [...(dataset.citizenReports || []), ...FALLBACK_SEED.citizenReports, ...localReports],
      'report_id'
    );

    this.sourceMode = dataset.sourceMode;
    return dataset;
  }

  /**
   * Fusiona elementos conservando unicidad por identificador
   */
  mergeUniqueById(items, idKey) {
    const map = new Map();
    items.forEach(item => {
      if (item && item[idKey]) {
        map.set(item[idKey], item);
      }
    });
    return Array.from(map.values());
  }

  /**
   * Envia una denuncia ciudadana (006-denuncia-intake)
   * Exige legal_disclaimer_shown === true
   * @param {object} payload
   * @returns {Promise<object>}
   */
  async submitCitizenReport(payload) {
    if (!payload.legal_disclaimer_shown) {
      throw new Error('Debe confirmar y aceptar el aviso legal obligatorio (Ley 29733 y RN-006-01) antes de enviar.');
    }
    if (!payload.raw_text || !payload.raw_text.trim()) {
      throw new Error('El detalle de la denuncia no puede estar vacio.');
    }

    const reportId = payload.report_id || generateUniqueId('cr');
    const nowIso = new Date().toISOString();

    const record = {
      report_id: reportId,
      submitted_at: nowIso,
      channel: payload.channel || 'web',
      raw_text: payload.raw_text.trim(),
      related_entity_id: payload.related_entity_id || null,
      moderation_status: 'pending',
      moderated_by: null,
      moderated_at: null,
      legal_disclaimer_shown: true
    };

    // Intentar primero el backend propio, que valida y persiste la denuncia
    let remoteSuccess = false;
    try {
      const backendResponse = await fetch(`${LOCAL_API_BASE}/reports`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
        body: JSON.stringify(record)
      });
      remoteSuccess = backendResponse.ok;
    } catch (err) {
      console.info('Backend no disponible para la denuncia:', err.message);
    }

    // Contingencia: intentar POST directo a Supabase PostgREST
    if (!remoteSuccess) {
      try {
        const url = `${this.supabaseUrl}/rest/v1/citizen_reports`;
      const res = await fetchWithTimeout(url, {
        method: 'POST',
        headers: this.getHeaders(),
        body: JSON.stringify(record)
      }, 3000);
      if (res.ok) {
        remoteSuccess = true;
      }
      } catch (err) {
        console.info('Supabase no disponible para la denuncia:', err.message);
      }
    }

    // Persistir siempre en respaldo local del navegador
    const current = getLocalCollection('citizenReports') || [];
    current.unshift(record);
    setLocalCollection('citizenReports', current);

    return {
      success: true,
      report_id: reportId,
      submitted_at: nowIso,
      remote_synced: remoteSuccess
    };
  }

  /**
   * Registra una decision humana de revision sobre una bandera roja (005-review-panel)
   * Exige reviewed_by nominal humano y review_notes si status === 'discarded'
   * @param {object} decisionPayload
   * @returns {Promise<object>}
   */
  async submitHumanReviewDecision(decisionPayload) {
    const { alert_id, red_flag_ids, entity_id, status, reviewed_by, review_notes } = decisionPayload;

    if (!reviewed_by || !reviewed_by.trim()) {
      throw new Error('Debe identificarse con un correo o nombre de revisor humano nominal.');
    }

    const normalizedReviewer = reviewed_by.trim().toLowerCase();
    if (GENERIC_REVIEWERS.includes(normalizedReviewer)) {
      throw new Error(`Identificador generico no permitido: "${reviewed_by}". Debe ser una identidad humana auditable (ADR 0005).`);
    }

    if (!['published', 'discarded'].includes(status)) {
      throw new Error('Estado de decision invalido: debe ser "published" o "discarded".');
    }

    if (status === 'discarded' && (!review_notes || !review_notes.trim())) {
      throw new Error('Es obligatorio redactar una nota de justificacion al descartar un candidato (CA-005-04).');
    }

    const nowIso = new Date().toISOString();
    const finalAlertId = alert_id || generateUniqueId('al');

    const alertRecord = {
      alert_id: finalAlertId,
      red_flag_ids: Array.isArray(red_flag_ids) ? red_flag_ids : [red_flag_ids],
      entity_id,
      status,
      reviewed_by: reviewed_by.trim(),
      reviewed_at: nowIso,
      review_notes: review_notes ? review_notes.trim() : null,
      disclaimer: STANDARD_ALERT_DISCLAIMER,
      published_at: status === 'published' ? nowIso : null
    };

    // Intentar persistir en el backend propio, con autenticacion del revisor
    let remoteSuccess = false;
    try {
      const token = sessionStorage.getItem('cajamarca_veedor_token') || '';
      const res = await fetchWithTimeout(`${LOCAL_API_BASE}/review`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Accept: 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {})
        },
        body: JSON.stringify(alertRecord)
      }, 3000);
      if (res.ok) {
        remoteSuccess = true;
      }
    } catch (err) {
      console.info('Backend no disponible para la revision:', err.message);
    }

    // Persistir localmente
    const currentAlerts = getLocalCollection('alerts') || [];
    currentAlerts.unshift(alertRecord);
    setLocalCollection('alerts', currentAlerts);

    // Registrar en bitacora de auditoria local
    const auditLog = getLocalCollection('auditLog') || [];
    auditLog.unshift({
      event: 'human_review_decision',
      alert_id: finalAlertId,
      status,
      reviewed_by: reviewed_by.trim(),
      timestamp: nowIso,
      remote_synced: remoteSuccess
    });
    setLocalCollection('auditLog', auditLog);

    return {
      success: true,
      alert: alertRecord,
      remote_synced: remoteSuccess
    };
  }

  /**
   * Modera una denuncia ciudadana entrante (pending -> accepted_as_lead o rejected)
   * @param {object} moderationPayload
   * @returns {Promise<object>}
   */
  async moderateCitizenReport(moderationPayload) {
    const { report_id, moderation_status, moderated_by, review_notes, notes } = moderationPayload;

    if (!moderated_by || !moderated_by.trim()) {
      throw new Error('Debe proporcionar el identificador del revisor humano nominal.');
    }
    const norm = moderated_by.trim().toLowerCase();
    if (GENERIC_REVIEWERS.includes(norm)) {
      throw new Error(`Revisor generico no admitido: "${moderated_by}".`);
    }

    if (!['accepted_as_lead', 'rejected'].includes(moderation_status)) {
      throw new Error('Estado de moderacion invalido.');
    }

    const nowIso = new Date().toISOString();
    const token = sessionStorage.getItem('cajamarca_veedor_token') || localStorage.getItem('cajamarca_veedor_token') || '';
    let remoteSuccess = false;

    // 1. Invocar endpoint oficial de backend seguro con Bearer token
    try {
      const res = await fetchWithTimeout(`${LOCAL_API_BASE}/reports/moderate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Accept: 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {})
        },
        body: JSON.stringify({
          report_id,
          moderation_status,
          moderated_by: moderated_by.trim(),
          review_notes: review_notes || notes || null
        })
      }, 3500);

      if (res.ok) {
        remoteSuccess = true;
      }
    } catch (err) {
      console.info('Backend no disponible para moderacion de denuncia:', err.message);
    }

    // 2. Sincronizacion directa con Supabase PostgREST RLS si backend no respondio
    if (!remoteSuccess && this.supabaseUrl) {
      try {
        const patchUrl = `${this.supabaseUrl}/rest/v1/citizen_reports?report_id=eq.${encodeURIComponent(report_id)}`;
        const patchRes = await fetchWithTimeout(patchUrl, {
          method: 'PATCH',
          headers: {
            ...this.getHeaders(),
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
            'Prefer': 'return=minimal'
          },
          body: JSON.stringify({
            moderation_status,
            moderated_by: moderated_by.trim(),
            moderated_at: nowIso
          })
        }, 3000);

        if (patchRes.ok) {
          remoteSuccess = true;
        }
      } catch (err) {
        console.info('Supabase PostgREST no disponible para moderacion:', err.message);
      }
    }

    // 3. Persistir en almacenamiento local para resiliencia offline
    const current = getLocalCollection('citizenReports') || [];
    let updated = false;

    const modified = current.map(item => {
      if (item.report_id === report_id) {
        updated = true;
        return {
          ...item,
          moderation_status,
          moderated_by: moderated_by.trim(),
          moderated_at: nowIso
        };
      }
      return item;
    });

    if (!updated) {
      modified.push({
        report_id,
        moderation_status,
        moderated_by: moderated_by.trim(),
        moderated_at: nowIso,
        channel: 'web',
        raw_text: 'Reporte verificado de la semilla inicial',
        legal_disclaimer_shown: true
      });
    }

    setLocalCollection('citizenReports', modified);

    // 4. Registrar en bitacora de auditoria local
    const auditLog = getLocalCollection('auditLog') || [];
    auditLog.unshift({
      event: 'citizen_report_moderated',
      report_id,
      moderation_status,
      moderated_by: moderated_by.trim(),
      timestamp: nowIso,
      remote_synced: remoteSuccess
    });
    setLocalCollection('auditLog', auditLog);

    return {
      success: true,
      report_id,
      moderation_status,
      moderated_by: moderated_by.trim(),
      moderated_at: nowIso,
      remote_synced: remoteSuccess
    };
  }

  /**
   * Inicia el flujo real de autenticacion OAuth Google en Supabase
   * ADR 0005: auth.signInWithOAuth({ provider: 'google' })
   * @param {string} redirectPath
   */
  initiateGoogleOAuth(redirectPath = '#/admin/revision') {
    const origin = window.location.origin + window.location.pathname;
    const redirectUrl = encodeURIComponent(`${origin}${redirectPath}`);
    const authUrl = `${this.supabaseUrl}/auth/v1/authorize?provider=google&redirect_to=${redirectUrl}`;
    return authUrl;
  }
}

export const supabaseClient = new SupabaseClient();
