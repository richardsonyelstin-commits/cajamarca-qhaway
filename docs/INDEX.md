---
title: "Índice de documentación - cajamarca-qhaway"
status: active
updated: 2026-10-16
source: ai
generator: codex
generated_at: 2026-10-16T07:20:30.359018+00:00
confidence: high
verified: false
---

# Índice de documentación - cajamarca-qhaway

Este mapa separa guías actuales, requisitos, decisiones y registros de corridas anteriores.
Cargar solo los documentos que la tarea requiera; no usar notas IA como autoridad factual.
La aprobación humana y la disponibilidad productiva no se deducen del estado de un documento.

## Entrada

[README](../README.md), [AGENTS](../AGENTS.md), [PROJECT](../PROJECT.yaml) y
[mapa de capacidades](../specs/README.md) describen el árbol y sus comandos.
Los snapshots de contexto son observaciones generadas de su fecha, no sustituyen el código.

## Guías y diseño por área

| Documento | Cargar cuando |
|---|---|
| [Índice de decisiones de arquitectura](adr/README.md) | Consultar al modificar adr |
| [Cosecha continua y fuentes oficiales](architecture/002-live-harvester-worker.md) | Consultar al modificar architecture |
| [Persistencia y durabilidad](architecture/003-supabase-persistence-architecture.md) | Consultar al modificar architecture |
| [Mapa de páginas y acceso](architecture/004-sitemap-cajamarca-qhaway.md) | Consultar al modificar architecture |
| [Arquitectura web MPA y API privada](architecture/005-web-platform-architecture.md) | Consultar al modificar architecture |
| [Presupuesto institucional y evidencia dual de contrataciones](architecture/006-budget-and-procurement-evidence.md) | Consultar al modificar architecture |
| [Correccion de F01 a F08](architecture/007-audit-remediation-security-consistency.md) | Consultar al modificar architecture |
| [Arquitectura - cajamarca-qhaway](architecture/overview.md) | Consultar al modificar architecture |
| [Despliegue y operación del proyecto](deployment/001-cloud-deployment-guide.md) | Consultar al modificar deployment |
| [Glosario técnico del proyecto](glossary.md) | Consultar al modificar docs |
| [Roadmap - cajamarca-qhaway](roadmap.md) | Consultar al modificar docs |
| [Constitución del método - cajamarca-qhaway](sdd/constitution.md) | Consultar al modificar sdd |
| [SDD - cajamarca-qhaway](sdd/README.md) | Consultar al modificar sdd |

## Especificaciones y contratos

| Documento | Uso |
|---|---|
| [Mapa de specs](../specs/README.md) | Estados y módulos por capacidad |
| [Decisiones pendientes](../specs/pending-adrs.md) | Historia de decisiones y pendientes humanos |
| [Spec 011](../specs/011-deterministic-engine/spec.md) | Reglas y aceptación |
| [Plan 011](../specs/011-deterministic-engine/plan.md) | Selección, precedencia y hashes |
| [Tareas 011](../specs/011-deterministic-engine/tasks.md) | Pruebas nominales por tarea |
| [Pruebas 011](../specs/011-deterministic-engine/test-plan.md) | Matriz y compuertas |
| [Trazabilidad 011](../specs/011-deterministic-engine/traceability.json) | RN, CA, tarea y test |
| [Schemas 011](../specs/011-deterministic-engine/contracts/) | Request, resultado y shadow |
| [Contratos ampliados](contracts/) | JSON Schema presupuestal y de análisis |
| [Herramientas](../scripts/README.md) | Comandos por área |

## Decisiones de arquitectura

[Índice ADR](adr/README.md) contiene todas las decisiones, sus nombres completos y estados.
Los ADR existentes no se editan al actualizar una guía.
No usar solo el prefijo 0005 o 0014: ambos tienen más de un documento histórico.

[Tareas activas](../tasks/active/) y [tareas completadas](../tasks/done/) conservan
sus antecedentes; sus metadatos de revisión no cambian el contenido histórico.

## Antecedentes y evidencia fechada

Los documentos siguientes conservan su corte y sus límites de validación.
Consultar la implementación y las guías antes de ejecutar comandos históricos.

