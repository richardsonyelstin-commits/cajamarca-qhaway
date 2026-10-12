---
id: adr-0001
title: Python como lenguaje y runtime del proyecto
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
tags: [decision, stack, lenguaje]
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

# Python como lenguaje y runtime del proyecto

Se adopta Python (3.12, en línea con `scientific-literature-pipeline`) como lenguaje único de
backend, ingesta y motor de red flags. El frontend del panel de revisión y del futuro dashboard
público usa el mínimo de JavaScript necesario para ser usable, sin comprometerse todavía a un
framework de frontend completo.

## Contexto y planteamiento del problema

`PROJECT.yaml` deja `stack.language: null`, explícitamente "por definir tras el hito 1 del
roadmap". Los seis `plan.md` de `001` a `006` citan esta ausencia como bloqueante de su "orden de
implementación": ninguno puede fijar una librería HTTP, un framework de persistencia ni una
librería de verificación de RUC sin saber en qué lenguaje corre el proyecto
(`specs/001-entity-mapping/plan.md`, sección "Dependencias nuevas"; mismo patrón en `002`, `003`,
`004`, `005`, `006`).

El sistema tiene cuatro superficies con necesidades distintas: ingesta HTTP contra APIs JSON
externas sin autenticación (SEACE/OCDS, MEF DataStore), un motor de reglas que evalúa indicadores
puros sobre datos estructurados, un panel de revisión web para un número pequeño de personas
(`005-review-panel`), y, más adelante, un dashboard público (`007`, sin especificar aún) con
posible integración SMS/WhatsApp (`009`, sin especificar aún). Ninguna de estas cuatro superficies
exige por sí sola un lenguaje concreto; la decisión importa porque las cuatro deben convivir en un
equipo pequeño sin capacidad de mantener dos ecosistemas de dependencias.

## Factores de decisión

- Coste de ingesta: peticiones HTTP simples a JSON, sin SDK propietario obligatorio en ninguna
  fuente verificada (§1-2 de `docs/research/2026-08-20-verificacion-tecnica-fuentes.md`).
- Ajuste con PostgreSQL y CTE recursivas, ya propuesto en `PROJECT.yaml` para el grafo
  proveedor-funcionario-contrato.
- Compatibilidad con Cardinal (OCP), el motor de red flags de referencia que
  `specs/004-red-flags-engine/spec.md` (AC-004-02) deja pendiente de evaluar — sin el lenguaje
  fijado, esa evaluación no puede ni empezar.
- Carga de mantenimiento para un equipo pequeño: cuántos ecosistemas de dependencias hay que
  sostener a la vez.
- Precedente operativo dentro de este mismo workspace (`scientific-literature-pipeline`, Python
  3.12, `httpx` + `pydantic` v2), que ya resolvió problemas de forma similares (ingesta HTTP con
  validación de cuerpo, contratos con pydantic) reutilizables como patrón, no como código.
- Necesidad de un panel web y, después, un dashboard público — superficies que en cualquier
  lenguaje de backend terminan sirviendo HTML/JS al navegador.

## Opciones consideradas

### Opción 1 — Python (3.12) como lenguaje único de backend/ingesta/motor

- A favor: la carga de trabajo central del proyecto (ingesta HTTP + validación + persistencia
  relacional con consultas recursivas) es exactamente el tipo de trabajo para el que el ecosistema
  Python (`httpx`, `pydantic`, `SQLAlchemy`/`psycopg`, `pytest`) ya está probado en este mismo
  workspace.
- A favor: mantiene abierta, sin comprometerla todavía, la opción de reutilizar Cardinal (OCP) —
  la decisión real de reúso se toma en el ADR 0004, pero solo es evaluable si el lenguaje de este
  proyecto no descarta la compatibilidad de entrada.
- A favor: reduce la carga cognitiva de un equipo pequeño que probablemente ya mantiene
  `scientific-literature-pipeline` en Python — mismas convenciones de testing (`pytest`), mismo
  patrón de validación de cuerpo de respuesta HTTP, mismo estilo de contratos (`pydantic`).
- A favor: el panel de revisión y el dashboard público, con el volumen bajo de este proyecto
  (cientos a pocos miles de registros/año), no necesitan una aplicación de página única compleja:
  un backend Python que sirve HTML server-rendered (con JavaScript mínimo tipo htmx, sin
  framework de frontend pesado) cubre los casos de uso documentados (CU1-CU5) sin forzar un
  segundo lenguaje.
- En contra: construir una interfaz web moderna y agradable de usar en Python es menos fluido que
  en un framework de frontend nativo en JavaScript/TypeScript; si el futuro dashboard público
  necesita interactividad rica, el proyecto igual tendrá que escribir JavaScript en el navegador,
  aunque no un framework completo.
- En contra: el fondo de voluntarios/colaboradores con experiencia en desarrollo web moderno
  (formularios, sesión, autenticación) puede tener más soltura en JavaScript/TypeScript que en
  Python para esas tareas — es una suposición, no una evidencia verificada sobre el equipo real de
  este proyecto, y se señala como límite honesto de esta decisión.

### Opción 2 — TypeScript/Node.js como lenguaje único (backend + frontend con un solo framework, p. ej. Next.js)

- A favor: un solo lenguaje cubre ingesta, backend, panel de revisión y dashboard público sin
  ningún cambio de contexto — ventaja real para un equipo pequeño que también construye la
  interfaz.
