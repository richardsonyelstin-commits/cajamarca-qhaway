---
title: Spec 002 - seace-ingestion
spec: "002"
capability: seace-ingestion
status: draft
created: 2026-08-20
updated: 2026-10-16
consumes: [ContractingEntity]
produces: [ProcurementRecord]
open_clarifications: 5
source: ai
generator: codex
generated_at: 2026-10-16T07:18:34.441452+00:00
confidence: medium
verified: false
---

# Spec 002 - seace-ingestion

## Estado contrastado (2026-10-16)

La implementación local correspondiente está en [código](../../src/cajamarca_qhaway/capabilities/seace_ingestion/).
El estado draft se conserva: tener implementación no constituye aprobación documental.
Las reglas siguientes son requisitos y diseño; no certifican cobertura o servicios remotos.

Ingiere contrataciones públicas desde la API OCDS del Portal de Contrataciones Abiertas (OECE,
ex-OSCE/SEACE), filtradas al universo de `001-entity-mapping`, con el payload original íntegro y
metadatos de fuente y fecha. Fundamentada en lo verificado realmente en
`docs/research/2026-08-20-verificacion-tecnica-fuentes.md` §1 - no en la suposición original del
diseño de producto de que existiría un filtro de región del lado del servidor.

## Problema

La verificación técnica (2026-08-20) confirmó que la API real
(`GET https://contratacionesabiertas.oece.gob.pe/api/v1/releases`) es un **feed rotativo de las
últimas publicaciones a nivel nacional**, sin parámetro de filtro geográfico server-side que
tenga efecto observable (se probaron cinco nombres de parámetro distintos, ninguno filtró). El
filtro real por Cajamarca solo es posible **después de descargar**, comparando
`parties[].address.department` contra `"CAJAMARCA"`.

Esto cambia el problema de diseño: no es "pedir solo lo de Cajamarca", es "descargar el feed
completo (o tanto como el feed exponga) y filtrar del lado del cliente, sin perder de vista qué
se descartó ni fingir que se consultó algo más amplio de lo que realmente se consultó". Un
`/downloads` en bloque documentado por OECE no resultó alcanzable en la verificación (redirige a
una IP privada no enrutable), así que no se puede asumir como alternativa sin volver a probarlo.

## Usuarios e intención

| Usuario | Qué quiere | Cómo se le falla |
|---|---|---|
| `red-flags-engine` | `ProcurementRecord` completos y con procedencia clara | Registros truncados o sin `raw_payload` |
| `review-panel` | Poder verificar el dato exacto contra la fuente original | Un dato ya normalizado sin el payload crudo |
| Analista de ONG (CU1) | Cobertura declarada, no cobertura fingida | Que la plataforma calle qué parte del feed no llegó a ver |
| Auditor del proyecto | Saber con qué frecuencia y contra qué endpoint exacto se ingirió | Ausencia de `retrieved_at`/`source` por registro |

## Entradas

| Campo | Origen | Obligatorio |
|---|---|---|
| Universo de entidades | `001-entity-mapping` (`ContractingEntity`, `ruc`/`consucode_id`) | sí |
| Endpoint de la API | `https://contratacionesabiertas.oece.gob.pe/api/v1/releases`, confirmado 2026-08-20 | sí |
| Ventana temporal de cosecha | No confirmada - ver Ambigüedades abiertas | sí, pero sin valor fijado |

No hay clave de API: el endpoint verificado responde sin autenticación.

## Salidas

Un conjunto de `ProcurementRecord` (contrato canónico, Artículo 19), uno por `release` OCDS cuyo
`party` con rol `buyer`/`procuringEntity` tenga `address.department == "CAJAMARCA"` **y** cuyo
RUC o `consucode_id` esté en el universo de `001-entity-mapping`.

Cada registro conserva el `release` OCDS completo en `raw_payload`, sin transformar más allá de
lo necesario para extraer `entity_id`, `ocid` y los campos declarados en el contrato canónico.

**Ubicación.** `[NECESITA ACLARACIÓN: se resuelve en plan.md una vez fijado el stack de
persistencia - ver specs/pending-adrs.md]`

## Reglas de negocio

