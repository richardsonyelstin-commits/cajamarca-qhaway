# TK-103: Implementación del Core Live Harvester Worker

**Estado:** DONE  
**Agente Delegado:** `backend-engineer`  
**Épica:** E2 - Cosecha Continua de Datos en Vivo  
**Fecha de Cierre:** 2026-10-12  

---

## 1. Descripción
Implementar el núcleo del trabajador de cosecha continua en el paquete `src/cajamarca_qhaway/capabilities/live_harvest/` con arquitectura asíncrona y modular:
1. `config.py`: `HarvestConfig`, `SeaceHarvestConfig`, `MefHarvestConfig`, `StorageConfig` con Pydantic v2 inmutable.
2. `backoff.py`: Reintentos exponenciales con Full Jitter.
3. `watermark_store.py`: Cursor atómico two-phase write compatible con Windows y Linux.
4. `coverage_logger.py`: Bitácora JSONL para ventanas de cobertura e incidentes.
5. `seace_poller.py`: Cliente asíncrono con semáforo (2 slots), rate limiting y doble filtrado (Cajamarca + 001).
6. `mef_poller.py`: Consulta a CKAN DataStore con veto constitucional a Consulta Amigable.
7. `daemon.py`: Orquestador concurrente con `run_once`, `run_daemon` y parada limpia.

## 2. Criterios de Aceptación
- [x] Implementar `src/cajamarca_qhaway/capabilities/live_harvest/daemon.py` con ciclo async no bloqueante.
- [x] Implementar `src/cajamarca_qhaway/capabilities/live_harvest/seace_poller.py` cumpliendo CA-002-01 a CA-002-05.
- [x] Implementar `src/cajamarca_qhaway/capabilities/live_harvest/mef_poller.py` cumpliendo CA-003-01 a CA-003-04.
- [x] Implementar `src/cajamarca_qhaway/capabilities/live_harvest/watermark_store.py` con persistencia de watermarks atómica.
- [x] Implementar `src/cajamarca_qhaway/capabilities/live_harvest/coverage_logger.py` para reportar ventanas reales y eventos de falla.
- [x] Tipado estricto y docstrings descriptivos sin errores.

## 3. Evidencia
- Código implementado bajo `src/cajamarca_qhaway/capabilities/live_harvest/`.
- 100% de módulos aprobados por `code-reviewer` y `security-reviewer`.
