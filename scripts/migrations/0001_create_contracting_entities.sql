-- Migracion 0001: tabla operativa `contracting_entities` (ADR 0002/0003/0006).
--
-- Espejo de lectura del dataset versionado `data/entities/*.yaml`. La fuente de verdad
-- es el fichero, no esta tabla (ADR 0006): esta tabla existe para que `002` y `003`
-- puedan hacer un JOIN por `entity_id` con indice, en vez de leer el YAML en cada
-- consulta.
--
-- No incluye el bloque `verification` del YAML (fuentes consultadas, notas de
-- procedencia): eso es gobernanza del propio dataset versionado, no parte del contrato
-- canonico `ContractingEntity` (Articulo 19 de la constitucion) que consumen las demas
-- capacidades. Auditar procedencia significa leer el YAML y su historial de Git, no
-- esta tabla.

CREATE TABLE IF NOT EXISTS contracting_entities (
    entity_id      TEXT PRIMARY KEY,
    official_name  TEXT NOT NULL,
    entity_level   TEXT NOT NULL
                   CHECK (entity_level IN ('regional', 'provincial_municipality', 'district_municipality')),
    province       TEXT,
    ruc            TEXT NOT NULL UNIQUE
                   CHECK (ruc ~ '^[0-9]{11}$'),
    consucode_id   TEXT,
    department     TEXT NOT NULL DEFAULT 'CAJAMARCA'
                   CHECK (department = 'CAJAMARCA'),
    verified_at    TIMESTAMPTZ NOT NULL,
    active         BOOLEAN NOT NULL DEFAULT TRUE,

    -- RN-001-08: province es NULL solo para el Gobierno Regional.
    CONSTRAINT province_null_solo_regional CHECK (
        (entity_level = 'regional' AND province IS NULL)
        OR (entity_level <> 'regional' AND province IS NOT NULL)
    )
);

CREATE INDEX IF NOT EXISTS idx_contracting_entities_province
    ON contracting_entities (province);

CREATE INDEX IF NOT EXISTS idx_contracting_entities_active
    ON contracting_entities (active);

COMMENT ON TABLE contracting_entities IS
    'Espejo operativo de data/entities/*.yaml (ADR 0006). RN-001-05: nunca se hace DELETE, solo active=false.';