**RN-002-09. Fuentes oficiales complementarias con evidencia independiente.**
Se admiten OCDS, Pentaho OECE y buscador público SEACE bajo Constitución v2.0.
Cada fila conserva payload, URL, fuente y extracción UTC.
El enlace exige comprador canónico e identificador oficial; no se fabrican OCID ni CUI.
Una denegación HTTP, CAPTCHA o sesión expirada registra brecha de esa fuente.
Las reglas OCDS siguientes se aplican al adaptador OCDS, sin impedir los complementarios.

**RN-002-01. El filtro geográfico es siempre del lado del cliente.**
Ningún parámetro de la petición HTTP se asume como filtro efectivo: la petición al endpoint
verificado no lleva parámetros de filtro (se confirmó que no tienen efecto). Todo el filtrado
ocurre después de recibir la respuesta, comparando contra el universo de `001`.

**RN-002-02. Doble criterio de pertenencia: departamento y universo verificado.**
Un `release` entra al corpus de Cajamarca solo si (a) algún `party` con rol
`buyer`/`procuringEntity` tiene `address.department == "CAJAMARCA"`, **y** (b) su RUC o
`consucode_id` coincide con una `ContractingEntity` activa del universo de `001`. El criterio
(a) solo no basta: un `department` mal declarado en origen (dato sucio) podría colar una entidad
fuera del universo verificado; el criterio (b) solo tampoco basta si el universo de `001` aún no
cubre alguna distrital relevante - la discrepancia entre ambos criterios se registra, no se
descarta en silencio.

**RN-002-03. `raw_payload` no se transforma.**
El `release` OCDS se persiste completo, tal como llegó. La única lectura permitida de su
contenido en esta etapa es la extracción de los campos del contrato `ProcurementRecord`; cualquier
normalización adicional (deduplicar por proveedor, calcular sobrecostos) pertenece a
`004-red-flags-engine`.

**RN-002-04. Identidad y no duplicación.**
Un `ProcurementRecord` se identifica por `ocid`. Reingerir el mismo `release` no produce un
registro duplicado; si el `release` trae una versión más nueva del mismo `ocid` (OCDS es un
formato de eventos acumulativos), se conserva la más reciente y se declara que hubo actualización,
nunca se sobrescribe en silencio sin dejar rastro de que existía una versión anterior.
`[NECESITA ACLARACIÓN: cómo se versiona un release actualizado - ver Ambigüedades abiertas]`

**RN-002-05. `retrieved_at` y `source` son obligatorios en todo registro.**
`source` es siempre `"seace-ocds"`; `retrieved_at` es el instante exacto de la petición HTTP que
trajo ese `release`, no la fecha de publicación de OCDS (`publishedDate`), que son cosas
distintas.

**RN-002-06. Un feed rotativo exige declarar la cobertura real, no la teórica.**
Como el único endpoint confirmado es un feed de las últimas publicaciones sin paginación
verificada, esta capacidad **no puede prometer** haber visto el histórico completo de
contrataciones de Cajamarca desde una fecha dada. Cada corrida de ingesta declara explícitamente
qué ventana de tiempo cubrió realmente (la del feed en el momento de la consulta), no una ventana
deseada. Prometer cobertura histórica sin haberla verificado es el mismo error que
`source-federation` evita en `scientific-literature-pipeline` con la validación de cuerpo: un
"200 OK" no prueba cobertura.

**RN-002-07. Fallo del endpoint no se sustituye en silencio.**
Si `GET /api/v1/releases` no responde con un `release package` válido (cuerpo JSON con
`releases[]`), la corrida de esa ejecución falla y se registra - no se intenta adivinar contra
`/downloads` u otro endpoint no confirmado sin que sea una decisión explícita de la ejecución.

**RN-002-08. Nomenclatura del campo `region` de OCDS.**
En el payload real, `parties[].address.region` contiene la **provincia**, no el departamento
(confirmado en la verificación técnica: `"CELENDIN"` para una entidad de esa provincia). Ningún
código ni documento de este proyecto usa "región" para referirse al campo OCDS `region` sin
aclarar que es la provincia - evita el error de leer `region` como sinónimo de "Cajamarca".

