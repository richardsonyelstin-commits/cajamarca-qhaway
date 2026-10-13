---
title: Spec 003 - mef-ingestion
spec: "003"
capability: mef-ingestion
status: draft
created: 2026-08-20
updated: 2026-08-20
consumes: [ContractingEntity]
produces: [BudgetExecutionRecord]
open_clarifications: 6
source: ai
generator: claude-sonnet-5
generated_at: 2026-08-20T00:00:00Z
confidence: low
verified: false
---

# Spec 003 - mef-ingestion

Ingiere ejecución presupuestal desde el Portal de Datos Abiertos del MEF, filtrada al universo de
`001-entity-mapping`, cruzada por entidad con `002-seace-ingestion`. Fundamentada en la
verificación técnica real (`docs/research/2026-08-20-verificacion-tecnica-fuentes.md`, §2), que
corrige una suposición del diseño de producto original: **Consulta Amigable** y el **Portal de
Datos Abiertos del MEF** no son la misma cosa técnica, y esta spec solo cubre lo segundo.

## Problema

El diseño de producto trataba "MEF Consulta Amigable / datos abiertos" como una sola fuente. La
verificación técnica encontró dos sistemas distintos:

1. **Consulta Amigable** (`apps5.mineco.gob.pe/transparencia/Navegador/`): una aplicación ASP.NET
   WebForms clásica, con `<frameset>` y postback de formulario - sin ninguna API confirmable, y
   sin indicio de que pueda tenerla.
2. **Portal de Datos Abiertos del MEF** (`datosabiertos.mef.gob.pe`): una SPA Angular que, según
   su propio código compilado, consume una API real en `api.datosabiertos.mef.gob.pe` con
   acciones tipo CKAN DataStore (`datastore_search`, `datastore_search_sql`, `dump`), confirmada
   viva (responde `409` con un error de SQL cuando se llama sin parámetros, no `404`).

Esta spec se especifica sobre el sistema (2), porque es el único con evidencia real de API. No se
sabe todavía si el Portal de Datos Abiertos republica el mismo dato que Consulta Amigable, un
subconjunto, o algo distinto - es la ambigüedad más importante que deja abierta.

## Usuarios e intención

| Usuario | Qué quiere | Cómo se le falla |
|---|---|---|
| `red-flags-engine` | `BudgetExecutionRecord` cruzables con `ProcurementRecord` por entidad y periodo | Datos sin la granularidad necesaria para el cruce |
| Analista de ONG (CU1) | Ejecución financiera real de una obra, no solo el monto adjudicado | Datos que no distinguen adjudicado de ejecutado |
| Auditor del proyecto | Saber contra qué dataset exacto (`resource_id`) se consultó | Un número sin procedencia verificable |

## Entradas

| Campo | Origen | Obligatorio |
|---|---|---|
| Universo de entidades | `001-entity-mapping` | sí |
| Host de API real | `https://api.datosabiertos.mef.gob.pe/DatosAbiertos/v1/` (confirmado 2026-08-20) | sí |
| `resource_id` del dataset de ejecución presupuestal | No confirmado - ver Ambigüedades abiertas | sí, y bloqueante |
| Esquema de columnas del dataset (nombres de campo reales) | No confirmado | sí, y bloqueante |

## Salidas

Un conjunto de `BudgetExecutionRecord` (contrato canónico, Artículo 19), uno por entidad y
periodo fiscal disponible en el dataset, con el registro crudo devuelto por la API en
`raw_payload`.

**Ubicación.** `[NECESITA ACLARACIÓN: depende del stack - ver specs/pending-adrs.md]`

## Reglas de negocio

**RN-003-01. Solo se consulta la API confirmada, nunca Consulta Amigable.**
Esta capacidad no automatiza `apps5.mineco.gob.pe` en ninguna forma (ni scraping de formularios
con postback): la evidencia técnica no sustenta que sea una fuente automatizable de forma
sostenible, y el diseño del proyecto prioriza fuentes con API estructurada sobre scraping frágil
(`docs/research/2026-08-20-diseno-cajamarca-qhaway-fase1.md`, §3.3).

