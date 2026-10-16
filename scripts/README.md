---
title: Herramientas del proyecto
source: ai
generator: codex
generated_at: 2026-10-16T06:48:23.245654+00:00
confidence: high
verified: false
---

# Herramientas del proyecto

Ejecutar estos comandos desde la raíz del repositorio.
Las herramientas del motor 011 están agrupadas en deterministic-engine/.
Los comandos operativos existentes conservan sus rutas para mantener sus integraciones.

| Área | Rutas | Uso |
|---|---|---|
| Motor 011 | `deterministic-engine/` | Generación, cobertura, mutación y benchmark |
| Auditoría web | `audit_*.py` | Accesibilidad, caracteres y paridad del snapshot |
| Cosecha | `harvest-*.py`, `probe-*.py` | Ingesta y diagnóstico de fuentes oficiales |
| Persistencia | `migrations/`, `verification/` | SQL versionado y comprobaciones de conexión |
| Evidencia | `prepare-*.py` | Preparación privada de expedientes y correspondencias |
| Web | `render-budget-panels.py`, `sync_static_snapshot.py` | Sincronización de vistas |
| Identidad | `regenerate-qhaway-identity.py` | Regeneración del shell y anclajes existentes |

## Motor determinista

```powershell
uv run python scripts/deterministic-engine/generate-deterministic-contracts.py --check
uv run python scripts/deterministic-engine/check-deterministic-coverage.py coverage-engine.json
uv run python scripts/deterministic-engine/mutate-deterministic-engine.py `
  --output context/snapshots/engine-mutations.json
uv run python scripts/deterministic-engine/benchmark-deterministic-engine.py `
  --output context/snapshots/engine-benchmark.json
```

Los dos últimos comandos generan evidencia sintética privada.
La CLI de evaluación se instala desde pyproject.toml como cajamarca-qhaway-engine.

## Verificación de documentación

El mapa global está en docs/INDEX.md y los estados de aprobación en docs/adr/README.md.
Los ejemplos de comandos se ejecutan desde la raíz; no lanzar cosecha, siembra o sincronización
solo para comprobar una guía.