## Criterios de aceptación

**CA-002-09** · RN-002-09
Reingerir evidencia de dos fuentes conserva los IDs y el payload original OCDS.
Un desafío JSF produce brecha explícita y cero filas sintéticas.
Un CUI solo se acepta desde campo explícito o etiqueta inequívoca de siete dígitos.

**CA-002-01** · RN-002-01
Dada cualquier petición de esta capacidad al endpoint, no lleva parámetros de filtro geográfico
en la URL.

**CA-002-02** · RN-002-02
Dado un `release` con `department == "CAJAMARCA"` pero cuyo RUC no está en el universo de `001`,
no se produce `ProcurementRecord`, y la discrepancia queda registrada.

**CA-002-03** · RN-002-03
Dado un `ProcurementRecord`, `raw_payload` es idéntico byte a byte al `release` recibido.

**CA-002-04** · RN-002-04
Dado el mismo `ocid` ingerido dos veces sin cambios, no se crea un segundo `ProcurementRecord`.

**CA-002-05** · RN-002-05
Dado cualquier `ProcurementRecord`, `source == "seace-ocds"` y `retrieved_at` es distinto de
`publishedDate` del `release` de origen.

**CA-002-06** · RN-002-06
Dada una corrida de ingesta completada, el informe declara la ventana de tiempo real cubierta
(no una ventana deseada o asumida).

**CA-002-07** · RN-002-07
Dado un cuerpo de respuesta que no sea un `release package` válido, la corrida de esa ejecución
falla explícitamente y no produce `ProcurementRecord` parciales sin declararlo.

## Casos límite

**CL-002-01** - Un `release` sin ningún `party` con rol `buyer`/`procuringEntity`.
No entra al corpus; se registra como descartado por falta de comprador identificable.

**CL-002-02** - Un `release` con dos `parties` con rol `buyer` de departamentos distintos
(consorcio interregional, poco común pero posible).
`[NECESITA ACLARACIÓN: si basta con que uno sea de Cajamarca o deben serlo todos]`

**CL-002-03** - El feed devuelve menos de 20 `releases` en una consulta (el tamaño observado en
la verificación fue de ~20 por respuesta, sin parámetro de tamaño confirmado).
Se acepta lo que el feed entregue; no se asume un tamaño de página fijo.

**CL-002-04** - Una entidad de Cajamarca no aparece en ninguna consulta durante semanas.
No es necesariamente un fallo de la ingesta: puede ser que esa entidad no publicó nada en ese
periodo. La corrida no lo trata como error, pero el hueco de cobertura se puede hacer visible en
el informe si se detecta un patrón (competencia de una capacidad de monitoreo, no de esta spec).

**CL-002-05** - `parties[].address.department` viene vacío o con un valor no estandarizado
(p. ej. `"Cajamarca"` en minúsculas, o con tilde distinta).
La comparación contra `"CAJAMARCA"` se hace normalizando mayúsculas/acentos, no con
correspondencia exacta byte a byte - de lo contrario un dato sucio de origen excluiría entidades
legítimas en silencio.

## Evidencia y manifiesto

Por cada `ProcurementRecord`, el registro de procedencia incluye: `source`, `retrieved_at`, y el
`raw_payload` íntegro, que juntos permiten reconstruir exactamente qué se vio y cuándo - es la
base de la capa de explicabilidad exigida por el Artículo 15 de la constitución para cualquier
`RedFlag` que después se derive de este dato.
`[NECESITA ACLARACIÓN: si existe un concepto de "corrida"/manifiesto propio de este proyecto,
análogo al `RunManifest` de scientific-literature-pipeline, o si el registro vive solo a nivel de
cada `ProcurementRecord` - ver specs/pending-adrs.md]`

## Fuera de alcance

- Calcular indicadores de riesgo: corresponde a `004-red-flags-engine`.
  El enlace de evidencia oficial y la deduplicación canónica sí pertenecen a esta ingesta.
- Cruzar con ejecución presupuestal: eso es responsabilidad de `004`, usando la salida de `002` y
  `003` juntas - esta capacidad no llama a `003`.
