---
id: adr-0003
title: PostgreSQL como motor de base de datos
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
tags: [decision, stack, base-de-datos]
source: ai
generator: claude-sonnet-5
generated_at: 2026-08-20T00:00:00Z
confidence: medium
verified: false
decides:
  - entity-mapping
  - seace-ingestion
  - mef-ingestion
  - red-flags-engine
  - review-panel
  - denuncia-intake
---

# PostgreSQL como motor de base de datos

Se adopta PostgreSQL como el motor concreto que implementa el almacén operativo compartido
decidido en el ADR 0002, sobre SQLite como alternativa real evaluada y descartada para este
patrón de uso.

## Contexto y planteamiento del problema

El ADR 0002 ya decidió que este proyecto necesita un almacén compartido y consultable (no
artefactos en disco) porque `005-review-panel` requiere una cola de revisión concurrente entre
varios humanos, y porque `PROJECT.yaml` ya anticipa consultas con CTE recursivas sobre el grafo
proveedor-funcionario-contrato. Lo que esa decisión no fija es el motor concreto: `PROJECT.yaml`
propone PostgreSQL, pero `specs/pending-adrs.md` (fila 2) señala que esa propuesta viene de un
documento `verified: false` (`docs/research/2026-08-20-diseno-cajamarca-qhaway-fase1.md`) y que,
según el Artículo 8 de la constitución, una decisión de este tipo la aprueba un humano, no queda
validada solo porque un documento de diseño la proponga.

El volumen de datos de Fase 1 es bajo (cientos a pocos miles de registros por año, una sola
región), lo que en principio hace de SQLite una alternativa real y no de paja: SQLite soporta
`WITH RECURSIVE` (CTE recursivas) desde hace años y no tiene problema de volumen a esta escala.
La pregunta real no es de volumen sino de patrón de acceso: cuántos procesos concurrentes escriben
y leen al mismo tiempo, dado que el ADR 0002 ya comprometió a este proyecto con un panel de
revisión concurrente y, en Fase 2 o antes, un dashboard público con lectores concurrentes.

## Factores de decisión

- Concurrencia de escritura: ingesta recurrente (`002`, `003`) y decisiones del panel de revisión
  (`005`) pueden ocurrir al mismo tiempo, sobre las mismas tablas.
- Concurrencia de lectura: el futuro dashboard público (`007`) servirá lecturas concurrentes de
  varios visitantes a la vez, sobre el mismo almacén que recibe escrituras de ingesta.
- Soporte de CTE recursivas para el grafo proveedor-funcionario-contrato (ambos motores lo
  ofrecen, así que este factor no diferencia por sí solo).
- Coste operativo para un equipo pequeño: hosting, backup, disciplina de migraciones.
- Topología de despliegue: si el proceso de ingesta (posiblemente un cron/worker) y el servidor
  web del panel/dashboard corren como procesos separados, necesitan acceso remoto concurrente al
  mismo almacén.
- Ausencia de datos reales de volumen o de carga (nadie ha medido cuántas peticiones concurrentes
  soportará el dashboard público): esta decisión se toma sin ese benchmark, y se declara como
  límite honesto más abajo.

## Opciones consideradas

### Opción 1 - PostgreSQL

- A favor: modelo de concurrencia cliente-servidor con múltiples escritores nativo, sin necesidad
  de trabajar alrededor de un bloqueo de escritor único - encaja directamente con el patrón
  "ingesta recurrente + decisiones humanas concurrentes" que el ADR 0002 estableció.
  concurrentes) sin fricción adicional de configuración.
- A favor: tipo `JSONB` nativo, adecuado para `raw_payload` (Artículo 10 de la constitución) con
  capacidad de indexar/consultar dentro del JSON si hiciera falta más adelante.
- A favor: hosting gestionado barato y ampliamente disponible (Supabase, Neon, Railway, entre
  otros) reduce la carga operativa real para un equipo pequeño, pese a ser "un servicio más".
- A favor: coincide con la propuesta ya declarada en `PROJECT.yaml`, evitando reescribir esa parte
  del manifiesto del proyecto si la decisión se confirma.
- En contra: es un servicio adicional que administrar (aunque gestionado), con conexión, límites
  de conexiones concurrentes en capas gratuitas/económicas, y necesidad de herramienta de
  migraciones (p. ej. Alembic) que el equipo debe aprender a operar con disciplina.
- En contra: no hay benchmark real de este proyecto que confirme que PostgreSQL es necesario a
  este volumen - la justificación es de patrón de acceso (concurrencia), no de throughput medido.

### Opción 2 - SQLite

- A favor: cero infraestructura que operar - un solo fichero, backup trivial (copiar el fichero),
  sin servicio que administrar ni monitorear.
- A favor: `WITH RECURSIVE` disponible, cubre el mismo requisito de CTE recursivas que PostgreSQL
  para el volumen y profundidad de saltos (2-3) que `PROJECT.yaml` anticipa.
- A favor: encaja bien con el volumen bajo de Fase 1 si el proyecto fuera solo una herramienta de
  ingesta y consulta batch, sin componente web concurrente.
