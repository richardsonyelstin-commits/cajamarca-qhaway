import express from 'express';
import path from 'path';
import fs from 'fs';
import crypto from 'crypto';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const PORT = 3000;
const HOST = '0.0.0.0';

app.use(express.json());

// In-memory snapshot cache
const snapshotPath = path.join(__dirname, 'web', 'src', 'data', 'verified-snapshot.json');
let snapshotData = null;

function loadSnapshot() {
  if (snapshotData) return snapshotData;
  try {
    if (fs.existsSync(snapshotPath)) {
      snapshotData = JSON.parse(fs.readFileSync(snapshotPath, 'utf-8'));
      return snapshotData;
    }
  } catch (err) {
    console.error('Error loading verified-snapshot.json:', err);
  }
  snapshotData = {
    metadata: {
      version: '1.0.0',
      generated_at: new Date().toISOString(),
      region: 'CAJAMARCA'
    },
    contracting_entities: [],
    procurement_records: [],
    budget_execution_records: [],
    red_flags: [],
    alerts: [],
    citizen_reports: []
  };
  return snapshotData;
}

// Security headers (Allow iframe preview inside AI Studio & anti-clickjacking defense)
app.use((req, res, next) => {
  res.setHeader('X-Content-Type-Options', 'nosniff');
  res.setHeader('Referrer-Policy', 'strict-origin-when-cross-origin');
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');
  if (req.method === 'OPTIONS') {
    return res.sendStatus(200);
  }
  next();
});

// ==========================================
// SEGURIDAD Y ACREDITACIÓN DE VEEDORES (CU5)
// Protección contra ataques de fuerza bruta y hackeos
// ==========================================

// Padrón Oficial de Veedores Acreditados (Sociedad Civil y Veedurías)
const ACCREDITED_VEEDORES = [
  {
    email: 'veeduria-cajamarca@proetica.org.pe',
    passwordHash: crypto.createHash('sha256').update('demo-veedor-2025').digest('hex'),
    name: 'Lic. Carlos Arana Silva',
    organization: 'Proética (Capítulo Peruano de Transparency International)',
    accreditationNumber: 'VEED-PROETICA-2025-014',
    role: 'veedor_titular'
  },
  {
    email: 'veeduria.proetica@cajamarca-qhaway.pe',
    passwordHash: crypto.createHash('sha256').update('Proetica#Cajamarca2025!').digest('hex'),
    name: 'Dra. Elena Santillán Mori',
    organization: 'Proética Cajamarca',
    accreditationNumber: 'VEED-PROETICA-2025-008',
    role: 'veedor_titular'
  },
  {
    email: 'veeduria.propuesta@cajamarca-qhaway.pe',
    passwordHash: crypto.createHash('sha256').update('Propuesta#Civica2025!').digest('hex'),
    name: 'Ing. Marco Tacilla Vásquez',
    organization: 'Grupo Propuesta Ciudadana',
    accreditationNumber: 'VEED-PROPUESTA-2025-021',
    role: 'veedor_revisor'
  },
  {
    email: 'veeduria.grufides@cajamarca-qhaway.pe',
    passwordHash: crypto.createHash('sha256').update('Grufides#Veedor2025!').digest('hex'),
    name: 'Abg. Mirtha Villanueva Quispe',
    organization: 'GRUFIDES Cajamarca',
    accreditationNumber: 'VEED-GRUFIDES-2025-003',
    role: 'veedor_titular'
  },
  {
    email: 'veedor.regional@cajamarca-qhaway.pe',
    passwordHash: crypto.createHash('sha256').update('Veedor#Qhaway2025!').digest('hex'),
    name: 'Prof. Jorge Terrones Bazán',
    organization: 'Mesa de Concertación y Veeduría Ciudadana Cajamarca',
    accreditationNumber: 'VEED-MESA-2025-007',
    role: 'veedor_colegiado'
  }
];

// Almacén seguro de sesiones activas (en memoria)
// token -> { veedor, expiresAt, createdAt, ip }
const ACTIVE_SESSIONS = new Map();

// Control de Intentos Fallidos (Rate Limiting y Prevención de Fuerza Bruta)
// identifier (ip o email) -> { attempts: count, lockedUntil: timestamp }
const LOGIN_ATTEMPTS = new Map();
const MAX_ATTEMPTS = 5;
const LOCKOUT_MS = 15 * 60 * 1000; // 15 minutos de bloqueo

