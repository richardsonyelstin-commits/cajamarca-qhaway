---
id: adr-0004
title: Motor de red flags propio, informado por la metodología de Cardinal
type: adr
status: accepted
created: 2026-08-20
updated: 2026-08-20
date: 2026-08-20
accepted_at: 2026-08-20
deciders: [richardsonyelstin]
consulted: []
supersedes: null
superseded_by: null
tags: [decision, red-flags, cardinal]
source: ai
generator: claude-sonnet-5
generated_at: 2026-08-20T00:00:00Z
confidence: low
verified: false
decides:
  - red-flags-engine
---

# Motor de red flags propio, informado por la metodología de Cardinal

Se construye un motor de red flags propio y pequeño (5-10 indicadores, per RN-004-01), usando la
metodología pública de Cardinal (OCP) como referencia de diseño para las fórmulas, no como
dependencia de código.

## Contexto y planteamiento del problema

`specs/004-red-flags-engine/spec.md` (AC-004-02) deja explícitamente pendiente si se adapta
Cardinal, la herramienta de red flags de Open Contracting Partnership (documentada con 73
indicadores alineados a OCDS), o si se construye el catálogo desde cero. La propia spec fija que
Fase 1 solo necesita entre 5 y 10 indicadores calibrados para Cajamarca (RN-004-01), no los 73, y
que ningún umbral puede fijarse todavía porque depende de datos reales de `002`/`003`
(AC-004-01) — ambigüedad que ninguna decisión de "qué motor usar" resuelve por sí sola.

Ninguna spec, plan ni el documento de verificación técnica de este proyecto confirma con evidencia
real (código fuente inspeccionado, prueba de integración) en qué lenguaje o forma de distribución
está Cardinal, ni el coste real de integrarlo desde un backend Python. El diseño de producto
(`docs/research/2026-08-20-diseno-cajamarca-qhaway-fase1.md`, §3.4) lo describe como "open-source,
73 indicadores documentados", pero eso es una descripción de alcance, no una verificación técnica
de integración — y ese documento es `verified: false`. Esta decisión se toma, por tanto, sin ese
dato, y lo declara como límite en vez de inventarlo.

## Factores de decisión

- Tamaño real del catálogo necesario en Fase 1: 5-10 indicadores (RN-004-01), no 73.
- Calibración obligatoria contra datos reales de Cajamarca (AC-004-01) — el umbral de cualquier
  indicador, venga de Cardinal o no, tiene que recalibrarse para este volumen regional antes de
  ser útil, según RN-004-06 (umbrales absolutos, no comparación estadística contra muestra
  nacional).
- Ausencia de verificación técnica del stack real de Cardinal y de su coste de integración desde
  Python (ADR 0001) — información que ninguna fuente de este proyecto confirma en esta ronda.
- Explicabilidad no negociable (Artículo 15 de la constitución): cada indicador debe exponer
  fórmula y umbral en lenguaje simple, verificable por un tercero no técnico (CU3, CU4).
- Carga de mantenimiento para un equipo pequeño: una dependencia externa de código evolutivo
  añade un ciclo de actualización que gestionar, frente a un código propio pequeño y autocontenido.

## Opciones consideradas

### Opción 1 — Adoptar/integrar Cardinal directamente como motor

Usar Cardinal como dependencia o servicio, alimentándolo con los datos OCDS ya normalizados de
`002-seace-ingestion` y consumiendo su salida como fuente de `RedFlag`.

- A favor: evita reimplementar fórmulas de indicadores ya publicadas y potencialmente revisadas
  por la comunidad de OCP, en vez de que este proyecto las escriba desde cero.
