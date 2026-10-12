---
title: Constitución del método — cajamarca-qhaway
status: active
created: 2026-08-20
updated: 2026-08-20
applies_to: specs/**
source: ai
generator: claude-sonnet-5
generated_at: 2026-08-20T00:00:00Z
confidence: medium
verified: false
---

# Constitución del método — cajamarca-qhaway

Diecinueve artículos que gobiernan cómo se escribe, se aprueba y se deriva una especificación en
este proyecto. Adaptada del método de `scientific-literature-pipeline`
(`docs/sdd/constitution.md` de ese proyecto) — misma forma, mismo rigor falsable, vocabulario
propio de este dominio. Los artículos 14-18 no tienen equivalente allá: encapsulan los
invariantes de `CLAUDE.md` de este proyecto, que en un sistema que produce señales de posible
corrupción no son negociables ni discutibles spec por spec.

Cada artículo dice qué prohíbe y cómo se comprueba que se cumple. Si el código y la spec
discrepan, el defecto está en el código; cambiar la spec para justificarlo es la única forma de
romper este método.

## Artículo 1. La especificación manda

La spec es la fuente de verdad de cada capacidad. El código, las pruebas y la documentación
técnica se derivan de ella, nunca al revés.

**Comprobación:** ante una discrepancia entre `specs/NNN-*/spec.md` y `src/`, se corrige `src/`.
Un cambio a una spec `approved` para hacer pasar una prueba es rechazable.

## Artículo 2. Separación estricta de artefactos

Cada capacidad tiene hasta tres artefactos y ninguno invade el terreno del otro.

| Artefacto | Responde a | Prohibido |
|---|---|---|
| `spec.md` | qué y por qué | librerías, clases, rutas de fichero, firmas, nombres de endpoint |
| `plan.md` | cómo | requisitos nuevos que no estén ya en la spec |
| `tasks.md` | en qué orden y quién | diseño nuevo que no esté en el plan |

**Comprobación:** un `spec.md` que contenga `import`, `src/`, el nombre de una librería concreta
o una firma de función está mal escrito. Un `plan.md` que introduzca una regla de negocio ausente
de la spec está mal escrito. Un `tasks.md` no existe para una capacidad cuya spec o plan todavía
tenga una ambigüedad bloqueante: fabricar tareas sobre una base inestable es peor que no tener
tareas.

## Artículo 3. Prohibido el supuesto silencioso

Toda ambigüedad no resuelta se marca en el propio texto con `[NECESITA ACLARACIÓN: …]`. Inventar
la respuesta y seguir adelante es el fallo más caro de este método: el supuesto sobrevive
escondido hasta que el código ya depende de él, y en este dominio un supuesto equivocado puede
convertirse en una acusación pública infundada.

**Comprobación:** ninguna spec con un `[NECESITA ACLARACIÓN]` abierto puede pasar a `approved`.
La comprobación es un `grep` sobre el fichero, no un juicio.

## Artículo 4. Criterios de aceptación falsables

Cada criterio se enuncia de forma que un tercero pueda escribir la prueba sin preguntar nada. Un
criterio que no se pueda convertir en un `assert` no es un criterio: es un deseo.

**Comprobación:** «debe ser explicable» y «debe ser confiable» son defectos. «Toda `Alert`
publicada expone `red_flag_id`, `evidence.field`, `evidence.source`, `evidence.retrieved_at`» es
un criterio.

## Artículo 5. La prueba precede al código

Cada criterio de aceptación tiene una prueba nombrada en `tasks.md` **antes** de que exista la
implementación, y esa prueba falla al escribirse. Una tarea sin prueba asociada no está terminada
aunque el código funcione.

**Comprobación:** `tasks.md` nombra el fichero y la función de prueba de cada tarea.

## Artículo 6. Los contratos canónicos son compartidos y no se negocian en una spec

`ContractingEntity`, `ProcurementRecord`, `BudgetExecutionRecord`, `RedFlag`, `Alert` y
`CitizenReport` son vocabulario común a las seis capacidades activas de Fase 1 (definidos en el
Artículo 15). Los nombres de campo son en inglés y en `snake_case`.

Una spec **usa** esos contratos; no los redefine, no los renombra y no les añade campos por su
cuenta. Si una capacidad necesita un campo que no existe, eso es un `[NECESITA ACLARACIÓN]` con
propuesta, y se resuelve con un ADR que afecta a todas las capacidades a la vez.

**Comprobación:** dos specs que describan el mismo contrato con campos distintos son un defecto
bloqueante, no una diferencia de criterio.

## Artículo 7. Trazabilidad de extremo a extremo

Toda tarea apunta a un criterio de aceptación, y todo criterio apunta a una regla de negocio.
Código que no se pueda rastrear hasta una regla es alcance no pedido y se borra.

**Comprobación:** los identificadores `RN-NNN-nn` (regla), `CA-NNN-nn` (criterio) y `T-NNN-nn`
(tarea) se citan explícitamente y forman una cadena sin huecos.

## Artículo 8. Ciclo de vida y aprobación

```mermaid
stateDiagram-v2
    [*] --> draft
    draft --> review: sin [NECESITA ACLARACIÓN] abiertos
    review --> approved: aprueba un humano
    approved --> implemented: todas las tareas cerradas y en verde
    implemented --> superseded: la sustituye otra spec
    review --> draft: el humano devuelve con objeciones
