---
title: Spec 005 - review-panel
spec: "005"
capability: review-panel
status: draft
created: 2026-08-20
updated: 2026-10-15
consumes: [RedFlag]
produces: [Alert]
open_clarifications: 4
source: ai
generator: codex-gpt-6
generated_at: 2026-10-15T18:33:00Z
confidence: medium
verified: false
---

# Spec 005 - review-panel

Recibe los candidatos de `RedFlag` producidos por `004-red-flags-engine` y decide, por acción
humana explícita, publicarlos como `Alert` o descartarlos. Es la implementación directa del
Artículo 14 de la constitución: ninguna alerta existe sin pasar por aquí, sin excepción y sin
atajo técnico.

## Problema

Toda la literatura revisada (`brain/70-inbox/2026-08-20-estado-del-arte-ia-anticorrupcion.md`,
§8.2) coincide en que el patrón de mayor riesgo legal y reputacional es publicar alertas
automáticas sin revisión humana previa. El problema de esta capacidad no es solo "quién aprueba"
sino **cómo se garantiza técnicamente que no exista ningún camino que salte este paso** - porque
una regla de negoción documentada pero no forzada por el propio flujo de datos es una promesa que
un error de implementación futuro puede romper sin que nadie lo note hasta que ya haya daño
reputacional real.

## Usuarios e intención

| Usuario | Qué quiere | Cómo se le falla |
|---|---|---|
| Revisor humano (voluntario ONG o equipo) | Ver el `RedFlag` con su evidencia completa antes de decidir | Un resumen que oculte el dato exacto que lo disparó |
| Revisor humano | Descartar un falso positivo evidente sin fricción | Un flujo que solo permita aprobar, no descartar con motivo |
| Dashboard público (`007`, no construido aún) | Consumir solo `Alert` con `status == published` | Que se filtre por otro criterio y se filtre un `RedFlag` sin revisar |
| Auditor del proyecto | Saber quién decidió qué y cuándo, siempre | Un registro sin `reviewed_by` o con un valor genérico tipo "sistema" |

## Entradas

| Campo | Origen | Obligatorio |
|---|---|---|
| `RedFlag` candidatos | `004-red-flags-engine` | sí |
| Identidad del revisor humano | Ver Ambigüedades abiertas (quién compone el panel) | sí |
| Decisión (publicar/descartar) y motivo | El propio acto de revisión | sí |

## Salidas

El expediente previo a decisión admite generated e in_review con evidencia y sin firma fabricada.
Solo published o discarded representan decisiones humanas y exigen identidad, fecha y notas.

Un `Alert` (contrato canónico, Artículo 19) por cada decisión de publicar, y un registro de
descarte (mismo contrato, con `status == "discarded"`) por cada decisión de no publicar - ambos
casos quedan registrados, no solo el positivo, porque un `RedFlag` descartado sin rastro sería
indistinguible de uno que nunca se generó, y eso rompería la auditoría de qué se revisó.

**Ubicación.** `[NECESITA ACLARACIÓN: depende del stack - ver specs/pending-adrs.md]`

## Reglas de negocio

**RN-005-08. Copiloto privado anclado a evidencia.**
Los expedientes in_review reciben resumen, hipótesis, contra-hipótesis y checklist.
Cada afirmación referencia evidencia suministrada o declara ausencia de dato.
La síntesis determinista y la respuesta LLM con esquema estricto indican su modo de generación.
El análisis no genera señales, firmas ni decisiones y no se incluye en el snapshot público.
La cola se ordena por prioridad explicable del expediente, sin puntuar personas.

**RN-005-01. Un `RedFlag` no se convierte en `Alert` sin una decisión humana explícita.**
No existe ninguna regla de auto-aprobación por antigüedad, por umbral de confianza ni por
ausencia de objeción en un plazo. El silencio nunca equivale a aprobación.

**RN-005-02. `reviewed_by` identifica a una persona concreta, nunca a un rol genérico ni a
"sistema".**
Un valor como `"admin"` compartido por varias personas no cumple esta regla: debe poder
distinguir, meses después, exactamente quién tomó cada decisión - es lo que exige la
defensibilidad legal del proyecto (`CLAUDE.md`, invariantes).

