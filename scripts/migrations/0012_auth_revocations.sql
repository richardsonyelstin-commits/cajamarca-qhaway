-- Revocaciones compartidas. Solo el backend operativo accede a esta tabla.
CREATE TABLE IF NOT EXISTS public.auth_revocations (
    token_hash TEXT PRIMARY KEY CHECK (length(token_hash) = 64),
    expires_at BIGINT NOT NULL
);
ALTER TABLE public.auth_revocations ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.auth_revocations FROM anon, authenticated;
CREATE INDEX IF NOT EXISTS auth_revocations_expiry_idx
    ON public.auth_revocations (expires_at);
-- Mantenimiento privado permitido: DELETE WHERE expires_at < EXTRACT(EPOCH FROM NOW()).
