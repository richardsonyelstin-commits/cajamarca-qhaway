---
id: adr-0006
title: Universo de ContractingEntity como dataset versionado en el repo, sembrado a PostgreSQL
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
tags: [decision, entity-mapping, persistencia]
source: ai
generator: claude-sonnet-5
generated_at: 2026-08-20T00:00:00Z
confidence: medium
verified: false
decides:
  - entity-mapping
  - seace-ingestion
  - mef-ingestion
---

# Universo de ContractingEntity como dataset versionado en el repo, sembrado a PostgreSQL

El universo de `ContractingEntity` vive como un dataset declarativo versionado en el propio
repositorio del proyecto (formato a fijar en `plan.md` de `001-entity-mapping`, no en este ADR),
que se siembra a la base de datos operativa (PostgreSQL, ADR 0003) como fuente de lectura para el
resto del sistema.

## Contexto y planteamiento del problema

`specs/001-entity-mapping/spec.md` (AC-001-02) deja explícitamente pendiente si el universo de
`ContractingEntity` vive "versionado en el propio repo (p. ej. como dataset declarativo) o en la
base de datos operativa", y señala que la respuesta depende del stack (ADR 0001) y de si el
proyecto adopta un concepto de "corrida" (ADR 0002). Ambas decisiones ya están tomadas: el
almacén operativo es PostgreSQL (ADR 0002, ADR 0003), y este proyecto no adopta un concepto de
corrida tipo `run_manifest` — la procedencia vive por registro (ADR 0002).

Pero `ContractingEntity` tiene una característica que ninguna otra salida de este proyecto
comparte: la propia spec la describe como algo que "cambia poco" y exige que cada cambio "pueda
auditarse como un diff legible" (spec.md, sección "Salidas"), y `RN-001-02` exige que cada
municipalidad distrital incluida lleve "una justificación de inclusión distinta de 'aparece en el
feed'". Es un universo pequeño (14 entidades obligatorias más un subconjunto priorizado de
distritales, decenas como máximo, no miles) y de baja frecuencia de cambio (`RN-001-06`: "se
revisa por evento, no en tiempo real"). El resto de contratos canónicos (`ProcurementRecord`,
`BudgetExecutionRecord`, `RedFlag`, `Alert`, `CitizenReport`) son de alto volumen relativo y alta
frecuencia de escritura, y ya están decididos para vivir directamente en PostgreSQL por el ADR
0002. La pregunta de este ADR es si `ContractingEntity` sigue esa misma regla general o merece un
tratamiento distinto dado su perfil particular.

## Factores de decisión

- Baja frecuencia de cambio y bajo volumen (decenas de filas, no miles) — perfil muy distinto del
  resto de contratos canónicos.
- Exigencia explícita de la spec de un "diff legible" por cambio (spec.md, sección "Salidas").
- RN-001-02: cada distrital incluida necesita una justificación documentada de inclusión — un
  requisito de gobernanza sobre el propio dato, no solo de almacenamiento.
- Coherencia con el ADR 0002/0003 (almacén operativo compartido en PostgreSQL) para todo lo demás
  que `002` y `003` consumen como llave foránea (`entity_id`).
- Riesgo de doble fuente de verdad si el universo vive en dos sitios a la vez (fichero + tabla).

## Opciones consideradas

### Opción 1 — Dataset declarativo versionado en el repo, sembrado a PostgreSQL

El universo vive como un fichero de datos (formato exacto a fijar en `plan.md`, p. ej. YAML/JSON)
bajo control de versiones del propio repositorio; un paso de siembra/carga lo escribe en la tabla
operativa de PostgreSQL, que es lo que `002` y `003` consultan realmente en tiempo de ingesta.

- A favor: satisface literalmente lo que la spec pide ("diff legible" por cambio) sin construir
  nada nuevo — el historial de Git de ese fichero **es** el diff legible, con autor y fecha
  incluidos gratis.
- A favor: RN-001-02 (justificación de inclusión de una distrital) encaja de forma natural en un
  flujo de revisión de código (una solicitud de cambio sobre el fichero, con su descripción, es
  exactamente esa justificación) — sin construir un mecanismo de justificación aparte.
- A favor: el volumen y la frecuencia de cambio de este contrato en particular (decenas de filas,
  cambios por evento) son precisamente el perfil para el que un fichero versionado es apropiado,
  a diferencia del resto de contratos canónicos, de mayor volumen y escritura concurrente.
- En contra: introduce una segunda fuente de verdad (el fichero y la tabla sembrada), con el
  riesgo de que ambas queden desincronizadas si el paso de siembra se olvida o falla en silencio —
  ningún registro de `002`/`003` puede referenciar un `entity_id` que no exista en la tabla, así
  que un fallo de sincronización rompe la ingesta corriente abajo, no solo la lectura.
- En contra: añade un paso operativo más (el script de siembra) que documentar como dependencia en
  los planes de `002` y `003`.

### Opción 2 — Tabla ordinaria en PostgreSQL, con registro de auditoría propio

`ContractingEntity` vive únicamente como tabla en la misma base de datos operativa que todo lo
demás, con una tabla adicional de historial de cambios (quién, cuándo, por qué) construida a nivel
de aplicación.

- A favor: una sola fuente de verdad, sin paso de siembra ni riesgo de desincronización.
- A favor: consistente con el resto de contratos canónicos, que ya viven en PostgreSQL por el ADR
  0002/0003 — no hay caso especial que explicar.
