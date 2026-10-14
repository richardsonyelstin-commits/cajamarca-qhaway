---
title: Spec 004 - red-flags-engine
spec: "004"
capability: red-flags-engine
status: draft
created: 2026-08-20
updated: 2026-10-14
consumes: [ProcurementRecord, BudgetExecutionRecord]
produces: [RedFlag]
open_clarifications: 5
source: ai
generator: codex-gpt-6
generated_at: 2026-10-14T04:02:22Z
confidence: medium
verified: false
---

# Spec 004 - red-flags-engine

Aplica un subconjunto priorizado de indicadores de riesgo tipo Cardinal/OCP sobre los datos de
`002-seace-ingestion` y `003-mef-ingestion`, y produce candidatos de `RedFlag` con fórmula y
umbral explícitos. Nunca produce un score compuesto de caja negra, y nunca puntúa a una persona
(Artículo 16 de la constitución).

## Problema

El estado del arte (`brain/70-inbox/2026-08-20-estado-del-arte-ia-anticorrupcion.md`, §2.1)
documenta 73 indicadores de riesgo publicados por Open Contracting Partnership (Cardinal), pero
implementar los 73 desde el inicio sobre datos de una sola región pequeña produce dos problemas:
indicadores calibrados para volumen nacional que no tienen significancia estadística sobre
decenas de entidades (el propio diseño de producto lo señala en su sección 5), y una superficie
tan grande que ningún panel humano puede revisarla con cuidado. El problema de esta capacidad no
es "cuántos indicadores implementar" sino "cuáles son defendibles con el volumen real de
Cajamarca y explicables a un usuario no técnico" (CU3, CU4 del diseño de producto).

## Usuarios e intención

| Usuario | Qué quiere | Cómo se le falla |
|---|---|---|
| `review-panel` | Candidatos con fórmula, umbral y evidencia listos para decidir | Un score sin desglose que obligue a re-investigar desde cero |
| Analista de ONG (CU1) | Filtrar por indicador concreto (p. ej. "proveedor único") | Una etiqueta genérica de "riesgo alto" sin decir cuál |
| Periodista (CU3) | Un indicador con fórmula pública citable | Una salida que no resiste la pregunta "¿por qué dice esto?" |
| Auditor del proyecto | Trazabilidad completa hasta el dato de origen | Un `RedFlag` sin referencia a los `ProcurementRecord` que lo sustentan |

## Entradas

| Campo | Origen | Obligatorio |
|---|---|---|
| `ProcurementRecord` | `002-seace-ingestion` | sí |
| `BudgetExecutionRecord` | `003-mef-ingestion` | no - algunos indicadores no lo requieren |
| Catálogo de indicadores activos, con fórmula y umbral | Ver Reglas de negocio | sí |

## Salidas

Un conjunto de `RedFlag` (contrato canónico, Artículo 19), cada uno trazable a uno o más
`ProcurementRecord`/`BudgetExecutionRecord` concretos, listo para que `005-review-panel` decida.

**Ubicación.** `[NECESITA ACLARACIÓN: depende del stack - ver specs/pending-adrs.md]`

## Reglas de negocio

**RN-004-01. El catálogo de indicadores de Fase 1 tiene entre 5 y 10 entradas, elegidas por
relevancia documentada a Cajamarca, no por copiar los 73 de Cardinal.**
Priorización basada en el diseño de producto (§3.4) y en los patrones ya señalados con evidencia
para Cajamarca (obras públicas, canon minero): proveedor único, plazos de licitación anormalmente
cortos, ejecución financiera fuera de rango del monto adjudicado, proveedor de reciente creación.
El catálogo exacto (los 5-10 indicadores con su fórmula final) es una ambigüedad abierta de esta
spec - ver más abajo - porque calibrar el umbral de cada uno exige ver datos reales de
`002`/`003`, que todavía no existen.

