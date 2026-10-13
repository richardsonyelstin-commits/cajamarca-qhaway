# Estado de projects/cajamarca-qhaway

Generado automaticamente el 2026-10-13 14:22. No editar a mano: lo reescriben los hooks de memoria.

- Rama: `agent/infra/cloud-migration`
- HEAD: `11b93f6 docs: update latest session snapshot (24 minutes ago)`
- Arbol de trabajo: 15 archivo(s) con cambios.
    M context/snapshots/latest.md
     M package.json
     D server.js
     M src/cajamarca_qhaway/capabilities/live_harvest/daemon.py
     M src/cajamarca_qhaway/capabilities/live_harvest/watermark_store.py
     M src/cajamarca_qhaway/persistence/connection.py
     M src/cajamarca_qhaway/persistence/repositories/citizen_report_repository.py
     M src/cajamarca_qhaway/persistence/repositories/entity_repository.py
     M src/cajamarca_qhaway/web/exporter.py
     M tests/test_persistence.py
     M web/entidades.html
     M web/src/data/verified-snapshot.json
    ... y 3 mas

## Ultimos commits

- `11b93f6 docs: update latest session snapshot`
- `9cf21c0 merge: incorporar capacidad 007 geoespacial en CLI y visor web, y sincronizacion de moderacion con RLS (Sprint 3)`
- `930df27 feat(capabilities): integrar capacidad 007 geoespacial en CLI y visor web, y sincronizar moderacion de denuncias (Sprint 3)`
- `ebcf7c5 merge: consolidacion frontend, ADR 0008 MPA, pantallas 404 y retiro de Consulta Amigable (Sprint 2)`
- `bd1d7cd feat(arch): formalizar arquitectura MPA en ADR 0008, pantallas 404 y retiro de Consulta Amigable`
- `d76da84 merge: remediar privacidad en denuncias, datos reales en panel revisor y persistencia DB (Sprint 1)`

## Por donde entrar

- `docs/INDEX.md` — mapa de la documentacion
- `AGENTS.md` — reglas del proyecto
- `PROJECT.yaml` — alcance y contexto

## Pruebas: `.venv/Scripts/python -m pytest -q` o `npm test`