**RN-003-02. El filtro geográfico, si existe, se aplica vía `datastore_search_sql`.**
La acción `datastore_search_sql` acepta consultas SQL contra la tabla del `resource_id`, lo que
en principio permite filtrar por entidad/departamento del lado del servidor si el esquema del
dataset trae esas columnas. Esta regla queda condicionada: si el esquema no expone un campo de
ubicación geográfica o de entidad identificable por RUC, el filtro se hace del lado del cliente,
igual que en `002-seace-ingestion`.
`[NECESITA ACLARACIÓN: columnas reales del dataset - ver Ambigüedades abiertas]`

**RN-003-03. `raw_payload` no se transforma.**
El registro devuelto por `datastore_search`/`datastore_search_sql` se persiste completo. La
extracción de campos del contrato `BudgetExecutionRecord` es la única lectura permitida en esta
etapa.

**RN-003-04. Cruce con `002-seace-ingestion` es por `entity_id`, no por texto de nombre.**
El cruce entre `BudgetExecutionRecord` y `ProcurementRecord` para que `004-red-flags-engine`
compare monto adjudicado contra monto ejecutado se hace exclusivamente por `entity_id` (RUC), y
opcionalmente por periodo/proyecto si el dataset lo permite - nunca por coincidencia aproximada
de nombre de entidad o de obra, que es frágil y no auditable.

**RN-003-05. `retrieved_at` y `source` son obligatorios en todo registro.**
`source` es siempre `"mef-datastore"`.

**RN-003-06. Fallo de la API no se sustituye por scraping de Consulta Amigable.**
Si la API del Portal de Datos Abiertos falla o no cubre lo que se necesita, la corrida lo declara
como hueco de cobertura - no se degrada silenciosamente a otra fuente con garantías técnicas
distintas (RN-003-01).

## Criterios de aceptación

**CA-003-01** · RN-003-01
Dado el conjunto de peticiones de esta capacidad, ninguna se dirige a `apps5.mineco.gob.pe`.

**CA-003-02** · RN-003-03
Dado un `BudgetExecutionRecord`, `raw_payload` es idéntico al registro devuelto por la API.

**CA-003-03** · RN-003-04
Dado un `BudgetExecutionRecord` y un `ProcurementRecord` de la misma entidad, ambos referencian el
mismo `entity_id`.

**CA-003-04** · RN-003-05
Dado cualquier `BudgetExecutionRecord`, `source == "mef-datastore"` y `retrieved_at` está
presente.

**CA-003-05** · RN-003-06
Dado un fallo de la API del MEF, la corrida registra el hueco de cobertura y no produce ningún
registro sustituto de otra fuente.

## Casos límite

**CL-003-01** - El dataset de ejecución presupuestal no tiene un campo explícito de RUC ni de
código CONSUCODE, solo nombre de entidad en texto libre.
`[NECESITA ACLARACIÓN: cómo se cruza con el universo de 001 si no hay identificador estructurado
- ver Ambigüedades abiertas]`

**CL-003-02** - El `resource_id` correcto cambia de un año a otro (dataset republicado por
periodo fiscal en vez de un solo dataset acumulado).
`[NECESITA ACLARACIÓN: si hay un resource_id por año o uno acumulado - depende de explorar el
Portal con navegador real]`

**CL-003-03** - La API responde con datos que no coinciden con lo que muestra Consulta Amigable
para la misma entidad y periodo (dado que son sistemas distintos, confirmado en la verificación).
Se documenta la discrepancia; no se asume que uno es más correcto que el otro sin evidencia
adicional. `[sin verificar]`

## Evidencia y manifiesto

Por cada `BudgetExecutionRecord`: `source`, `retrieved_at`, `raw_payload` íntegro y -una vez
resuelta AC-003-01- el `resource_id` exacto consultado, porque sin ese dato no se puede
reconstruir contra qué dataset se habló, y eso es tan importante para la explicabilidad como el
propio número.

## Fuera de alcance