```

Solo un humano mueve una spec a `approved`. Un agente puede redactar, revisar y proponer; no
puede aprobar su propio trabajo ni el de otro agente. Esto no es cortesía: es la misma regla que
protege la revisión de `Alert` (Artículo 14) aplicada al propio método que las produce.

## Artículo 9. Una spec aprobada no se edita en silencio

Un cambio sobre una spec `approved` se registra en su sección de historial con fecha y motivo, y
vuelve a `review`. Si el cambio altera un contrato canónico o el orden del pipeline, exige un ADR
en `status: proposed` antes de tocar el texto.

## Artículo 10. Evidencia como requisito, no como adorno

Toda capacidad que produce o transforma un `RedFlag` o una `Alert` declara explícitamente, en su
spec, de qué fuente exacta, con qué fecha de extracción y con qué payload original respalda cada
salida. Una capacidad cuyo resultado no se pueda reconstruir hasta el dato de origen está
incompleta, aunque funcione — es una reformulación del Artículo 15 aplicada a nivel de
implementación, y se repite aquí porque es la defensa legal y periodística de todo el proyecto
(ver `CLAUDE.md`, invariantes).

**Comprobación:** la spec nombra el campo de procedencia (`source`, `retrieved_at`,
`raw_payload_ref`) que rellena cada capacidad. Si no lo nombra, no está terminada.

## Artículo 11. Simplicidad deliberada

Se especifica lo que la capacidad debe hacer en Fase 1, acotada a Cajamarca, no lo que podría
necesitar en una expansión a otras regiones. Un apartado «fuera de alcance» explícito es
obligatorio: sirve para cerrar debates, no para adornar.

**Comprobación:** una spec que mencione otra región peruana fuera de la sección "fuera de
alcance" está mal escrita, salvo que `PROJECT.yaml` haya cambiado antes.

## Artículo 12. Límites del agente que escribe specs

- No inventa endpoints, campos de API ni cobertura de datos: los toma de
  `docs/research/2026-08-20-verificacion-tecnica-fuentes.md` o los marca `[sin verificar]`.
- No toca `src/`, `tests/`, `docs/adr/` ni specs que no le hayan asignado.
- No hace `commit` ni `push` salvo petición explícita.
- No cita como autoridad una nota con `verified: false`, ni siquiera propia — incluidos
  `docs/research/2026-08-20-diseno-cajamarca-qhaway-fase1.md` y
  `brain/70-inbox/2026-08-20-estado-del-arte-ia-anticorrupcion.md`, que se usan como punto de
  partida, no como hecho establecido.

## Artículo 13. Enmienda de esta constitución

Este documento solo lo modifica un humano. Un agente puede proponer una enmienda por ADR,
citando el caso concreto que la motiva; hasta que se acepte, la regla vigente es la de aquí.

---

## Artículo 14. Ninguna alerta sin revisión humana

Ninguna capacidad publica una `Alert` de forma autónoma. El motor de red flags (`004`) produce
candidatos; solo una decisión humana explícita, registrada con `reviewed_by` y `reviewed_at`, en
`005-review-panel`, convierte un candidato en `Alert` publicable.

**Comprobación:** una spec cuyo flujo permita que un `RedFlag` se convierta en `Alert` sin pasar
por `005-review-panel` es un defecto bloqueante de máxima severidad, no una optimización a
discutir. Ningún ADR puede levantar esta regla — solo un cambio a esta constitución, por un
humano (Artículo 13).

## Artículo 15. Explicabilidad completa como criterio de aceptación, no como nota al margen

Toda `Alert` expone, sin excepción, como parte de sus **criterios de aceptación** (no de su
descripción): qué `RedFlag` la origina, con qué fórmula y umbral; el dato exacto que la disparó;
la fuente (`seace-ingestion`, `mef-ingestion` o `dji-ingestion` cuando exista) con su
`retrieved_at`; y el descargo estándar de que es un indicador automatizado, no una prueba.

**Comprobación:** una spec que describa la capa de explicabilidad en prosa pero no la traduzca en
al menos un `CA-NNN-nn` verificable no puede pasar a `approved`. Es el mismo criterio del
Artículo 4, aplicado sin excepción a esta capa concreta.

## Artículo 16. Prohibido el scoring o ranking de personas

Ninguna spec asigna un puntaje, ranking o nivel de riesgo a una persona identificada por nombre.
Las alertas son sobre procesos y contratos (`ProcurementRecord`, `BudgetExecutionRecord`), nunca
sobre funcionarios, proveedores o denunciantes como individuos puntuados.

Si una capacidad, al especificarse, revela una tentación de hacerlo — por ejemplo, un indicador
que naturalmente produce "funcionarios con más contratos de riesgo"— **no se decide en la spec**.
Se marca `[NECESITA ACLARACIÓN: esta capacidad tienta a puntuar personas, escalar antes de
implementar]` y se detiene ahí. No es una decisión de diseño que un agente pueda tomar en
silencio ni resolver reformulando el indicador por su cuenta.

**Comprobación:** `grep` sobre cualquier `spec.md` en busca de un campo o cálculo cuya unidad de
análisis sea una persona con nombre propio. Si aparece fuera de una ambigüedad marcada, es un
defecto bloqueante.

## Artículo 17. DJI solo para relaciones declaradas, nunca cruzado con patrimonio no declarado

Cualquier spec que involucre datos de Declaraciones Juradas de Intereses (DJI) se limita a
mapear relaciones **declaradas** funcionario-empresa-familiar. Ninguna spec cruza DJI con gasto
observable, propiedades, redes sociales o cualquier fuente de terceros para inferir patrimonio no
declarado — ese análisis (*lifestyle audit*) está fuera de alcance de Fase 1 por decisión de
`PROJECT.yaml` y por el riesgo legal bajo la Ley 29733 que señala
`brain/70-inbox/2026-08-20-estado-del-arte-ia-anticorrupcion.md` (sección 6, `verified: false`,
pero suficiente para justificar cautela).

Ninguna spec de este tipo pasa de `draft` sin una nota explícita: **"requiere evaluación legal
previa bajo Ley 29733, no realizada por este agente"**. No se redacta como si la base legal ya
estuviera resuelta.

**Comprobación:** `008-dji-ingestion` no se especifica en esta ronda (ver `specs/README.md`)
precisamente por este artículo. Cuando se especifique, debe citar aquí el sign-off legal humano
antes de pasar a `review`.

## Artículo 18. Ámbito geográfico fijo en Cajamarca

Ninguna spec generaliza a otra región del Perú. `PROJECT.yaml` fija el alcance; un agente que
detecte la tentación de abstraer "por si se expande a otras regiones" lo marca como ambigüedad
abierta o lo omite, nunca lo construye por iniciativa propia (Artículo 11).

## Artículo 19. Vocabulario canónico de contratos compartidos

Seis contratos son vocabulario común a las seis capacidades activas de Fase 1. Se definen aquí
en forma preliminar; cada spec los usa sin redefinirlos (Artículo 6). Los nombres de campo son
`snake_case` en inglés; el contenido narrativo de los propios datos (nombres de entidad,
descripciones de obra) permanece en el idioma de origen (español).

### `ContractingEntity`

La entidad contratante verificada — producida por `001-entity-mapping`, consumida por todas las
demás.

| Campo | Tipo | Nota |
|---|---|---|
| `entity_id` | string | Identificador canónico interno, estable entre corridas |
| `official_name` | string | Razón social/denominación oficial, tal como la publica la fuente |
| `entity_level` | enum | `regional` \| `provincial_municipality` \| `district_municipality` |
| `province` | string \| null | Una de las 13 provincias de Cajamarca, o `null` si es el Gobierno Regional |
| `ruc` | string | RUC de 11 dígitos — `scheme: PE-RUC` en OCDS |
| `consucode_id` | string \| null | Identificador `PE-CONSUCODE` usado como `buyer.id`/`procuringEntity.id` en la API OCDS de OECE — ver `docs/research/2026-08-20-verificacion-tecnica-fuentes.md` §1.2 |
| `department` | string | Fijo: `"CAJAMARCA"` en Fase 1 — el mismo valor que `parties[].address.department` en OCDS |
| `verified_at` | ISO 8601 UTC | Cuándo se confirmó este registro contra la fuente oficial |
| `active` | boolean | Si sigue vigente como sujeto de ingesta |

### `ProcurementRecord`

Un proceso o contrato de contratación pública, alineado a OCDS para no reinventar campos que el
propio estándar ya resuelve. Ver
`docs/research/2026-08-20-verificacion-tecnica-fuentes.md` §1 antes de asumir cualquier campo no
confirmado aquí.

| Campo | Tipo | Nota |
|---|---|---|
| `procurement_id` | string | Determinista, derivado de `ocid` + fecha de captura |
| `ocid` | string | El `ocid` de OCDS, sin modificar |
| `entity_id` | string | FK a `ContractingEntity` |
| `title` | string | `tender.title`, sin transformar |
| `procurement_method` | string \| null | Tal como lo publica OCDS |
| `awarded_amount` | number \| null | Monto adjudicado, en soles |
| `executed_amount` | number \| null | Se rellena, si aplica, con datos cruzados de `BudgetExecutionRecord`; `null` si no hay cruce todavía |
| `number_of_bidders` | integer \| null | Cuando OCDS lo declare |
| `supplier_name` | string \| null | Del `party` con rol `supplier`, si existe |
| `supplier_ruc` | string \| null | Idem, `additionalIdentifiers[].scheme == "PE-RUC"` |
| `raw_payload` | objeto | El `release` OCDS completo, sin transformar |
| `source` | string | Fijo: `"seace-ocds"` |
| `retrieved_at` | ISO 8601 UTC | Cuándo se obtuvo este payload |

### `BudgetExecutionRecord`

Un registro de ejecución presupuestal, por entidad y periodo. Los campos exactos dependen del
esquema real del dataset del MEF, que `002-mef-ingestion`… (léase `003-mef-ingestion`) no pudo
confirmar por completo (ver ambigüedades abiertas de esa spec). Forma preliminar:

| Campo | Tipo | Nota |
|---|---|---|
| `execution_record_id` | string | Determinista, derivado de `entity_id` + periodo + fuente |
| `entity_id` | string | FK a `ContractingEntity` |
| `fiscal_year` | integer | Año fiscal |
| `budgeted_amount` | number | Presupuesto institucional modificado (PIM) u homólogo — `[NECESITA ACLARACIÓN: campo exacto, spec 003]` |
| `executed_amount` | number | Monto devengado o ejecutado — `[NECESITA ACLARACIÓN: campo exacto, spec 003]` |
| `budget_category` | string \| null | Genérica de gasto o categoría presupuestal, si el dataset la expone |
| `raw_payload` | objeto | El registro tal como lo devuelve la API del MEF, sin transformar |
| `source` | string | Fijo: `"mef-datastore"` |
| `retrieved_at` | ISO 8601 UTC | Cuándo se obtuvo este registro |

### `RedFlag`

Un indicador de riesgo activado sobre uno o más `ProcurementRecord`/`BudgetExecutionRecord`.
Nunca un score compuesto: siempre trazable a una fórmula pública y un umbral declarado.

| Campo | Tipo | Nota |
|---|---|---|
| `red_flag_id` | string | Determinista |
| `indicator_code` | string | Identificador estable del indicador (p. ej. `single-bidder`, `execution-overrun`) |
| `formula_description` | string | La fórmula en lenguaje simple, tal como la vería un usuario final |
| `threshold` | valor | El umbral exacto que se cruzó |
| `observed_value` | valor | El valor real observado que cruzó el umbral |
| `procurement_ids` | lista de string | Uno o más `ProcurementRecord.procurement_id` que sustentan el indicador |
| `execution_record_ids` | lista de string | Idem para `BudgetExecutionRecord`, si aplica |
| `evidence_source` | string | De qué ingesta viene el dato que disparó la regla |
| `evidence_retrieved_at` | ISO 8601 UTC | Fecha de extracción del dato de origen |
| `generated_at` | ISO 8601 UTC | Cuándo el motor produjo este candidato |

### `Alert`

Lo único que puede llegar al dashboard público (`007`, no especificado aún). Nunca existe sin
decisión humana.

| Campo | Tipo | Nota |
|---|---|---|
| `alert_id` | string | Determinista |
| `red_flag_ids` | lista de string | Uno o más `RedFlag` agrupados bajo esta alerta |
| `entity_id` | string | La `ContractingEntity` afectada |
| `status` | enum | `published` \| `discarded` |
| `reviewed_by` | string | Identificador del revisor humano — nunca vacío |
| `reviewed_at` | ISO 8601 UTC | Cuándo se decidió |
| `review_notes` | string \| null | Motivo de la decisión, obligatorio si `status == discarded` |
| `disclaimer` | string | Texto fijo: indicador automatizado, no prueba de corrupción |
| `published_at` | ISO 8601 UTC \| null | Solo si `status == published` |

### `CitizenReport`

Una denuncia ciudadana entrante, antes de moderación.

| Campo | Tipo | Nota |
|---|---|---|
| `report_id` | string | Generado al recibir la denuncia |
| `submitted_at` | ISO 8601 UTC | |
| `channel` | enum | `web` \| `sms` \| `whatsapp` — los dos últimos dependen de `009`, no construida aún |
| `raw_text` | string | Tal como la escribió la persona, sin tocar |
| `related_entity_id` | string \| null | Si la persona señaló una entidad conocida |
| `moderation_status` | enum | `pending` \| `accepted_as_lead` \| `rejected` |
| `moderated_by` | string \| null | Obligatorio si `moderation_status != pending` |
| `moderated_at` | ISO 8601 UTC \| null | |
| `legal_disclaimer_shown` | boolean | Debe ser `true` antes de aceptar el envío — ver `006-denuncia-intake` |

Estos seis contratos son la base; una spec que necesite un campo adicional lo marca
`[NECESITA ACLARACIÓN]` y propone el ADR correspondiente (Artículo 6).
