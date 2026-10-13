---
id: adr-0005
title: Autenticación del panel de revisión vía OAuth con Google
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
tags: [decision, autenticacion, review-panel]
source: ai
generator: claude-sonnet-5
generated_at: 2026-08-20T00:00:00Z
confidence: medium
verified: false
decides:
  - review-panel
  - denuncia-intake
---

# Autenticación del panel de revisión vía OAuth con Google

El panel de revisión (`005`) y la interfaz de moderación de denuncias (`006`) autentican a sus
usuarios humanos mediante "iniciar sesión con Google" (OAuth), sin sistema propio de cuentas y
contraseñas.

## Contexto y planteamiento del problema

`specs/005-review-panel/spec.md` (RN-005-02) y `specs/006-denuncia-intake/spec.md` (RN-006-04)
exigen, sin excepción, que `reviewed_by`/`moderated_by` identifiquen a una persona concreta -
nunca un rol genérico ni un valor compartido tipo `"admin"`. Ninguna spec de esta ronda evaluó
opciones de autenticación (`specs/pending-adrs.md`, fila 6): la ambigüedad quedó abierta porque
dependía del lenguaje/runtime (ADR 0001) y de quién compone el panel, decisión de producto todavía
pendiente (`AC-005-01`, `docs/research/2026-08-20-diseno-cajamarca-qhaway-fase1.md`, §6, punto 5).

El perfil de usuario que sí está documentado -aunque la composición exacta no lo esté- es
consistente: "voluntarios de las ONG aliadas o el propio equipo" (§2, CU5 del diseño de producto),
un panel explícitamente reducido, no una organización con cientos de empleados ni necesidad de
integración con un directorio corporativo. Diseñar un sistema de autenticación pensado para un
panel grande sería sobre-ingeniería para el tamaño real de usuarios que las specs describen.

## Factores de decisión

- Cumplimiento no negociable de RN-005-02/RN-006-04: identidad de persona real, nunca compartida
  ni genérica.
- Tamaño del panel: pocos usuarios (voluntarios de ONG aliadas, equipo reducido), no una
  organización grande con necesidad de SSO corporativo.
- Carga de mantenimiento de seguridad para un equipo pequeño sin operación de seguridad dedicada,
  en un sistema cuyo contenido (indicadores de posible corrupción) es un blanco real de ataque o
  manipulación.
- Fricción de incorporación de un nuevo revisor (cuánto cuesta darle acceso).
- Disponibilidad de identidad ya existente en el perfil de usuario probable (cuentas Gmail/Google
  Workspace, ampliamente usadas en Perú, aunque no verificado para las ONG concretas mencionadas
  en el diseño de producto).

## Opciones consideradas

### Opción 1 - OAuth con un proveedor existente (Google)

Inicio de sesión delegado a Google; el proyecto no almacena contraseñas, solo asocia el correo
verificado por Google a un registro interno de revisor autorizado.

- A favor: elimina por completo la responsabilidad de almacenar y proteger contraseñas -una
  superficie de riesgo real para un proyecto cuyo contenido puede ser blanco de manipulación- sin
  que el equipo tenga que operar esa infraestructura de seguridad.
- A favor: prácticamente cualquier persona en el perfil de usuario esperado (voluntario de ONG,
  equipo técnico) ya tiene una cuenta Google, lo que reduce la fricción de incorporación a "añadir
  su correo a la lista de revisores autorizados".
- A favor: librerías maduras (p. ej. Authlib en Python, compatible con el ADR 0001) resuelven la
  integración en pocas líneas, con el token/sesión ya hardenizados por años de uso comunitario.
- A favor: satisface RN-005-02/RN-006-04 directamente: el correo verificado por Google identifica
  a una persona concreta, nunca un rol compartido.
- En contra: introduce una dependencia externa (Google) para el acceso a una herramienta cuya
  independencia institucional importa por diseño (el proyecto evita deliberadamente parecer
  vinculado a un organismo oficial) - riesgo de percepción menor, no de funcionamiento.
- En contra: un reclutador o voluntario sin cuenta Google (poco común, pero posible, p. ej. alguien
  que solo usa correo institucional de otro proveedor) queda fuera sin una vía alterna definida en
  este ADR.
- En contra: requiere conectividad a internet para autenticar contra Google - aceptable dado que
  el perfil de usuario del panel (voluntarios de ONG, equipo técnico) es de contexto urbano/de
  oficina, distinto del ciudadano rural que consume el dashboard público, pero no verificado con
  certeza.

### Opción 2 - Cuentas propias con usuario y contraseña

Sistema de registro y autenticación operado enteramente por el proyecto: hash de contraseñas,
flujo de recuperación, límites de intentos.

- A favor: control total, sin dependencia de un proveedor externo; funciona con cualquier persona,
  tenga o no una cuenta en un proveedor OAuth.
- A favor: no genera ninguna pregunta de percepción sobre dependencia de una empresa externa.
- En contra: el equipo asume la responsabilidad completa de una superficie de seguridad real
  (almacenamiento seguro de contraseñas, flujo de recuperación, protección contra fuerza bruta)
  para un panel de pocos usuarios - desproporcionado frente al tamaño real del problema que hay
  que resolver, y exactamente el tipo de sobre-diseño que este ADR busca evitar.
