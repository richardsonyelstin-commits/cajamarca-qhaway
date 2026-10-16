---
title: "SDD - cajamarca-qhaway"
status: active
updated: 2026-10-16
source: ai
generator: codex
generated_at: 2026-10-16T07:14:27.989761+00:00
confidence: high
verified: false
---

# SDD - cajamarca-qhaway

Cada capacidad separa requisitos, diseño y evidencia de implementación.
El estado documental no se infiere de que un módulo exista o sus pruebas pasen.
La Constitución vigente y sus propuestas se identifican explícitamente.

## Artefactos

spec.md fija reglas y aceptación; plan.md describe el diseño y tasks.md organiza la ejecución.
011 incorpora test-plan.md, traceability.json, contratos cerrados y vectores sintéticos.
El generador emite DTO desde JSON Schema y --check detecta divergencias.
La referencia normativa del método es [constitution.md](constitution.md).

## Estados y aprobación

Las specs heredadas conservan draft y los ADR mantienen sus estados originales.
011 conserva proposed aunque su implementación privada esté disponible.
No se cambia verified:false a true ni se inventan firmas de aceptación.
La Constitución v2 sigue vigente; la sección v3 de 011 permanece propuesta.
La ejecución técnica fue autorizada por el propietario en esta conversación.
La calibración y la promoción productiva requieren evidencia y decisiones propias.

## Contratos y coexistencia

Los seis modelos heredados siguen en [models/](../../src/cajamarca_qhaway/models/).
011 usa [contratos versionados](../../specs/011-deterministic-engine/contracts/).
Sus evaluaciones no son Alert ni trasladan decisiones humanas o prioridad histórica.
Las fuentes concretas de comportamiento son el código y sus pruebas, no las notas IA sin verificar.
El [mapa de capacidades](../../specs/README.md) permite localizar requisitos y módulos.
