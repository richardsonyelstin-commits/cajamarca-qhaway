/**
 * config.js: Configuracion centralizada de Cajamarca Qhaway
 * Observatorio Civico Regional (Region Cajamarca, Fase 1)
 *
 * Restricciones:
 * - Antislop R-02: Cero rayas em-dash en todo el archivo.
 * - Seguridad RLS: Clave publica/anon de Supabase.
 */

export const SUPABASE_URL = 'https://tiythjlrjhvwkiqsnvwq.supabase.co';
export const SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRpeXRoamxyamh2d2tpcXNudndxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODcxMDA4NTgsImV4cCI6MjEwMjY3Njg1OH0.9XJYT7VNOwRAgAjjrqSmL_pOTwk9oH78HEeixoGqFDE';
export const SUPABASE_PUBLISHABLE_KEY = 'sb_publishable_Oznams5bONH35-O7kim37Q_I6g6sKJz';
export const LOCAL_API_BASE = '/api';
export const LOCAL_SNAPSHOT_URL = 'src/data/verified-snapshot.json';

export const STANDARD_ALERT_DISCLAIMER =
  'Indicador de riesgo automatizado, no constituye prueba ni acusación formal de corrupción.';

export const CITIZEN_REPORT_DISCLAIMER =
  'Aviso legal obligatorio (Ley 29733 y RN-006-01): Cajamarca Qhaway es una plataforma cívica independiente y NO es el SINAD de la Contraloría General de la República. No otorga medidas de protección laboral ni reserva legal estatal. No incluya datos personales sensibles de terceros no verificables.';

export const GENERIC_REVIEWERS = Object.freeze([
  'admin',
  'system',
  'root',
  'bot',
  'auto',
  'automated',
  'null',
  'none',
  'anonymous'
]);

export const CAJAMARCA_PROVINCES = Object.freeze([
  'CAJAMARCA',
  'CAJABAMBA',
  'CELENDIN',
  'CHOTA',
  'CONTUMAZA',
  'CUTERVO',
  'HUALGAYOC',
  'JAEN',
  'SAN IGNACIO',
  'SAN MARCOS',
  'SAN MIGUEL',
  'SAN PABLO',
  'SANTA CRUZ'
]);

