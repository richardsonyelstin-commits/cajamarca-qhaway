-- Allow alerts to remain generated/in review until a verifiable human decision.
-- Existing published rows are quarantined because this database has no acta/dictamen
-- artifact field that substantiates publication independently of reviewer metadata.

ALTER TABLE public.alerts
    ALTER COLUMN reviewed_by DROP NOT NULL,
    ALTER COLUMN reviewed_at DROP NOT NULL,
    ALTER COLUMN review_notes DROP NOT NULL;

ALTER TABLE public.alerts
    DROP CONSTRAINT IF EXISTS alerts_status_check,
    DROP CONSTRAINT IF EXISTS alert_discard_requires_notes,
    DROP CONSTRAINT IF EXISTS alert_publication_requires_review,
    DROP CONSTRAINT IF EXISTS alerts_reviewed_by_check;

ALTER TABLE public.alerts
    ADD CONSTRAINT alerts_status_check
        CHECK (status IN ('generated', 'in_review', 'published', 'discarded')),
    ADD CONSTRAINT alerts_reviewed_by_check
        CHECK (
            reviewed_by IS NULL
            OR (
                length(trim(reviewed_by)) > 0
                AND lower(trim(reviewed_by)) NOT IN
                    ('admin', 'system', 'root', 'bot', 'auto', 'automated')
            )
        ),
    ADD CONSTRAINT alert_discard_requires_notes
        CHECK (
            (status = 'discarded' AND review_notes IS NOT NULL
                AND length(trim(review_notes)) > 0 AND published_at IS NULL)
            OR (status = 'published' AND published_at IS NOT NULL)
            OR (status IN ('generated', 'in_review') AND published_at IS NULL)
        ),
    ADD CONSTRAINT alert_publication_requires_review
        CHECK (
            (
                status IN ('generated', 'in_review')
                AND published_at IS NULL
            )
            OR (
                reviewed_by IS NOT NULL
                AND length(trim(reviewed_by)) > 0
                AND lower(trim(reviewed_by)) NOT IN
                    ('admin', 'system', 'root', 'bot', 'auto', 'automated')
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
            )
        );

UPDATE public.alerts
SET status = 'in_review', published_at = NULL
WHERE status = 'published';
