---
title: Spec 001 — entity-mapping
spec: "001"
capability: entity-mapping
status: draft
created: 2026-08-20
updated: 2026-08-20
consumes: []
produces: [ContractingEntity]
open_clarifications: 3
source: ai
generator: claude-sonnet-5
generated_at: 2026-08-20T00:00:00Z
confidence: medium
verified: false
---

# Spec 001 — entity-mapping

Construye y mantiene el universo verificado de entidades contratantes de la región Cajamarca:
Gobierno Regional, las 13 municipalidades provinciales y un subconjunto priorizado de
municipalidades distritales. Produce `ContractingEntity`, el contrato que filtra toda ingesta
posterior — `002-seace-ingestion` y `003-mef-ingestion` no consultan nada que no esté aquí.

## Problema

`002-seace-ingestion` consume un feed nacional de contrataciones sin filtro geográfico
server-side confirmado (ver `docs/research/2026-08-20-verificacion-tecnica-fuentes.md`, §1): el
único filtro fiable es comparar `parties[].address.department` contra `"CAJAMARCA"` y cruzar el
RUC o el `consucode_id` de la entidad contra una lista conocida. Sin un universo de entidades
verificado y estable, cada capacidad de ingesta tendría que redescubrir "qué es Cajamarca" por su
cuenta, con el riesgo de que dos capacidades usen listas distintas y produzcan datos
incomparables.

El problema no es solo técnico: **qué entidades entran en el universo de Fase 1 es una decisión
de alcance y de recursos**, no un accidente de qué aparece primero en un feed. El Gobierno
Regional y las 13 provinciales entran completas por decisión ya fijada en `PROJECT.yaml`; el
subconjunto de distritales requiere un criterio explícito de priorización, porque cubrir las
~127 municipalidades distritales de Cajamarca desde el día uno excede lo que un equipo pequeño
puede mantener con calidad.

## Usuarios e intención

| Usuario | Qué quiere | Cómo se le falla |
|---|---|---|
| `seace-ingestion` | La lista exacta de RUC/`consucode_id` a filtrar | Una lista desactualizada o con nombres mal escritos |
| `mef-ingestion` | El mismo universo, con el mismo `entity_id` | Un universo distinto al de SEACE, que rompe el cruce |
| Analista de ONG (CU1) | Buscar por provincia y confiar en que la cobertura es la declarada | Que la plataforma calle qué distritos no cubre |
| Auditor del proyecto | Saber cuándo se verificó cada entidad y contra qué fuente | Un RUC copiado de una lista de terceros sin verificación propia |

## Entradas

| Campo | Origen | Obligatorio |
|---|---|---|
| Lista de las 13 provincias de Cajamarca | Fija, del propio Perú (Cajamarca, Cajabamba, Celendín, Chota, Contumazá, Cutervo, Hualgayoc, Jaén, San Ignacio, San Marcos, San Miguel, San Pablo, Santa Cruz) — enumerada en `docs/research/2026-08-20-diseno-cajamarca-qhaway-fase1.md`, §0 | sí |
| Criterio de priorización de distritales | Ver Ambigüedades abiertas — no fijado en esta spec | sí, para completar el universo |
| Fuente oficial de RUC/razón social por entidad | SUNAT (padrón de entidades públicas) o el propio feed OCDS de OECE, con verificación cruzada | sí |
| Fuente oficial de `consucode_id` | El propio feed OCDS de OECE (`parties[].identifier`, `scheme: PE-CONSUCODE`) | sí |

Esta etapa no recibe datos de contrataciones ni de ejecución presupuestal: solo construye el
universo de entidades, antes de que exista ningún dato asociado a ellas.

## Salidas

Un conjunto de `ContractingEntity` (contrato canónico, Artículo 19 de la constitución), uno por
entidad verificada, más un registro explícito de qué distritales quedaron **fuera** y por qué.

**Ubicación.** El universo vive como un artefacto versionado del proyecto (no en una base de
datos de ejecución), porque cambia poco y cada cambio debe poder auditarse como un diff legible.
Resuelto por [ADR 0006](../../docs/adr/0006-persistencia-universo-contracting-entity.md): dataset
declarativo en `data/entities/cajamarca-universe.yaml` (YAML, un mapeo con la clave `entities`),
versionado en el propio repo, sembrado a la tabla `contracting_entities` de PostgreSQL por
`scripts/seed_contracting_entities.py` — ver AC-001-02 en "Ambigüedades resueltas".

## Reglas de negocio

**RN-001-01. El Gobierno Regional y las 13 provinciales entran completos.**
Ninguna entidad de este subconjunto se excluye por criterio de priorización: `PROJECT.yaml` ya
fijó que son universo obligatorio de Fase 1.

