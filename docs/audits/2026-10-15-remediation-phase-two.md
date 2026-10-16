---
title: Segunda fase de remediación de autenticación y privacidad
status: draft
source: ai
generator: codex-gpt-6
generated_at: 2026-10-15
confidence: medium
verified: false
---

# Segunda fase de remediación de autenticación y privacidad

Se reforzó la validación de sesiones de veedores y la atribución de moderaciones.
El snapshot público ahora permite únicamente campos expresamente autorizados.
Las pruebas locales pasaron; la validación de despliegue y revocación distribuida está pendiente.

## Causas raíz y cambios

En `src/cajamarca_qhaway/web/server.py` se corrigieron cinco contratos:

1. Acreditación: firma, vigencia y registro acreditado vigente.
2. Token: estructura, codificación, plazo y longitud estrictos.
3. Moderación: autoría vinculada a la sesión autenticada.
4. Snapshot: lista positiva de claves públicas y metadatos.
5. Métricas: contadores recalculados a partir de alertas publicadas.

## Validaciones ejecutadas

- `pytest -q tests/test_veedor_auth_guards.py tests/test_review_persistence_guards.py`
  `tests/test_report_persistence_guards.py`: 20 aprobadas.
- `pytest -q tests/test_public_snapshot_privacy.py`: 1 aprobada.
- `pytest -q tests/test_web_platform.py`: 29 aprobadas.
- `node --test tests/admin-review-security.test.mjs`: 5 aprobadas.
- `python -m compileall -q api src tests` y `git diff --check`: correctos.

## Riesgos todavía abiertos

- La revocación por logout se almacena en memoria y no se replica entre instancias.
  Requiere una decisión de sesión distribuida, persistencia y pruebas multiinstancia.
  Evidencia: `src/cajamarca_qhaway/web/server.py` (`_REVOKED_TOKENS`).
- La acreditación se carga al iniciar el proceso; la retirada exige recarga o reinicio.
  Evidencia: `src/cajamarca_qhaway/web/server.py` (`ACCREDITED_VEEDORES`).
- El conflicto de escrituras concurrentes de alertas y las migraciones SQL continúan pendientes.
  [sin verificar] No se ha probado esta fase contra PostgreSQL o Supabase real.
- El funcionamiento en producción, RLS y paridad del runtime serverless están [sin verificar].

## Compuerta de salida

Esta fase no constituye aprobación humana ni autoriza despliegue.
No se efectuaron commits, push ni migraciones de producción durante esta intervención.