**RN-004-02. Cada indicador declara su fórmula en lenguaje simple y su umbral, de forma pública
y estable.**
Un indicador sin fórmula legible por un no técnico (CU4) o sin umbral numérico explícito no es un
indicador válido de esta capacidad - es la traducción operativa del principio "nunca un score
compuesto de caja negra" del diseño de producto (§3.4).

**RN-004-03. Ningún indicador combina múltiples señales en un solo número compuesto.**
Cada `RedFlag` corresponde a un único `indicator_code`. Si dos indicadores se activan sobre el
mismo `ProcurementRecord`, se producen dos `RedFlag` distintos - nunca se suman en un score
único. La agrupación de varios `RedFlag` en una sola `Alert` ocurre en `005-review-panel`, por
decisión humana, no aquí.

**RN-004-04. Ningún indicador tiene como unidad de análisis una persona identificada por
nombre.**
Todo indicador se calcula sobre `ProcurementRecord`/`BudgetExecutionRecord` (procesos y
contratos) o sobre `entity_id` (una entidad contratante, no una persona). Un indicador que
naturalmente produciría "funcionario con más contratos de riesgo" o similar no se implementa: se
marca `[NECESITA ACLARACIÓN: tienta a puntuar personas]` y se escala (Artículo 16 de la
constitución) - esta spec no resuelve esa tentación por su cuenta, ni siquiera reformulándola.

**RN-004-05. Cada `RedFlag` referencia el dato exacto que lo disparó, no un resumen.**
`observed_value` es el valor real medido (p. ej. "1 postor", no "postores insuficientes");
`threshold_value` es el umbral exacto cruzado; `procurement_ids`/`execution_record_ids` apuntan a los
registros concretos. Esto es lo que permite que `review-panel` (y después, cualquier `Alert`)
cumpla el Artículo 15 de la constitución.

**RN-004-06. Indicadores basados en umbrales absolutos, no en comparación estadística contra una
muestra grande.**
El diseño de producto (§5) señala que el menor volumen de una sola región reduce la significancia
estadística de comparaciones tipo "outlier respecto a la media nacional". El catálogo de Fase 1
prioriza reglas con umbral fijo y justificable en lenguaje simple (p. ej. "un solo postor" es
verificable sin estadística) sobre reglas que dependen de una distribución muestral.

**RN-004-07. Un `RedFlag` se recalcula, no se acumula, si los datos de origen cambian.**
Si un `ProcurementRecord` se actualiza (ver AC-002-03 de `002-seace-ingestion`, todavía abierta),
el `RedFlag` correspondiente se recalcula contra el dato más reciente. No queda un `RedFlag`
obsoleto compitiendo con uno nuevo sobre el mismo proceso sin que quede claro cuál es vigente.
`[NECESITA ACLARACIÓN: mecanismo exacto de recálculo, depende de cómo 002 resuelva el
versionado]`

**RN-004-08. `red-flags-engine` no publica nada.**
Produce candidatos exclusivamente. El paso de `RedFlag` a `Alert` ocurre única y exclusivamente
en `005-review-panel` (Artículo 14 de la constitución) - esta regla es la aplicación directa de
ese artículo a esta capacidad concreta, y se repite aquí para que no se pueda alegar que
"la spec de red-flags-engine no lo prohibía explícitamente".

**RN-004-09. `mef-underspending` evalua ejercicios cerrados y cortes oficiales vencidos
con PIM mayor que cero.**
Para entidad, categoria presupuestal y ejercicio fiscal, calcula `(PIM - devengado) / PIM`; se
activa cuando el resultado es al menos `0.50`. Los registros con PIM cero no generan division ni
señal. Un ejercicio abierto solo se evalua si todos sus registros provienen de Consulta Amigable,
conservan la misma `FECHA_CORTE_OFICIAL` ISO 8601, y el corte es anterior a la fecha de evaluacion
y pertenece al ejercicio fiscal del registro. El corte permanece en `raw_payload`.
La regla queda modificada parcialmente por ADR 0012; ADR 0010 conserva vigencia para sus demas
decisiones.

