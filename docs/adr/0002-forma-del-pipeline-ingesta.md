---
id: adr-0002
title: Estado operativo compartido en base de datos, no artefactos en disco
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
tags: [decision, pipeline, persistencia]
source: ai
generator: claude-sonnet-5
generated_at: 2026-08-20T00:00:00Z
confidence: medium
verified: false
decides:
  - seace-ingestion
  - mef-ingestion
  - red-flags-engine
  - review-panel
  - denuncia-intake
---

# Estado operativo compartido en base de datos, no artefactos en disco

Las capacidades de este proyecto se comunican por un almacén de datos compartido y consultable
(no por artefactos en disco versionados por corrida), con `raw_payload`/evidencia como columnas
JSON dentro de cada registro para conservar la inspeccionabilidad sin renunciar a la consulta.

## Contexto y planteamiento del problema

`specs/pending-adrs.md` (fila 4) señala explícitamente que este debate ya se resolvió en
`scientific-literature-pipeline` (ADR 0001 de ese proyecto: artefactos en disco bajo `runs/<run_id>/`,
sin base de datos compartida) y pide **no copiar esa decisión**, porque las restricciones de este
proyecto son distintas: el pipeline de `scientific-literature-pipeline` es lineal y lo opera una
sola persona desde una CLI; el de `cajamarca-qhaway` tiene un panel de revisión humana en medio del
flujo (`005-review-panel`) que necesita listar, filtrar y decidir sobre candidatos concurrentemente
—varias personas revisando la misma cola—, y en el futuro un dashboard público (`007`, no
especificado aún) que sirve lecturas concurrentes sobre los mismos datos. El volumen es menor, pero
el patrón de acceso es más parecido a una aplicación web con estado compartido que a una tubería de
procesamiento por lotes.

`005-review-panel/plan.md` ya asume, sin decidirlo formalmente, un mecanismo de "reclamo" tipo
`SELECT ... FOR UPDATE` para evitar que dos revisores decidan de forma contradictoria sobre el
mismo `RedFlag` (CL-005-01) — ese diseño da por sentado un almacén con primitivas de concurrencia,
no un directorio de ficheros. `004-red-flags-engine` necesita cruzar `ProcurementRecord` y
`BudgetExecutionRecord` por `entity_id` y periodo, y `PROJECT.yaml` ya anticipa consultas con CTE
recursivas sobre el grafo proveedor-funcionario-contrato — un patrón de consulta relacional, no de
lectura secuencial de artefactos.

## Factores de decisión