**RN-005-03. `Alert.legal_disclaimer` es el texto fijo del descargo estándar, sin excepción y sin
edición por el revisor.**
"Esto es un indicador de riesgo automatizado, no una prueba ni una acusación de corrupción" (o su
formulación final, fijada una sola vez para todo el proyecto) aparece en toda `Alert` publicada.
Un revisor no puede publicar sin ese texto ni reformularlo caso por caso - la consistencia es
parte de la defensa legal.

**RN-005-04. Toda decisión exige una nota de revisión.**
`review_notes` es obligatorio y no vacío cuando `status` es `discarded` o `published`.
En el descarte documenta el motivo; en la publicación documenta la revisión humana de la
evidencia. La extensión del contrato está propuesta en ADR 0010 y requiere aceptación humana.

**RN-005-05. Una `Alert` puede agrupar más de un `RedFlag` sobre la misma entidad o proceso, por
decisión humana explícita del revisor, nunca automáticamente por el motor.**
`red_flag_ids` acepta una lista; agrupar dos indicadores en una sola alerta pública es una
decisión editorial (p. ej. "esta obra tiene proveedor único y sobrecosto, cuéntese como una sola
alerta con dos indicadores") que un humano toma explícitamente, no una fusión automática por
similitud.

**RN-005-06. Ningún revisor aprueba su propio trabajo de generación de datos.**
Análogo al Artículo 8 de la constitución (un agente no aprueba su propia spec): si en el futuro
alguna parte de la ingesta o del motor de red flags corre bajo la responsabilidad operativa de
una persona concreta, esa persona no puede ser la única revisora de sus propios candidatos.
`[NECESITA ACLARACIÓN: cómo se aplica en la práctica con un equipo pequeño - ver Ambigüedades
abiertas]`

**RN-005-07. Una decisión de revisión es inmutable una vez tomada; una corrección es una decisión
nueva que referencia a la anterior.**
Si se detecta un error después de publicar (p. ej. una `Alert` publicada por error), no se
edita el registro original: se crea una acción de retiro explícita que referencia la `Alert`
original y declara el motivo. El historial de decisiones nunca se reescribe.

## Criterios de aceptación

**CA-005-07** · RN-005-08
El dossier contiene executive_summary, risk_hypothesis, legal_counter_hypothesis
y verification_checklist, con procedencia y limitaciones.
Evidencia faltante se informa sin fabricar datos SUNAT, satelitales ni ejecución de obra.
Ningún error LLM cambia el estado de revisión o crea una RedFlag.
El acceso anónimo no recibe el dossier ni las señales individuales pendientes.

**CA-005-01** · RN-005-01
Dado un `RedFlag` recién generado, no existe ningún camino de código que produzca una `Alert` a
partir de él sin pasar por un registro de decisión con `reviewed_by` no vacío.

**CA-005-02** · RN-005-02
Dada cualquier `Alert` o descarte, `reviewed_by` identifica a una persona concreta, distinta de
valores genéricos como `"system"`, `"admin"` o vacío.

**CA-005-03** · RN-005-03
Dada cualquier `Alert` con `status == "published"`, `legal_disclaimer` es idéntico al texto fijo
declarado para todo el proyecto.

**CA-005-04** · RN-005-04
Dado cualquier registro publicado o descartado, `review_notes` no está vacío.

**CA-005-05** · RN-005-05
Dada una `Alert` con más de un `red_flag_id`, existe un registro explícito de que un revisor
decidió agruparlos (no una fusión automática por coincidencia de `entity_id`).

**CA-005-06** · RN-005-07
Dada una `Alert` publicada y luego retirada, el registro original permanece sin modificar y existe
un registro nuevo que referencia su `alert_id` con el motivo del retiro.

## Casos límite

**CL-005-01** - Dos revisores deciden lo contrario sobre el mismo `RedFlag` (uno publica, otro
descarta) por error de coordinación.
`[NECESITA ACLARACIÓN: mecanismo de bloqueo/asignación para evitar decisión concurrente sobre el
mismo candidato - depende de cuántas personas componen el panel]`

**CL-005-02** - Un `RedFlag` queda sin revisar durante semanas.
No se resuelve automáticamente (RN-005-01); pero un panel sin capacidad de revisar el volumen de
candidatos generados es un riesgo operativo real que esta spec no puede resolver por sí sola -
depende de cuántas personas y cuánto tiempo dedica el panel (Ambigüedades abiertas del diseño de
producto, punto 5).

**CL-005-03** - Un revisor quiere publicar parte de la evidencia de un `RedFlag` pero no toda
(p. ej. ocultar un dato sensible).
No está permitido: RN-005-03 y el Artículo 15 de la constitución exigen la capa de explicabilidad
completa. Si un dato es demasiado sensible para publicar, la decisión correcta es descartar la
alerta entera con ese motivo, no publicar una versión editada de la evidencia.

## Evidencia y manifiesto

Cada decisión de revisión (publicar o descartar) es en sí misma el registro de evidencia:
`reviewed_by`, `reviewed_at`, `review_notes`. No hace falta un ledger aparte si el propio contrato
`Alert` obliga a estos campos, pero si el proyecto adopta un concepto de corrida/auditoría más
amplio (ver `specs/pending-adrs.md`), esta capacidad declara sus eventos igual que las demás.

## Fuera de alcance

- Generar `RedFlag`: eso es `004-red-flags-engine`.
- Moderar `CitizenReport`: aunque conceptualmente parecido (revisión humana antes de convertir
  algo en candidato accionable), el diseño de producto trata la denuncia ciudadana como un canal
  con su propia moderación (`006-denuncia-intake`) - no se fusionan en esta spec porque los
  criterios de admisión son distintos (una denuncia no trae fórmula ni umbral).
- Publicar la `Alert` en el dashboard público: eso es `007-public-dashboard`, no construida aún.
- Notificar por SMS/WhatsApp: eso es `009-sms-whatsapp-notify`, no construida aún.

## Ambigüedades abiertas

**AC-005-01. Quién compone el panel de revisión.**
Es la pregunta 5 del diseño de producto (`docs/research/2026-08-20-diseno-cajamarca-qhaway-fase1.md`,
§6), explícitamente sin resolver por el usuario. No la cierro yo: afecta directamente RN-005-06
(cómo se evita que alguien revise su propio trabajo con un equipo pequeño) y CL-005-01 (mecanismo
de concurrencia).
`[NECESITA ACLARACIÓN: composición del panel - decisión de producto pendiente, señalada
explícitamente por el usuario]`

**AC-005-02. Texto final del descargo estándar (RN-005-03).**
El diseño de producto propone una redacción (§3.5) pero no está confirmada como texto legal
definitivo - podría requerir revisión de alguien con criterio legal, dado que es la pieza central
de la defensa del proyecto ante un cuestionamiento.
`[NECESITA ACLARACIÓN: redacción final del disclaimer, posiblemente con revisión legal]`

**AC-005-03. Mecanismo de asignación/bloqueo para evitar decisión concurrente (CL-005-01).**
`[NECESITA ACLARACIÓN: depende de AC-005-01 (tamaño del panel) y del stack]`

**AC-005-04. SLA o expectativa de tiempo de revisión (CL-005-02).**
`[NECESITA ACLARACIÓN: depende de capacidad operativa real, no fijable sin conocer el equipo]`

## Ambigüedades resueltas

**AC-005-05. Si el panel puede editar el contenido de un `RedFlag` antes de publicarlo.**
**Decisión: no.** El panel decide `publicar`/`descartar` y añade `review_notes` de contexto, pero
no reescribe `formula_description`, `observed_value` ni `threshold_value` del `RedFlag` original -
eso rompería la trazabilidad hasta el dato de origen que exige el Artículo 15. Si el `RedFlag`
está mal calculado, el defecto se corrige en `004-red-flags-engine`, no editando la salida a mano
en el panel.

## Historial

Enmienda humana 2026-10-15: TIER_2 privado y prioridad de casos, Constitución v2.0.

| Fecha | Cambio | Estado |
|---|---|---|
| 2026-08-20 | Redacción inicial | `draft` |
