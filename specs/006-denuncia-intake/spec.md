---
title: Spec 006 — denuncia-intake
spec: "006"
capability: denuncia-intake
status: draft
created: 2026-08-20
updated: 2026-08-20
consumes: []
produces: [CitizenReport]
open_clarifications: 6
source: ai
generator: claude-sonnet-5
generated_at: 2026-08-20T00:00:00Z
confidence: low
verified: false
---

# Spec 006 — denuncia-intake

Recibe una denuncia ciudadana curada, la modera antes de convertirla en candidato de
investigación, y muestra el aviso obligatorio de que la plataforma no ofrece protección legal
equivalente al SINAD por no ser una entidad gubernamental. Decisión ya tomada por el usuario
(`PROJECT.yaml`, 2026-08-20): el canal de denuncia está incluido desde Fase 1, contra la
recomendación inicial del diseño de producto de mantener solo monitoreo pasivo.

## Problema

El estado del arte (`brain/70-inbox/2026-08-20-estado-del-arte-ia-anticorrupcion.md`, §8.3)
documenta que el modelo que funciona a escala (DoZorro, Ucrania) exige una comunidad de
verificadores capacitados, no un buzón anónimo abierto. El diseño de producto ya descartó
explícitamente el crowdsourcing sin curaduría como el patrón de mayor riesgo de abuso. El problema
de esta capacidad no es "cómo recibir texto de un ciudadano" —eso es trivial— sino cómo moderar
antes de que una denuncia se convierta en algo accionable, sin prometer al denunciante una
protección que la plataforma no puede dar, y sin que el propio canal se convierta en vector de
denuncias falsas con fines políticos en una región con conflicto social activo
(`docs/research/2026-08-20-diseno-cajamarca-qhaway-fase1.md`, §0).

## Usuarios e intención

| Usuario | Qué quiere | Cómo se le falla |
|---|---|---|
| Ciudadano denunciante | Que su reporte llegue a alguien que investigue | Un buzón que nadie modera nunca |
| Ciudadano denunciante | Entender qué protección tiene (o no tiene) antes de enviar | Un formulario que no menciona el riesgo hasta después de enviar |
| Moderador humano | Distinguir una denuncia seria de ruido/spam/ataque político | Un flujo que fuerce aceptar o rechazar sin espacio intermedio |
| `red-flags-engine`/`review-panel` | Recibir solo denuncias ya moderadas como candidato de investigación | Denuncias sin moderar mezcladas con `RedFlag` generados por datos |

## Entradas

| Campo | Origen | Obligatorio |
|---|---|---|
| `raw_text` | Persona denunciante, texto libre | sí |
| Canal de envío | `web` en Fase 1; `sms`/`whatsapp` dependen de `009`, no construida | sí |
| Confirmación de haber visto el aviso legal | Ver Reglas de negocio | sí |
| `related_entity_id` | Opcional, si la persona identifica una entidad conocida del universo de `001` | no |

## Salidas

Un `CitizenReport` (contrato canónico, Artículo 19) por cada envío aceptado por el formulario
(antes de moderación) — el estado `moderation_status` distingue lo recién llegado de lo ya
revisado.

**Ubicación.** `[NECESITA ACLARACIÓN: depende del stack — ver specs/pending-adrs.md]`

## Reglas de negocio

**RN-006-01. El aviso legal se muestra y se confirma antes de que el envío sea posible, no
después.**
`legal_disclaimer_shown` debe ser `true` en el momento de la creación del `CitizenReport`; un
envío sin esa confirmación previa no se acepta. El texto declara explícitamente que la plataforma
no es una entidad gubernamental y no ofrece la protección del SINAD (identidad del denunciante,
protección laboral) — ver Ambigüedades abiertas para el texto exacto.

**RN-006-02. Toda denuncia entra en `moderation_status: pending`, sin excepción.**
Ninguna denuncia se convierte en candidato de investigación (no se cruza con `004-red-flags-engine`
ni se muestra en ningún panel de trabajo activo) sin pasar por moderación humana explícita —
mismo principio del Artículo 14 de la constitución, aplicado a un tipo de entrada distinto
(denuncia, no dato estructurado).

