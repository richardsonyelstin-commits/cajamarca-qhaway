-- source: ai | generator: codex-gpt-6 | generated_at: 2026-10-15T19:00:00Z
-- confidence: high | verified: false
-- Expansión aditiva: evidencia de órdenes y dossier privado por expediente.
ALTER TABLE public.red_flags
    ADD COLUMN IF NOT EXISTS source_evidence_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
    ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT true;

CREATE TABLE IF NOT EXISTS public.review_case_analyses (
    alert_id TEXT PRIMARY KEY REFERENCES public.alerts(alert_id),
    entity_id TEXT NOT NULL REFERENCES public.contracting_entities(entity_id),
    case_priority_score NUMERIC NOT NULL CHECK (case_priority_score BETWEEN 0 AND 100),
    priority_components JSONB NOT NULL CHECK (jsonb_typeof(priority_components) = 'object'),
    ai_copilot_analysis JSONB NOT NULL CHECK (jsonb_typeof(ai_copilot_analysis) = 'object'),
    generated_at TIMESTAMPTZ NOT NULL
);
ALTER TABLE public.review_case_analyses ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.review_case_analyses FROM anon, authenticated;
GRANT ALL ON public.review_case_analyses TO service_role;
COMMENT ON TABLE public.review_case_analyses IS
    'Asistencia privada; acceso por backend autenticado. No constituye decisión humana.';
