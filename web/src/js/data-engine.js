/**
 * data-engine.js: Motor de datos, calculos analiticos y metricas HHI para Cajamarca Qhaway
 * Conecta con los datos oficiales de SEACE OCDS y MEF SIAF DataStore
 *
 * Politicas:
 * - Antislop R-02: Cero rayas em-dash en todo el archivo.
 * - Prioridad de carga: API backend con timeout -> verified-snapshot.json -> SEED_DATA.
 * - Soporte para enriquecimiento RUC/SUNAT (supplier_sunat / /api/sunat/ruc).
 */

import {
  CANONICAL_ENTITIES,
  CANONICAL_INDICATORS,
  LOCAL_API_BASE
} from './config.js';

class DataEngine {
  constructor() {
    this.snapshot = null;
    this.loaded = false;
    this.loadPromise = null;
    this.sunatCache = new Map();
    this.budgetView = { year: null, scope: 'ActProy', cutType: null, funding: 'all' };
  }

  async _fetch(url, options = {}, timeoutMs = 3500) {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), timeoutMs);
    try {
      return await fetch(url, { ...options, signal: controller.signal });
    } finally {
      clearTimeout(timer);
    }
  }

  async _fetchBackendSnapshot() {
    try {
      const response = await this._fetch(`${LOCAL_API_BASE}/snapshot`, {
        headers: { Accept: 'application/json' }
      });
      if (!response.ok) return null;
      const snapshot = await response.json();
      if (!snapshot || !Array.isArray(snapshot.contracting_entities)) return null;
      return snapshot;
    } catch (error) {
      console.warn('Backend API no disponible:', error.message);
      return null;
    }
  }

  async load() {
    if (this.loaded && this.snapshot) return this.snapshot;
    if (this.loadPromise) return this.loadPromise;

    this.loadPromise = (async () => {
      // Prioridad 1: Backend propio, que centraliza la conexion con datos reales
      const backendSnapshot = await this._fetchBackendSnapshot();
      if (backendSnapshot) {
        this.snapshot = {
          ...backendSnapshot,
          metadata: {
            ...(backendSnapshot.metadata || {}),
            source_mode: backendSnapshot.metadata?.source_mode || 'backend-api'
          },
          alerts: backendSnapshot.alerts || []
        };
        this.loaded = true;
        return this.snapshot;
      }

      // Prioridad 2: snapshot estatico verificado con timeout estricto.
      const snapshotPaths = ['/src/data/verified-snapshot.json', './src/data/verified-snapshot.json'];
      for (const snapPath of snapshotPaths) {
        try {
          const res2 = await this._fetch(snapPath);
          if (res2.ok) {
            const fileSnapshot = await res2.json();
            if (fileSnapshot && fileSnapshot.contracting_entities) {
              this.snapshot = {
                ...fileSnapshot,
                metadata: {
                  ...(fileSnapshot.metadata || {}),
                  source_mode: 'local-snapshot'
                }
              };
              this.loaded = true;
              return this.snapshot;
            }
          }
        } catch (fileErr) {
          console.warn(`No se pudo leer ${snapPath}:`, fileErr.message);
        }
      }

      // Prioridad 3: respaldo de contingencia con semilla canonica.
      this.snapshot = {
        metadata: {
          version: '1.0.0',
          generated_at: new Date().toISOString(),
          region: 'CAJAMARCA',
          source_mode: 'seed-contingency'
        },
        contracting_entities: CANONICAL_ENTITIES,
        procurement_records: [],
        budget_execution_records: [],
        red_flags: [],
        alerts: [],
        citizen_reports: []
      };
      this.loaded = true;
      return this.snapshot;
    })();

    return this.loadPromise;
  }

  async init() {
    return this.load();
  }

  async getSnapshot() {
    await this.load();
    return this.snapshot;
  }

  async getEntities() {
    await this.load();
    return this.snapshot.contracting_entities || CANONICAL_ENTITIES;
  }

  async getEntityById(id) {
    if (!id) return null;
    const entities = await this.getEntities();
    const cleanId = String(id).trim().toLowerCase();
    return entities.find(e => {
      if (e.entity_id === id || e.ruc === id) return true;
      const provSlug = (e.province || '').toLowerCase().replace(/\s+/g, '-');
      if (cleanId === `mp-${provSlug}` || cleanId === provSlug) return true;
      if (cleanId === 'gore-cajamarca' && e.entity_level === 'regional') return true;
      return false;
    }) || null;
  }

  async getProcurements(entityId = null, fiscalYear = null) {
    await this.load();
    let records = this.snapshot.procurement_records || [];
    if (entityId) {
      records = records.filter(p => p.entity_id === entityId);
    }
    if (fiscalYear && fiscalYear !== 'all' && fiscalYear !== 'Todos') {
      const yearStr = String(fiscalYear);
      records = records.filter(p => {
        return String(this.getProcurementYear(p) || '') === yearStr;
      });
    }
    return records;
  }

  getProcurementYear(record) {
    const raw = record.raw_payload || {};
    const date = raw.tender?.tenderPeriod?.startDate || raw.publishedDate || raw.tender?.datePublished;
    if (date && /^\d{4}-/.test(date)) return Number(date.slice(0, 4));
    const years = [...new Set((record.source_evidence || [])
      .filter(e => e.dataset === 'convocatorias').map(e => Number(e.fiscal_year)))];
    return years.length === 1 ? years[0] : null;
  }

  async getProcurementByOcid(ocid) {
    const list = await this.getProcurements();
    return list.find(p => p.ocid === ocid || p.procurement_id === ocid) || null;
  }

  async getBudgetRecords(entityId = null, fiscalYear = null) {
    await this.load();
    let records = (this.snapshot.budget_execution_records || []).filter(b =>
      b.is_canonical_total === true || ['TOTAL', 'TOTAL_INSTITUCIONAL_ACTPROY'].includes(b.budget_category));
    const seen = new Set();
    for (const record of records) {
      const key = `${record.entity_id}:${record.fiscal_year}`;
      if (seen.has(key)) throw new Error(`Maestro presupuestal duplicado: ${key}`);
      seen.add(key);
    }
    const year = fiscalYear ?? this.budgetView.year ?? Math.max(0, ...records.map(b => Number(b.fiscal_year)));
    if (entityId) {
      records = records.filter(b => b.entity_id === entityId);
    }
    if (year && year !== 'all' && year !== 'Todos') {
      records = records.filter(b => String(b.fiscal_year) === String(year));
    }
    return records;
  }

  _viewRecord(record, scope, cutType) {
    const currentCut = record.cut_type || record.raw_payload?.CUT_TYPE || 'monthly';
    if (cutType && cutType !== currentCut) {
      const comparison = (record.comparison_cuts || []).find(cut => cut.cut_type === cutType);
      if (!comparison || scope !== 'ActProy') return null;
      return { ...record, ...comparison.total.moments, cut_type: cutType,
        official_cut_date: comparison.total.official_cut_date,
        breakdown_by_funding_source: comparison.total.breakdown_by_funding_source,
        raw_payload: comparison.total.raw_payload, selected_scope: 'ActProy' };
    }
    if (scope === 'ActProy') return { ...record, selected_scope: scope, cut_type: currentCut };
    const detail = record.breakdown_by_scope?.[scope];
    if (!detail) return null;
    return { ...record, ...detail.moments, official_cut_date: detail.official_cut_date,
      breakdown_by_funding_source: detail.breakdown_by_funding_source,
      raw_payload: detail.raw_payload, selected_scope: scope, cut_type: currentCut };
  }

  _fundingView(record) {
    const code = this.budgetView.funding || 'all';
    if (code === 'all') return record;
    const sources = record.breakdown_by_funding_source || [];
    if (!sources.length) throw new Error('Este corte no conserva el desglose de financiamiento');
    const matches = sources.flatMap(source => source.rubros || []).filter(rubro => rubro.code === code);
    if (matches.length > 1) throw new Error('Rubro duplicado en las fuentes de financiamiento');
    const fields = ['pia_amount','modification_amount','budgeted_amount','certified_amount',
      'committed_annual_amount','monthly_commitment_amount','executed_amount','paid_amount','execution_pct'];
    const moments = Object.fromEntries(fields.map(field => [field, matches.length ? matches[0].moments[field] ?? null : 0]));
    return { ...record, ...moments, selected_funding: code, funding_absent: !matches.length,
      raw_payload: matches.length ? matches[0].raw_payload : record.raw_payload };
  }

  async getBudgetView(entityId = null, fiscalYear = null, scope = null, cutType = null) {
    const records = await this.getBudgetRecords(entityId, fiscalYear);
    const expected = this.snapshot.contracting_entities || [];
    if (expected.length && !records.length) throw new Error('No hay cobertura MEF para la seleccion');
    if (!entityId && expected.length) {
      for (const year of new Set(records.map(record => record.fiscal_year))) {
        const covered = new Set(records.filter(record => record.fiscal_year === year).map(record => record.entity_id));
        if (expected.some(entity => !covered.has(entity.entity_id))) throw new Error('Cobertura MEF parcial para el ejercicio elegido');
      }
    }
    const selectedScope = scope || this.budgetView.scope;
    const selectedCut = cutType || this.budgetView.cutType;
    const views = records.map(record => this._viewRecord(record, selectedScope, selectedCut));
    if (views.some(record => !record)) throw new Error('Desglose no disponible para el ambito y corte elegidos');
    return views.map(record => this._fundingView(record));
  }

  async getBudgetSummary(entityId = null, fiscalYear = null, scope = null, cutType = null) {
    const rows = await this.getBudgetView(entityId, fiscalYear, scope, cutType);
    const years = new Set(rows.map(row => Number(row.fiscal_year)));
    if (years.size > 1) throw new Error('El comparativo debe presentar cada ejercicio por separado');
    const fields = ['pia_amount', 'modification_amount', 'budgeted_amount', 'certified_amount',
      'committed_annual_amount', 'monthly_commitment_amount', 'executed_amount', 'paid_amount'];
    const moments = {};
    for (const field of fields) {
      moments[field] = rows.length && rows.every(row => row[field] != null && Number.isFinite(Number(row[field])))
        ? rows.reduce((sum, row) => sum + Number(row[field]), 0) : null;
    }
    moments.execution_pct = moments.budgeted_amount > 0
      ? Number((moments.executed_amount / moments.budgeted_amount * 100).toFixed(1)) : 0;
    return { rows, moments, officialCutDates: [...new Set(rows.map(row => row.official_cut_date ||
      row.raw_payload?.FECHA_CORTE_OFICIAL).filter(Boolean))] };
  }

  async getAlerts(entityId = null) {
    await this.load();
    let records = (this.snapshot.alerts || []).filter(a => a.status === 'published');
    if (entityId) {
      records = records.filter(a => a.entity_id === entityId);
    }
    return records;
  }

  async getRedFlags(entityId = null) {
    await this.load();
    let flags = this.snapshot.red_flags || [];
    if (entityId) {
      const entityProcs = (await this.getProcurements(entityId)).map(p => p.procurement_id);
      const entityBudgets = (await this.getBudgetRecords(entityId, 'all')).map(b => b.execution_record_id);
      flags = flags.filter(f =>
        (f.procurement_ids || []).some(pid => entityProcs.includes(pid)) ||
        (f.execution_record_ids || []).some(bid => entityBudgets.includes(bid))
      );
    }
    return flags;
  }

  /**
   * Obtiene estadisticas consolidadas y monto auditado de alertas publicadas (Art. 14)
   */
  async getPublishedAlertsStats() {
    await this.load();
    const alerts = await this.getAlerts();
    const flagsMap = new Map((this.snapshot.red_flags || []).map(f => [f.red_flag_id, f]));
    const procsMap = new Map((this.snapshot.procurement_records || []).map(p => [p.procurement_id, p]));
    const budgetsMap = new Map((this.snapshot.budget_execution_records || []).map(b => [b.execution_record_id, b]));

    let flaggedAmount = 0;
    const distinctEntities = new Set();
    let critCount = 0;
    let highCount = 0;
    let medCount = 0;

    for (const a of alerts) {
      distinctEntities.add(a.entity_id);
      const flagId = (a.red_flag_ids && a.red_flag_ids[0]) || '';
      const flag = flagsMap.get(flagId) || {};
      const code = flag.indicator_code || '';
      const isCrit = code === 'single-bidder' || code === 'mef-underspending' || code === 'recurrent-direct-award';

      if (isCrit) {
        critCount++;
      } else {
        highCount++;
      }

      // Sumar montos observados
      for (const pid of (flag.procurement_ids || [])) {
        const proc = procsMap.get(pid);
        if (proc && proc.awarded_amount) flaggedAmount += Number(proc.awarded_amount);
      }
      for (const bid of (flag.execution_record_ids || [])) {
        const b = budgetsMap.get(bid);
        if (b && b.executed_amount) flaggedAmount += Number(b.executed_amount);
      }
    }

    return {
      total: alerts.length,
      critCount,
      highCount,
      medCount,
      distinctEntitiesCount: distinctEntities.size,
      flaggedAmount
    };
  }

  async getMacroKPIs(fiscalYear = null) {
    await this.load();
    const singleYear = ['all', 'Todos'].includes(fiscalYear) ? null : fiscalYear;
    const budgets = await this.getBudgetView(null, singleYear);

    const procurements = await this.getProcurements(null, fiscalYear);
    const alerts = this.snapshot.alerts || [];
    const redFlags = this.snapshot.red_flags || [];

    const totalPim = budgets.reduce((acc, b) => acc + (Number(b.budgeted_amount) || 0), 0);
    const totalDevengado = budgets.reduce((acc, b) => acc + (Number(b.executed_amount) || 0), 0);
    const executionRate = totalPim > 0 ? Number(((totalDevengado / totalPim) * 100).toFixed(1)) : 0.0;
    const totalAwarded = procurements.reduce((acc, p) => acc + (Number(p.awarded_amount) || 0), 0);

    return {
      totalPim,
      totalDevengado,
      executionRate,
      totalProcurements: procurements.length,
      totalAwarded,
      totalAlerts: alerts.filter(a => a.status === 'published').length,
      totalRedFlags: redFlags.length,
      entitiesCount: (this.snapshot.contracting_entities || []).length
    };
  }

  /**
   * Obtiene estadisticas presupuestales consolidadas para una entidad especifica
   * @param {string} entityId
   * @param {string|null} fiscalYear
   * @returns {Promise<object>}
   */
  async getEntityBudgetStats(entityId, fiscalYear = null) {
    const singleYear = ['all', 'Todos'].includes(fiscalYear) ? null : fiscalYear;
    const budgets = await this.getBudgetView(entityId, singleYear);
    const pim = budgets.reduce((acc, b) => acc + (Number(b.budgeted_amount) || 0), 0);
    const devengado = budgets.reduce((acc, b) => acc + (Number(b.executed_amount) || 0), 0);
    const rate = pim > 0 ? Number(((devengado / pim) * 100).toFixed(1)) : 0.0;
    return {
      entityId,
      pim,
      devengado,
      rate
    };
  }

  /** Suma rubros del ambito elegido sin agregar sus fuentes padre. */
  getFundingComposition(entityId = null, fiscalYear = null) {
    const all = this.snapshot?.budget_execution_records || [];
    const year = fiscalYear ?? this.budgetView.year ?? Math.max(0, ...all.map(row => Number(row.fiscal_year)));
    const records = all.filter(row => Number(row.fiscal_year) === Number(year) &&
      (!entityId || row.entity_id === entityId) &&
      (row.is_canonical_total || ['TOTAL', 'TOTAL_INSTITUCIONAL_ACTPROY'].includes(row.budget_category)));
    const bases = records.map(row => this._viewRecord(row, this.budgetView.scope, this.budgetView.cutType));
    const views = bases.map(row => row ? this._fundingView(row) : null);
    if (!views.length || views.some(row => !row?.breakdown_by_funding_source?.length)) return null;
    const rubros = new Map();
    let total = 0;
    for (const view of views) {
      total += Number(view.budgeted_amount);
      for (const source of view.breakdown_by_funding_source) {
        for (const rubro of source.rubros || []) {
          if (this.budgetView.funding && this.budgetView.funding !== 'all' && rubro.code !== this.budgetView.funding) continue;
          const current = rubros.get(rubro.code) || { code: rubro.code, label: rubro.label,
            pim: 0, devengado: 0, girado: 0, sourceCode: source.code };
          current.pim += Number(rubro.moments.budgeted_amount);
          current.devengado += Number(rubro.moments.executed_amount);
          current.girado += Number(rubro.moments.paid_amount);
          rubros.set(rubro.code, current);
        }
      }
    }
    const component = code => ({ amount: rubros.get(code)?.pim || 0,
      pct: total ? Number(((rubros.get(code)?.pim || 0) / total * 100).toFixed(1)) : 0 });
    return { total, rubros: [...rubros.values()], canon: component('18'),
      recursosOrdinarios: component('00'), foncomun: component('07'), rdr: component('09') };
  }

  /**
   * Enriquecimiento de Proveedor via SUNAT (Padrón RUC oficial)
   * Soporta /api/sunat/ruc y enriquecimiento determinista OCDS
   * @param {string} ruc
   * @param {string} name
   * @returns {Promise<object>}
   */
  async getSupplierSunat(ruc, name = '') {
    if (!ruc || ruc === 'Sin RUC') return null;
    const cleanRuc = String(ruc).trim();
    if (this.sunatCache.has(cleanRuc)) {
      return this.sunatCache.get(cleanRuc);
    }

    // 1. Consultar endpoint REST /api/sunat/ruc si esta disponible
    try {
      const res = await fetch(`/api/sunat/ruc?ruc=${encodeURIComponent(cleanRuc)}`);
      if (res.ok) {
        const data = await res.json();
        this.sunatCache.set(cleanRuc, data);
        return data;
      }
    } catch {
      // Continuar con enriquecimiento OCDS
    }

    // 2. Enriquecimiento determinista con validacion de RUC peruano
    const isRucValido = /^([12]\d{10})$/.test(cleanRuc);
    const sunatData = {
      ruc: cleanRuc,
      razon_social: name || 'PROVEEDOR REGISTRADO',
      estado: isRucValido ? 'NO VERIFICADO' : 'RUC INVALIDO',
      condicion: isRucValido ? 'CONSULTA PENDIENTE' : 'NO REGISTRADO',
      domicilio_fiscal: 'CAJAMARCA, PERU',
      sistema_emision: 'ELECTRONICA',
      tipo_contribuyente: cleanRuc.startsWith('20') ? 'PERSONA JURIDICA' : 'PERSONA NATURAL CON NEGOCIO'
    };
    this.sunatCache.set(cleanRuc, sunatData);
    return sunatData;
  }

  formatSupplierId(rawId) {
    if (!rawId || rawId === 'Sin RUC' || rawId === 'undefined' || rawId === 'null') {
      return {
        clean: 'Sin RUC',
        label: 'Sin RUC',
        isConsorcio: false,
        isRuc11: false,
        badgeHtml: '<span class="px-1.5 py-0.5 rounded text-[10px] bg-surface-container text-outline font-mono">Sin RUC</span>'
      };
    }
    const clean = String(rawId).replace(/^PE-RUC-/, '').trim();
    if (/^\d{11}$/.test(clean)) {
      return {
        clean,
        label: clean,
        isConsorcio: false,
        isRuc11: true,
        badgeHtml: `<span class="font-mono text-xs font-semibold text-on-surface">${clean}</span>`
      };
    }
    if (/^\d{6,9}$/.test(clean)) {
      return {
        clean,
        label: `OSCE-${clean}`,
        isConsorcio: true,
        isRuc11: false,
        badgeHtml: `<span class="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-mono font-medium bg-secondary-container/30 text-secondary border border-secondary/20" title="Consorcio Registrado en OSCE N° ${clean}"><span class="material-symbols-outlined text-[11px]">badge</span><span>Consorcio OSCE: ${clean}</span></span>`
      };
    }
    return {
      clean,
      label: clean,
      isConsorcio: false,
      isRuc11: false,
      badgeHtml: `<span class="font-mono text-caption text-outline">${clean}</span>`
    };
  }

  /**
   * Calcula el Indice Herfindahl-Hirschman (HHI) y cuotas de mercado
   * Formula HHI = Sum(s_i ^ 2) donde s_i es la fraccion de mercado [0..1]
   */
  async calculateHHI(entityId = null, fiscalYear = null) {
    const procurements = await this.getProcurements(entityId, fiscalYear);
    const supplierTotals = new Map();
    let grandTotal = 0;

    for (const p of procurements) {
      const rawAwardSupp = (p.raw_payload && p.raw_payload.awards && p.raw_payload.awards[0] && p.raw_payload.awards[0].suppliers && p.raw_payload.awards[0].suppliers[0]) ? p.raw_payload.awards[0].suppliers[0] : null;
      const name = p.supplier_name || (rawAwardSupp ? rawAwardSupp.name : null) || 'Proveedor en Convocatoria';
      let rawRuc = p.supplier_ruc || (rawAwardSupp ? String(rawAwardSupp.id) : 'Sin RUC');
      const rucInfo = this.formatSupplierId(rawRuc);
      const ruc = rucInfo.clean;
      const supKey = ruc !== 'Sin RUC' ? ruc : name;
      const amount = Number(p.awarded_amount) || Number(p.executed_amount) || 0;

      if (!supplierTotals.has(supKey)) {
        supplierTotals.set(supKey, {
          ruc,
          rucInfo,
          name,
          totalAmount: 0,
          contractsCount: 0,
          contracts: []
        });
      }
      const item = supplierTotals.get(supKey);
      item.totalAmount += amount;
      item.contractsCount += 1;
      item.contracts.push(p);
      grandTotal += amount;
    }

    if (grandTotal === 0) {
      grandTotal = 1;
    }

    const suppliers = Array.from(supplierTotals.values()).map(s => {
      const share = s.totalAmount / grandTotal;
      return {
        ...s,
        share,
        sharePct: Number((share * 100).toFixed(1))
      };
    });

    suppliers.sort((a, b) => b.totalAmount - a.totalAmount);

    const hhi = suppliers.reduce((sum, s) => sum + Math.pow(s.share, 2), 0);

    return {
      hhi: Number(hhi.toFixed(2)),
      hhiScore: Math.round(hhi * 10000),
      grandTotal,
      suppliersCount: suppliers.length,
      topSuppliers: suppliers
    };
  }

  /**
   * Obtiene el catalogo de obras publicas geo-monitoreadas (Capacidad 007).
   * @param {string|null} province
   * @returns {Promise<Array>}
   */
  async getGeospatialWorks(province = null) {
    try {
      const url = province ? `/api/geospatial/works?province=${encodeURIComponent(province)}` : '/api/geospatial/works';
      const res = await fetch(url);
      if (res.ok) {
        return await res.json();
      }
    } catch {}

    const snap = await this.getSnapshot();
    let works = snap.geospatial_works || [];
    if (province) {
      const target = province.trim().toLowerCase();
      works = works.filter(w => (w.province || '').trim().toLowerCase() === target);
    }
    return works;
  }

  /**
   * Obtiene las senales de divergencia fisico-financiera (Capacidad 007).
   * @param {string|null} siteId
   * @param {string|null} severity
   * @returns {Promise<Array>}
   */
  async getGeospatialDivergences(siteId = null, severity = null) {
    try {
      const params = new URLSearchParams();
      if (siteId) params.append('site_id', siteId);
      if (severity) params.append('severity', severity);
      const query = params.toString() ? `?${params.toString()}` : '';
      const res = await fetch(`/api/geospatial/divergence${query}`);
      if (res.ok) {
        return await res.json();
      }
    } catch {}

    const snap = await this.getSnapshot();
    let signals = snap.geospatial_signals || [];
    if (siteId) {
      signals = signals.filter(s => s.site_id === siteId);
    }
    if (severity) {
      const target = severity.trim().toLowerCase();
      signals = signals.filter(s => (s.severity || '').trim().toLowerCase() === target);
    }
    return signals;
  }

  formatMillions(amount) {
    if (!amount) return 'S/ 0.0 M';
    const millions = amount / 1000000;
    return `S/ ${millions.toLocaleString('es-PE', { minimumFractionDigits: 1, maximumFractionDigits: 1 })} M`;
  }

  formatBudgetAmount(amount) {
    return `S/ ${Number(amount).toLocaleString('en-US', { maximumFractionDigits: 0 })}`;
  }

  formatCurrency(amount) {
    if (amount == null) return 'S/ 0.00';
    return `S/ ${Number(amount).toLocaleString('es-PE', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  }
}

export const dataEngine = new DataEngine();
