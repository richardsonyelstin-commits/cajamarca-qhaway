---
title: Spec 003 - mef-ingestion
spec: "003"
capability: mef-ingestion
status: draft
created: 2026-08-20
updated: 2026-10-15
consumes: [ContractingEntity]
produces: [BudgetExecutionRecord]
open_clarifications: 6
source: ai
generator: codex-gpt-6
generated_at: 2026-10-15T18:33:00Z
confidence: low
verified: false
---

# Spec 003 - mef-ingestion

Ingiere ejecución presupuestal desde las fuentes oficiales verificables del MEF, filtrada al
universo de `001-entity-mapping` y cruzada por entidad con `002-seace-ingestion`. El catálogo
CKAN/PNDA y la Consulta de Ejecución del Gasto Presupuestal (`id=504`) son fuentes primarias en
paridad; sus registros conservan su fuente y payload diferenciados.

## Problema

La verificación técnica identifica dos sistemas oficiales distintos, ahora tratados como fuentes
primarias en paridad:

1. **Consulta Amigable** (`apps5.mineco.gob.pe/transparencia/Mensual/` y `/Navegador/`): módulo
   ASP.NET WebForms con sesión, campos hidden y postbacks. Su enlace oficial de catálogo tiene
   `id=504`.
2. **Portal de Datos Abiertos del MEF** (`datosabiertos.mef.gob.pe`): portal con API CKAN DataStore
   (`datastore_search`, `datastore_search_sql`, `dump`) y recursos anuales publicados.

Los valores conservan fuente, fecha y granularidad propias. No se combinan como si ambas
publicaciones tuvieran el mismo esquema o corte.

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

Un `BudgetExecutionRecord` por pliego y ejercicio para los 14 pliegos Cajamarca cuando Consulta
Amigable publique la fila, y registros CKAN según la granularidad de su dataset. La fila y
procedencia de cada fuente se conservan en `raw_payload`.

**Ubicación.** `[NECESITA ACLARACIÓN: depende del stack - ver specs/pending-adrs.md]`

## Reglas de negocio

**RN-003-07. Presupuesto institucional multidimensional.**
Se navega exclusivamente por ¿Quién gasta?, Pliego 445 o SEC_EJEC provinciales verificados.
Cada entidad tiene un maestro ActProy por ejercicio 2024, 2025 y 2026.
Se conservan PIA, modificación, PIM, certificación, compromiso anual, atención mensual,
devengado, girado, avance y fecha oficial del corte diario o mensual.
Actividad, Proyecto, fuentes y rubros son particiones del maestro, nunca totales adicionales.
El corte mensual se compara por separado y no se suma al diario.

**RN-003-01. Solo se consultan fuentes oficiales verificadas del MEF.**
La fuente Consulta Amigable es el módulo `id=504` bajo
`apps5.mineco.gob.pe/transparencia/Mensual/` y `/Navegador/`. Su formulario ASP.NET se navega
con una sesión persistente, cookies y valores hidden frescos por respuesta. El catálogo CKAN/PNDA
se mantiene como fuente primaria paritaria; no se mezclan silenciosamente registros entre fuentes.

**RN-003-02. El filtro geográfico, si existe, se aplica vía `datastore_search_sql`.**
La acción `datastore_search_sql` acepta consultas SQL contra la tabla del `resource_id`, lo que
en principio permite filtrar por entidad/departamento del lado del servidor si el esquema del
dataset trae esas columnas. Esta regla queda condicionada: si el esquema no expone un campo de
ubicación geográfica o de entidad identificable por RUC, el filtro se hace del lado del cliente,
igual que en `002-seace-ingestion`.
`[NECESITA ACLARACIÓN: columnas reales del dataset - ver Ambigüedades abiertas]`

**RN-003-03. `raw_payload` conserva la fila fuente completa.**
Para Consulta Amigable se conservan las columnas originales `codigo_entidad`, `nombre_entidad`,
`PIA`, `PIM`, `CERTIFICACION`, `COMPROMISO_ANUAL`, `ATENCION_COMPROMISO_MENSUAL`, `DEVENGADO`,
`GIRADO`, `AVANCE_PCT`, `ANO_EJE`, `FECHA_CORTE_OFICIAL`, `FUENTE_URL` y `ruta_navegacion`.
Para CKAN/PNDA se conserva el objeto original devuelto por la fuente. Los campos canónicos se
derivan aparte, sin mutar el payload.

**RN-003-04. Cruce con `002-seace-ingestion` es por `entity_id`, no por texto de nombre.**
El cruce entre `BudgetExecutionRecord` y `ProcurementRecord` para que `004-red-flags-engine`
compare monto adjudicado contra monto ejecutado exige `entity_id`, CUI verificado y periodo
comparable; el devengado institucional no se atribuye a un contrato - nunca por coincidencia aproximada
de nombre de entidad o de obra, que es frágil y no auditable.

**RN-003-05. `retrieved_at` y `source` son obligatorios en todo registro.**
`source` identifica exactamente `"mef-datastore"` o `"mef-consulta-amigable"`.