export const CANONICAL_INDICATORS = Object.freeze({
  'single-bidder': {
    code: 'single-bidder',
    name: 'Licitacion con postor unico',
    formula_description: 'Licitacion competitiva adjudicada con un unico postor participante (numberOfTenderers == 1)',
    default_threshold: 1,
    unit: 'postores',
    plain_title: 'Unica oferta presentada',
    plain_description: 'Solo una empresa participo en la licitacion, por lo que no existio competencia de precios ni de propuestas tecnicas para el Estado.',
    recommendation: 'Revisar si las bases tecnicas tuvieron clausulas restrictivas que desalentaron a otros proveedores locales.'
  },
  'execution-overrun': {
    code: 'execution-overrun',
    name: 'Sobrecosto o desvio presupuestal',
    formula_description: 'Monto ejecutado excede el presupuesto institucional modificado o adjudicado en mas del 10%',
    default_threshold: 1.10,
    unit: 'ratio',
    plain_title: 'Incremento del presupuesto contractual',
    plain_description: 'El gasto devengado o en ejecucion supero en mas del 10% el presupuesto institucional modificado o adjudicado.',
    recommendation: 'Auditar adendas contractuales y valorizaciones de obra aprobadas por la supervision.'
  },
  'contract-concentration': {
    code: 'contract-concentration',
    name: 'Concentracion de contratacion en un proveedor',
    formula_description: 'Un solo proveedor concentra mas del 40% del monto total adjudicado por la entidad en el periodo',
    default_threshold: 0.40,
    unit: 'ratio',
    plain_title: 'Concentracion inusual de compras en una firma',
    plain_description: 'Mas del 40% del total de recursos licitados por esta entidad en el periodo fueron asignados al mismo proveedor.',
    recommendation: 'Inspeccionar la rotacion de proveedores y la neutralidad de los comites de seleccion.'
  },
  'short-tender-window': {
    code: 'short-tender-window',
    name: 'Ventana anormalmente corta de licitacion',
    formula_description: 'Periodo de convocatoria y presentacion de ofertas inferior al plazo minimo prudencial de 5 dias',
    default_threshold: 5,
    unit: 'dias',
    plain_title: 'Plazo muy corto para postular',
    plain_description: 'El tiempo otorgado entre la publicacion y la entrega de ofertas fue menor a 5 dias calendario, impidiendo una evaluacion tecnica rigurosa.',
    recommendation: 'Verificar si la premura obedecio a una emergencia acreditada o a una limitacion indebida del acceso publico.'
  },
  'direct-award-threshold': {
    code: 'direct-award-threshold',
    name: 'Adjudicacion directa en umbral critico',
    formula_description: 'Contratacion directa cuyo monto roza sospechosamente el umbral limite de exoneracion legal',
    default_threshold: 40000.0,
    unit: 'PEN',
    plain_title: 'Contratacion directa cerca del tope sin concurso',
    plain_description: 'El monto adjudicado directamente se ubica justo en el limite legal para evitar un proceso competitivo abierto.',
    recommendation: 'Verificar presupuestos de referencia y cotizaciones previas del estudio de mercado.'
  },
  'direct-administration-equipment-rent': {
    code: 'direct-administration-equipment-rent',
    name: 'Alquiler irregular de maquinaria en administracion directa',
    formula_description: 'Facturacion o cobro de alquiler de maquinaria propia en obras por administracion directa hacia RDR',
    default_threshold: 1,
    unit: 'ocurrencias',
    plain_title: 'Cobro cruzado de maquinaria propia municipal',
    plain_description: 'Se registro facturacion interna o alquiler de maquinaria propia en obras de administracion directa hacia recursos directamente recaudados.',
    recommendation: 'Solicitar partes diarios de maquinaria y bitacoras de combustible de la subgerencia de obras.'
  },
  'contract-splitting-orders': {
    code: 'contract-splitting-orders',
    name: 'Fraccionamiento en ordenes consecutivas menores a 8 UIT',
    formula_description: 'Emision de 3 o mas ordenes de compra o servicio menores a 8 UIT al mismo proveedor en menos de 30 dias',
    default_threshold: 3,
    unit: 'ordenes',
    plain_title: 'Compras divididas para evitar licitacion (menor a 8 UIT)',
    plain_description: 'Se emitieron 3 o mas ordenes menores a 8 UIT a favor del mismo proveedor en menos de un mes por bienes o servicios similares.',
    recommendation: 'Cruzar el registro de ordenes de compra SIAF/SEACE del mes para descartar fraccionamiento prohibido.'
  }
});