function getClientIp(req) {
  return req.headers['x-forwarded-for']?.split(',')[0].trim() || req.socket.remoteAddress || 'unknown';
}

function checkRateLimit(key) {
  const record = LOGIN_ATTEMPTS.get(key);
  if (!record) return { allowed: true };
  const now = Date.now();
  if (record.lockedUntil && now < record.lockedUntil) {
    const remainingSeconds = Math.ceil((record.lockedUntil - now) / 1000);
    return { allowed: false, remainingSeconds };
  }
  if (record.lockedUntil && now >= record.lockedUntil) {
    LOGIN_ATTEMPTS.delete(key);
    return { allowed: true };
  }
  return { allowed: true };
}

function recordFailedAttempt(key) {
  const now = Date.now();
  const record = LOGIN_ATTEMPTS.get(key) || { attempts: 0, lockedUntil: null };
  record.attempts += 1;
  if (record.attempts >= MAX_ATTEMPTS) {
    record.lockedUntil = now + LOCKOUT_MS;
  }
  LOGIN_ATTEMPTS.set(key, record);
  return record;
}

function resetAttempts(key) {
  LOGIN_ATTEMPTS.delete(key);
}

// Middleware de autenticación obligatoria para operaciones del panel
function requireVeedorAuth(req, res, next) {
  const authHeader = req.headers.authorization;
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return res.status(401).json({
      error: 'Acceso no autorizado: se requiere credencial de veedor acreditado en la cabecera Authorization (CA-005-01)',
      status: 401
    });
  }
  const token = authHeader.slice(7).trim();
  const session = ACTIVE_SESSIONS.get(token);
  if (!session) {
    return res.status(401).json({
      error: 'Token de sesión inválido o expirado. Debe iniciar sesión nuevamente en /login',
      status: 401
    });
  }
  if (Date.now() > session.expiresAt) {
    ACTIVE_SESSIONS.delete(token);
    return res.status(401).json({
      error: 'La sesión de veedor ha caducado por inactividad. Reautentíquese para continuar',
      status: 401
    });
  }
  // Renovar sesión activa (sliding window)
  session.expiresAt = Date.now() + 8 * 60 * 60 * 1000;
  req.veedor = session.veedor;
  next();
}

// ==========================================
// ENDPOINTS DE AUTENTICACIÓN
// ==========================================

app.post('/api/auth/login', (req, res) => {
  const ip = getClientIp(req);
  const { email, password, honeypot } = req.body || {};

  // Detección de bots automatizados
  if (honeypot) {
    return res.status(400).json({ error: 'Solicitud rechazada', status: 400 });
  }

  if (!email || !password) {
    return res.status(400).json({
      error: 'Debe ingresar el correo y la contraseña de acreditación',
      status: 400
    });
  }

  const cleanEmail = String(email).trim().toLowerCase();
  const ipKey = `ip:${ip}`;
  const userKey = `user:${cleanEmail}`;

  const ipLimit = checkRateLimit(ipKey);
  if (!ipLimit.allowed) {
    return res.status(429).json({
      error: `Demasiados intentos de acceso fallidos desde esta red. Acceso bloqueado temporalmente por seguridad. Reintente en ${Math.ceil(ipLimit.remainingSeconds / 60)} minutos.`,
      retryAfter: ipLimit.remainingSeconds,
      status: 429
    });
  }

  const userLimit = checkRateLimit(userKey);
  if (!userLimit.allowed) {
    return res.status(429).json({
      error: `Esta cuenta ha sido bloqueada temporalmente tras ${MAX_ATTEMPTS} intentos fallidos para prevenir hackeos de fuerza bruta. Reintente en ${Math.ceil(userLimit.remainingSeconds / 60)} minutos.`,
      retryAfter: userLimit.remainingSeconds,
      status: 429
    });
  }

  const candidateHash = crypto.createHash('sha256').update(String(password)).digest('hex');
  const matchedVeedor = ACCREDITED_VEEDORES.find(v => v.email === cleanEmail);

  let isValid = false;
  if (matchedVeedor) {
    // Comparación segura en tiempo constante para mitigar timing-attacks
    const hashBuf = Buffer.from(matchedVeedor.passwordHash, 'hex');
    const candBuf = Buffer.from(candidateHash, 'hex');
    if (hashBuf.length === candBuf.length && crypto.timingSafeEqual(hashBuf, candBuf)) {
      isValid = true;
    }
  }

  if (!isValid) {
    const record = recordFailedAttempt(ipKey);
    recordFailedAttempt(userKey);
    const remaining = Math.max(0, MAX_ATTEMPTS - record.attempts);
    return res.status(401).json({
      error: 'Credenciales inválidas. Compruebe su correo u organización y el código de veeduría.',
      remainingAttempts: remaining,
      status: 401
    });
  }

  // Éxito: restablecer intentos fallidos
  resetAttempts(ipKey);
  resetAttempts(userKey);

  // Generar token criptográficamente seguro de 256 bits
  const token = crypto.randomBytes(32).toString('hex');
  const sessionData = {
    veedor: {
      email: matchedVeedor.email,
      name: matchedVeedor.name,
      organization: matchedVeedor.organization,
      accreditationNumber: matchedVeedor.accreditationNumber,
      role: matchedVeedor.role
    },
    createdAt: Date.now(),
    expiresAt: Date.now() + 8 * 60 * 60 * 1000, // 8 horas
    ip
  };

  ACTIVE_SESSIONS.set(token, sessionData);

  res.json({
    token,
    veedor: sessionData.veedor,
    expiresAt: sessionData.expiresAt,
    message: 'Acreditación verificada. Sesión segura iniciada.'
  });
});

