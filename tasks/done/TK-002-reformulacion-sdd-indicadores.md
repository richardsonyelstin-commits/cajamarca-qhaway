# TK-002: Reformulación SDD y Ampliación del Catálogo de Banderas Rojas

**Estado:** DONE  
**Agente Delegado:** `sdd-reformulator` & `execution-engineer`  
**Épica:** E2 - Evolución de Especificaciones y Reglas de Negocio  
**Fecha de Cierre:** 2026-10-12  

---

## 1. Descripción
Incorporar en la arquitectura SDD y en el motor de detección dos nuevas tipologías de riesgo identificadas en las discusiones reales del chat municipal de WhatsApp:
1. `direct-administration-equipment-rent`: Cobro indebido o facturación simulada hacia RDR por uso de maquinaria propia en obras por administración directa.
2. `contract-splitting-orders`: Fraccionamiento en órdenes consecutivas de compra o servicio menores a 8 UIT a un mismo proveedor para eludir licitaciones públicas.

Elevar el catálogo activo de 5 a 7 indicadores, preservando el rango constitucional `[5, 10]` (`CA-004-01`).

## 2. Criterios de Aceptación
- [x] Actualización de `catalog.py` con 7 indicadores activos con fórmula y umbral.
- [x] Implementación de los evaluadores en `engine.py`.
- [x] Pruebas unitarias de los 2 nuevos indicadores en `test_red_flags_engine.py`.
- [x] 63/63 pruebas pasando sin regresiones.

## 3. Evidencia
- `tests/test_red_flags_engine.py` pasando al 100%.
- Handoff M3 formal completado.
