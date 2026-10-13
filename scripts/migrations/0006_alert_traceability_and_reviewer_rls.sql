-- Migracion 0006: trazabilidad obligatoria de alertas y lectura limitada a veedores.

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM alerts
        WHERE status = 'published'
          AND (review_notes IS NULL OR length(trim(review_notes)) = 0)
    ) THEN
        RAISE EXCEPTION 'Migracion bloqueada: existen alertas publicadas sin review_notes';
    END IF;
END $$;

ALTER TABLE alerts ADD COLUMN IF NOT EXISTS legal_disclaimer TEXT;
UPDATE alerts
SET legal_disclaimer = disclaimer
WHERE legal_disclaimer IS NULL;
ALTER TABLE alerts ALTER COLUMN legal_disclaimer SET NOT NULL;
ALTER TABLE alerts ALTER COLUMN disclaimer DROP NOT NULL;
ALTER TABLE alerts ALTER COLUMN review_notes SET NOT NULL;
ALTER TABLE alerts ADD COLUMN IF NOT EXISTS evidence JSONB NOT NULL DEFAULT '[]'::jsonb;
UPDATE alerts AS alert
SET evidence = COALESCE((
    SELECT jsonb_agg(jsonb_build_object(
        'red_flag_id', flag.red_flag_id,
        'formula_description', flag.formula_description,
        'observed_value', flag.observed_value,
        'threshold_value', flag.threshold,
        'retrieved_at', flag.evidence_retrieved_at,
        'evidence_source', flag.evidence_source
    ))
    FROM red_flags AS flag
    JOIN jsonb_array_elements_text(alert.red_flag_ids) AS ids(red_flag_id)
      ON ids.red_flag_id = flag.red_flag_id
), '[]'::jsonb)
WHERE alert.status = 'published' AND jsonb_array_length(alert.evidence) = 0;

ALTER TABLE red_flags ADD COLUMN IF NOT EXISTS threshold_value TEXT;
ALTER TABLE red_flags ADD COLUMN IF NOT EXISTS retrieved_at TIMESTAMPTZ;
UPDATE red_flags SET threshold_value = threshold WHERE threshold_value IS NULL;
UPDATE red_flags SET retrieved_at = evidence_retrieved_at WHERE retrieved_at IS NULL;
ALTER TABLE red_flags ALTER COLUMN threshold_value SET NOT NULL;
ALTER TABLE red_flags ALTER COLUMN retrieved_at SET NOT NULL;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM alerts
        WHERE status = 'published' AND jsonb_array_length(evidence) = 0
    ) THEN
        RAISE EXCEPTION 'Migracion bloqueada: faltan RedFlags de evidencia para alertas publicadas';
    END IF;
END $$;

ALTER TABLE alerts DROP CONSTRAINT IF EXISTS alert_publication_requires_review;
ALTER TABLE alerts ADD CONSTRAINT alert_publication_requires_review CHECK (
    reviewed_by IS NOT NULL
    AND length(trim(reviewed_by)) > 0
    AND lower(trim(reviewed_by)) NOT IN ('admin', 'system', 'root', 'bot', 'auto', 'automated')
    AND reviewed_at IS NOT NULL
    AND review_notes IS NOT NULL
    AND length(trim(review_notes)) > 0
    AND legal_disclaimer IS NOT NULL
    AND length(trim(legal_disclaimer)) > 0
    AND (status <> 'published' OR jsonb_array_length(evidence) > 0)
    AND (
        (status = 'published' AND published_at IS NOT NULL)
        OR (status = 'discarded' AND published_at IS NULL)
    )
);

ALTER TABLE citizen_reports ADD COLUMN IF NOT EXISTS tracking_token_hash TEXT;
CREATE UNIQUE INDEX IF NOT EXISTS idx_citizen_reports_tracking_token_hash
    ON citizen_reports(tracking_token_hash)
    WHERE tracking_token_hash IS NOT NULL;
ALTER TABLE citizen_reports DROP CONSTRAINT IF EXISTS citizen_report_tracking_hash_format;
ALTER TABLE citizen_reports ADD CONSTRAINT citizen_report_tracking_hash_format CHECK (
    tracking_token_hash IS NULL OR tracking_token_hash ~ '^[0-9a-f]{64}$'
);

-- Las politicas permisivas de 0003 se reemplazan: ser authenticated no acredita ser veedor.
DROP POLICY IF EXISTS p_select_red_flags_authenticated ON red_flags;
CREATE POLICY p_select_red_flags_reviewers
    ON red_flags FOR SELECT
    TO authenticated
    USING ((auth.jwt() -> 'app_metadata' ->> 'role') = 'reviewer');

DROP POLICY IF EXISTS p_select_citizen_reports_moderator ON citizen_reports;
CREATE POLICY p_select_citizen_reports_reviewers
    ON citizen_reports FOR SELECT
    TO authenticated
    USING ((auth.jwt() -> 'app_metadata' ->> 'role') = 'reviewer');

DROP POLICY IF EXISTS p_insert_citizen_reports_public ON citizen_reports;
CREATE POLICY p_insert_citizen_reports_public
    ON citizen_reports FOR INSERT
    TO anon, authenticated
    WITH CHECK (legal_disclaimer_shown = TRUE);
