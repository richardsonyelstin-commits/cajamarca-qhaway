---
id: adr-0019-shadow-migration-and-case-priority
title: Migración shadow y prioridad fuera del núcleo
type: adr
status: proposed
date: 2026-10-15
created: 2026-10-15
deciders: []
consulted: []
supersedes: null
tags: [deterministic-engine, sdd]
source: ai
generator: codex-gpt-6
generated_at: 2026-10-16T04:41:12Z
confidence: medium
verified: false
---

# Migración shadow y prioridad fuera del núcleo

Proponer shadow privado, mapas versionados y ninguna copia de published,score o aprobación.
La adopción requiere decisión humana y no modifica runtime ni ADR anteriores.
Los detalles falsables residen en la propuesta 011, sin presumir aprobación de sus umbrales.

## Contexto y planteamiento del problema

La historia existente contiene candidatos, revisiones y prioridad que no equivale a prueba.
El código es evidencia de estado, no justificación normativa de sus reglas actuales.

## Factores de decisión

Preservar dictámenes, evitar publicación automática, rollback y separar medición de decisión.
Privacidad, revisión humana y alcance Cajamarca se mantienen como garantías.

## Opciones consideradas

### Opción 1

Incluir nueva prioridad determinista en011: una sola salida, añade pesos y doble conteo potencial.

### Opción 2

Excluir prioridad011 y mantener análisis004 separado durante shadow: más reconciliación explícita.

## Decisión propuesta

Proponer shadow privado, mapas versionados y ninguna copia de published,score o aprobación.
Esta propuesta no está accepted ni implementada.

## Consecuencias positivas

El contrato permite probar límites y razones antes de cambiar el productor operativo.
La evidencia de cada resultado puede reconstruirse sin LLM ni fuentes consultadas durante replay.

## Consecuencias negativas

011 no entrega una cola priorizada compuesta; el panel interpreta señales y cobertura separadas.

## Qué se vuelve difícil de revertir

Consumidores de prioridad deberán adoptar una capacidad futura explícita; no hay conversión ciega.
Preservar historial y mapas de identidad tiene coste permanente aunque se retire el productor.

## Comprobación de adopción

Ejecutar RN/CA-011-01 a 16 y pruebas del plan antes de solicitar promoción.
Ninguna validación documental sustituye pruebas del runtime ni aprobación del panel.

## Enlaces y evidencia

[Plan 011](../../specs/011-deterministic-engine/plan.md) y su inventario de código con líneas.
[Spec 011](../../specs/011-deterministic-engine/spec.md): decisión propuesta, no autoridad factual.
[Pruebas 011](../../specs/011-deterministic-engine/test-plan.md).