| Documento | Cargar cuando |
|---|---|
| [Auditoría de accesibilidad](a11y/2026-10-13-wcag-2.1-aa-audit.md) | Consultar el corte y sus límites; no representa un estado vivo |
| [Estudio de Factibilidad y Arquitectura: Monitoreo Geoespacial Satelital y Camaras Publicas para Obras Publicas en Cajamarca](architecture/2026-10-13-estudio-factibilidad-monitoreo-geoespacial-satelital-camaras.md) | Consultar el corte y sus límites; no representa un estado vivo |
| [Auditoria Tecnica Integral y de Brechas: Cajamarca Qhaway](audits/2026-10-13-full-project-gap-audit.md) | Consultar el corte y sus límites; no representa un estado vivo |
| [Certificacion operativa del corte MEF 2024-2026](audits/2026-10-14-prod-cutover-certification.md) | Consultar el corte y sus límites; no representa un estado vivo |
| [Verificacion de presupuesto, evidencia dual e identidad Qhaway](audits/2026-10-15-budget-identity-certification.md) | Consultar el corte y sus límites; no representa un estado vivo |
| [Compuertas de la reforma v2 y cobertura oficial](audits/2026-10-15-constitutional-v2-gates.md) | Consultar el corte y sus límites; no representa un estado vivo |
| [Revisión del SDD del motor determinista](audits/2026-10-15-deterministic-engine-sdd-review.md) | Consultar el corte y sus límites; no representa un estado vivo |
| [Auditoría base de extremo a extremo de Cajamarca Qhaway](audits/2026-10-15-e2e-security-baseline.md) | Consultar el corte y sus límites; no representa un estado vivo |
| [Cuadro de control institucional MEF 2024-2026](audits/2026-10-15-mef-control-table.md) | Consultar el corte y sus límites; no representa un estado vivo |
| [Limpieza del proyecto y actualización desde GitHub](audits/2026-10-15-project-cleanup.md) | Consultar el corte y sus límites; no representa un estado vivo |
| [Segunda fase de remediación de autenticación y privacidad](audits/2026-10-15-remediation-phase-two.md) | Consultar el corte y sus límites; no representa un estado vivo |
| [Verificacion local de TK-307](audits/2026-10-15-remediation-validation.md) | Consultar el corte y sus límites; no representa un estado vivo |
| [Implementación privada del motor determinista 011](audits/2026-10-16-deterministic-engine-implementation.md) | Consultar el corte y sus límites; no representa un estado vivo |
| [Actualización integral de documentación](audits/2026-10-16-documentation-refresh.md) | Consultar el corte y sus límites; no representa un estado vivo |
| [Organización y limpieza del repositorio](audits/2026-10-16-project-cleanup.md) | Consultar el corte y sus límites; no representa un estado vivo |
| [Plan Integral de Pedagogía Cívica, Lenguaje Claro y Accesibilidad Cognitiva](plans/2026-10-13-plan-lenguaje-claro-pedagogia-civica.md) | Consultar el corte y sus límites; no representa un estado vivo |
| [Cajamarca Qhaway - Diseño de Fase 1 (plataforma de monitoreo ciudadano de corrupción, ámbito regional)](research/2026-08-20-diseno-cajamarca-qhaway-fase1.md) | Consultar el corte y sus límites; no representa un estado vivo |
| [Verificación técnica de fuentes - OECE/OCDS y MEF](research/2026-08-20-verificacion-tecnica-fuentes.md) | Consultar el corte y sus límites; no representa un estado vivo |
| [Protocolo maestro de remediación de Cajamarca Qhaway](sdd/2026-10-15-master-remediation.md) | Consultar el corte y sus límites; no representa un estado vivo |

## Presupuesto y acceso

L0: AGENTS.md y PROJECT.yaml, hasta 4000 tokens.
L1: documentos seleccionados, hasta 20000 tokens por tarea.
Una actualización amplia puede inventariar metadatos y referencias sin cargar todo el archivo.
No cargar secretos, entornos, dependencias, datos privados o todo el historial por defecto.
brain/ se consulta únicamente para conocimiento transversal y no se duplica aquí.
