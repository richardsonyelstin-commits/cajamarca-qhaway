# TK-004: Persistencia y Sincronización Operativa en Base de Datos

**Estado:** DONE  
**Agente Delegado:** `execution-engineer`  
**Épica:** E4 - Operatividad de Almacenamiento y Plataforma  
**Fecha de Cierre:** 2026-10-12  

---

## 1. Descripción
Establecer la persistencia relacional operativa para los 6 contratos canónicos de Fase 1:
1. Esquema DDL en `scripts/migrations/0001_create_contracting_entities.sql` y `scripts/migrations/0002_create_pipeline_tables.sql`.
2. Cobertura completa de constraints: cheques de departamentos, RUCs de 11 dígitos, JSONB para `raw_payload`, compuertas de notas obligatorias para alertas descartadas y rechazo de revisores genéricos.
3. Respetar ADR 0003 (PostgreSQL sobre SQLite) y ADR 0006 (siembra desacoplada).

## 2. Criterios de Aceptación
- [x] Esquema DDL SQL en `scripts/migrations/` cubriendo los 6 contratos.
- [x] Índices relacionales en claves foráneas y búsquedas frecuentes (RUC, OCID, entidad).
- [x] Inmutabilidad y constraints de integridad referencial.

## 3. Evidencia
- `scripts/migrations/0001_create_contracting_entities.sql`
- `scripts/migrations/0002_create_pipeline_tables.sql`
