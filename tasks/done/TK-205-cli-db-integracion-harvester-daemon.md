# TK-205: Integración CLI y Acoplamiento Transaccional con HarvesterDaemon

**Estado:** DONE  
**Agente Delegado:** `sdd-architect` / `tdd-guide`  
**Épica:** E3 - Base de Datos Operativa Conectada a Supabase  
**Fecha de Cierre:** 2026-10-12  

---

## 1. Descripción
Integrar la capa de base de datos operativa con el CLI principal y el trabajador continuo en segundo plano:
1. Añadir el subcomando `db` al CLI (`src/cajamarca_qhaway/cli.py`):
   - `cajamarca-qhaway db status`: Inspección de modo, tablas y cola de spool.
   - `cajamarca-qhaway db seed`: Siembra del universo verificado de 14 entidades.
   - `cajamarca-qhaway db sync`: Desahogo manual de la cola de contingencia.
2. Inyectar opcionalmente `SyncManager` en `HarvesterDaemon`:
   - Al cosechar releases OCDS del SEACE y ejecuciones del MEF, persistir tanto en particiones locales JSONL como en la base de datos operativa.
   - Ante desconexión o fallo temporal de Supabase, encolar en spool automáticamente sin bloquear el daemon ni abortar el sondeo.

## 2. Criterios de Aceptación
- [x] Subcomando `db` implementado en `src/cajamarca_qhaway/cli.py`.
- [x] `HarvesterDaemon` sincronizado con `SyncManager` en `_persist_records()`.
- [x] Comandos CLI testeados en `tests/test_persistence.py`.
- [x] Comportamiento documentado en `README.md` y `docs/roadmap.md`.

## 3. Evidencia
- Verificación CLI interactiva y pruebas de integración superadas.
- Harvester daemon operando con persistencia transaccional y fallback resiliente.