**RN-001-02. Las distritales entran por un criterio de priorización explícito y documentado.**
No se puede incluir una municipalidad distrital "porque apareció en el feed" o "porque alguien la
mencionó": la inclusión se justifica por un criterio declarado (ver Ambigüedades abiertas,
AC-001-01) y queda registrada junto a la entidad.

**RN-001-03. Toda entidad lleva RUC y, si existe, `consucode_id`, verificados contra una fuente
oficial.**
No se acepta un RUC copiado de una fuente no oficial sin verificación cruzada contra al menos una
fuente primaria (SUNAT o el propio feed OCDS).

**RN-001-04. `entity_id` es determinista y estable.**
Se deriva del RUC, que es el único identificador que existe con independencia de si la entidad
aparece o no en el feed de OECE en un momento dado. Dos ejecuciones de esta capacidad sobre el
mismo RUC producen el mismo `entity_id`.

**RN-001-05. Una entidad que deja de existir (fusión, disolución) no se borra: se marca
`active: false`.**
Los `ProcurementRecord` y `BudgetExecutionRecord` históricos siguen apuntando a un `entity_id`
válido aunque la entidad ya no sea sujeto de ingesta activa.

**RN-001-06. El universo se revisa por evento, no en tiempo real.**
No hay obligación de sincronía inmediata con creaciones o fusiones de municipalidades: se
revisa cuando cambia la fuente oficial (SUNAT/OECE) o por ciclo declarado.
`[NECESITA ACLARACIÓN: periodicidad exacta de revisión — ver Ambigüedades abiertas]`

**RN-001-07. `department` es siempre `"CAJAMARCA"` en Fase 1.**
Ninguna entidad de otro departamento entra en este universo, aunque aparezca en resultados de
búsqueda por nombre parecido (Artículo 18 de la constitución).

**RN-001-08. `province` es `null` únicamente para el Gobierno Regional.**
Toda municipalidad, provincial o distrital, declara su provincia explícita — nunca se infiere del
nombre por texto libre; se toma de la fuente oficial.

**RN-001-09. Cero scoring o clasificación de riesgo de una entidad en esta capacidad.**
`entity-mapping` no produce ninguna noción de "entidad más o menos riesgosa": eso es
competencia exclusiva de `004-red-flags-engine`, y aplicado a procesos y contratos, nunca a la
entidad como tal (Artículo 16).

## Criterios de aceptación

**CA-001-01** · RN-001-01
Dado el universo construido, contiene exactamente el Gobierno Regional de Cajamarca y las 13
municipalidades provinciales, sin excepción.

**CA-001-02** · RN-001-03
Dada cualquier `ContractingEntity`, su `ruc` tiene 11 dígitos y coincide con al menos una fuente
oficial consultada, registrada en el propio artefacto.

**CA-001-03** · RN-001-04
Dado el mismo RUC procesado dos veces, el `entity_id` resultante es idéntico.

**CA-001-04** · RN-001-05
Dada una entidad marcada `active: false`, sigue presente en el universo (no se elimina el
registro).

**CA-001-05** · RN-001-07
Dado el universo completo, todas las entidades tienen `department == "CAJAMARCA"`.

**CA-001-06** · RN-001-08
Dada cualquier entidad con `entity_level != "regional"`, `province` no es `null` y pertenece a la
lista fija de 13 provincias.

**CA-001-07** · RN-001-02
Dada cualquier municipalidad distrital en el universo, existe una justificación de inclusión
distinta de "aparece en el feed", registrada junto a la entidad.

## Casos límite

**CL-001-01** — Una municipalidad distrital cambia de nombre oficial sin cambiar de RUC.
El `entity_id` no cambia (RN-001-04); `official_name` se actualiza y el cambio anterior queda en
el historial del artefacto, no se pierde silenciosamente.

**CL-001-02** — Dos entidades con RUC distinto pero nombre casi idéntico (típico en
municipalidades distritales con nombres compuestos).
Se tratan como entidades distintas; no hay deduplicación por similitud de nombre en esta
capacidad.

**CL-001-03** — Una entidad aparece en el feed OCDS con `consucode_id` pero SUNAT no tiene el
RUC correspondiente indexado con el mismo nombre exacto.
La entidad no se acepta sin verificación cruzada manual — RN-001-03 es estricta; no se adivina.

**CL-001-04** — El Gobierno Regional de Cajamarca tiene unidades ejecutoras propias (p. ej. UGEL
Celendín, observada en la verificación técnica) que aparecen como `buyer` independiente en OCDS,
con su propio `consucode_id` y a veces su propio RUC.
`[NECESITA ACLARACIÓN: si una unidad ejecutora del Gobierno Regional es una `ContractingEntity`
propia o se agrupa bajo la entidad matriz — ver Ambigüedades abiertas]`

