ALTER TABLE public.procurement_records ADD COLUMN IF NOT EXISTS source_evidence jsonb NOT NULL DEFAULT '[]';
CREATE UNIQUE INDEX procurement_identity_entity ON public.procurement_records(procurement_id, entity_id);
CREATE TABLE public.procurement_source_records (
  source_evidence_id text PRIMARY KEY,
  source_system text NOT NULL CHECK (source_system IN ('oece_pentaho_bi', 'seace_buscador_publico')),
  dataset text NOT NULL,
  fiscal_year integer NOT NULL CHECK (fiscal_year BETWEEN 2024 AND 2026),
  entity_id text NOT NULL REFERENCES public.contracting_entities(entity_id),
  source_record_id text NOT NULL,
  official_process_id text,
  procurement_id text REFERENCES public.procurement_records(procurement_id),
  cui text CHECK (cui ~ '^[0-9]{7}$'),
  source_url text NOT NULL CHECK (source_url ~ '^https://'),
  retrieved_at timestamptz NOT NULL,
  raw_payload jsonb NOT NULL CHECK (raw_payload ? 'source_system' AND raw_payload->>'source_system' = source_system),
  CONSTRAINT evidence_procurement_entity FOREIGN KEY (procurement_id, entity_id)
    REFERENCES public.procurement_records(procurement_id, entity_id)
);
ALTER TABLE public.procurement_source_records ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.procurement_source_records FROM anon, authenticated;
GRANT ALL ON public.procurement_source_records TO service_role;
CREATE INDEX procurement_source_process ON public.procurement_source_records(entity_id, official_process_id);
CREATE INDEX procurement_source_link ON public.procurement_source_records(procurement_id) WHERE procurement_id IS NOT NULL;