**RN-004-10. `recurrent-direct-award` cuenta procesos de modalidad directa por entidad y RUC.**
Se activa con tres o mas adjudicaciones de modalidad confirmada al mismo RUC en una ventana
movil inclusiva de 365 dias. Excluye registros sin RUC, modalidad confirmada o fecha explicita
de adjudicacion. La unidad nunca es una persona natural. La regla queda aprobada por ADR 0010.

**RN-004-11. `hhi-concentration` calcula el indice por entidad y ejercicio fiscal en escala
0-10,000.**
La formula es `sum((monto_adjudicado_RUC / monto_total) ** 2) * 10000`; se activa desde 2,500.
Exige montos adjudicados positivos, fecha de adjudicacion y RUC en todas las adjudicaciones del
universo anual. Si falta un RUC, no se produce una señal que pudiera sobreestimar concentracion.
La regla queda aprobada por ADR 0010.

## Criterios de aceptación

**CA-004-01** · RN-004-01
Dado el catálogo de indicadores activos, tiene entre 5 y 10 entradas, ni más ni menos.

**CA-004-02** · RN-004-02
Dado cualquier indicador del catálogo, tiene un campo de fórmula en lenguaje simple no vacío y un
umbral numérico o categórico explícito.

**CA-004-03** · RN-004-03
Dado un `ProcurementRecord` que activa dos indicadores distintos, se producen dos `RedFlag`
distintos, cada uno con su propio `indicator_code`.

**CA-004-04** · RN-004-04
Dado cualquier indicador del catálogo, su unidad de análisis (`procurement_ids` o
`execution_record_ids`) nunca es una lista de nombres de persona.

**CA-004-05** · RN-004-05
Dado cualquier `RedFlag`, `formula_description`, `observed_value`, `threshold_value`, `evidence_source` y
`retrieved_at` están presentes y no son valores por defecto o placeholder.

**CA-004-06** · RN-004-08
Dado el conjunto completo de salidas de esta capacidad, ninguna tiene `status == "published"` -
ese campo pertenece exclusivamente a `Alert`, que esta capacidad no produce.

**CA-004-07** · RN-004-09
El motor calcula baja ejecucion con PIM positivo, agrupa partidas de igual
entidad/categoria/ejercicio y deja sin señal ratios inferiores a 0.50. Para ejercicio cerrado,
usa sus registros MEF. En el ejercicio abierto, solo evalua registros de Consulta Amigable con
una misma `FECHA_CORTE_OFICIAL` vencida, ISO 8601 y perteneciente al ejercicio.

**CA-004-08** · RN-004-10
El motor solo agrupa adjudicaciones directas con fecha explicita y RUC, y activa al llegar a 3
procesos dentro de 365 dias.

**CA-004-09** · RN-004-11
El motor usa escala HHI 0-10,000, activa desde 2,500 y omite universos con total cero o RUC
faltante.

## Casos límite

**CL-004-01** - Un `ProcurementRecord` sin `BudgetExecutionRecord` cruzado todavía (la ingesta de
`003` no ha llegado a esa entidad/periodo).
Los indicadores que dependen solo de `002` se calculan igual; los que necesitan el cruce con `003`
simplemente no se evalúan para ese registro, y no se genera un `RedFlag` falso por dato faltante.

**CL-004-02** - Un indicador de "proveedor de reciente creación" sin fecha de constitución de la
empresa disponible en ningún dato ingerido.
`[NECESITA ACLARACIÓN: fuente del dato de antigüedad del proveedor - no está en el alcance
confirmado de 002 ni 003, podría requerir una fuente adicional no contemplada en Fase 1]`

**CL-004-03** - Dos `ProcurementRecord` del mismo `ocid` en distintas versiones (ver AC-002-03 de
`002`, abierta), ambos activando el mismo indicador con valores distintos.
No se genera un `RedFlag` por cada versión: se recalcula sobre la versión vigente (RN-004-07),
pero el mecanismo exacto queda bloqueado por la misma ambigüedad de `002`.

