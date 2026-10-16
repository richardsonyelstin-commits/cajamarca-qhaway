---
title: Compuertas de la reforma v2 y cobertura oficial
source: ai
generator: codex-gpt-6
generated_at: 2026-10-15T18:36:00Z
confidence: high
verified: false
---
# Compuertas de la reforma v2 y cobertura oficial
La reforma documental autorizada está aplicada en una rama aislada y pendiente de integración.
Las consultas de producción verifican 42 presupuestos y 475 procesos sin alterar sus datos.
SEACE devuelve CAPTCHA_REQUIRED; la compuerta 2 estricta sigue pendiente de cobertura real.

## Autorización y cambios

Fuente de alcance: contrato arquitectónico adjunto por el propietario y su autorización expresa
en esta conversación el 2026-10-15.
Rama de trabajo: agent/codex/constitutional-neurosymbolic-v2.
Base local: 9fe3750, que incluye la corrección a777ec3 de brechas HTTP del buscador.
Evidencia: git status, git log y git rev-list ejecutados en el repositorio.

La constitución v2.0 admite fuentes primarias oficiales plurales y dos niveles de IA.
Las specs 001-007 y el manifiesto registran el alcance y los contratos autorizados.
El ADR 0014 registra la autorización humana; los ADR históricos no se modifican.
La prioridad y el copiloto siguen pendientes del Nodo 3.
La aceptación de arquitectura no publica alertas ni acredita una evaluación legal profesional.
Evidencia: diff de esta rama frente a 9fe3750.

## Verificación del presupuesto existente

Consulta de solo lectura mediante Supabase MCP en oglltrpvvifqvwmxmkjq:

| Ejercicio | Maestros | Entidades | PIM (S/) | Devengado (S/) |
|---|---:|---:|---:|---:|
| 2024 | 14 | 14 | 5.088.605.186 | 4.618.558.165 |
| 2025 | 14 | 14 | 5.437.828.399 | 5.008.118.791 |
| 2026 | 14 | 14 | 6.011.280.694 | 4.006.118.779 |

La consulta verifica orden de momentos, cero maestros duplicados y cero registros distritales.
Cero registros exceden S/ 1 de diferencia entre PIM ActProy y Actividad más Proyecto.
Fuente: budget_execution_records y contracting_entities consultadas el 2026-10-15.
La procedencia por fila apunta al módulo institucional oficial MEF y conserva el payload.
Los nombres serializados vigentes se preservan en el contrato canónico.

Los códigos SEC_EJEC del documento humano difieren de los ya verificados en el proyecto.
Se conserva el mapa institucional vigente: 300549, 300562, 300566, 300578, 300597, 300605,
300620, 300623, 300635, 300642, 300649, 300662 y 300666; GORE mantiene Pliego 445.
Evidencia: payload.codigo_entidad de las 14 filas de 2026 y mapa de parser.py.
Este informe no reemplaza identificadores acreditados por los números del encargo.

## Conectores y compuerta 2

Sondeo real con los clientes existentes el 2026-10-15:
Pentaho descubre 43 recursos que abarcan 2024, 2025 y 2026.
SEACE buscador devuelve CAPTCHA_REQUIRED y cero filas.
La portada accesible no acredita haber ejecutado la consulta protegida.
Evidencia: OECEPentahoClient.discover y probe_public_source ejecutados en terminal.

Supabase contiene 475 procesos y 77.981 filas oficiales complementarias, 438 vinculadas.
Las 471 señales existentes carecen de referencias huérfanas a procesos o presupuestos.
Hay seis expedientes in_review, dos descartados y cero publicados sin revisión válida.
Fuente: consultas SQL de solo lectura a las tablas correspondientes.
El motor actual conserva 432 señales short-tender-window; no se recalibró en esta fase.
Reducir su cantidad no demostraría falsos positivos sin validación humana etiquetada.

El DAG humano exige superar cada compuerta antes de avanzar.
Se solicitó permitir la continuación con brecha declarada mediante pregunta en esta conversación.
Hasta resolver esa condición, los nodos 3-5 y el despliegue integral quedan pendientes.

## Pruebas

- pytest -q: 220 PASS, 100,56 segundos.
- Presupuesto, conectores duales e identidad: 17 PASS dentro de la suite anterior.
- node --test: 12 PASS de periodos y desgloses presupuestales.
- web audit: CONFORME.
- audit_snapshot_parity.py: PASS.
- harvest status: SEACE y MEF activos; sus watermarks tienen instantes diferentes.
- git diff --check: limpio.

Evidencia: salidas de los comandos ejecutados durante esta conversación.
La prueba web regeneró únicamente generated_at del snapshot; se restauró ese artefacto de prueba.
No se afirma paridad SQL de todos los campos sin un EXCEPT bidireccional completo.
No hubo migraciones, borrados de producción, commits, push ni despliegue en esta fase.