- En contra: cada incidente de seguridad (contraseña débil, reutilizada, filtrada en otro sitio)
  se convierte en un riesgo propio del proyecto, no de un proveedor con equipo de seguridad
  dedicado.
- En contra: mayor fricción de incorporación: hay que diseñar y mantener un flujo de registro,
  activación y recuperación desde cero.

### Opción 3 - Enlace firmado por correo (magic link), sin contraseña

El revisor recibe por correo un enlace de un solo uso, con expiración, que autentica la sesión sin
contraseña.

- A favor: más simple que un sistema de contraseñas completo - sin almacenamiento de credenciales.
- A favor: no depende de un proveedor OAuth externo; funciona con cualquier correo.
- En contra: el equipo debe construir y mantener por su cuenta la generación, firma, expiración e
  invalidación segura de los enlaces - una pieza de seguridad propia, con menos escrutinio
  comunitario que una librería OAuth madura, para un requisito (RN-005-02) que es defensa legal
  del proyecto y no admite un bug sutil.
- En contra: la fortaleza real de esta opción depende igual de la seguridad de la cuenta de correo
  del revisor (el mismo supuesto de fondo que OAuth), pero sin el hardening de sesión/token que
  una librería OAuth ya resuelve - es "reinventar" la mitad de lo que OAuth ya ofrece, con más
  riesgo de implementación propia.

## Decisión

**Opción 1: OAuth con Google.**

Gana sobre cuentas propias y sobre enlaces firmados porque minimiza lo que un equipo pequeño, sin
operación de seguridad dedicada, tiene que construir y mantener para cumplir un requisito no
negociable (RN-005-02/RN-006-04) en un sistema cuyo contenido es un blanco plausible de
manipulación. El perfil de usuario documentado -panel reducido de voluntarios de ONG y equipo
técnico- hace razonable asumir disponibilidad amplia de cuentas Google sin necesitar un sistema de
identidad propio. Esta decisión no sobre-diseña para un panel grande: es la opción de menor
esfuerzo de construcción y menor superficie de riesgo propio para el tamaño real de usuarios que
las specs describen.

Esta decisión queda condicionada a que la composición real del panel (`AC-005-01`, todavía
pendiente de decisión de producto) confirme que sus miembros tienen o pueden obtener cuentas
Google sin fricción desproporcionada. Si esa decisión de producto revela lo contrario, este ADR
debe revisitarse con uno nuevo, no editarse.

## Consecuencias

### Positivas

- Ningún almacenamiento de contraseñas ni flujo de recuperación que construir o mantener.
- Incorporar a un nuevo revisor es añadir su correo a una lista de autorizados, no crear una
  cuenta desde cero.
- RN-005-02/RN-006-04 se cumplen directamente con el correo verificado por Google como identidad.
- Superficie de seguridad de sesión/token resuelta por una librería madura y ampliamente usada, no
  por código propio sin escrutinio comunitario.

### Negativas

- Dependencia externa de disponibilidad y políticas de Google para el acceso al panel de un
  proyecto cuya independencia institucional importa por diseño - riesgo de percepción, no
  únicamente técnico.
- Un revisor sin cuenta Google (o que no quiera usarla) queda fuera del flujo definido aquí; este
  ADR no define una vía alterna, y su necesidad depende de una decisión de producto todavía
  pendiente (`AC-005-01`).
- Requiere conectividad para autenticar, lo cual es razonable para el perfil de usuario del panel
  pero no está verificado con certeza para cada miembro real.
- Si la composición del panel cambia hacia personas sin cuentas Google fácilmente disponibles, esta
  decisión debe revisitarse - es un riesgo de acoplamiento a un supuesto sobre el perfil de
  usuario, no verificado con el panel real todavía inexistente.

### Qué se vuelve difícil de revertir

`reviewed_by`/`moderated_by` almacenarán el identificador de correo verificado por Google como
identidad canónica de cada decisión histórica. RN-005-07 prohíbe editar un registro de decisión ya
tomado: cambiar de proveedor de identidad después de que existan decisiones históricas exige una
capa de mapeo de identidades antiguas a nuevas, no una simple migración de esquema, porque los
registros originales no se pueden reescribir.

## Enlaces

- `specs/pending-adrs.md`, fila 6.
- `specs/005-review-panel/spec.md`, RN-005-02, RN-005-06.
- `specs/005-review-panel/plan.md`, sección "Contrato interno de la operación de revisión" -
  declara que `reviewed_by` debe venir de "un sistema que exista fuera de esta capacidad", que este
  ADR resuelve.
- `specs/006-denuncia-intake/spec.md`, RN-006-04.
- `docs/research/2026-08-20-diseno-cajamarca-qhaway-fase1.md`, §2 (perfil "analista de ONG") y §6,
  punto 5 (composición del panel, todavía pendiente).
- [ADR 0001](0001-lenguaje-y-runtime-python.md) - decisión de la que este ADR depende: fija el
  stack (Python) sobre el que se integra la librería OAuth.

---

> [!warning] Los ADR son inmutables.
> Si esta decisión cambia, no edites este archivo: crea uno nuevo con `supersedes` y pon
> este en `status: superseded`. El registro histórico es todo el valor de un ADR.
