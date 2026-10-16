---
title: Protocolo maestro de remediación de Cajamarca Qhaway
source: ai
generator: codex-gpt-6
generated_at: 2026-10-15
confidence: medium
verified: false
status: draft
---

# Protocolo maestro de remediación de Cajamarca Qhaway

Este SDD dirige la reparación integral del observatorio por riesgos y contratos verificables.
Cada intervención elimina la causa raíz y demuestra que el fallo no reaparece.
Ninguna exposición de datos privados, alerta o escritura de producción se acepta sin evidencia.

## 1. Base y alcance

La auditoría de partida está en
[`2026-10-13-full-project-gap-audit.md`](../audits/2026-10-13-full-project-gap-audit.md).
Las restricciones de producto se establecen en [`constitution.md`](constitution.md).
La revisión constitucional posterior está en
[`2026-10-15-constitutional-v2-gates.md`](../audits/2026-10-15-constitutional-v2-gates.md).
Las evaluaciones iniciales identificaron divergencias entre runtimes, flujos privados,
persistencia, fuentes y visualizaciones; cualquier estado actual no reevaluado queda
**[sin verificar]**.

El alcance incluye los runtimes de Python y Vercel, persistencia y migraciones SQL,
autenticación, revisión humana, denuncias, fuentes oficiales, frontend,
pipeline de datos, pruebas y operaciones de despliegue.
Los datos oficiales o ciudadanos jamás se sustituyen por ejemplos ficticios en producción.

## 2. Invariantes de seguridad y comportamiento

| ID | Invariante | Evidencia mínima para aprobar |
| --- | --- | --- |
| INV-01 | Proteger denuncias y dossiers privados. | API/UI niegan sin sesión. |
| INV-02 | Prohibir credenciales locales de contingencia. | 401 o error cierran el panel. |
| INV-03 | Confirmar persistencia antes de responder éxito. | Fallo no muta estado. |
| INV-04 | Evitar decisiones humanas duplicadas. | SQL atómico y concurrencia. |
| INV-05 | Publicar alertas solo tras revisión humana. | Prueba de decisión y origen. |
| INV-06 | Introducir datos externos al DOM como texto. | Pruebas XSS en lista y detalle. |
| INV-07 | Cerrar fallback sin seguridad o durabilidad. | 503 en rutas afectadas. |
| INV-08 | No inventar datos cuando falta un ID. | 404/sin datos en UI y API. |
| INV-09 | Ejecutar migraciones reproducibles y reversibles. | Ensayo de esquema y RLS. |
| INV-10 | Mantener paridad de contratos entre runtimes. | Pruebas comparativas. |

## 3. Protocolo obligatorio por defecto

1. Registrar hallazgo, ruta, versión y reproducción antes de cambiar código.
2. Dibujar recorrido completo: entrada, validación, servicio, repositorio, salida y consumidor.
3. Identificar causa raíz y todas sus instancias, incluidas rutas de contingencia.
4. Establecer un contrato observable de éxito, rechazo, error y recuperación.
5. Añadir prueba que reproduzca el defecto; comprobar que falla en el estado vulnerable.
6. Aplicar la corrección mínima **estructural** que restaure el contrato en cada capa.
7. Ejecutar pruebas unitarias, integración, seguridad y regresión sobre runtimes afectados.
8. Inspeccionar diff, dependencias, migraciones, rutas y efectos secundarios.
9. Registrar evidencia, anomalías residuales, reversión y compuertas antes del despliegue.
10. Mantener `verified: false` hasta que un humano revise y acepte la evidencia.

Cuando la reparación requiere cambios incompatibles, documentar la decisión en un ADR
**nuevo**, con `status: proposed`; conservar ADR anteriores.
Nunca ejecutar un cambio de base productiva como parte de la mera validación local.

## 4. Orden de intervención

### P0-A. Confidencialidad, autenticación y ejecución segura

**Raíz:** rutas privadas y componentes capaces de continuar sin garantías de identidad.
**Trabajos:** validar credenciales en servidor; eliminar credenciales de ejemplo;
impedir uso de perfil en caché; comprobar expiración, revocación y rotación;
denegar todas las escrituras cuando falta un backend durable;
cerrar rutas privadas del fallback; revisar cabeceras de caché y autorización.
**Cierre:** INV-01, INV-02 y INV-07, con regresiones HTTP y del DOM.

### P0-B. Durabilidad y transiciones de estado

**Raíz:** estado en memoria o respuestas de éxito antes del commit.
**Trabajos:** unicidad por identificador, condiciones SQL de transición,
transacciones en revisiones y alertas, manejo de duplicados e idempotencia;
probar indisponibilidad de base y peticiones concurrentes.
**Cierre:** INV-03, INV-04 e INV-05 sin falsos positivos de éxito.