- Consulta en vivo por el panel de revisión y por casos de uso del producto (CU1: "busca por
  provincia y filtra por regla activada") — necesita índices, no *grep* sobre ficheros.
- Concurrencia de escritura: varios revisores humanos decidiendo sobre la misma cola de
  candidatos, y (más adelante) ingesta recurrente escribiendo al mismo tiempo.
- Auditabilidad e inmutabilidad de decisiones ya exigidas por las specs (RN-005-07: una decisión
  de revisión es inmutable, una corrección es un registro nuevo que referencia al anterior;
  RN-006 exige lo mismo para moderación de denuncias) — el mecanismo debe garantizar esto, no solo
  declararlo.
- Trazabilidad hasta el dato de origen (Artículo 10 de la constitución): cada registro conserva su
  `raw_payload` íntegro, sin importar dónde viva el estado operativo.
- Coste operativo para un equipo pequeño: cuántos sistemas hay que administrar.
- Consultas relacionales de varios saltos (proveedor↔contrato↔funcionario), ya anticipadas en
  `PROJECT.yaml` con CTE recursivas.

## Opciones consideradas

### Opción 1 — Almacén operativo compartido y consultable (base de datos), con `raw_payload` como columna

Cada capacidad lee y escribe contra un almacén relacional compartido; el payload crudo y los
campos de procedencia (`source`, `retrieved_at`) viven como columnas (JSON/JSONB) dentro del
mismo registro, no en un fichero aparte.

- A favor: soporta directamente el caso de uso central del panel de revisión — listar, filtrar,
  reclamar y decidir sobre una cola compartida de candidatos — sin construir un índice casero
  sobre ficheros.
- A favor: las consultas cruzadas entre `ProcurementRecord` y `BudgetExecutionRecord` por
  `entity_id`, y el grafo proveedor-funcionario-contrato con CTE recursivas que `PROJECT.yaml` ya
  anticipa, son operaciones nativas de un motor relacional.
- A favor: la concurrencia de escritura (varios revisores, ingesta recurrente) tiene primitivas
  estándar (transacciones, bloqueos de fila) en vez de tener que inventarlas sobre un sistema de
  ficheros.
- En contra: se pierde el truco de "una corrida es una carpeta copiable" que hace tan simple la
  auditabilidad en `scientific-literature-pipeline` — aquí la inmutabilidad y el historial de
  decisiones hay que diseñarlos explícitamente como tablas append-only o un registro de eventos,
  no vienen gratis por la forma del almacenamiento.
- En contra: una migración de esquema mal hecha, o un `UPDATE` fuera de disciplina, puede mutar
  estado en su sitio y romper la inmutabilidad que RN-005-07/RN-006 exigen — la garantía depende
  del diseño de las tablas, no de una propiedad estructural del disco.

### Opción 2 — Artefactos versionados en disco por corrida (mismo patrón que `scientific-literature-pipeline`)

Cada capacidad lee el artefacto de la anterior y escribe el suyo bajo un directorio de corrida,
igual que resolvió el proyecto de referencia.

- A favor: auditabilidad e inspeccionabilidad "gratis" — abrir un fichero con un editor de texto
  basta para ver qué pasó entre dos etapas.
- A favor: coste operativo mínimo — no hay que administrar un servicio de base de datos aparte.
- A favor: reejecutar una etapa aislada es trivial porque su entrada está congelada en un fichero.
- En contra: no soporta de forma natural el caso de uso central de `005-review-panel` — una cola
  de revisión filtrable y con reclamo concurrente sobre ficheros exige reinventar, con código
  propio, exactamente las primitivas que una base de datos ya ofrece (índices, bloqueos), lo cual
  es más trabajo y más riesgo de errores de concurrencia que adoptar el almacén directamente.
- En contra: las consultas cruzadas del tipo "todas las alertas de una provincia con ejecución
  fuera de rango del monto adjudicado" implican leer y parsear potencialmente todos los artefactos
  relevantes, sin índice — inviable de mantener rápido a medida que el proyecto acumula corridas.
- En contra: no encaja con el compromiso ya declarado en `PROJECT.yaml` de usar CTE recursivas
  sobre PostgreSQL para el grafo proveedor-funcionario-contrato — esa operación no tiene un
  equivalente razonable sobre ficheros planos.

## Decisión

**Opción 1: almacén operativo compartido y consultable.**

Gana sobre la opción de artefactos en disco precisamente por la razón que `specs/pending-adrs.md`
señala como la diferencia real con `scientific-literature-pipeline`: ese proyecto es una tubería
lineal operada por una sola persona desde una CLI, sin necesidad de servir lecturas y escrituras
concurrentes a varios humanos al mismo tiempo. `cajamarca-qhaway` tiene, desde `005-review-panel`,
un requisito explícito de cola compartida con reclamo concurrente, y desde `PROJECT.yaml` un
compromiso ya declarado de consultas relacionales recursivas. Ninguno de los dos encaja con
artefactos en disco sin reconstruir, con código propio y sin comunidad que lo valide, las
primitivas que un motor relacional ya resuelve. El volumen bajo de datos (factor que sí favorecería
ficheros en `scientific-literature-pipeline`) no es aquí el factor decisivo: lo es el patrón de
acceso concurrente y multi-usuario.

La inspeccionabilidad que la opción de ficheros da gratis no se abandona del todo: cada registro
conserva su `raw_payload` completo como columna, así que "ver el dato exacto que llegó" sigue
siendo tan directo como abrir un registro, aunque no sea abrir un fichero de texto plano.

## Consecuencias

### Positivas

- `005-review-panel` puede implementar su cola de revisión y su mecanismo de reclamo
  (`CL-005-01`) con primitivas estándar de base de datos, sin diseñar concurrencia propia.
- Las consultas de producto (CU1: filtrar por provincia y regla) son índices, no lectura
  secuencial de ficheros.
- El grafo proveedor-funcionario-contrato con CTE recursivas, ya comprometido en `PROJECT.yaml`,
  tiene un lugar natural donde vivir.
- La inmutabilidad de decisiones (RN-005-07, RN-006) se puede forzar con tablas append-only y
  restricciones de base de datos, más difícil de saltarse por accidente que una convención sobre
  ficheros.

### Negativas

- Hay que diseñar explícitamente el mecanismo de append-only/historial de decisiones: no viene
  gratis por la forma del almacenamiento, a diferencia de la opción de ficheros.
- El equipo debe operar y respaldar un sistema de base de datos, un componente más que administrar
  que "solo un directorio de ficheros en git".
- Se pierde el patrón de "entregar una corrida es copiar una carpeta" — archivar o compartir un
  snapshot de un momento del proyecto exige un volcado explícito (`pg_dump` o equivalente), que ya
  no es "la corrida misma" sino una exportación de ella.
- Una migración de esquema mal ejecutada puede corromper estado compartido de una forma que un
  artefacto en disco, por diseño append-only, no permite.

### Qué se vuelve difícil de revertir

El modelo de datos de las seis capacidades se diseñará contra tablas relacionales con relaciones
por `entity_id` y mecanismos de concurrencia (transacciones, bloqueos), no contra el formato de
artefacto de un `run_manifest`. Migrar después a artefactos en disco exigiría reconstruir la cola
de revisión concurrente y las consultas de grafo sin las primitivas que la base de datos da gratis
— es una migración de arquitectura completa, no un cambio de formato de fichero.

## Enlaces

- `specs/pending-adrs.md`, fila 4 — plantea explícitamente que este proyecto no debe copiar la
  decisión de `scientific-literature-pipeline` sin evaluarla para su propio dominio.
- `specs/005-review-panel/plan.md`, sección "Concurrencia (CL-005-01)" — el diseño ya asume un
  almacén con primitivas de bloqueo.
- `specs/002-seace-ingestion/spec.md`, AC-002-05 — deja pendiente el "concepto de corrida", que
  esta decisión resuelve: no hay concepto de corrida tipo `run_manifest`; la procedencia vive por
  registro (`source`, `retrieved_at`, `raw_payload`).
- `PROJECT.yaml`, `stack.datastore: PostgreSQL (propuesto)`.
- [ADR 0001](0001-lenguaje-y-runtime-python.md) — lenguaje base, compatible con cualquiera de las
  dos opciones evaluadas aquí.
- [ADR 0003](0003-motor-de-base-de-datos-postgresql.md) — depende directamente de esta decisión:
  fija qué motor concreto implementa el almacén compartido elegido aquí.
- Contraste directo: `../../scientific-literature-pipeline/docs/adr/0001-arquitectura-de-tuberia-por-etapas.md`.

---

> [!warning] Los ADR son inmutables.
> Si esta decisión cambia, no edites este archivo: crea uno nuevo con `supersedes` y pon
> este en `status: superseded`. El registro histórico es todo el valor de un ADR.
