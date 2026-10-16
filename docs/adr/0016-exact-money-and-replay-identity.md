---
id: adr-0016-exact-money-and-replay-identity
title: Dinero exacto e identidad de replay
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

# Dinero exacto e identidad de replay

Proponer céntimos enteros y racionales coprimos; SHA-256 completo con dominios y sin
autorreferencia.
La adopción requiere decisión humana y no modifica runtime ni ADR anteriores.
Los detalles falsables residen en la propuesta 011, sin presumir aprobación de sus umbrales.

## Contexto y planteamiento del problema

Importes float e IDs truncados heredados no expresan identidad de una corrida completa.
El código es evidencia de estado, no justificación normativa de sus reglas actuales.

## Factores de decisión

Exactitud de comparación, auditoría de preimage y estabilidad independiente del orden.
Privacidad, revisión humana y alcance Cajamarca se mantienen como garantías.

## Opciones consideradas

### Opción 1

Decimal con precisión fija y JCS: estándar externo, exige fijar coerciones y límites.

### Opción 2

Céntimos enteros y JSON restringido sin float: comparación exacta, serializador local especificado.

## Decisión propuesta

Proponer céntimos enteros y racionales coprimos; SHA-256 completo con dominios y sin
autorreferencia.
Esta propuesta no está accepted ni implementada.

## Consecuencias positivas

El contrato permite probar límites y razones antes de cambiar el productor operativo.
La evidencia de cada resultado puede reconstruirse sin LLM ni fuentes consultadas durante replay.

## Consecuencias negativas

El formato racional necesita presentación posterior y difiere de decimales de la UI.

## Qué se vuelve difícil de revertir

IDs históricos necesitan mapa; cambiar canonización cambia todos los IDs de replay.
Preservar historial y mapas de identidad tiene coste permanente aunque se retire el productor.

## Comprobación de adopción

Ejecutar RN/CA-011-01 a 16 y pruebas del plan antes de solicitar promoción.
Ninguna validación documental sustituye pruebas del runtime ni aprobación del panel.

## Enlaces y evidencia

[Plan 011](../../specs/011-deterministic-engine/plan.md) y su inventario de código con líneas.
[Spec 011](../../specs/011-deterministic-engine/spec.md): decisión propuesta, no autoridad factual.
[Pruebas 011](../../specs/011-deterministic-engine/test-plan.md).
