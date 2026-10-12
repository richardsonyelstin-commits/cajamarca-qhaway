# TK-102: Arquitectura y especificación técnica del Harvester Daemon / Background Worker

**Estado:** DONE  
**Agente Delegado:** `system-architect`  
**Épica:** E2 - Cosecha Continua de Datos en Vivo  
**Fecha de Cierre:** 2026-10-12  

---

## 1. Descripción
Diseñar y especificar la arquitectura del servicio en segundo plano (Harvester Daemon / Worker) encargado de la recolección continua, tolerante a fallos e idempotente de datos de SEACE y MEF:
1. Ciclo de Ejecución Asíncrono con `asyncio.TaskGroup` y pollers desacoplados.
2. `WatermarkStore` con persistencia atómica en dos fases (Two-Phase Write).
3. `CoverageGapLogger` con bitácora append-only en JSONL.
4. Resiliencia y Full Jitter con backoff exponencial.

## 2. Criterios de Aceptación
- [x] Especificación formal del ciclo de vida del worker daemon, estados del scheduler y aislamiento entre tareas de polling de SEACE y MEF.
- [x] Diseño del modelo de datos y persistencia transaccional del `WatermarkStore`.
- [x] Diseño del modelo de auditoría `CoverageGapLogger` garantizando trazabilidad de ventana horaria real y fallas.
- [x] Especificación de la estrategia de reintentos (exponential backoff + jitter) y políticas de rate limit.
- [x] Aprobación formal de `plan-critic` y preservación estricta de contratos canónicos.

## 3. Evidencia
- Especificación formal en `docs/architecture/002-live-harvester-worker.md` auditada y aprobada.
