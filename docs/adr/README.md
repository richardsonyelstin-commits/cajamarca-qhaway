# Decisiones de arquitectura — cajamarca-qhaway

Registro inmutable. Formato MADR. Plantilla: `brain/00-meta/templates/t-adr.md`.

## Reglas

1. **Los ADR no se editan.** Si una decisión cambia, se crea un ADR nuevo con `supersedes`
   y el anterior pasa a `status: superseded`. El registro histórico es todo el valor.
2. Numeración correlativa de cuatro dígitos. **Un número nunca se reutiliza**, ni aunque el
   ADR se rechace.
3. Mínimo dos opciones reales. Una opción de paja invalida el ADR.
4. Las consecuencias **negativas** son obligatorias. Sin ellas, el ADR no está terminado.
5. Un ADR rechazado se conserva: saber qué se descartó y por qué evita reabrir el debate.
6. Los agentes IA redactan en `status: proposed`. Solo un humano pasa a `accepted`.

## Cuándo escribir uno

Todo cambio arquitectónico irreversible o caro de revertir: elección de almacén de datos,
límites entre servicios, protocolo público, modelo de autenticación, dependencia
estructural.

Ante la duda, escríbelo. Un ADR cuesta veinte minutos; hacer arqueología de código para
reconstruir el porqué cuesta días.

## Índice

| # | Título | Estado | Fecha |
|---|---|---|---|
| [0001](0001-lenguaje-y-runtime-python.md) | Python como lenguaje y runtime del proyecto | `accepted` | 2026-08-20 |
| [0002](0002-forma-del-pipeline-ingesta.md) | Estado operativo compartido en base de datos, no artefactos en disco | `accepted` | 2026-08-20 |
| [0003](0003-motor-de-base-de-datos-postgresql.md) | PostgreSQL como motor de base de datos | `accepted` | 2026-08-20 |
| [0004](0004-motor-de-red-flags-propio.md) | Motor de red flags propio, informado por la metodología de Cardinal | `accepted` | 2026-08-20 |
| [0005](0005-autenticacion-panel-de-revision.md) | Autenticación del panel de revisión vía OAuth con Google | `accepted` | 2026-08-20 |
| [0006](0006-persistencia-universo-contracting-entity.md) | Universo de `ContractingEntity` como dataset versionado, sembrado a PostgreSQL | `accepted` | 2026-08-20 |
| [0007](0007-arquitectura-plataforma-web-hibrida.md) | Arquitectura de plataforma web híbrida (HTML5/CSS3/Bootstrap 5/JS ES6+ con Supabase y respaldo local) | `proposed` | 2026-10-12 |