**RN-006-03. Moderar es una decisión de tres estados, no dos.**
`accepted_as_lead` (se convierte en insumo de investigación), `rejected` (se descarta, con
motivo) — nunca un estado binario de "válida/inválida" que fuerce al moderador a decidir sin
espacio para "necesita más información antes de decidir", que en este caso se representa dejando
el reporte en `pending` más tiempo, no inventando un tercer estado adicional no declarado en el
contrato canónico.

**RN-006-04. `moderated_by` identifica a una persona concreta, igual que `reviewed_by` en
`005-review-panel` (RN-005-02).**
Mismo principio, misma razón: defensibilidad y trazabilidad.

**RN-006-05. Una denuncia aceptada como candidato (`accepted_as_lead`) no se convierte
automáticamente en `RedFlag` ni en `Alert`.**
Entra como insumo de investigación humana — puede orientar dónde mirar en `002`/`003`, pero no
genera por sí sola un indicador automatizado (una denuncia de texto libre no tiene fórmula ni
umbral, así que no encaja en el contrato `RedFlag`). El mecanismo exacto de cómo una denuncia
aceptada se convierte en trabajo de investigación queda fuera del alcance técnico de esta spec.

**RN-006-06. No se recolecta más dato personal del denunciante del que el propio canal exige
técnicamente.**
En el canal `web`, no se pide nombre, documento de identidad ni contacto salvo que la persona lo
incluya voluntariamente dentro de `raw_text`. Pedir un correo "para dar seguimiento" es una
decisión de producto que aumenta el riesgo de identificación y no está decidida aquí —
`[NECESITA ACLARACIÓN]` si se necesita algún canal de respuesta al denunciante.

**RN-006-07. Ninguna denuncia se publica en el dashboard público directamente.**
Una denuncia moderada como `accepted_as_lead` puede, en el futuro, alimentar un `RedFlag` si la
investigación humana produce datos que sí encajan en ese contrato — pero eso pasa por `004` y
`005` como cualquier otro candidato, nunca por una vía directa de "denuncia → alerta pública".

## Criterios de aceptación

**CA-006-01** · RN-006-01
Dado un intento de envío sin `legal_disclaimer_shown == true`, el `CitizenReport` no se crea.

**CA-006-02** · RN-006-02
Dado cualquier `CitizenReport` recién creado, `moderation_status == "pending"`.

**CA-006-03** · RN-006-03
Dado el conjunto de valores posibles de `moderation_status`, son exactamente `pending`,
`accepted_as_lead` y `rejected` — ningún otro valor es válido.

**CA-006-04** · RN-006-04
Dado cualquier `CitizenReport` con `moderation_status != "pending"`, `moderated_by` no está vacío
y no es un valor genérico.

**CA-006-05** · RN-006-05
Dado un `CitizenReport` con `moderation_status == "accepted_as_lead"`, no existe ningún `RedFlag`
que lo referencie directamente como su única fuente de evidencia estructurada.

**CA-006-06** · RN-006-06
Dado el formulario del canal `web`, no contiene ningún campo obligatorio de nombre, documento de
identidad o contacto.

## Casos límite

**CL-006-01** — Una denuncia con lenguaje que identifica claramente y por nombre a un
funcionario, acusándolo de forma directa.
`[NECESITA ACLARACIÓN: si el moderador debe redactar/anonimizar antes de aceptar como candidato,
dado que el Artículo 16 prohíbe cualquier salida que puntúe o exponga a una persona por nombre —
una denuncia de texto libre no es un RedFlag, pero si se usa como insumo visible de trabajo,
podría rozar el mismo riesgo]`

**CL-006-02** — Una oleada de denuncias coordinadas, con texto muy similar, en un periodo corto
(indicio de campaña política contra una entidad o persona).
`[NECESITA ACLARACIÓN: mecanismo de detección de abuso coordinado — no cubierto por esta spec,
podría requerir su propia regla de negocio en una revisión futura]`

**CL-006-03** — Una denuncia llega por SMS/WhatsApp antes de que `009-sms-whatsapp-notify`
exista.
No es un caso posible en Fase 1 actual: el canal `web` es el único disponible hasta que `009` se
especifique e implemente. El campo `channel` del contrato ya admite los tres valores para no
tener que romper el contrato canónico después.

**CL-006-04** — Un denunciante pide explícitamente que se elimine su denuncia después de
enviarla.
`[NECESITA ACLARACIÓN: mecanismo de retiro de una denuncia ya enviada — no cubierto, y con
implicación de protección de datos bajo Ley 29733 si la denuncia incluyó datos personales del
propio denunciante en el texto libre]`