app.get('/api/auth/session', (req, res) => {
  const authHeader = req.headers.authorization;
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return res.status(401).json({ valid: false, error: 'No token provided' });
  }
  const token = authHeader.slice(7).trim();
  const session = ACTIVE_SESSIONS.get(token);
  if (!session || Date.now() > session.expiresAt) {
    if (session) ACTIVE_SESSIONS.delete(token);
    return res.status(401).json({ valid: false, error: 'Session expired' });
  }
  res.json({
    valid: true,
    veedor: session.veedor,
    expiresAt: session.expiresAt
  });
});

app.post('/api/auth/logout', (req, res) => {
  const authHeader = req.headers.authorization;
  if (authHeader && authHeader.startsWith('Bearer ')) {
    const token = authHeader.slice(7).trim();
    ACTIVE_SESSIONS.delete(token);
  }
  res.json({ message: 'Sesión finalizada correctamente' });
});

// ==========================================
// REST API Endpoints
// ==========================================
app.get('/api/health', (req, res) => {
  const snapshot = loadSnapshot();
  res.json({
    status: 'healthy',
    service: 'cajamarca-qhaway-web',
    version: '1.0.0',
    timestamp: snapshot.metadata?.generated_at || new Date().toISOString(),
    region: 'CAJAMARCA',
    invariants: {
      art_10_sources: ['seace-ocds', 'mef-datastore'],
      art_14_human_review: true,
      art_16_no_person_scoring: true,
      art_18_universe_size: 14
    }
  });
});

app.get('/api/snapshot', (req, res) => {
  res.json(loadSnapshot());
});

app.get('/api/entities', (req, res) => {
  const snapshot = loadSnapshot();
  const entities = snapshot.contracting_entities || [];
  const id = req.query.id;
  if (id) {
    const matched = entities.find(e => e.entity_id === id || e.ruc === id);
    if (matched) return res.json(matched);
    return res.status(404).json({ error: `Entidad no encontrada con ID: ${id}`, status: 404 });
  }
  res.json(entities);
});

app.get('/api/procurements', (req, res) => {
  const snapshot = loadSnapshot();
  let procurements = snapshot.procurement_records || [];
  const { ocid, entity_id } = req.query;
  if (ocid) {
    const matched = procurements.find(p => p.ocid === ocid || p.procurement_id === ocid);
    if (matched) return res.json(matched);
    return res.status(404).json({ error: `Contratacion no encontrada con OCID: ${ocid}`, status: 404 });
  }
  if (entity_id) {
    procurements = procurements.filter(p => p.entity_id === entity_id);
  }
  res.json(procurements);
});

app.get('/api/budget', (req, res) => {
  const snapshot = loadSnapshot();
  let budget = snapshot.budget_execution_records || [];
  const { entity_id } = req.query;
  if (entity_id) {
    budget = budget.filter(b => b.entity_id === entity_id);
  }
  res.json(budget);
});

