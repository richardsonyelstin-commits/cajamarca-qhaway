---
title: "Índice de decisiones de arquitectura"
status: active
source: ai
generator: codex
generated_at: 2026-10-16T07:18:34.441452+00:00
confidence: high
verified: false
---

# Índice de decisiones de arquitectura

El índice refleja el estado escrito en cada ADR, sin conceder aceptaciones nuevas.
Los prefijos 0005 y 0014 están duplicados históricamente; se cita siempre el nombre completo.
La implementación de una decisión propuesta no altera por sí sola su estado documental.

## Decisiones existentes

| Archivo | Estado declarado | Título |
|---|---|---|
| [0001-lenguaje-y-runtime-python.md](0001-lenguaje-y-runtime-python.md) | accepted | Python como lenguaje y runtime del proyecto |
| [0002-forma-del-pipeline-ingesta.md](0002-forma-del-pipeline-ingesta.md) | accepted | Estado operativo compartido en base de datos, no artefactos en disco |
| [0003-motor-de-base-de-datos-postgresql.md](0003-motor-de-base-de-datos-postgresql.md) | accepted | PostgreSQL como motor de base de datos |
| [0004-motor-de-red-flags-propio.md](0004-motor-de-red-flags-propio.md) | accepted | Motor de red flags propio, informado por la metodología de Cardinal |
| [0005-autenticacion-panel-de-revision.md](0005-autenticacion-panel-de-revision.md) | accepted | Autenticación del panel de revisión vía OAuth con Google |
| [0005-monitoreo-geoespacial-satelital-y-camaras-publicas.md](0005-monitoreo-geoespacial-satelital-y-camaras-publicas.md) | proposed | Monitoreo geoespacial multi-temporal satelital y de camaras publicas para obras de infraestructura |
| [0006-persistencia-universo-contracting-entity.md](0006-persistencia-universo-contracting-entity.md) | accepted | Universo de ContractingEntity como dataset versionado en el repo, sembrado a PostgreSQL |
| [0007-arquitectura-plataforma-web-hibrida.md](0007-arquitectura-plataforma-web-hibrida.md) | proposed | Arquitectura Híbrida de Plataforma Web (Bootstrap 5.3, Vanilla JS ES6+, Supabase y Python Bridge) |
| [0008-adopcion-arquitectura-multi-pagina-y-retiro-spa.md](0008-adopcion-arquitectura-multi-pagina-y-retiro-spa.md) | proposed | Adopcion de Arquitectura Multi-Pagina (MPA) y Retiro de Enrutador SPA Residual |
| [0009-desacoplamiento-local-arquitectura-cloud-hibrida.md](0009-desacoplamiento-local-arquitectura-cloud-hibrida.md) | proposed | Desacoplamiento del Entorno Local y Adopcion de Arquitectura Cloud Hibrida |
| [0010-alert-trazabilidad-y-candidatos-004.md](0010-alert-trazabilidad-y-candidatos-004.md) | accepted | Trazabilidad reforzada de Alert y formulas candidatas del motor |
| [0011-fuente-oficial-mef-consulta-amigable.md](0011-fuente-oficial-mef-consulta-amigable.md) | accepted | Consulta Amigable del MEF como fuente primaria de ejecución presupuestal |
| [0012-corte-oficial-para-subejecucion-mef.md](0012-corte-oficial-para-subejecucion-mef.md) | accepted | Corte oficial para evaluar subejecucion MEF en el ejercicio abierto |
| [0013-presupuesto-institucional-conectores-duales-e-identidad.md](0013-presupuesto-institucional-conectores-duales-e-identidad.md) | proposed | Presupuesto institucional por corte, conectores duales e identidad Qhaway |
| [0014-constitucion-v2-y-priorizacion-de-expedientes.md](0014-constitucion-v2-y-priorizacion-de-expedientes.md) | accepted | Constitución v2 y priorización explicable de expedientes |
| [0014-identidad-acreditada-y-consistencia-privada.md](0014-identidad-acreditada-y-consistencia-privada.md) | proposed | Identidad acreditada delegada y consistencia de operaciones privadas |
| [0015-pure-deterministic-engine.md](0015-pure-deterministic-engine.md) | proposed | Núcleo puro y contratos deterministas versionados |
| [0016-exact-money-and-replay-identity.md](0016-exact-money-and-replay-identity.md) | proposed | Dinero exacto e identidad de replay |
| [0017-provenance-coverage-and-revisions.md](0017-provenance-coverage-and-revisions.md) | proposed | Procedencia, cobertura y revisiones por cohorte |
| [0018-finite-heuristic-policy.md](0018-finite-heuristic-policy.md) | proposed | Catálogo finito y política heurística explícita |
| [0019-shadow-migration-and-case-priority.md](0019-shadow-migration-and-case-priority.md) | proposed | Migración shadow y prioridad fuera del núcleo |

## Mantenimiento

No renumerar, renombrar ni reescribir un ADR existente para resolver los prefijos duplicados.
Una decisión que cambie crea un ADR nuevo con supersedes y estado proposed.
Solo un humano acepta decisiones y solo un humano cambia verified a true.
La coexistencia privada 004/011 se observa en el código y no acredita adopción productiva.