## Evidencia y manifiesto

Cada `RedFlag` es en sí mismo el registro de evidencia mínimo: no hace falta un ledger aparte
mientras el propio contrato canónico obligue a `evidence_source` y `retrieved_at`.
`[NECESITA ACLARACIÓN: si además se necesita un registro de auditoría de "qué corrida del motor
generó este RedFlag y cuándo" - depende de si el proyecto adopta un concepto de corrida, ver
specs/pending-adrs.md]`

## Fuera de alcance

- Publicar ninguna `Alert` (RN-004-08): eso es `005-review-panel`.
- Cualquier indicador cuya unidad de análisis sea una persona (RN-004-04, Artículo 16).
- Cualquier score compuesto o ranking agregado (RN-004-03).
- Análisis de grafo proveedor-funcionario-empresa vía DJI: fuera de alcance hasta que
  `008-dji-ingestion` exista, y esa capacidad depende de evaluación legal previa (Artículo 17).
- Reutilizar o adaptar directamente la librería Cardinal de OCP: esta spec no decide esa cuestión
  de implementación (ver `specs/pending-adrs.md`).

## Ambigüedades abiertas

**AC-004-01. Catálogo final de 5-10 indicadores, con fórmula y umbral definitivos.**
No lo cierro yo: calibrar un umbral (p. ej. "cuántos días es un plazo de licitación anormalmente
corto para Cajamarca") exige ver datos reales de `002`, que todavía no existen porque esa
capacidad sigue bloqueada por sus propias ambigüedades de paginación y frecuencia. Proponer un
número aquí sin esa evidencia produciría umbrales que o bien no activan nunca, o activan
constantemente - en ambos casos, inútiles y potencialmente engañosos.
`[NECESITA ACLARACIÓN: catálogo final calibrado contra datos reales de 002/003]`

**AC-004-02. Si se reutiliza la librería Cardinal (OCP) o se implementa el catálogo desde cero.**
Es una decisión de arquitectura, no de negocio, y por tanto pertenece a `specs/pending-adrs.md`,
no a esta spec - pero la spec sí necesita declarar que la decisión está pendiente porque afecta
directamente cómo se formula RN-004-01 en producción.
`[NECESITA ACLARACIÓN: ver specs/pending-adrs.md, fila "motor de red flags"]`

**AC-004-03. Mecanismo de recálculo ante actualización de datos de origen (RN-004-07).**
Depende de AC-002-03 (`002-seace-ingestion`), sin resolver.
`[NECESITA ACLARACIÓN: bloqueado por 002]`

**AC-004-04. Fuente del dato de antigüedad del proveedor (CL-004-02).**
`[NECESITA ACLARACIÓN: si existe una fuente confirmada dentro del alcance de Fase 1, o si ese
indicador concreto se descarta del catálogo final]`

**AC-004-05. Frecuencia de ejecución del motor.**
¿Corre sobre cada nuevo `ProcurementRecord` ingerido, o por lote periódico? Depende de la
frecuencia de `002`/`003`, ambas sin resolver.
`[NECESITA ACLARACIÓN: bloqueado por 002 y 003]`

## Ambigüedades resueltas

**AC-004-06. Si un indicador puede depender de una comparación entre `awarded_amount` y
`executed_amount`.**
**Decisión: sí, es uno de los indicadores centrales del catálogo (RN-004-01), pero exige el
campo `executed_amount` de `ProcurementRecord`, que a su vez depende del cruce con
`BudgetExecutionRecord` de `003-mef-ingestion`.** No se cierra el umbral exacto (AC-004-01), pero
sí se fija que este tipo de indicador es parte del catálogo y no una idea descartada, porque es
el indicador con más evidencia documentada de relevancia para Cajamarca (CU1 del diseño de
producto usa exactamente este ejemplo).

## Historial

| Fecha | Cambio | Estado |
|---|---|---|
| 2026-08-20 | Redacción inicial | `draft` |
