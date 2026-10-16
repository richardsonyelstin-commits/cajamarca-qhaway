---
id: adr-0015-pure-deterministic-engine
title: Núcleo puro y contratos deterministas versionados
type: adr
status: proposed
date: 2026-10-15
created: 2026-10-15
deciders: []
consulted: []
supersedes: adr-0004-motor-de-red-flags-propio
tags: [deterministic-engine, sdd]
source: ai
generator: codex-gpt-6
generated_at: 2026-10-16T04:41:12Z
confidence: medium
verified: false
---

# Núcleo puro y contratos deterministas versionados

Proponer núcleo 011 puro con as_of, estados exhaustivos y esquema engine-2.
La adopción requiere decisión humana y no modifica runtime ni ADR anteriores.
Los detalles falsables residen en la propuesta 011, sin presumir aprobación de sus umbrales.

## Contexto y planteamiento del problema

El motor heredado mezcla evaluación y reloj opcional; la reproducibilidad depende del llamador.
El código es evidencia de estado, no justificación normativa de sus reglas actuales.

## Factores de decisión

Reproducibilidad offline, contratos tipados, compatibilidad de historia y errores explícitos.
Privacidad, revisión humana y alcance Cajamarca se mantienen como garantías.

## Opciones consideradas

### Opción 1

Conservar 004 y endurecerlo incrementalmente: menor migración, mayor acoplamiento heredado.

### Opción 2

Crear núcleo 011 con adaptadores exteriores: más frontera y migración, semántica independiente.

## Decisión propuesta

Proponer núcleo 011 puro con as_of, estados exhaustivos y esquema engine-2.
Esta propuesta no está accepted ni implementada.

## Consecuencias positivas

El contrato permite probar límites y razones antes de cambiar el productor operativo.
La evidencia de cada resultado puede reconstruirse sin LLM ni fuentes consultadas durante replay.

## Consecuencias negativas

Las firmas y DTO nuevos requieren mantener adaptadores durante coexistencia.

## Qué se vuelve difícil de revertir

Los productores y consumidores deberán negociar schema_version y manejo de estados.
Preservar historial y mapas de identidad tiene coste permanente aunque se retire el productor.

## Comprobación de adopción

Ejecutar RN/CA-011-01 a 16 y pruebas del plan antes de solicitar promoción.
Ninguna validación documental sustituye pruebas del runtime ni aprobación del panel.

## Enlaces y evidencia

[Plan 011](../../specs/011-deterministic-engine/plan.md) y su inventario de código con líneas.
[Spec 011](../../specs/011-deterministic-engine/spec.md): decisión propuesta, no autoridad factual.
[Pruebas 011](../../specs/011-deterministic-engine/test-plan.md).