**RN-003-06. Las fallas preservan procedencia y cobertura.**
Una falla en una fuente se registra como hueco para esa fuente; la respuesta de la otra fuente no
se presenta como sustituto ni como cobertura equivalente.

## Criterios de aceptación

**CA-003-08** · RN-003-07
Hay 42 maestros: 14 entidades por tres ejercicios, sin filas distritales.
PIM de ActProy coincide con Actividad más Proyecto con tolerancia máxima de un sol.
Modificación es PIM menos PIA y el avance es devengado/PIM redondeado a un decimal.
Los importes son finitos y cumplen el orden presupuestal sin ajustar la evidencia original.

**CA-003-01** · RN-003-01
Dada una extracción de Consulta Amigable, se conserva la sesión ASP.NET y cada postback incluye
los campos hidden vigentes y la fila seleccionada.

**CA-003-02** · RN-003-03
Dado un `BudgetExecutionRecord`, `raw_payload` conserva las columnas fuente y metadatos de ruta
sin mutaciones posteriores.

**CA-003-03** · RN-003-04
Dado un `BudgetExecutionRecord` y un `ProcurementRecord` de la misma entidad, ambos referencian el
mismo `entity_id`.

**CA-003-04** · RN-003-05
Dado cualquier `BudgetExecutionRecord`, `source` identifica la fuente de origen y `retrieved_at`
está presente.

**CA-003-05** · RN-003-06
Dado un fallo de la API del MEF, la corrida registra el hueco de cobertura y no produce ningún
registro sustituto de otra fuente.

**CA-003-06** · RN-003-01 / RN-003-04
Dada una extracción completa de Consulta Amigable para 2024, 2025 o 2026, hay exactamente 14
registros, uno por el GORE y cada Municipalidad Provincial del universo canónico.

**CA-003-07** · RN-003-03
Dado un registro de Consulta Amigable, el payload conserva las ocho columnas presupuestales,
el ejercicio, la fecha de corte, la URL fuente y la ruta de navegación.

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

Por cada `BudgetExecutionRecord`: `source`, `retrieved_at` y `raw_payload` íntegro. CKAN registra
el `resource_id`; Consulta Amigable registra `FUENTE_URL` y `ruta_navegacion`.

## Fuera de alcance

- Calcular sobrecostos o cualquier indicador de riesgo: eso es `004-red-flags-engine`.
- Inferir avance de una obra desde el presupuesto institucional agregado.
  La v2.0 permite Invierte.pe/SSI como evidencia complementaria con CUI verificado.

## Ambigüedades abiertas

**AC-003-01. `resource_id` del dataset de ejecución presupuestal.**
Es una brecha del adaptador CKAN; no bloquea Consulta Amigable bajo la v2.0.
La API (`api.datosabiertos.mef.gob.pe`) exige un
`resource_id` (UUID) por dataset, que el *frontend* Angular obtiene dinámicamente al navegar a
cada página de dataset - no se encontró embebido en el *bundle* JavaScript principal descargado
en esta ronda de verificación, porque probablemente se carga en un módulo distinto (lazy-loaded).
No lo cierro yo: requiere abrir el sitio con un navegador real (ejecutando JavaScript) y capturar
la petición de red al navegar al dataset de ejecución de gasto, o inspección manual humana del
Portal para verificar este adaptador contra su esquema real.
`[NECESITA ACLARACIÓN: resource_id real - requiere sesión de verificación con navegador]`

**AC-003-02. Esquema de columnas del dataset (nombres de campo reales).**
Depende de AC-003-01: sin el `resource_id` no se puede consultar el esquema
(`datastore_search` con `limit=1` revelaría las columnas).
Para Consulta Amigable, PIM y Devengado ya tienen correspondencia canónica explícita.
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
**Decisión: sí, con límites verificables.** ADR 0011 acredita el módulo `id=504` como fuente
primaria paritaria. El sondeo GET del 2026-10-13 recibió HTTP 200; el formulario expuso
`aspnetForm`, estado WebForms y filas seleccionables en `pg_bd`. El postback en la misma sesión
devolvió los niveles de gobierno. No se considera una API: los campos hidden se renuevan en cada
respuesta y el fallo de DOM/postback queda visible como brecha de cobertura.

**AC-003-08. Pertenencia municipal provincial.**
Cada fila municipal se acepta solo cuando `SEC_EJEC` coincide con el universo canónico del
proyecto, el nombre fuente indica Municipalidad Provincial y la provincia coincide. Los códigos
enumerados en la orden v2.0 no coinciden todos con el padrón MEF validado; no sustituyen el mapa
`MUNICIPAL_EXECUTOR_PROVINCES` del proyecto.

## Historial

Enmienda humana 2026-10-15: momentos, cortes y particiones bajo Constitución v2.0.

| Fecha | Cambio | Estado |
|---|---|---|
| 2026-08-20 | Redacción inicial, corrige la suposición del diseño original de que Consulta Amigable y el Portal de Datos Abiertos son una sola fuente | `draft` |
| 2026-10-13 | Enmienda ADR 0011: integra Consulta Amigable como fuente primaria paritaria con extracción stateful y payload de fila íntegro | `draft` |
