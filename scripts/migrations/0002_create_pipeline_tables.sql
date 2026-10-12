-- Migracion 0002: Tablas operativas para el pipeline de Fase 1 (ADR 0002/0003).
-- Cubre los contratos canonicos restantes segun Articulo 19 de docs/sdd/constitution.md.

-- 1. Contrataciones publicas SEACE/OCDS
CREATE TABLE IF NOT EXISTS procurement_records (
    procurement_id      TEXT PRIMARY KEY,
    ocid                TEXT NOT NULL,
    entity_id           TEXT NOT NULL REFERENCES contracting_entities(entity_id),
    title               TEXT NOT NULL,
    procurement_method  TEXT,
    awarded_amount      NUMERIC(14, 2),
    executed_amount     NUMERIC(14, 2),
    number_of_bidders   INTEGER,
    supplier_name       TEXT,
    supplier_ruc        TEXT,
    raw_payload         JSONB NOT NULL DEFAULT '{}'::jsonb,
    source              TEXT NOT NULL DEFAULT 'seace-ocds',
    retrieved_at        TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_procurement_records_entity_id ON procurement_records(entity_id);
CREATE INDEX IF NOT EXISTS idx_procurement_records_supplier_ruc ON procurement_records(supplier_ruc);
CREATE INDEX IF NOT EXISTS idx_procurement_records_ocid ON procurement_records(ocid);

-- 2. Ejecucion presupuestal MEF
CREATE TABLE IF NOT EXISTS budget_execution_records (
    execution_record_id TEXT PRIMARY KEY,
    entity_id           TEXT NOT NULL REFERENCES contracting_entities(entity_id),
    fiscal_year         INTEGER NOT NULL CHECK (fiscal_year BETWEEN 2000 AND 2100),
    budgeted_amount     NUMERIC(14, 2) NOT NULL DEFAULT 0.0,
    executed_amount     NUMERIC(14, 2) NOT NULL DEFAULT 0.0,
    budget_category     TEXT,
    raw_payload         JSONB NOT NULL DEFAULT '{}'::jsonb,
    source              TEXT NOT NULL DEFAULT 'mef-datastore',
    retrieved_at        TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_budget_execution_records_entity_year ON budget_execution_records(entity_id, fiscal_year);

-- 3. Banderas rojas (Candidatos de riesgo) - Sin campo status (Art. 14 / CA-004-06)
CREATE TABLE IF NOT EXISTS red_flags (
    red_flag_id           TEXT PRIMARY KEY,
    indicator_code        TEXT NOT NULL,
    formula_description   TEXT NOT NULL,
    threshold             TEXT NOT NULL,
    observed_value        TEXT NOT NULL,
    procurement_ids       JSONB NOT NULL DEFAULT '[]'::jsonb,
    execution_record_ids  JSONB NOT NULL DEFAULT '[]'::jsonb,
    evidence_source       TEXT NOT NULL,
    evidence_retrieved_at TIMESTAMPTZ NOT NULL,
    generated_at          TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_red_flags_indicator ON red_flags(indicator_code);

-- 4. Alertas decididas por panel de revision humana
CREATE TABLE IF NOT EXISTS alerts (
    alert_id       TEXT PRIMARY KEY,
    red_flag_ids   JSONB NOT NULL,
    entity_id      TEXT NOT NULL REFERENCES contracting_entities(entity_id),
    status         TEXT NOT NULL CHECK (status IN ('published', 'discarded')),
    reviewed_by    TEXT NOT NULL CHECK (reviewed_by NOT IN ('admin', 'system', 'root', 'bot', '')),
    reviewed_at    TIMESTAMPTZ NOT NULL,
    review_notes   TEXT,
    disclaimer     TEXT NOT NULL,
    published_at   TIMESTAMPTZ,

    CONSTRAINT alert_discard_requires_notes CHECK (
        (status = 'discarded' AND review_notes IS NOT NULL AND length(trim(review_notes)) > 0 AND published_at IS NULL)
        OR (status = 'published' AND published_at IS NOT NULL)
    )
);

CREATE INDEX IF NOT EXISTS idx_alerts_entity_status ON alerts(entity_id, status);

-- 5. Denuncias ciudadanas moderadas
CREATE TABLE IF NOT EXISTS citizen_reports (
    report_id              TEXT PRIMARY KEY,
    submitted_at           TIMESTAMPTZ NOT NULL,
    channel                TEXT NOT NULL CHECK (channel IN ('web', 'sms', 'whatsapp')),
    raw_text               TEXT NOT NULL,
    related_entity_id      TEXT REFERENCES contracting_entities(entity_id),
    moderation_status      TEXT NOT NULL CHECK (moderation_status IN ('pending', 'accepted_as_lead', 'rejected')),
    moderated_by           TEXT,
    moderated_at           TIMESTAMPTZ,
    legal_disclaimer_shown BOOLEAN NOT NULL CHECK (legal_disclaimer_shown = TRUE),

    CONSTRAINT moderation_requires_user_and_date CHECK (
        (moderation_status = 'pending' AND moderated_by IS NULL AND moderated_at IS NULL)
        OR (moderation_status <> 'pending' AND moderated_by IS NOT NULL AND moderated_at IS NOT NULL)
    )
);

CREATE INDEX IF NOT EXISTS idx_citizen_reports_status ON citizen_reports(moderation_status);