### P0-C. Escritura segura en la interfaz

**Raíz:** interpolación de datos externos en HTML y bypass local de control de sesión.
**Trabajos:** usar nodos DOM y `textContent`, eventos ligados a objetos ya
validados y prueba de cargas con etiquetas, atributos y caracteres de escape.
**Cierre:** INV-02 e INV-06 en navegador y prueba automatizada.

### P1-A. Migraciones, repositorios y reglas RLS

**Raíz:** posible desalineación entre modelo, persistencia y permisos [sin verificar].
**Trabajos:** enumerar migraciones aplicadas, revisar dependencias y orden;
validar `0010_case_analysis_and_source_evidence.sql` sobre base desechable;
probar RLS con perfiles anónimo, veedor y rol de servicio;
probar constraints, concurrencia y reversión o recuperación por copia.
**Cierre:** INV-09 y matriz de permisos comprobada; aplicar solo previa revisión humana.

### P1-B. Paridad de contratos y fuentes

**Raíz:** coexistencia de implementaciones y datos de respaldo divergentes,
según la [auditoría de brechas](../audits/2026-10-13-full-project-gap-audit.md).
**Trabajos:** inventariar endpoints y estados HTTP, fijar backend autoritativo,
eliminar simulaciones de producción, asegurar origen de evidencia y fechas de corte,
verificar 404/503, cobertura de fuentes y deduplicación.
**Cierre:** INV-08 e INV-10 con suite por entorno.

### P2. Integración web, calidad y operaciones

**Trabajos:** verificar rutas MPA/SPA, enlaces y modales, CSP y scripts inline,
accesibilidad, compilación, lint, métricas, trazas sin datos privados,
monitoreo y recuperación ante degradación.
**Cierre:** pruebas E2E y revisión manual de rutas relevantes sin filtraciones.

## 5. Matriz de evidencia y estado a 2026-10-15

| Bloque | Estado de trabajo | Evidencia revisable | Pendiente |
| --- | --- | --- | --- |
| Fallback | En revisión | `tests/test_fallback_fail_closed.py` | Paridad externa. |
| Denuncias | En revisión | `tests/test_report_persistence_guards.py` | Base real. |
| Alertas | En revisión | `tests/test_review_persistence_guards.py` | Concurrencia. |
| Veedores | En revisión | `src/cajamarca_qhaway/web/server.py` | Revocación. |
| Sesión y XSS | Corregido local | `tests/admin-review-security.test.mjs` | E2E real. |
| Migraciones | [sin verificar] | `scripts/migrations/` | Esquema y RLS. |
| Contratos | [sin verificar] | Auditoría de brechas | Comparar runtimes. |

Las pruebas locales verifican solo los casos que realmente ejecutan.
Un resultado verde de una prueba unitaria no acredita una configuración externa.

## 6. Compuertas de aceptación antes de liberar

- **G0 — alcance:** cada hallazgo tiene severidad, propietario, reproducción y contrato.
- **G1 — seguridad:** todas las rutas privadas fallan cerradas sin identidad válida.
- **G2 — consistencia:** decisiones y denuncias tienen transición durable y atómica.
- **G3 — migraciones:** ensayo de esquema y RLS superado con respaldo verificable.
- **G4 — producto:** `pytest`, JS y E2E pasan sin nuevas regresiones críticas.
- **G5 — datos:** muestras auditadas llevan procedencia y no se inventan resultados.
- **G6 — operación:** alertas, rollback, secretos y permisos revisados por humano.
- **G7 — liberación:** autorización humana explícita antes de migración o despliegue.

Un fallo en G1, G2 o G3 bloquea la liberación.
No se permite rebajar severidad basándose solo en una mitigación visual.

## 7. Estrategia de reversión

Mantener cambios locales sin commit, push, migración productiva ni despliegue.
Para código: aislar diffs por dominio y restaurar únicamente cambios de esta intervención.
Para datos: preparar backup y plan de restauración antes de aplicar DDL irreversible.
Para autenticación: comprobar que la revocación desactiva acceso y existe recuperación
administrativa controlada, sin contraseñas ni claves embebidas en el repositorio.

## 8. Registro de ejecución

Registrar por iteración: fecha, hallazgo, causa raíz, cambios, pruebas,
comando y salida, impacto, incertidumbres, aprobador y decisión final.
Mantener este documento como protocolo y evidencias de cada corrida en `docs/audits/`.
Los estados de esta sección no constituyen aprobación de producción.
