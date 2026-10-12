-- Migracion 0003: Habilitar Row Level Security (RLS) y politicas de acceso seguro (TK-201)
--
-- Aplica el principio de minimo privilegio (Art. 14 y 16 de docs/sdd/constitution.md):
-- - contracting_entities, procurement_records, budget_execution_records: lectura publica abierta (transparencia activa).
-- - alerts: lectura publica unicamente de status = 'published' (las descartadas o en borrador quedan protegidas).
-- - red_flags: lectura restringida a revisores y analistas autenticados.
-- - citizen_reports: insercion publica de reportes (con legal_disclaimer_shown = true); lectura restringida a moderadores.
-- - Insercion y modificacion backend: reservada a service_role.

-- 1. Habilitar RLS en las 6 tablas
ALTER TABLE contracting_entities ENABLE ROW LEVEL SECURITY;
ALTER TABLE procurement_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE budget_execution_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE red_flags ENABLE ROW LEVEL SECURITY;
ALTER TABLE alerts ENABLE ROW LEVEL SECURITY;
ALTER TABLE citizen_reports ENABLE ROW LEVEL SECURITY;

-- 2. Politicas para contracting_entities
CREATE POLICY p_select_contracting_entities_public
    ON contracting_entities FOR SELECT
    USING (true);

CREATE POLICY p_write_contracting_entities_service
    ON contracting_entities FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- 3. Politicas para procurement_records
CREATE POLICY p_select_procurement_records_public
    ON procurement_records FOR SELECT
    USING (true);

CREATE POLICY p_write_procurement_records_service
    ON procurement_records FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- 4. Politicas para budget_execution_records
CREATE POLICY p_select_budget_execution_records_public
    ON budget_execution_records FOR SELECT
    USING (true);

CREATE POLICY p_write_budget_execution_records_service
    ON budget_execution_records FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- 5. Politicas para red_flags (Candidatos internos antes de comite)
CREATE POLICY p_select_red_flags_authenticated
    ON red_flags FOR SELECT
    TO authenticated, service_role
    USING (true);

CREATE POLICY p_write_red_flags_service
    ON red_flags FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- 6. Politicas para alerts (Publico solo ve status = 'published')
CREATE POLICY p_select_alerts_public_published
    ON alerts FOR SELECT
    TO anon, authenticated
    USING (status = 'published');

CREATE POLICY p_select_alerts_service_all
    ON alerts FOR SELECT
    TO service_role
    USING (true);

CREATE POLICY p_write_alerts_service
    ON alerts FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- 7. Politicas para citizen_reports
CREATE POLICY p_insert_citizen_reports_public
    ON citizen_reports FOR INSERT
    WITH CHECK (legal_disclaimer_shown = true);

CREATE POLICY p_select_citizen_reports_moderator
    ON citizen_reports FOR SELECT
    TO authenticated, service_role
    USING (true);

CREATE POLICY p_write_citizen_reports_service
    ON citizen_reports FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);
