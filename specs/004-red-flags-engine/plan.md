---
title: Plan 004 — red-flags-engine
spec: "004"
capability: red-flags-engine
status: draft
created: 2026-08-20
updated: 2026-08-20
source: ai
generator: claude-sonnet-5
generated_at: 2026-08-20T00:00:00Z
confidence: low
verified: false
---

# Plan 004 — red-flags-engine

Diseño técnico parcial. El catálogo final de indicadores (AC-004-01) es la ambigüedad más
bloqueante del proyecto en esta ronda: sin datos reales de `002`/`003` no hay umbral que
calibrar, y calibrar en el vacío produciría indicadores decorativos. Este plan fija la forma del
motor (cómo se declara y evalúa un indicador), no su contenido final.

## Módulos conceptuales (sin nombres de fichero: dependen del stack, ver
`specs/pending-adrs.md`)

- Un **registro de indicadores**, análogo en espíritu al `registry.py` de adaptadores de
  `source-federation` en `scientific-literature-pipeline`: cada indicador se declara con
  `indicator_code`, la función que lo evalúa, su fórmula en texto y su umbral, todo en un único
  lugar auditable — nunca umbrales dispersos en el código de negocio.
- Un **evaluador** que recibe `ProcurementRecord`/`BudgetExecutionRecord` y aplica el catálogo
  completo, produciendo cero o más `RedFlag` por registro de entrada.
- Ningún **agregador de score**: deliberadamente no existe un módulo que combine `RedFlag` en un
  número — esa ausencia es el diseño, no un olvido (RN-004-03).

## Forma de un indicador (contrato interno, no canónico)

```
indicator_code: str            # estable, p. ej. "single-bidder"
formula_description: str       # lenguaje simple, la misma que verá el usuario final
threshold: valor                # el umbral tal como se declara públicamente
applies_to: "procurement" | "procurement+execution"
evaluate(record, threshold) -> RedFlag | None
```

`evaluate()` es puro: mismo registro y mismo umbral producen siempre el mismo resultado —
necesario para que dos ejecuciones del motor sobre el mismo dato sean auditablemente idénticas,
mismo principio que el Artículo 10 de la constitución exige a nivel de proyecto.

## Candidatos de indicador ya identificados (no calibrados)

Documentados aquí como candidatos de diseño, explícitamente **no** como el catálogo final
(AC-004-01 sigue abierta):

| Candidato | Depende de | Umbral |
|---|---|---|
| Proveedor único (un solo postor) | Solo `002` | `[NECESITA ACLARACIÓN: calibrar]` |
| Plazo de licitación anormalmente corto | Solo `002` | `[NECESITA ACLARACIÓN: calibrar]` |
| Ejecución financiera fuera de rango del monto adjudicado | `002` + `003` | `[NECESITA ACLARACIÓN: calibrar]` |
| Proveedor de reciente creación | `002` + fuente de antigüedad no confirmada (CL-004-02) | Bloqueado por AC-004-04 |

Ninguno se implementa con un umbral inventado: implementarlos ahora exigiría fijar un número sin
evidencia, exactamente lo que el Artículo 3 de la constitución prohíbe.

## Dependencias nuevas

`specs/pending-adrs.md` registra la decisión pendiente de si se adapta Cardinal (OCP) o se
implementa el catálogo desde cero. Este plan no fija ninguna librería mientras esa decisión no
se tome, porque la forma del "registro de indicadores" de arriba cambiaría según la respuesta
(adaptar Cardinal implicaría un mapeo a su propio formato de indicador OCDS).

## Riesgos

| Riesgo | Impacto | Mitigación |
|---|---|---|
| Umbral calibrado sobre pocos datos reales de una región pequeña | Ruido: activa demasiado o casi nunca | RN-004-06, umbrales absolutos y justificables en lenguaje simple, no estadísticos |
| Un indicador tienta a evaluar personas en vez de procesos | Viola Artículo 16 | RN-004-04 y revisión explícita de cada candidato antes de implementarlo |
| Motor corre sobre datos parciales (002/003 con huecos de cobertura declarados) | RedFlag basado en información incompleta, sin decirlo | CL-004-01: no evaluar indicadores cuyo dato de entrada falte, en vez de asumir cero |

## Orden de implementación

1. Forma del registro de indicadores y del evaluador puro — no bloqueado.
2. Catálogo final calibrado — **bloqueado por AC-004-01**, que a su vez depende de que `002` y
   `003` produzcan datos reales.
3. Mecanismo de recálculo ante actualización — **bloqueado por AC-002-03 de `002`**.
4. Persistencia — depende de `specs/pending-adrs.md`.

No se escribe estrategia de prueba con casos concretos todavía: los casos de prueba de un
indicador son, literalmente, el corpus dorado que falta calibrar en el paso 2.
