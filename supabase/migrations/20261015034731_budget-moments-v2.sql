-- ADR 0013: expansion compatible del maestro institucional MEF.
ALTER TABLE public.budget_execution_records
    ADD COLUMN IF NOT EXISTS is_canonical_total boolean NOT NULL DEFAULT false,
    ADD COLUMN IF NOT EXISTS pia_amount numeric(16,2),
    ADD COLUMN IF NOT EXISTS certified_amount numeric(16,2),
    ADD COLUMN IF NOT EXISTS committed_annual_amount numeric(16,2),
    ADD COLUMN IF NOT EXISTS monthly_commitment_amount numeric(16,2),
    ADD COLUMN IF NOT EXISTS paid_amount numeric(16,2),
    ADD COLUMN IF NOT EXISTS modification_amount numeric(16,2),
    ADD COLUMN IF NOT EXISTS execution_pct numeric(8,3),
    ADD COLUMN IF NOT EXISTS cut_type text,
    ADD COLUMN IF NOT EXISTS official_cut_date date,
    ADD COLUMN IF NOT EXISTS breakdown_by_scope jsonb,
    ADD COLUMN IF NOT EXISTS breakdown_by_funding_source jsonb NOT NULL DEFAULT '[]'::jsonb,
    ADD COLUMN IF NOT EXISTS comparison_cuts jsonb NOT NULL DEFAULT '[]'::jsonb;

ALTER TABLE public.budget_execution_records
    ADD CONSTRAINT budget_canonical_moments_v2 CHECK (
        NOT is_canonical_total OR (
            pia_amount IS NOT NULL AND certified_amount IS NOT NULL
            AND committed_annual_amount IS NOT NULL AND monthly_commitment_amount IS NOT NULL
            AND paid_amount IS NOT NULL AND modification_amount IS NOT NULL
            AND execution_pct IS NOT NULL AND official_cut_date IS NOT NULL
            AND cut_type IN ('daily', 'monthly') AND cut_type IS NOT NULL
            AND budget_category IN ('TOTAL', 'TOTAL_INSTITUCIONAL_ACTPROY')
            AND pia_amount >= 0 AND paid_amount >= 0 AND monthly_commitment_amount >= 0
            AND budgeted_amount >= certified_amount
            AND certified_amount >= committed_annual_amount
            AND committed_annual_amount >= executed_amount AND executed_amount >= paid_amount
            AND modification_amount = budgeted_amount - pia_amount
            AND (budgeted_amount = 0 OR abs(round(executed_amount / budgeted_amount * 100, 1)
                 - execution_pct) <= 0.1)
            AND breakdown_by_scope IS NOT NULL
            AND jsonb_typeof(breakdown_by_scope) = 'object'
            AND breakdown_by_scope ? 'Proyecto' AND breakdown_by_scope ? 'Actividad'
            AND raw_payload ? 'CUT_TYPE' AND raw_payload ? 'SCOPE'
            AND raw_payload ->> 'CUT_TYPE' = cut_type
            AND raw_payload ->> 'SCOPE' = 'ActProy'
            AND abs(budgeted_amount
                - (breakdown_by_scope #>> '{Proyecto,moments,budgeted_amount}')::numeric
                - (breakdown_by_scope #>> '{Actividad,moments,budgeted_amount}')::numeric) <= 1
            AND execution_pct BETWEEN 0 AND 100
            AND pia_amount <> 'NaN'::numeric AND budgeted_amount <> 'NaN'::numeric
            AND certified_amount <> 'NaN'::numeric AND committed_annual_amount <> 'NaN'::numeric
            AND monthly_commitment_amount <> 'NaN'::numeric AND executed_amount <> 'NaN'::numeric
            AND paid_amount <> 'NaN'::numeric AND modification_amount <> 'NaN'::numeric
            AND execution_pct <> 'NaN'::numeric
        )
    );
