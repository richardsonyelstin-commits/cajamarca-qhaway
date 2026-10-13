# Decisiones de arquitectura - cajamarca-qhaway

Registro inmutable. Formato MADR. Plantilla: `brain/00-meta/templates/t-adr.md`.

## Reglas

1. **Los ADR no se editan.** Si una decision cambia, se crea un ADR nuevo con `supersedes`
   y el anterior pasa a `status: superseded`. El registro historico es todo el valor.
2. Numeracion correlativa de cuatro digitos. **Un numero nunca se reutiliza**, ni aunque el
   ADR se rechace.
3. Minimo dos opciones reales. Una opcion de paja invalida el ADR.
4. Las consecuencias **negativas** son obligatorias. Sin ellas, el ADR no esta terminado.
5. Un ADR rechazado se conserva: saber que se descarto y por que evita reabrir el debate.
6. Los agentes IA redactan en `status: proposed`. Solo un humano pasa a `accepted`.

## Cuando escribir uno

Todo cambio arquitectonico irreversible o caro de revertir: eleccion de almacen de datos,
limites entre servicios, protocolo publico, modelo de autenticacion, dependencia
estructural.

Ante la duda, escribelo. Un ADR cuesta veinte minutos; hacer arqueologia de codigo para
reconstruir el porque cuesta dias.

## Indice

| # | Titulo | Estado | Fecha |
|---|---|---|---|
| [0001](0001-lenguaje-y-runtime-python.md) | Python como lenguaje y runtime del proyecto | `accepted` | 2026-08-20 |
| [0002](0002-forma-del-pipeline-ingesta.md) | Estado operativo compartido en base de datos, no artefactos en disco | `accepted` | 2026-08-20 |
| [0003](0003-motor-de-base-de-datos-postgresql.md) | PostgreSQL como motor de base de datos | `accepted` | 2026-08-20 |
| [0004](0004-motor-de-red-flags-propio.md) | Motor de red flags propio, informado por la metodologia de Cardinal | `accepted` | 2026-08-20 |
| [0005](0005-autenticacion-panel-de-revision.md) | Autenticacion del panel de revision via OAuth con Google | `accepted` | 2026-08-20 |
| [0005-geo](0005-monitoreo-geoespacial-satelital-y-camaras-publicas.md) | Monitoreo geoespacial multi-temporal satelital y de camaras publicas para obras | `proposed` | 2026-10-13 |
| [0006](0006-persistencia-universo-contracting-entity.md) | Universo de `ContractingEntity` como dataset versionado, sembrado a PostgreSQL | `accepted` | 2026-08-20 |
| [0007](0007-arquitectura-plataforma-web-hibrida.md) | Arquitectura de plataforma web hibrida (HTML5/CSS3/Bootstrap 5/JS ES6+ con Supabase y respaldo local) | `proposed` | 2026-10-12 |
