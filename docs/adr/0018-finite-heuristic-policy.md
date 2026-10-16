---
id: adr-0018-finite-heuristic-policy
title: Catálogo finito y política heurística explícita
type: adr
status: proposed
date: 2026-10-15
created: 2026-10-15
deciders: []
consulted: []
supersedes: adr-0010-alert-trazabilidad-y-candidatos-004
tags: [deterministic-engine, sdd]
source: ai
generator: codex-gpt-6
generated_at: 2026-10-16T04:41:12Z
confidence: medium
verified: false
---

# Catálogo finito y política heurística explícita

Proponer catálogo de 6 reglas y política qhaway-exploratory-1 sin cifras UIT ni plazos legales.
La adopción requiere decisión humana y no modifica runtime ni ADR anteriores.
Los detalles falsables residen en la propuesta 011, sin presumir aprobación de sus umbrales.

## Contexto y planteamiento del problema

Las diez reglas actuales mezclan estadística, texto y supuestos normativos con cobertura desigual.
El código es evidencia de estado, no justificación normativa de sus reglas actuales.

## Factores de decisión

Explicabilidad, ausencia de acusación legal, mínimos y denominadores completos.
Privacidad, revisión humana y alcance Cajamarca se mantienen como garantías.

## Opciones consideradas

### Opción 1

Conservar 10 reglas con perfiles normativos por modalidad: más alcance y mayor carga probatoria.

### Opción 2

Evaluar 6 reglas descriptivas en shadow y aplazar 4 familias no acreditadas: menor alcance inicial.

## Decisión propuesta

Proponer catálogo de 6 reglas y política qhaway-exploratory-1 sin cifras UIT ni plazos legales.
Esta propuesta no está accepted ni implementada.

## Consecuencias positivas

El contrato permite probar límites y razones antes de cambiar el productor operativo.
La evidencia de cada resultado puede reconstruirse sin LLM ni fuentes consultadas durante replay.

## Consecuencias negativas

Se retiran capacidades visibles del cálculo nuevo hasta reunir evidencia contractual suficiente.

## Qué se vuelve difícil de revertir

Los analistas deberán interpretar diferencias frente a 004 y calibrar umbrales antes de uso.
Preservar historial y mapas de identidad tiene coste permanente aunque se retire el productor.

## Comprobación de adopción

Ejecutar RN/CA-011-01 a 16 y pruebas del plan antes de solicitar promoción.
Ninguna validación documental sustituye pruebas del runtime ni aprobación del panel.

## Enlaces y evidencia

[Plan 011](../../specs/011-deterministic-engine/plan.md) y su inventario de código con líneas.
[Spec 011](../../specs/011-deterministic-engine/spec.md): decisión propuesta, no autoridad factual.
[Pruebas 011](../../specs/011-deterministic-engine/test-plan.md).
