-- Perfiles podados del padron reducido oficial SUNAT. No guardar el padron nacional.
CREATE TABLE IF NOT EXISTS public.sunat_ruc_profiles (
    ruc TEXT PRIMARY KEY CHECK (ruc ~ '^[0-9]{11}$'),
    razon_social TEXT NOT NULL,
    estado_contribuyente TEXT NOT NULL,
    condicion_domicilio TEXT NOT NULL,
    tipo_contribuyente TEXT,
    direccion_fiscal TEXT,
    ubigeo TEXT,
    departamento TEXT,
    provincia TEXT,
    distrito TEXT,
    es_entidad_publica BOOLEAN NOT NULL DEFAULT FALSE,
    source_provider TEXT NOT NULL CHECK (source_provider = 'sunat_padron_reducido'),
    queried_at TIMESTAMPTZ NOT NULL,
    raw_payload JSONB NOT NULL CHECK (jsonb_typeof(raw_payload) = 'object')
);

ALTER TABLE public.sunat_ruc_profiles ENABLE ROW LEVEL SECURITY;
