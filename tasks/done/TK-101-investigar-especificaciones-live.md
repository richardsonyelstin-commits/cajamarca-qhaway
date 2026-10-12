# TK-101: Investigar especificaciones live de OECE/SEACE OCDS y MEF DataStore

**Estado:** DONE  
**Agente Delegado:** `tech-researcher`  
**Épica:** E2 - Cosecha Continua de Datos en Vivo  
**Fecha de Cierre:** 2026-10-12  

---

## 1. Descripción
Ejecutar la verificación y caracterización empírica de los endpoints en vivo de Contrataciones Abiertas (OECE/SEACE) y del Portal de Datos Abiertos del MEF para despejar las ambigüedades técnicas abiertas en `specs/002-seace-ingestion/spec.md` y `specs/003-mef-ingestion/spec.md`:
1. **OECE / SEACE OCDS API (`/api/v1/releases`)**:
   - Comprobados parámetros y feed rotativo nacional sin filtro geográfico server-side.
   - Definidos límites de concurrencia (máx 2 semáforos, 3 req/segundo) y User-Agent identificativo.
2. **MEF DataStore API (`api.datosabiertos.mef.gob.pe`)**:
   - Identificado `resource_id` de gasto diario (`35bdc5b5-017c-42c1-ba20-8820bf1248b7`) y filtro departamental `DEPARTAMENTO_EJECUTORA = '06'`.
   - Veto explícito constitucional a Consulta Amigable (`apps5.mineco.gob.pe`).

## 2. Criterios de Aceptación
- [x] Documentar el comportamiento exacto de `/api/v1/releases` (parámetros de paginación, tamaño de respuesta, rate limits observados y ventanas temporales).
- [x] Obtener e identificar el UUID `resource_id` del dataset de ejecución presupuestal del MEF DataStore aplicable al periodo fiscal actual.
- [x] Registrar el esquema JSON completo de columnas y tipos de datos del MEF DataStore con el mapeo explícito hacia `BudgetExecutionRecord`.
- [x] Verificar el soporte y sintaxis exacta de consultas SQL en `datastore_search_sql` para filtrado por departamento o RUC.
- [x] Validar que ninguna prueba ni consulta toque `apps5.mineco.gob.pe` (Consulta Amigable).
- [x] Crear el reporte de evidencia técnica con payloads JSON y especificaciones en la arquitectura.

## 3. Evidencia
- Reporte técnico de scout web y documento de arquitectura `docs/architecture/002-live-harvester-worker.md`.
