---
title: SDD — cajamarca-qhaway
status: active
created: 2026-08-20
source: ai
generator: claude-sonnet-5
generated_at: 2026-08-20T00:00:00Z
confidence: medium
verified: false
---

# SDD — cajamarca-qhaway

Este proyecto se construye con Spec-Driven Development (SDD): antes de escribir código, cada
capacidad se especifica en `specs/NNN-<slug>/`. Las reglas del método están en
`constitution.md`, en este mismo directorio — léelo antes de escribir o cambiar una spec.

## Por qué SDD aquí

Este no es un pipeline de datos cualquiera: produce señales que pueden dañar reputaciones si se
equivocan. Especificar primero, con reglas de negocio numeradas y criterios falsables, es lo que
permite defender después —legal y periodísticamente— por qué una alerta dice lo que dice. La
spec **es** la documentación de esa defensa, no un trámite previo al código.

## Cómo se usa

1. Cada capacidad vive en `specs/NNN-<slug>/`, con hasta tres artefactos: `spec.md` (qué y por
   qué), `plan.md` (cómo), `tasks.md` (en qué orden). Ver Artículo 2 de la constitución.
2. Una spec nace en `draft`. Nadie —humano o agente— la mueve a `approved` sin que esté vacía de
   `[NECESITA ACLARACIÓN]` sin resolver. Ver Artículo 8.
3. `plan.md` no existe, o existe pero está incompleto, cuando la spec todavía tiene ambigüedades
   que cambiarían el diseño técnico. `tasks.md` solo se escribe cuando spec y plan son lo
   bastante sólidos como para que una tarea tenga sentido — fabricar tareas sobre una base
   inestable es peor que no tenerlas (Artículo 2).
4. Los seis contratos de datos compartidos (`ContractingEntity`, `ProcurementRecord`,
   `BudgetExecutionRecord`, `RedFlag`, `Alert`, `CitizenReport`) están en el Artículo 19 de la
   constitución. Ninguna spec los redefine por su cuenta.
5. Las decisiones arquitectónicas que una spec destapa —pero no puede resolver por sí sola— se
   listan en `specs/pending-adrs.md`, no se deciden en silencio dentro de la spec.

## Qué no es SDD aquí

- No sustituye la coordinación previa con Proética Cajamarca, Propuesta Ciudadana y GRUFIDES que
  bloquea el desarrollo técnico (`CLAUDE.md`, sección "Estado").
- No decide temas legales (Ley 29733 sobre DJI) ni éticos (scoring de personas) — esos quedan
  escalados por diseño, nunca resueltos en una spec (Artículos 16 y 17).
- No reemplaza los ADR: una spec puede *pedir* uno, nunca *ser* uno.
