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
  LOCAL_API_BASE,
  STANDARD_ALERT_DISCLAIMER,
  GENERIC_REVIEWERS,
  CANONICAL_ENTITIES
} from './config.js';

const TIMEOUT_MS = 3500;
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
  procurements: [],
  budgetExecutions: [],
  alerts: [],
  redFlags: [],
  citizenReports: []
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

    dataset.redFlags = this.mergeUniqueById(dataset.redFlags || [], 'red_flag_id');
    dataset.alerts = this.mergeUniqueById(
      (dataset.alerts || []).filter(alert => alert.status === 'published'),
      'alert_id'
    );
    dataset.citizenReports = [];

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

    const response = await fetchWithTimeout(`${LOCAL_API_BASE}/reports`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
      body: JSON.stringify(payload)
    }, 3500);
    const result = await response.json();
    if (!response.ok || !result.report_id || !result.tracking_token) {
      throw new Error(result.error || 'No se pudo confirmar la recepcion de la denuncia.');
    }
    return { ...result, success: true, remote_synced: true };
  }

  /**
   * Registra una decision humana de revision sobre una bandera roja (005-review-panel)
   * Exige identidad de sesion y notas para toda decision humana
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

    if (!review_notes || !review_notes.trim()) {
      throw new Error('Es obligatorio redactar una nota para toda decision humana.');
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
      review_notes: review_notes.trim(),
      legal_disclaimer: STANDARD_ALERT_DISCLAIMER,
      published_at: status === 'published' ? nowIso : null
    };

    const token = sessionStorage.getItem('cajamarca_veedor_token') || '';
    const res = await fetchWithTimeout(`${LOCAL_API_BASE}/review`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Accept: 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}) },
      body: JSON.stringify(alertRecord)
    }, 3500);
    const result = await res.json();
    if (!res.ok || !result.alert) {
      throw new Error(result.error || 'No se pudo confirmar la decision de revision.');
    }
    return { success: true, alert: result.alert, remote_synced: true };
  }

  /** Modera solo cuando el servidor confirma la escritura y la identidad. */
  async moderateCitizenReport(moderationPayload) {
    const token = sessionStorage.getItem('cajamarca_veedor_token') || '';
    const res = await fetchWithTimeout(`${LOCAL_API_BASE}/reports/moderate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Accept: 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}) },
      body: JSON.stringify(moderationPayload)
    }, 3500);
    const result = await res.json();
    if (!res.ok || !result.success || !result.report) {
      throw new Error(result.error || 'No se pudo confirmar la moderacion.');
    }
    return { ...result, remote_synced: true };
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