export const CANONICAL_ENTITIES = Object.freeze([
  {
    entity_id: 'ce-f5f5d8fc32518855',
    official_name: 'GOBIERNO REGIONAL DE CAJAMARCA',
    entity_level: 'regional',
    province: null,
    ruc: '20453744168',
    consucode_id: null,
    department: 'CAJAMARCA',
    verified_at: '2026-08-20T00:00:00Z',
    active: true
  },
  {
    entity_id: 'ce-2caad0e1b7467492',
    official_name: 'MUNICIPALIDAD PROVINCIAL DE CAJAMARCA',
    entity_level: 'provincial_municipality',
    province: 'CAJAMARCA',
    ruc: '20143623042',
    consucode_id: null,
    department: 'CAJAMARCA',
    verified_at: '2026-08-20T00:00:00Z',
    active: true
  },
  {
    entity_id: 'ce-b4a52d15b3cffe4f',
    official_name: 'MUNICIPALIDAD PROVINCIAL DE CAJABAMBA',
    entity_level: 'provincial_municipality',
    province: 'CAJABAMBA',
    ruc: '20148288853',
    consucode_id: null,
    department: 'CAJAMARCA',
    verified_at: '2026-08-20T00:00:00Z',
    active: true
  },
  {
    entity_id: 'ce-2b779c1e84ff4365',
    official_name: 'MUNICIPALIDAD PROVINCIAL DE CELENDIN',
    entity_level: 'provincial_municipality',
    province: 'CELENDIN',
    ruc: '20148289825',
    consucode_id: null,
    department: 'CAJAMARCA',
    verified_at: '2026-08-20T00:00:00Z',
    active: true
  },
  {
    entity_id: 'ce-45fad1d64ba4bf0f',
    official_name: 'MUNICIPALIDAD PROVINCIAL DE CHOTA',
    entity_level: 'provincial_municipality',
    province: 'CHOTA',
    ruc: '20220499767',
    consucode_id: null,
    department: 'CAJAMARCA',
    verified_at: '2026-08-20T00:00:00Z',
    active: true
  },
  {
    entity_id: 'ce-3337df921084c80a',
    official_name: 'MUNICIPALIDAD PROVINCIAL DE CONTUMAZA',
    entity_level: 'provincial_municipality',
    province: 'CONTUMAZA',
    ruc: '20191657447',
    consucode_id: null,
    department: 'CAJAMARCA',
    verified_at: '2026-08-20T00:00:00Z',
    active: true
  },
  {
    entity_id: 'ce-360cf7aadccadabb',
    official_name: 'MUNICIPALIDAD PROVINCIAL DE CUTERVO',
    entity_level: 'provincial_municipality',
    province: 'CUTERVO',
    ruc: '20174691267',
    consucode_id: null,
    department: 'CAJAMARCA',
    verified_at: '2026-08-20T00:00:00Z',
    active: true
  },
  {
    entity_id: 'ce-dfd10c914365bbe3',
    official_name: 'MUNICIPALIDAD PROVINCIAL DE HUALGAYOC',
    entity_level: 'provincial_municipality',
    province: 'HUALGAYOC',
    ruc: '20148260843',
    consucode_id: null,
    department: 'CAJAMARCA',
    verified_at: '2026-08-20T00:00:00Z',
    active: true
  },
  {
    entity_id: 'ce-1817b32570ae7027',
    official_name: 'MUNICIPALIDAD PROVINCIAL DE JAEN',
    entity_level: 'provincial_municipality',
    province: 'JAEN',
    ruc: '20201987297',
    consucode_id: null,
    department: 'CAJAMARCA',
    verified_at: '2026-08-20T00:00:00Z',
    active: true
  },
  {
    entity_id: 'ce-697eb5a0a1b4e6c6',
    official_name: 'MUNICIPALIDAD PROVINCIAL SAN IGNACIO',
    entity_level: 'provincial_municipality',
    province: 'SAN IGNACIO',
    ruc: '20148261572',
    consucode_id: null,
    department: 'CAJAMARCA',
    verified_at: '2026-08-20T00:00:00Z',
    active: true
  },
  {
    entity_id: 'ce-ad540c85ce98e1d8',
    official_name: 'MUNICIPALIDAD PROVINCIAL DE SAN MARCOS',
    entity_level: 'provincial_municipality',
    province: 'SAN MARCOS',
    ruc: '20175083937',
    consucode_id: null,
    department: 'CAJAMARCA',
    verified_at: '2026-08-20T00:00:00Z',
    active: true
  },
  {
    entity_id: 'ce-3511b005adba63bf',
    official_name: 'MUNICIPALIDAD PROVINCIAL SAN MIGUEL',
    entity_level: 'provincial_municipality',
    province: 'SAN MIGUEL',
    ruc: '20143625843',
    consucode_id: null,
    department: 'CAJAMARCA',
    verified_at: '2026-08-20T00:00:00Z',
    active: true
  },
  {
    entity_id: 'ce-d7fc753b1fb5ff5b',
    official_name: 'MUNICIPALIDAD PROVINCIAL DE SAN PABLO',
    entity_level: 'provincial_municipality',
    province: 'SAN PABLO',
    ruc: '20172446800',
    consucode_id: null,
    department: 'CAJAMARCA',
    verified_at: '2026-08-20T00:00:00Z',
    active: true
  },
  {
    entity_id: 'ce-f29ffd64eff3fe9a',
    official_name: 'MUNICIPALIDAD PROVINCIAL DE SANTA CRUZ',
    entity_level: 'provincial_municipality',
    province: 'SANTA CRUZ',
    ruc: '20200367376',
    consucode_id: null,
    department: 'CAJAMARCA',
    verified_at: '2026-08-20T00:00:00Z',
    active: true
  }
]);