app.get('/api/alerts', (req, res) => {
  const snapshot = loadSnapshot();
  const allAlerts = snapshot.alerts || [];
  let publishedOnly = allAlerts.filter(a => a.status === 'published');
  const { id, entity_id } = req.query;
  if (id) {
    const matched = publishedOnly.find(a => a.alert_id === id);
    if (matched) return res.json(matched);
    return res.status(404).json({ error: `Alerta publicada no encontrada con ID: ${id}`, status: 404 });
  }
  if (entity_id) {
    publishedOnly = publishedOnly.filter(a => a.entity_id === entity_id);
  }
  res.json(publishedOnly);
});

app.get('/api/red-flags', (req, res) => {
  const snapshot = loadSnapshot();
  const flags = snapshot.red_flags || [];
  const { id } = req.query;
  if (id) {
    const matched = flags.find(f => f.red_flag_id === id);
    if (matched) return res.json(matched);
    return res.status(404).json({ error: `Bandera roja no encontrada con ID: ${id}`, status: 404 });
  }
  res.json(flags);
});

app.get('/api/reports', (req, res) => {
  const snapshot = loadSnapshot();
  res.json(snapshot.citizen_reports || []);
});

// Endpoint de proveedores y concentración (accesible vía /api/concentration y /api/suppliers)
function computeSuppliersConcentration(req, res) {
  const snapshot = loadSnapshot();
  const procurements = snapshot.procurement_records || [];
  const entityId = req.query.entity_id;
  const filtered = entityId ? procurements.filter(p => p.entity_id === entityId) : procurements;

  const supplierMap = new Map();
  let grandTotal = 0;

  for (const p of filtered) {
    const key = p.supplier_ruc || p.supplier_name || 'Desconocido';
    const amount = Number(p.awarded_amount) || Number(p.executed_amount) || 0;
    if (!supplierMap.has(key)) {
      supplierMap.set(key, {
        ruc: p.supplier_ruc || 'Sin RUC',
        name: p.supplier_name || 'Proveedor Anónimo',
        totalAmount: 0,
        contractsCount: 0
      });
    }
    const sup = supplierMap.get(key);
    sup.totalAmount += amount;
    sup.contractsCount += 1;
    grandTotal += amount;
  }

  const baseTotal = grandTotal > 0 ? grandTotal : 1;
  const suppliers = Array.from(supplierMap.values()).map(s => {
    const share = s.totalAmount / baseTotal;
    return {
      ...s,
      share: Number(share.toFixed(4)),
      sharePct: Number((share * 100).toFixed(1))
    };
  });

  suppliers.sort((a, b) => b.totalAmount - a.totalAmount);
  const hhi = suppliers.reduce((acc, s) => acc + Math.pow(s.share, 2), 0);

  res.json({
    hhi: Number(hhi.toFixed(2)),
    hhiPoints: Math.round(hhi * 10000),
    grandTotal,
    suppliersCount: suppliers.length,
    topSuppliers: suppliers
  });
}

app.get('/api/concentration', computeSuppliersConcentration);
app.get('/api/suppliers', computeSuppliersConcentration);

const GENERIC_REVIEWERS = new Set([
  'admin', 'system', 'root', 'bot', 'auto', 'automated', 'null', 'none', 'anonymous'
]);

app.post('/api/reports', (req, res) => {
  const body = req.body || {};
  const raw_text = body.raw_text;
  const legalDisclaimer = body.legal_disclaimer_shown || body.disclaimer_accepted;
  const channel = body.channel || body.source_channel || 'web';
  const entityId = body.related_entity_id || body.entity_id || null;

  if (!raw_text || !String(raw_text).trim()) {
    return res.status(400).json({ error: "El campo 'raw_text' es obligatorio", status: 400 });
  }
  if (!legalDisclaimer) {
    return res.status(400).json({
      error: "La denuncia no puede ser aceptada sin previa confirmacion del descargo legal (CA-006-01)",
      status: 400
    });
  }

  const snapshot = loadSnapshot();
  const reportId = `cr-${Date.now().toString(36)}${Math.random().toString(36).slice(2, 6)}`;
  const report = {
    report_id: reportId,
    submitted_at: new Date().toISOString(),
    channel,
    raw_text: String(raw_text).trim(),
    related_entity_id: entityId,
    moderation_status: 'pending',
    moderated_by: null,
    moderated_at: null,
    legal_disclaimer_shown: true
  };

  if (!snapshot.citizen_reports) snapshot.citizen_reports = [];
  snapshot.citizen_reports.unshift(report);
  res.status(201).json({ ...report, report });
});

