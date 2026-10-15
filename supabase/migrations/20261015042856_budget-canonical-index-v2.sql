-- El indice productivo se construyo en linea antes de esta migracion idempotente.
CREATE UNIQUE INDEX IF NOT EXISTS budget_canonical_entity_year_v2
ON public.budget_execution_records(entity_id, fiscal_year) WHERE is_canonical_total;
