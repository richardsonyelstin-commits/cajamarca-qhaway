-- Ejecutar en autocommit, fuera de una transaccion de migracion.
-- Aplicado por execute_sql el 2026-10-15 antes de la sincronizacion de maestros.
CREATE UNIQUE INDEX CONCURRENTLY IF NOT EXISTS budget_canonical_entity_year_v2
ON public.budget_execution_records(entity_id, fiscal_year) WHERE is_canonical_total;