## Evidencia y manifiesto

Cada `CitizenReport` guarda `submitted_at`, `channel` y, tras moderación, `moderated_by` y
`moderated_at` — es la traza mínima para que una decisión de moderación sea auditable, aunque el
contenido de la denuncia en sí no tenga "fuente" en el sentido de `002`/`003` (la fuente es la
propia persona).

## Fuera de alcance

- Cualquier mecanismo de protección de identidad más allá de no recolectar datos innecesarios
  (RN-006-06): no se construye un sistema de anonimización criptográfica ni de intermediación
  legal en Fase 1 — el aviso (RN-006-01) es la mitigación primaria, no una promesa de protección
  técnica que la plataforma no puede cumplir.
- Canales `sms`/`whatsapp`: dependen de `009-sms-whatsapp-notify`, no construida.
- Conversión automática de una denuncia en `RedFlag` o `Alert` (RN-006-05, RN-006-07).
- Verificación de identidad del denunciante: el canal es deliberadamente de baja fricción, no
  exige registro ni autenticación.
- Comunicación de vuelta al denunciante sobre el estado de su denuncia: no decidido (RN-006-06,
  ambigüedad).

## Ambigüedades abiertas

**AC-006-01. Texto exacto del aviso legal (RN-006-01).**
El diseño de producto exige que se comunique "con claridad" que no hay protección tipo SINAD,
pero no fija la redacción. Igual que AC-005-02 de `005-review-panel`, es una pieza con
implicación legal real que un agente no debe redactar como si fuera definitiva sin revisión
humana con criterio legal.
`[NECESITA ACLARACIÓN: redacción final del aviso, con revisión legal recomendada]`

**AC-006-02. Cómo una denuncia `accepted_as_lead` se convierte en trabajo de investigación
concreto (RN-006-05).**
No decido el mecanismo operativo: ¿la ve el mismo panel de `005-review-panel`? ¿un flujo de
trabajo distinto, más cercano a las ONG aliadas? Depende de la coordinación previa con Proética,
Propuesta Ciudadana y GRUFIDES que ya bloquea el roadmap — con esas organizaciones probablemente
se defina quién investiga qué.
`[NECESITA ACLARACIÓN: flujo operativo de investigación de denuncias aceptadas — depende de la
coordinación con actores externos, bloqueante del roadmap general]`

**AC-006-03. Redacción/anonimización de denuncias que nombran a una persona (CL-006-01).**
`[NECESITA ACLARACIÓN: política de moderación ante nombres propios — tensiona con Artículo 16]`

**AC-006-04. Detección de abuso coordinado (CL-006-02).**
`[NECESITA ACLARACIÓN: si se necesita en Fase 1 o se acepta el riesgo con un panel pequeño que
revisa todo manualmente]`

**AC-006-05. Mecanismo de retiro de una denuncia ya enviada (CL-006-04).**
`[NECESITA ACLARACIÓN: implicación de Ley 29733 sobre datos personales que el propio denunciante
incluyó — posiblemente requiere el mismo tipo de evaluación legal que DJI, aunque por un motivo
distinto]`

**AC-006-06. Si se ofrece algún canal de respuesta al denunciante (RN-006-06).**
`[NECESITA ACLARACIÓN: decisión de producto, no de esta spec — trade-off explícito entre dar
seguimiento y minimizar dato personal recolectado]`

## Ambigüedades resueltas

**AC-006-07. Si el canal de denuncia compite o reemplaza a `005-review-panel`.**
**Decisión: no, son flujos separados que convergen en trabajo humano, no en el mismo contrato de
salida.** `CitizenReport` no se convierte directamente en `Alert`: solo `RedFlag` (de
`004-red-flags-engine`) sigue ese camino. Fusionarlos habría requerido forzar el contrato
`CitizenReport` a tener fórmula y umbral, que no tiene sentido para texto libre de un ciudadano,
o forzar `RedFlag` a admitir texto libre sin estructura, que rompería el Artículo 15
(explicabilidad basada en dato exacto y fuente verificable).

## Historial

| Fecha | Cambio | Estado |
|---|---|---|
| 2026-08-20 | Redacción inicial | `draft` |