- Descargar o interpretar el `/downloads` en bloque de OECE mientras no se reverifique que
  resuelve desde una red externa.
- Afirmar un histórico completo por cargar el feed rotativo OCDS.
  La cobertura histórica de Pentaho se declara por recurso y ejercicio capturados.

## Ambigüedades abiertas

**AC-002-01. Mecanismo de paginación o ventana temporal real del endpoint.**
La verificación técnica no encontró un parámetro de fecha, cursor o página con efecto observable
en `/api/v1/releases`. No lo cierro yo: hace falta seguir probando el endpoint (con más tiempo del
que tuvo esta ronda) o contactar a OECE/OSCE para confirmar si existe una forma documentada de
paginar más allá del feed rotativo - sin eso, cualquier estrategia de cosecha "diaria" o "por
ventana" que se especifique sería una suposición.
`[NECESITA ACLARACIÓN: mecanismo real de paginación/ventana - requiere más verificación técnica
o contacto con OECE]`

**AC-002-02. Frecuencia de ejecución de la ingesta.**
El diseño de producto proponía "diario o semanal" sin verificar cuántos `releases` nuevos entran
por día a nivel nacional (y menos aún para Cajamarca). Sin ese dato, fijar una frecuencia es
adivinar cuánto solapamiento hace falta para no perder releases entre corridas dado que el feed
solo muestra ~20 a la vez.
`[NECESITA ACLARACIÓN: frecuencia de ejecución, informada por el volumen real de publicaciones]`

**AC-002-03. Versionado de un `release` actualizado (RN-002-04).**
No decido si un `release` actualizado reemplaza al anterior con historial visible, o si cada
versión es un `ProcurementRecord` distinto enlazado por `ocid`. Es una decisión de modelo de
datos que interactúa con cómo `004-red-flags-engine` compara "monto adjudicado" contra "monto
ejecutado" a lo largo del tiempo, y no se debe fijar sin ver primero cómo se comporta el feed real
ante una actualización (no se observó ninguna en esta ronda de verificación).
`[NECESITA ACLARACIÓN: modelo de versionado de releases actualizados]`

**AC-002-04. Consorcios/compradores multi-departamento (CL-002-02).**
`[NECESITA ACLARACIÓN: criterio de inclusión cuando un release tiene compradores de más de un
departamento]`

**AC-002-05. Concepto de "corrida" propio del proyecto.**
Ver la nota en Evidencia y manifiesto. No decido si este proyecto necesita un artefacto de tipo
`RunManifest` (como en `scientific-literature-pipeline`) o si basta con que cada
`ProcurementRecord` lleve su propia procedencia. La respuesta depende del stack elegido y del
volumen real, y pertenece a `specs/pending-adrs.md`, no a esta spec.
`[NECESITA ACLARACIÓN: modelo de ejecución/corrida - ver specs/pending-adrs.md]`

## Ambigüedades resueltas

**AC-002-06. Si se puede asumir que existe un filtro de región server-side.**
**Decisión: no. Se verificó lo contrario.** Cinco nombres de parámetro distintos
(`department`, `region`, `buyer`, `supplierOrBuyer`, `filter`) se probaron contra el endpoint
real el 2026-08-20 y ninguno tuvo efecto observable en el tamaño ni contenido de la respuesta.
Diseñar sobre la suposición optimista del documento de diseño original habría producido una
capacidad que en producción ignora silenciosamente su propio filtro. Ver
`docs/research/2026-08-20-verificacion-tecnica-fuentes.md` §1.2 para la evidencia completa.

**AC-002-07. Si `parties[].address.department` es un campo confiable para filtrar.**
**Decisión: sí, es el campo correcto**, confirmado con un payload real que trae
`"department": "CAJAMARCA"` para una entidad efectivamente cajamarquina. Es preferible a inferir
la región del RUC (que no codifica ubicación geográfica de forma estándar) o del nombre de la
entidad (frágil ante variaciones de escritura).

## Historial

Enmienda humana 2026-10-15: fuentes duales y trazabilidad según Constitución v2.0.

| Fecha | Cambio | Estado |
|---|---|---|
| 2026-08-20 | Redacción inicial, fundamentada en verificación técnica real | `draft` |
