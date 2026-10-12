# TK-305: Herramientas Web Bridge Supabase, Comando CLI y Pruebas E2E

**Estado:** DONE  
**Agente Delegado:** `web-backend-integrator` / `qa-engineer`  
**Épica:** E4 - Plataforma Web Integral, Auditoría y Despliegue Cloud  
**Fecha de Creación:** 2026-10-12  

---

## 1. Descripción
Construir las herramientas de soporte, sincronización y pruebas automatizadas para la plataforma web:
1. **Directorio `web/tools/`**:
   - `web/tools/sync_web_snapshot.py`: Script ejecutable para regenerar `web/src/data/verified-snapshot.json` y sincronizar con la persistencia operativa.
   - `web/tools/validate_web_integrity.py`: Herramienta de auditoría integral que valida existencia de carpetas, cero em-dash (R-02), modelos Pydantic v2 (Art. 19) e invariantes éticos (Art. 10, 14, 15, 16, 18, CA-006-01).
2. **Integración CLI en `cajamarca-qhaway`**:
   - Comando `cajamarca-qhaway web serve [--port 8080]`: Inicia servidor local de desarrollo sirviendo la plataforma web y los endpoints REST JSON.
   - Comando `cajamarca-qhaway web export-snapshot`: Exporta la instantánea verificada a `web/src/data/verified-snapshot.json`.
   - Comando `cajamarca-qhaway web audit`: Ejecuta la auditoría integral de integridad estática y constitucional con retorno 0.
3. **Suite de Pruebas Automatizadas (`tests/test_web_platform.py`)**:
   - 16 pruebas deterministas con `pytest` que verifican:
     * Estructura de archivos de `web/` (`index.html`, `DESIGN.md`, `src/css/`, `src/js/`, `src/data/`, `media/`, `tools/`).
     * Validación de los 6 modelos canónicos de Pydantic v2.
     * Cumplimiento del Artículo 14 (bloqueo de revisores genéricos, solo alertas publicadas en API pública).
     * Cumplimiento del Artículo 15 (explicabilidad algorítmica y descargo legal inmutable).
     * Cumplimiento de CA-006-01 (denuncia requiere descargo previo).
     * Endpoints de API REST (`/api/health`, `/api/entities`, `/api/alerts`, `/api/red-flags`, `/api/reports`, `/api/review`).
     * Comandos CLI `cajamarca-qhaway web export-snapshot` y `cajamarca-qhaway web audit`.

## 2. Criterios de Aceptación
- [x] **CA-305-01**: Herramientas `web/tools/sync_web_snapshot.py` y `exporter.py` generan `web/src/data/verified-snapshot.json` con las 14 entidades, contratos OCDS, registros MEF, banderas rojas, alertas publicadas y denuncias.
- [x] **CA-305-02**: Comandos CLI `cajamarca-qhaway web export-snapshot`, `cajamarca-qhaway web audit` y `cajamarca-qhaway web serve` implementados en `src/cajamarca_qhaway/cli.py` pasando con retorno 0.
- [x] **CA-305-03**: Suite `tests/test_web_platform.py` creada con pruebas ejecutables bajo `pytest`.
- [x] **CA-305-04**: Todas las pruebas en `tests/test_web_platform.py` pasan al 100% (16 tests de validación web y constitucional).
- [x] **CA-305-05**: Verificación de compatibilidad multiplataforma (Windows pwsh y Linux) y cero caracteres em-dash (Antislop R-02).

## 3. Evidencia
- Salida exitosa de `pytest tests/test_web_platform.py` (16 passed in 20.49s).
- Salida exitosa de suite global `pytest` (104 passed in 22.10s).
- Salida exitosa de `cajamarca-qhaway web audit` y `cajamarca-qhaway web export-snapshot`.
- Despliegue Cloud configurado en `vercel.json` y `api/index.py`.