- En contra: pierde la auditabilidad "gratis" del historial de Git — hay que diseñar, construir y
  mantener una tabla de auditoría de cambios desde cero, replicando en la práctica el mismo patrón
  append-only que RN-005-07 ya exige para decisiones del panel de revisión, ahora para un tercer
  tipo de contrato.
- En contra: un cambio de base de datos no pasa por el mismo proceso de revisión de código que un
  cambio de fichero versionado — cumplir RN-001-02 (justificación explícita por distrital)
  exigiría construir una interfaz o convención de captura de esa justificación en la propia base
  de datos, en vez de heredarla gratis de un flujo de *pull request*.

## Decisión

**Opción 1: dataset declarativo versionado en el repo, sembrado a PostgreSQL.**

Gana porque `ContractingEntity` tiene un perfil claramente distinto del resto de contratos
canónicos —bajo volumen, baja frecuencia de cambio, con una exigencia explícita de auditabilidad
por diff que la propia spec nombra— y ese perfil es exactamente el que justificó, en
`scientific-literature-pipeline`, preferir ficheros versionados sobre una base de datos: pocos
registros, cambios raros, beneficio claro de ser copiable/diffable. Esto **no** revierte el ADR
0002: el resto de la operación (`ProcurementRecord`, `BudgetExecutionRecord`, `RedFlag`, `Alert`,
`CitizenReport`) sigue viviendo en PostgreSQL porque su volumen y su necesidad de concurrencia
son opuestos al de `ContractingEntity`. Es una excepción acotada y justificada por la propia spec
de `001`, no una alternativa general al ADR 0002.

El riesgo de doble fuente de verdad se mitiga, no se ignora: el paso de siembra debe fallar
ruidosamente si detecta una discrepancia entre el fichero y la tabla (mismo principio que
`RN-002-07`, "fallo no se sustituye en silencio"), en vez de servir datos desactualizados sin
avisar.

## Consecuencias

### Positivas

- La spec de `001` queda satisfecha literalmente: el historial de Git del dataset es el "diff
  legible" que pide, sin construir nada adicional.
- RN-001-02 se cumple con el propio proceso de revisión de código (una solicitud de cambio con su
  descripción es la justificación de inclusión de una distrital).
- `002` y `003` siguen consultando una tabla PostgreSQL indexada para el cruce por `entity_id`, sin
  perder rendimiento de consulta.
- El perfil de bajo volumen/baja frecuencia de `ContractingEntity` queda tratado de forma
  proporcional a su naturaleza, sin forzar el mismo patrón que datos de alto volumen.

### Negativas

- Doble fuente de verdad (fichero y tabla sembrada): si el paso de siembra se olvida o falla en
  silencio, la ingesta corriente abajo puede operar contra un universo desactualizado sin que
  nadie lo note de inmediato, salvo que el proceso de siembra/arranque valide explícitamente la
  sincronía y falle ruidosamente si no la hay.
- Un paso operativo más (siembra) que documentar y mantener como dependencia explícita en los
  planes de `002` y `003`, que hoy no lo mencionan.
- Si el universo eventualmente necesita cambiar con mucha frecuencia (más distritales incorporadas
  rápido, por ejemplo tras la coordinación con Proética/Propuesta Ciudadana/GRUFIDES), el flujo de
  fichero + *pull request* podría convertirse en un cuello de botella — en ese caso, esta decisión
  debe revisitarse con evidencia real de esa fricción, no se descarta preventivamente aquí.

### Qué se vuelve difícil de revertir

`entity_id` (derivado del RUC, RN-001-04) se convierte en la clave estable que tanto el fichero
como la tabla sembrada deben preservar idéntica; todo `ProcurementRecord`/`BudgetExecutionRecord`
histórico queda enlazado a ese identificador. Migrar el universo por completo a una tabla ordinaria
después (Opción 2) exigiría, o bien renunciar al historial de Git como mecanismo de auditoría y
construir uno nuevo desde cero, o bien mantener el fichero como archivo histórico congelado sin
seguir siendo la fuente activa — cualquiera de las dos rutas es una migración de proceso, no solo
de esquema.

## Enlaces

- `specs/pending-adrs.md`, fila 7.
- `specs/001-entity-mapping/spec.md`, sección "Salidas" y AC-001-02, RN-001-02, RN-001-06.
- `specs/001-entity-mapping/plan.md`, sección "Orden de implementación", paso 6 — bloqueado por
  esta decisión y por el stack, ambos ya resueltos por este ADR y el ADR 0001.
- [ADR 0002](0002-forma-del-pipeline-ingesta.md) — regla general de la que este ADR declara una
  excepción acotada para `ContractingEntity`.
- [ADR 0003](0003-motor-de-base-de-datos-postgresql.md) — fija el motor al que se siembra el
  dataset versionado.
- Precedente de diseño (no de decisión): `../../scientific-literature-pipeline/docs/adr/0001-arquitectura-de-tuberia-por-etapas.md`,
  factores de decisión "auditabilidad" e "inspección sin instrumentación".

---

> [!warning] Los ADR son inmutables.
> Si esta decisión cambia, no edites este archivo: crea uno nuevo con `supersedes` y pon
> este en `status: superseded`. El registro histórico es todo el valor de un ADR.