- En contra: modelo de un solo escritor a la vez (bloqueo de base de datos completa en escritura,
  incluso en modo WAL con matices) entra en conflicto directo con el patrón ya comprometido en el
  ADR 0002: ingesta recurrente escribiendo mientras varios revisores humanos deciden sobre la cola
  de `005-review-panel` al mismo tiempo, y, más adelante, un dashboard público con lectores
  concurrentes sobre el mismo fichero.
- En contra: sin un sistema de ficheros compartido, un despliegue con el servidor web (panel,
  dashboard) y el proceso de ingesta como servicios separados (topología común incluso para un
  equipo pequeño, p. ej. una función programada aparte del servidor web) no puede acceder al mismo
  fichero SQLite de forma remota sin soluciones adicionales (réplica, sincronización) que
  reintroducen buena parte de la complejidad operativa que se quería evitar.
- En contra: aunque SQLite en modo WAL permite varios lectores concurrentes con un escritor, tunear
  eso correctamente para el patrón de este proyecto es trabajo adicional no trivial, comparado con
  la concurrencia nativa de un motor cliente-servidor.

## Decisión

**Opción 1: PostgreSQL.**

Gana sobre SQLite no por volumen de datos -a ese volumen, SQLite sería suficiente por sí solo-
sino porque el ADR 0002 ya comprometió a este proyecto con un patrón de acceso concurrente
multi-proceso (ingesta recurrente + panel de revisión humana +, después, dashboard público) que
choca directamente con el modelo de escritor único de SQLite. Rechazar PostgreSQL aquí obligaría a
reabrir el ADR 0002, no a sustituirlo por una alternativa equivalente. El coste operativo adicional
de administrar PostgreSQL se acepta porque el hosting gestionado económico lo reduce a un nivel
razonable para un equipo pequeño, y porque encaja con lo ya propuesto en `PROJECT.yaml`.

**Limitación reconocida**: no existe en este proyecto ningún benchmark real de carga o volumen que
confirme cuantitativamente esta elección; la justificación es de patrón de concurrencia
(cualitativa, derivada de las specs), no de medición. Si en la práctica el volumen y la
concurrencia reales resultan mucho menores de lo previsto, esta decisión se revisita con evidencia,
no se asume errónea por adelantado.

## Consecuencias

### Positivas

- El panel de revisión (`005`) puede usar transacciones y bloqueos de fila para el mecanismo de
  reclamo (`CL-005-01`) sin trabajar alrededor de limitaciones de escritor único.
- La ingesta recurrente y las decisiones humanas pueden ocurrir simultáneamente sin coordinación
  manual adicional.
- `raw_payload` como `JSONB` permite, si hace falta más adelante, indexar o consultar dentro del
  payload crudo sin cambiar de motor.
- Coincide con lo ya declarado en `PROJECT.yaml`, evitando una discrepancia entre el manifiesto del
  proyecto y esta decisión formal.

### Negativas

- El equipo debe operar (o contratar hosting gestionado para) un servicio de base de datos
  adicional, con backup, monitoreo básico y una herramienta de migraciones que aprender a usar con
  disciplina.
- Para desarrollo local, cada persona necesita una instancia de PostgreSQL (mitigable con
  contenedor de desarrollo, no diseñado en este ADR).
- Esta decisión no está respaldada por ningún benchmark real de este proyecto - es una inferencia
  razonada a partir de las specs, no una medición; queda como riesgo declarado.
- Si el volumen real termina siendo tan bajo que ni la concurrencia justifica el coste operativo,
  el equipo habrá pagado la complejidad de PostgreSQL sin necesitarla - reevaluable con datos
  reales tras los primeros meses de operación.

### Qué se vuelve difícil de revertir

El esquema relacional, las convenciones de `JSONB` para `raw_payload`, las consultas CTE
recursivas para el grafo de entidades, y cualquier mecanismo de bloqueo de fila para el panel de
revisión se escribirán contra la sintaxis y las garantías específicas de PostgreSQL. Migrar a
SQLite (o a otro motor) después de tener datos de producción exige reescribir consultas y
mecanismos de concurrencia, no solo cambiar una cadena de conexión.

## Enlaces

- `specs/pending-adrs.md`, fila 2.
- `PROJECT.yaml`, `stack.datastore: PostgreSQL (propuesto)`.
- `docs/sdd/constitution.md`, Artículo 19 - asume campos tipo clave foránea que encajan con un
  motor relacional.
- [ADR 0002](0002-forma-del-pipeline-ingesta.md) - decisión de la que este ADR depende
  directamente: fija que el almacén es compartido y concurrente, lo cual descarta SQLite para este
  patrón de uso.
- [ADR 0006](0006-persistencia-universo-contracting-entity.md) - depende de esta decisión para
  fijar dónde vive el universo de `ContractingEntity`.

---

> [!warning] Los ADR son inmutables.
> Si esta decisión cambia, no edites este archivo: crea uno nuevo con `supersedes` y pon
> este en `status: superseded`. El registro histórico es todo el valor de un ADR.
