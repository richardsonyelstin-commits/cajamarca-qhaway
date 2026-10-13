---
title: Roadmap - cajamarca-qhaway
status: active
created: 2026-08-20
updated: 2026-10-12
source: ai
generator: claude-sonnet-5
generated_at: 2026-08-20T00:00:00Z
confidence: high
verified: false
---

# Roadmap - cajamarca-qhaway

Organizado por **horizontes**, no por fechas. Un roadmap con fechas concretas a más de un
trimestre es ficción, y la ficción se convierte en deuda de credibilidad.
Se revisa el primer lunes de cada mes.

## Now - en curso

| Qué | Por qué (resultado esperado) | Tamaño | Tarea |
|---|---|---|---|
| ~~Implementar `001-entity-mapping` según spec + ADR 0006~~ **Hecho.** | Corpus dorado de 14 entidades verificado | S | |
| ~~Fundación Contractual SDD y 6 Modelos Canónicos (Art. 19)~~ **Hecho (2026-10-12).** | Contratos Pydantic v2 inviolables con inmutabilidad y validaciones | M | |
| ~~Capacidades de Ingesta y Motor (002, 003, 004, 005, 006, CLI)~~ **Hecho (2026-10-12).** | Ingestas desacopladas, motor con 5 indicadores, compuerta humana y denuncias | L | |
| ~~Pilar 1: Cosecha Continua de Datos en Vivo (`live_harvest`)~~ **Hecho (2026-10-12).** | HarvesterDaemon, pollers SEACE/MEF, persistencia atómica de marcas de agua y log de brechas | M | |
| ~~Pilar 2: Base de Datos Operativa Conectada a Supabase~~ **Hecho (2026-10-12).** | Repositorios para los 6 modelos canónicos, RLS activo, spooling fallback y comandos CLI `db` | M | |
| ~~Pilar 3: Plataforma Web Integral (`web/`), Panel de Revisión (CU5), Dashboard Público (CU1-CU4) y Canal de Denuncia (`006`)~~ **Hecho (2026-10-12).** | Plataforma web completa en `web/` (`index.html`, `DESIGN.md`, `src/`, `media/`, `tools/`), puente Python/Vercel y conexión en vivo con Supabase | L | `TK-301`..`TK-306` |
| Resolver fila 8 de `specs/pending-adrs.md`: re-verificar `GET /downloads` de OECE desde otra red | Condiciona si `002-seace-ingestion` en producción puede apoyarse en descarga masiva | S | |

<!-- Solo este horizonte enlaza a tareas concretas. -->

## Next - siguiente ciclo

| Qué | Por qué | Tamaño |
|---|---|---|
| Validación operativa en campo con aliados regionales (Proética Cajamarca, Propuesta Ciudadana, GRUFIDES) sobre la plataforma web desplegada | Confirma ahorro de trabajo real en investigación y moderación | M |

## Later - comprometido, sin fecha

| Qué | Por qué |
|---|---|
| Evaluación legal formal de uso de DJI bajo Ley 29733, luego ingesta de DJI limitada a relaciones declaradas | Dominio legalmente más sensible - requiere sign-off explícito antes de construir |
| Canal SMS/WhatsApp piloto automatizado con un grupo reducido | Cubre el vacío de conectividad rural documentado en el diseño de Fase 1 |

## Someday - no comprometido

<!-- Ideas vivas. Que algo esté aquí no promete nada a nadie. -->

- Generalizar el modelo a otras regiones (`<region>-qhaway`) si Cajamarca valida la hipótesis.
- Imágenes satelitales para verificación física de obras.
- App móvil nativa, si el uso real demuestra que web + SMS/WhatsApp no basta.

## Descartado

<!-- Lo que salió del roadmap, con fecha y motivo. Evita reabrir el mismo debate cada
     trimestre. -->