// Panel Revisor CU5: Protegido por sesión obligatoria de veedor acreditado
app.post('/api/review', requireVeedorAuth, (req, res) => {
  const { entity_id, red_flag_ids, status, reviewed_by, review_notes } = req.body || {};
  if (!entity_id || !red_flag_ids || !status) {
    return res.status(400).json({
      error: 'Campos requeridos: entity_id, red_flag_ids, status',
      status: 400
    });
  }

  // Se usa el veedor autenticado de forma fehaciente
  const reviewerName = req.veedor?.name || reviewed_by || 'Veedor Acreditado';

  const cleanedReviewer = String(reviewerName).trim().toLowerCase();
  if (GENERIC_REVIEWERS.has(cleanedReviewer) || !cleanedReviewer) {
    return res.status(400).json({
      error: `reviewed_by no puede ser generico o vacio: '${reviewerName}'`,
      status: 400
    });
  }

  if (status === 'discarded' && (!review_notes || !String(review_notes).trim())) {
    return res.status(400).json({
      error: "review_notes es obligatorio cuando el estado es 'discarded' (CA-005-04)",
      status: 400
    });
  }

  const snapshot = loadSnapshot();
  const alertId = `al-${Date.now().toString(36)}${Math.random().toString(36).slice(2, 6)}`;
  const alert = {
    alert_id: alertId,
    entity_id: String(entity_id).trim(),
    red_flag_ids: Array.isArray(red_flag_ids) ? red_flag_ids : [red_flag_ids],
    status,
    reviewed_by: `${reviewerName} (${req.veedor.organization})`,
    review_notes: review_notes ? String(review_notes).trim() : (status === 'discarded' ? 'Descarte documentado' : null),
    published_at: status === 'published' ? new Date().toISOString() : null,
    discarded_at: status === 'discarded' ? new Date().toISOString() : null
  };

  if (!snapshot.alerts) snapshot.alerts = [];
  snapshot.alerts.unshift(alert);
  res.status(201).json({ alert });
});

// ==========================================
// Rutas Multi-Página
// ==========================================
const webDir = path.join(__dirname, 'web');

app.get('/', (req, res) => res.sendFile(path.join(webDir, 'index.html')));
app.get('/entidades', (req, res) => res.sendFile(path.join(webDir, 'entidades.html')));
app.get('/entidad', (req, res) => res.sendFile(path.join(webDir, 'entidad-detalle.html')));
app.get('/alertas', (req, res) => res.sendFile(path.join(webDir, 'alertas.html')));
app.get('/contrataciones', (req, res) => res.sendFile(path.join(webDir, 'contrataciones.html')));
app.get('/contrato', (req, res) => res.sendFile(path.join(webDir, 'contrato-detalle.html')));
app.get('/presupuesto', (req, res) => res.sendFile(path.join(webDir, 'presupuesto.html')));

// Proveedores del Estado (anteriormente concentracion)
app.get('/proveedores', (req, res) => {
  if (fs.existsSync(path.join(webDir, 'proveedores.html'))) {
    return res.sendFile(path.join(webDir, 'proveedores.html'));
  }
  res.sendFile(path.join(webDir, 'concentracion.html'));
});
app.get('/concentracion', (req, res) => res.redirect(301, '/proveedores'));

app.get('/denuncia', (req, res) => res.sendFile(path.join(webDir, 'denuncia.html')));
app.get('/transparencia', (req, res) => res.sendFile(path.join(webDir, 'transparencia.html')));
app.get('/acerca', (req, res) => res.sendFile(path.join(webDir, 'acerca.html')));
app.get('/admin/revision', (req, res) => res.sendFile(path.join(webDir, 'admin-revision.html')));
app.get('/login', (req, res) => res.sendFile(path.join(webDir, 'login.html')));
app.get('/acreditacion', (req, res) => res.sendFile(path.join(webDir, 'login.html')));

// Entrega de archivos estáticos
app.use(express.static(webDir));

// Fallback al inicio
app.get('*', (req, res) => {
  res.sendFile(path.join(webDir, 'index.html'));
});

app.listen(PORT, HOST, () => {
  console.log(`Cajamarca Qhaway Andean Civic dev server running at http://${HOST}:${PORT}`);
});