- Automatizar Consulta Amigable en cualquier forma (RN-003-01).
- Calcular sobrecostos o cualquier indicador de riesgo: eso es `004-red-flags-engine`.
- Cubrir datasets del MEF que no sean de ejecución presupuestal (p. ej. inversión pública detallada
  por proyecto SNIP/Invierte.pe): fuera del alcance declarado por `PROJECT.yaml` para Fase 1,
  salvo que una spec futura lo incorpore explícitamente.

## Ambigüedades abiertas

**AC-003-01. `resource_id` del dataset de ejecución presupuestal.**
Es la ambigüedad bloqueante de esta spec. La API real (`api.datosabiertos.mef.gob.pe`) exige un
`resource_id` (UUID) por dataset, que el *frontend* Angular obtiene dinámicamente al navegar a
cada página de dataset - no se encontró embebido en el *bundle* JavaScript principal descargado
en esta ronda de verificación, porque probablemente se carga en un módulo distinto (lazy-loaded).
No lo cierro yo: requiere abrir el sitio con un navegador real (ejecutando JavaScript) y capturar
la petición de red al navegar al dataset de ejecución de gasto, o inspección manual humana del
Portal. Sin este dato, ningún campo de `RN-003-02` en adelante se puede verificar contra el
esquema real.
`[NECESITA ACLARACIÓN: resource_id real - requiere sesión de verificación con navegador]`

**AC-003-02. Esquema de columnas del dataset (nombres de campo reales).**
Depende de AC-003-01: sin el `resource_id` no se puede consultar el esquema
(`datastore_search` con `limit=1` revelaría las columnas). Los campos `budgeted_amount` y
`executed_amount` del contrato canónico (Artículo 19) son nombres provisionales, no confirmados
contra el dataset real.
`[NECESITA ACLARACIÓN: nombres de columna reales - depende de AC-003-01]`

**AC-003-03. Relación entre el Portal de Datos Abiertos y Consulta Amigable.**
No se sabe si son la misma información republicada en dos sistemas, o si divergen. Afecta
directamente si esta capacidad puede afirmar "cubre la ejecución presupuestal de Cajamarca" o
solo "cubre lo que el Portal de Datos Abiertos publica, que puede o no coincidir con Consulta
Amigable".
`[NECESITA ACLARACIÓN: relación entre ambos sistemas MEF - requiere comparación manual de una
muestra]`

**AC-003-04. Identificador de cruce cuando el dataset no trae RUC (CL-003-01).**
`[NECESITA ACLARACIÓN: mecanismo de cruce alternativo - depende del esquema real, AC-003-02]`

**AC-003-05. Un `resource_id` por año fiscal o uno acumulado (CL-003-02).**
`[NECESITA ACLARACIÓN: estructura de publicación del dataset - depende de exploración con
navegador]`

**AC-003-06. Si `datastore_search_sql` es de acceso público sin restricción adicional.**
La respuesta `409` observada no reveló ninguna exigencia de autenticación, pero tampoco se probó
una consulta SQL completa (solo la petición vacía que reveló el error de sintaxis). No se puede
descartar que exista un límite de tasa o una restricción no observada en una consulta real con
`resource_id` válido.
`[sin verificar]`

## Ambigüedades resueltas

**AC-003-07. Si Consulta Amigable es una fuente automatizable.**
**Decisión: no, en esta spec.** La evidencia técnica (frameset ASP.NET con postback,
confirmado 2026-08-20) no sustenta tratarla como una fuente con API. Automatizarla exigiría
scraping de formulario con manejo de estado de sesión - exactamente el patrón que el estado del
arte (`brain/70-inbox/2026-08-20-estado-del-arte-ia-anticorrupcion.md`) señala como frágil y que
el diseño de producto ya prioriza evitar. Si en el futuro se confirma que el Portal de Datos
Abiertos no cubre lo mismo que Consulta Amigable (AC-003-03), esta decisión se revisita con una
spec nueva o una enmienda registrada en el historial, no en silencio.

## Historial

| Fecha | Cambio | Estado |
|---|---|---|
| 2026-08-20 | Redacción inicial, corrige la suposición del diseño original de que Consulta Amigable y el Portal de Datos Abiertos son una sola fuente | `draft` |
