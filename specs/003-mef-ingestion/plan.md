---
title: Plan 003 — mef-ingestion
spec: "003"
capability: mef-ingestion
status: draft
created: 2026-08-20
updated: 2026-08-20
source: ai
generator: claude-sonnet-5
generated_at: 2026-08-20T00:00:00Z
confidence: low
verified: false
---

# Plan 003 — mef-ingestion

Plan deliberadamente mínimo. Dos ambigüedades de `spec.md` (AC-003-01, `resource_id`; AC-003-02,
esquema de columnas) bloquean casi todo el diseño técnico de esta capacidad: sin saber contra qué
tabla y qué columnas se consulta, no hay algoritmo de filtrado, ni cruce, ni contrato de campos
que fijar sin adivinar. Escribir un plan completo aquí violaría el Artículo 3 de la constitución
tanto como escribirlo en la spec.

## Lo único que no depende de esas dos ambigüedades

**Cliente HTTP base.** `GET https://api.datosabiertos.mef.gob.pe/DatosAbiertos/v1/datastore_search`
con parámro `resource_id` (una vez conocido) y `limit`/`offset` para paginar — la forma de
paginación de una API tipo CKAN DataStore es estándar y no depende del dataset concreto.

**Primer paso de reconocimiento, no de ingesta.** Antes de poder implementar nada de esta
capacidad, hace falta una sesión de verificación con un navegador real (no `curl`) que:
1. Navegue a `https://datosabiertos.mef.gob.pe/organization/presupuesto-publico`.
2. Abra el dataset de ejecución de gasto relevante.
3. Capture, de la pestaña de red del navegador, la petición real a
   `api.datosabiertos.mef.gob.pe` y su `resource_id`.
4. Ejecute `datastore_search?resource_id=<id>&limit=1` para ver el esquema de columnas real.

Este reconocimiento no es parte de la implementación de la capacidad — es la verificación técnica
que le falta a `docs/research/2026-08-20-verificacion-tecnica-fuentes.md` para que esta spec
pueda avanzar de `draft` a `review`.

## Riesgos

| Riesgo | Impacto | Mitigación |
|---|---|---|
| El `resource_id` correcto no es único (varios datasets candidatos) | Ambigüedad sobre cuál ingerir | Confirmar con el propio Portal cuál corresponde a "ejecución del gasto" por entidad |
| El esquema no trae RUC ni código de entidad | Sin cruce estructurado con `001`/`002` | AC-003-04, sin resolver todavía |
| `datastore_search_sql` permite inyección si se construye la consulta con texto libre del usuario | Riesgo de seguridad si se expone sin control | No implementar `datastore_search_sql` con entrada no controlada; usar `datastore_search` con filtros parametrizados donde sea posible |

## Orden de implementación

1. Sesión de verificación con navegador real para obtener `resource_id` y esquema — **bloquea
   todo lo demás**.
2. Una vez resuelto: algoritmo de filtrado y cruce, siguiendo el mismo patrón de dos pasos que
   `002-seace-ingestion` si el esquema lo permite.
3. Persistencia — depende de `specs/pending-adrs.md`.

No se detalla estrategia de prueba: no hay nada que probar sin el esquema real. Escribirla ahora
produciría pruebas contra un contrato inventado.