- A favor: los SDK de mensajería más usados (Twilio, Meta Business SDK) tienen soporte de primera
  clase en Node, relevante para `009-sms-whatsapp-notify` cuando se especifique.
- A favor: el ecosistema de frameworks de frontend modernos (React/Next.js) da al dashboard
  público y al panel de revisión una experiencia de usuario más pulida con menos esfuerzo que
  construirla en Python.
- En contra: Cardinal (OCP) queda fuera de alcance de reúso directo sin un paso de integración
  poliglota (subproceso, microservicio aparte) — coste operativo añadido para un equipo pequeño
  que este ADR busca evitar precisamente por el factor "carga de mantenimiento".
- En contra: el ecosistema de Node para trabajo de datos con PostgreSQL y consultas recursivas
  (CTE) es funcional pero menos maduro y menos usado en este tipo de tarea que el de Python
  (`psycopg`/`SQLAlchemy` frente a clientes Node más genéricos).
- En contra: no hay precedente operativo dentro de este workspace en TypeScript/Node para un
  proyecto de este tipo (ingesta + persistencia relacional), a diferencia de Python.

## Decisión

**Opción 1: Python 3.12.**

Gana sobre TypeScript/Node porque el trabajo central de este proyecto en Fase 1 —ingesta HTTP
contra APIs JSON, validación de contratos, persistencia relacional con consultas recursivas— es
exactamente donde Python tiene ventaja probada dentro de este mismo workspace, y porque mantiene
abierta la evaluación real de Cardinal (ADR 0004) sin forzar una decisión de "reescribir o
integrar poliglota" antes de tiempo. El volumen bajo de datos y el número reducido de usuarios del
panel de revisión (voluntarios de ONG aliadas, no miles de usuarios concurrentes) hacen que la
ventaja de TypeScript en experiencia de frontend rico no sea decisiva: un backend Python con HTML
server-rendered y JavaScript mínimo cubre los casos de uso documentados sin sobre-diseñar para una
escala que este proyecto no tiene.

No hay evidencia real (benchmark, prueba de integración) de cuánto costaría en la práctica
integrar Cardinal desde Python — esa evaluación es, precisamente, el contenido del ADR 0004; esta
decisión solo garantiza que la pregunta sigue siendo evaluable.

## Consecuencias

### Positivas

- Todas las ambigüedades de "Dependencias nuevas" bloqueadas por el lenguaje en los seis planes
  (`001`-`006`) quedan desbloqueadas: pueden fijar `httpx` para HTTP, `pydantic` para los
  contratos canónicos, `pytest` para pruebas.
- Un solo ecosistema de dependencias y de convenciones de testing para todo el backend/ingesta.
- Precedente reutilizable de `scientific-literature-pipeline` (validación de cuerpo de respuesta,
  patrón de contratos con pydantic) sin copiar código, solo convención.
- Cardinal (OCP) sigue siendo una opción real de evaluación técnica en el ADR 0004.

### Negativas

- El panel de revisión (`005`) y el futuro dashboard público (`007`) necesitarán, en algún punto,
  JavaScript en el navegador para interactividad — Python no elimina esa necesidad, solo evita
  comprometerse a un framework de frontend pesado ahora.
- Si el equipo real que termina construyendo esto tiene más experiencia en JavaScript/TypeScript
  que en Python para desarrollo web, esta decisión impone una curva de aprendizaje — no verificado
  contra la composición real del equipo, que hoy no está definida (mismo vacío que
  `AC-005-01`, quién compone el panel).
- Compromete el proyecto a un único lenguaje de backend antes de que exista ningún código: si en
  la práctica `009-sms-whatsapp-notify` termina necesitando fuertemente el ecosistema Node
  (poco probable, dado que los proveedores de SMS/WhatsApp exponen APIs REST simples), habría que
  aceptar un microservicio aparte en vez de reabrir esta decisión para todo el proyecto.

### Qué se vuelve difícil de revertir

Todos los contratos canónicos (`ContractingEntity`, `ProcurementRecord`, `BudgetExecutionRecord`,
`RedFlag`, `Alert`, `CitizenReport`) se implementarán como modelos `pydantic`; toda prueba se
escribirá en `pytest`; toda petición HTTP usará `httpx` o equivalente. Revertir a otro lenguaje
después de que exista código de las seis capacidades exige reescribir la ingesta, el motor de red
flags y el panel completos, no solo una capa de presentación.

## Enlaces

- `specs/pending-adrs.md`, fila 1.
- `PROJECT.yaml`, `stack.language: null`.
- Todos los `plan.md` de `001` a `006`, sección "Dependencias nuevas".
- [ADR 0002](0002-forma-del-pipeline-ingesta.md) — depende de esta decisión solo indirectamente
  (ambas capas de persistencia funcionan igual en Python).
- [ADR 0004](0004-motor-de-red-flags-propio.md) — depende directamente de esta decisión: la
  evaluación de Cardinal solo es posible porque este ADR mantiene Python como lenguaje base.
- Precedente: `../../scientific-literature-pipeline/CLAUDE.md`, sección "Stack".

---

> [!warning] Los ADR son inmutables.
> Si esta decisión cambia, no edites este archivo: crea uno nuevo con `supersedes` y pon
> este en `status: superseded`. El registro histórico es todo el valor de un ADR.