- A favor: aporta credibilidad externa ("usa la misma metodología que la herramienta de referencia
  de Open Contracting Partnership") frente a cuestionamientos sobre la rigurosidad del proyecto.
- A favor: si Fase 2 amplía el catálogo más allá de 5-10 indicadores, tener a Cardinal ya
  integrado facilitaría incorporar más de sus 73 indicadores sin duplicar trabajo.
- En contra: el coste real de integración es desconocido — ninguna fuente de este proyecto
  verificó el lenguaje, la forma de distribución (librería, binario, servicio) ni la compatibilidad
  de Cardinal con el stack Python elegido en el ADR 0001; adoptarlo sin esa verificación sería
  exactamente el tipo de "supuesto silencioso" que el Artículo 3 de la constitución prohíbe.
- En contra: Fase 1 solo necesita 5-10 indicadores calibrados específicamente para Cajamarca
  (RN-004-01); traer un motor de propósito general con 73 indicadores para usar una fracción
  pequeña es desproporcionado para el alcance actual.
- En contra: los 73 indicadores de Cardinal están, presumiblemente, calibrados con referencia a
  volumen nacional o internacional; RN-004-06 exige umbrales absolutos justificables para el
  volumen bajo de una sola región — es decir, la calibración de Cardinal no serviría "tal cual" de
  todos modos, y habría que recalibrar exactamente igual que si se construyera desde cero, lo que
  reduce el beneficio real de "reúso" a "referencia metodológica", no a "código reutilizable".

### Opción 2 — Motor propio pequeño, informado por la metodología pública de Cardinal como referencia

Construir el catálogo de 5-10 indicadores desde cero en Python, consultando las fórmulas y la
justificación de los indicadores de Cardinal (donde estén documentadas públicamente) como punto de
partida conceptual, sin depender de su código.

- A favor: control total sobre la forma exacta de cada indicador (`indicator_code`,
  `formula_description`, `threshold`), que ya está fijada en el contrato canónico `RedFlag`
  (Artículo 19) y en el plan 004 (`registro de indicadores` + `evaluador puro`) — no hace falta
  adaptar la salida de una herramienta externa al contrato propio.
- A favor: sin dependencia externa de código cuyo ciclo de mantenimiento y versión no controla
  este equipo pequeño.
- A favor: un catálogo pequeño y autocontenido es más fácil de auditar y explicar a un usuario no
  técnico (CU4) que una integración con una herramienta de propósito general.
- A favor: evita comprometerse a una integración cuyo coste real no se ha verificado.
- En contra: renuncia a la validación implícita de la comunidad de OCP sobre las fórmulas de
  Cardinal — mayor riesgo de un error sutil en una fórmula propia que nadie más ha revisado.
- En contra: si Fase 2 necesita escalar el catálogo más allá de 5-10 indicadores, no hay beneficio
  de reúso previo — habría que evaluar esta decisión de nuevo desde cero.
- En contra: coste de "no inventado aquí" — más código propio que mantener a largo plazo si el
  catálogo crece.

## Decisión

**Opción 2: motor propio pequeño, informado por la metodología pública de Cardinal.**

Gana porque el alcance real de Fase 1 (5-10 indicadores, RN-004-01) no aprovecha la ventaja
principal de Cardinal (73 indicadores ya construidos), y porque cualquier indicador —venga de
Cardinal o no— exige recalibración contra datos reales de Cajamarca con umbrales absolutos
(RN-004-06, AC-004-01), lo que reduce el beneficio de "reúso de código" a "referencia de
metodología". Comprometerse a integrar Cardinal sin verificación técnica de su stack real y su
coste de integración sería exactamente el tipo de decisión sin evidencia que el Artículo 3 de la
constitución prohíbe tomar en una spec, y este ADR aplica el mismo estándar aquí. La forma ya
esbozada en `specs/004-red-flags-engine/plan.md` (registro de indicadores + evaluador puro,
`evaluate(record, threshold) -> RedFlag | None`) es compatible con esta decisión sin cambios.

Esta decisión no descarta usar los nombres y las fórmulas publicadas de los indicadores de
Cardinal como referencia de diseño al calibrar el catálogo de Fase 1 (AC-004-01) — solo descarta
depender de su código o su ejecución como parte del sistema en producción.

**Limitación reconocida**: esta decisión se toma sin haber verificado técnicamente el lenguaje,
la licencia de uso concreta ni el coste real de integración de Cardinal. Si en el futuro se
confirma que Cardinal integra de forma directa y barata con el stack Python de este proyecto (ADR
0001), y el catálogo necesita escalar más allá de 5-10 indicadores, esta decisión se revisita con
un ADR nuevo que la sustituya, no editando este documento.

## Consecuencias

### Positivas

- El catálogo de 5-10 indicadores se implementa directamente contra el contrato `RedFlag` sin capa
  de adaptación a un formato externo.
- Sin dependencia externa cuyo ciclo de actualización el equipo no controla.
- El código del motor permanece pequeño y auditable, apto para explicar a usuarios no técnicos
  (CU3, CU4).
- No se compromete el proyecto a una integración cuyo coste real nadie ha verificado.

### Negativas

- Se renuncia a la validación comunitaria implícita de las fórmulas de Cardinal — el equipo asume
  toda la responsabilidad de que cada fórmula sea correcta y defendible.
- Si Fase 2 necesita escalar el catálogo, no hay ningún trabajo de integración previo del que
  partir — la evaluación de Cardinal se repetiría desde cero en ese momento.
- Mayor volumen de código propio a largo plazo si el catálogo crece más allá de lo previsto en
  Fase 1.
- Posible percepción externa de "reinventar la rueda" frente a interlocutores familiarizados con
  Cardinal/OCP (p. ej. Proética, que sigue el estado del arte de vigilancia de contrataciones) —
  riesgo reputacional menor, mitigable citando explícitamente que la metodología de Cardinal
  informó el diseño, aunque no el código.

### Qué se vuelve difícil de revertir

El `indicator_code`, la forma de `formula_description`/`threshold` y el patrón de "registro de
indicadores + evaluador puro" (ya esbozado en `plan.md`) se convierten en la convención propia del
proyecto para expresar un indicador. Adoptar Cardinal después de tener un catálogo propio en
producción exigiría, o bien mapear la salida de Cardinal al contrato `RedFlag` ya establecido
(coste de adaptación, no de reescritura completa gracias al Artículo 19), o bien migrar el
catálogo entero — cualquiera de las dos rutas es trabajo real, no un cambio de configuración.

## Enlaces

- `specs/pending-adrs.md`, fila 3.
- `specs/004-red-flags-engine/spec.md`, RN-004-01, RN-004-06, AC-004-01, AC-004-02.
- `specs/004-red-flags-engine/plan.md`, sección "Módulos conceptuales" y "Forma de un indicador".
- `docs/research/2026-08-20-diseno-cajamarca-qhaway-fase1.md`, §3.4 (`verified: false`, usado como
  punto de partida, no como autoridad).
- [ADR 0001](0001-lenguaje-y-runtime-python.md) — decisión de la que este ADR depende: solo con
  Python como lenguaje base era evaluable la integración directa de Cardinal.

---

> [!warning] Los ADR son inmutables.
> Si esta decisión cambia, no edites este archivo: crea uno nuevo con `supersedes` y pon
> este en `status: superseded`. El registro histórico es todo el valor de un ADR.
