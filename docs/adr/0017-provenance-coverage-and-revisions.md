---
id: adr-0017-provenance-coverage-and-revisions
title: Procedencia, cobertura y revisiones por cohorte
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

# Procedencia, cobertura y revisiones por cohorte

Proponer revisiones por fuente y consenso de fact/deleted; conflicto invalida scope completo.
La adopción requiere decisión humana y no modifica runtime ni ADR anteriores.
Los detalles falsables residen en la propuesta 011, sin presumir aprobación de sus umbrales.

## Contexto y planteamiento del problema

Varias fuentes y lotes permiten contar dos veces o elegir silenciosamente observaciones opuestas.
El código es evidencia de estado, no justificación normativa de sus reglas actuales.

## Factores de decisión

No doble conteo, ausencia explícita, trazabilidad de cobertura y conflictos conservados.
Privacidad, revisión humana y alcance Cajamarca se mantienen como garantías.

## Opciones consideradas

### Opción 1

Prioridad de fuentes con fallback: más resultados, oculta contradicciones si no se registran.

### Opción 2

Consenso de hechos elegibles por clave y manifiesto explícito: menos resultados y más auditoría.

## Decisión propuesta

Proponer revisiones por fuente y consenso de fact/deleted; conflicto invalida scope completo.
Esta propuesta no está accepted ni implementada.

## Consecuencias positivas

El contrato permite probar límites y razones antes de cambiar el productor operativo.
La evidencia de cada resultado puede reconstruirse sin LLM ni fuentes consultadas durante replay.

## Consecuencias negativas

Un error de una fuente puede impedir evaluar un scope hasta reconciliarlo; menor disponibilidad.

## Qué se vuelve difícil de revertir

La identidad oficial del award y la certificación de revisión quedan en la frontera de adaptadores.
Preservar historial y mapas de identidad tiene coste permanente aunque se retire el productor.

## Comprobación de adopción

Ejecutar RN/CA-011-01 a 16 y pruebas del plan antes de solicitar promoción.
Ninguna validación documental sustituye pruebas del runtime ni aprobación del panel.

## Enlaces y evidencia

[Plan 011](../../specs/011-deterministic-engine/plan.md) y su inventario de código con líneas.
[Spec 011](../../specs/011-deterministic-engine/spec.md): decisión propuesta, no autoridad factual.
[Pruebas 011](../../specs/011-deterministic-engine/test-plan.md).