## Evidencia y manifiesto

Esta capacidad no participa del `evidence-ledger` de una corrida de ingesta (no hay corridas
todavía en el vocabulario de este proyecto — ese concepto, si se necesita, es una ambigüedad
para `002`). Lo que sí registra, por entidad: la fuente exacta consultada para verificar el RUC,
la fecha de verificación (`verified_at`) y, si aplica, el criterio de priorización que justificó
incluir una distrital.

## Fuera de alcance

- Cualquier dato de contrataciones, presupuesto o DJI asociado a una entidad: eso es competencia
  de las capacidades de ingesta.
- Cobertura de otras regiones del Perú (Artículo 18).
- Automatizar la detección de fusiones o disoluciones de municipalidades: se revisa por evento
  declarado, no por monitoreo continuo (RN-001-06).
- Geolocalización o límites administrativos en mapa: no hace falta para filtrar por RUC/nombre.

## Ambigüedades abiertas

Quedan tres de las cuatro originales — AC-001-02 se movió a "Ambigüedades resueltas".

**AC-001-01. Criterio de priorización de municipalidades distritales.**
No lo cierro yo: exige una decisión de producto sobre cuántas distritales puede sostener el
equipo con calidad, cruzada con el criterio de "sectores priorizados por evidencia de riesgo"
que ya señala el diseño de Fase 1 (obras públicas y canon minero). Fijar un número o una lista
aquí, sin ese cruce, produciría una priorización arbitraria que después habría que deshacer.
`[NECESITA ACLARACIÓN: número y criterio de selección de distritales priorizadas — requiere
decisión de producto, posiblemente informada por la coordinación con Proética/Propuesta
Ciudadana/GRUFIDES que ya bloquea el roadmap]`

**AC-001-03. Unidades ejecutoras del Gobierno Regional como entidad propia o agrupada.**
Ver CL-001-04. Requiere mirar más muestras del feed OCDS para saber si el patrón
"Gobierno Regional - UGEL X" es sistemático o incidental, y una decisión de si el análisis de
red flags debe tratarlas como una sola entidad regional o como entidades separadas (afecta
directamente los indicadores de `004-red-flags-engine`, p. ej. "proveedor recurrente por
entidad").
`[NECESITA ACLARACIÓN: agrupación de unidades ejecutoras — necesita más muestras del feed OCDS
antes de decidir]`

**AC-001-04. Periodicidad de revisión del universo (RN-001-06).**
"Por evento" queda declarado como principio, pero no hay todavía un ciclo mínimo garantizado
(¿trimestral? ¿semestral?) para el caso en que no ocurra ningún evento detectable. Fijar un
número sin saber cuánto cambia el padrón de municipalidades en la práctica sería una promesa
sin base.
`[NECESITA ACLARACIÓN: periodicidad mínima de revisión, aunque no haya evento detectado]`

## Ambigüedades resueltas

**AC-001-02. Formato y ubicación del artefacto del universo.** Resuelto por
[ADR 0006](../../docs/adr/0006-persistencia-universo-contracting-entity.md) (`accepted`,
2026-08-20): el universo vive como dataset declarativo versionado en el propio repo — formato
YAML, un mapeo con la clave `entities` en la raíz, ruta `data/entities/cajamarca-universe.yaml` —
y se siembra a la tabla `contracting_entities` de PostgreSQL (ADR 0002/0003) mediante
`scripts/seed_contracting_entities.py`. El ADR no fija el formato concreto de fichero (YAML vs.
JSON); esa elección puntual la hizo la implementación de esta ronda (`specs/001-entity-mapping/plan.md`,
"Orden de implementación", paso 6). El historial de Git de ese fichero es el "diff legible" que
pedía esta sección; el paso de siembra falla ruidosamente si la tabla y el fichero divergen tras
el commit, en vez de servir datos desactualizados sin avisar.

Las otras tres ambigüedades (AC-001-01, AC-001-03, AC-001-04) siguen abiertas — ninguna se toca
en esta ronda.

## Historial

| Fecha | Cambio | Estado |
|---|---|---|
| 2026-08-20 | Redacción inicial | `draft` |
| 2026-08-20 | AC-001-02 resuelta por ADR 0006 (dataset YAML versionado, sembrado a PostgreSQL); implementados los pasos 1-3 y 6 de `plan.md` (corpus dorado de 14 entidades, `entity_id`, verificación cruzada de RUC, script de siembra) | `draft` |
