-- Evalua el JWT una vez por sentencia en vez de repetirlo por fila.
DROP POLICY IF EXISTS p_select_red_flags_reviewers ON public.red_flags;
CREATE POLICY p_select_red_flags_reviewers
    ON public.red_flags
    FOR SELECT
    TO authenticated
    USING (((SELECT auth.jwt())->'app_metadata'->>'role') = 'reviewer');

DROP POLICY IF EXISTS p_select_citizen_reports_reviewers ON public.citizen_reports;
CREATE POLICY p_select_citizen_reports_reviewers
    ON public.citizen_reports
    FOR SELECT
    TO authenticated
    USING (((SELECT auth.jwt())->'app_metadata'->>'role') = 'reviewer');
