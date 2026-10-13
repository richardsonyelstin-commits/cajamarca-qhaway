-- Migracion 0005: Tabla para estado persistente de cursores de recoleccion continua (Watermarks)
-- Elimina la dependencia estricta del filesystem local (data/state/watermarks.json) para
-- ejecucion en runners y workers de nube.

CREATE TABLE IF NOT EXISTS harvest_watermarks (
    source_name     TEXT PRIMARY KEY,
    last_timestamp  TIMESTAMPTZ,
    last_offset     INTEGER NOT NULL DEFAULT 0,
    seen_ids        JSONB NOT NULL DEFAULT '[]'::jsonb,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE harvest_watermarks IS
    'Estado persistente de cursores de recoleccion (SEACE OCDS, MEF SIAF y Satelite).';
