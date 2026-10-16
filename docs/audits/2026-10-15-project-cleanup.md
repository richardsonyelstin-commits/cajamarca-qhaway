---
title: Limpieza del proyecto y actualización desde GitHub
source: ai
generator: codex-gpt-6.1-sol
generated_at: 2026-10-16T04:29:12Z
confidence: high
verified: false
---

# Limpieza del proyecto y actualización desde GitHub
Las ramas locales y remotas conocidas quedaron incorporadas al historial local de main.
Se corrigieron los errores de tipos, lint y las incompatibilidades de la integración.
La instrucción humana establece trabajo directo en main, sin nuevas ramas divergentes.

## Consolidación autorizada

El propietario autorizó expresamente la integración y las correcciones el 2026-10-15.
El fetch recuperó main remoto en `25f2974`, que incorpora la remediación `eabb76b`.
La consolidación local conserva los dos desarrollos posteriores mediante estos merges:

- `136322f`: capacidades v2 y remediación de seguridad.
- `0d8f9e5`: reconciliación de la rama presupuestal, ya incorporada por el PR 12.

Fuentes: `git log --oneline origin/main..main` y los padres de ambos commits.
Las 22 ramas locales auxiliares se eliminaron con `git branch -d`, tras verificar ascendencia.
Solo permanece `main`; no se eliminaron ramas en GitHub.
Cada referencia remota conocida se comprobó con `git merge-base --is-ancestor <ref> main`.
La autenticación Supabase de main prevalece sobre las antiguas credenciales locales.
Los contratos v2 de expedientes, conectores y privacidad permanecen incorporados.
Los dos ADR 0014 existentes se preservan con sus nombres e historial originales.
No se hizo push, migración productiva ni despliegue.

## Correcciones y fuentes

- Imports y variables sin uso, ordenación, UTC y simplificaciones equivalentes: diff Python.
- T1: nombres canónicos `threshold_value` y `retrieved_at` en el modelo geoespacial.
- T2: validación y tipado de `ChannelType` en `web/server.py`.
- T3: SQL de migración versionada y conjunto de IDs tipados en `entity_mapping/seed.py`.
- T4: comprobaciones explícitas de campos SUNAT en `sunat_enrichment/client.py`.
- T5: listas canónicas en los repositorios de alertas y señales.
- L1-L3: excepciones específicas o registradas y contextos combinados en pruebas.
- Tokens malformados se rechazan antes de construir cabeceras HTTP: `web/auth.py`.
- El intercambio OAuth y las revocaciones compartidas sustituyen las pruebas de firma local.
- Las decisiones se guardan una vez mediante `AlertRepository.save_decision`.
- La moderación usa `CitizenReportRepository.moderate_pending` con transición condicional.
- La validación JSON ocurre antes del rechazo de operaciones privadas en el respaldo WSGI.
- Ambos runtimes filtran campos desconocidos y contadores privados del snapshot público.
- El panel distingue rechazo de sesión de indisponibilidad: `web/src/js/veedor-auth.js`.
- El harness Node carga el módulo real de sesión y verifica el cierre sin perfil de respaldo.

Fuentes de privacidad: `tests/test_public_snapshot_privacy.py`
y `tests/test_fallback_fail_closed.py`.
Fuentes de durabilidad: `tests/test_audit_remediation.py`
y las pruebas de persistencia de reportes y revisión.
La prueba del snapshot se reprodujo en rojo para el fallback antes de corregirlo.
La política futura está en `AGENTS.md` y en la memoria operativa del workspace.

## Evidencia de verificación

Comandos Python ejecutados con `.venv/Scripts/python.exe` desde la raíz del proyecto.

| Compuerta | Comando | Resultado |
| --- | --- | --- |
| Tipos | `-m pyright --pythonpath .venv/Scripts/python.exe src` | 0 errores |
| Lint | `-m ruff check src tests scripts api web/tools` | 0 incidencias |
| Python conjunto | `-m pytest -q --tb=short` | 337 pasan antes de ampliar privacidad |
| Python final | `-m pytest -q --tb=short` | 338 pasan en 101,51 segundos |
| Node | `node --test tests/*.test.mjs` | 25 pasan |
| Privacidad y remediación | Pytest de snapshot, fallback y remediación | 59 pasan |
| Integridad web | `-m cajamarca_qhaway.cli web audit` | CONFORME |
| Cifras | `scripts/audit_snapshot_parity.py` | PASS |
| Accesibilidad estática | `scripts/audit_accessibility_static.py` | PASS, 16 páginas |
| Caracteres | `scripts/audit_antislop.py` | PASS |
| Dependencias instaladas | `-m pip check` | Sin conflictos |
| Diff | `git diff --check` | PASS |

Estas pruebas locales no certifican configuración externa, CAPTCHA ni ejecución cloud.
El JSON de datos públicos no forma parte de las correcciones funcionales de esta intervención.

## Cachés y alcance operativo

En la primera intervención se localizaron 21 directorios pycache y dos cachés de herramientas.
La revisión automática rechazó ambos intentos de borrado con `blocked by policy`.
Las cachés siguen presentes y están excluidas explícitamente en `.gitignore`.
No se intentaron otras vías de eliminación tras el rechazo.
Los datos cosechados, fuentes originales y entorno virtual se conservaron.
