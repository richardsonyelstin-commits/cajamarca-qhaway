# TK-201: Esquemas DDL Relacionales, Migraciones y RLS en Supabase

**Estado:** DONE  
**Agente Delegado:** `database-reviewer` / `sdd-architect`  
**Épica:** E3 - Base de Datos Operativa Conectada a Supabase  
**Fecha de Cierre:** 2026-10-12  

---

## 1. Descripción
Desplegar y validar el esquema relacional en PostgreSQL bajo la instancia activa de Supabase (`tiythjlrjhvwkiqsnvwq`) mediante MCP `apply_migration` y `execute_sql`:
1. Aplicar la migración inicial de entidades territoriales (`0001_create_contracting_entities.sql`).
2. Aplicar la migración de las tablas del pipeline de compras, presupuesto, banderas y reportes (`0002_create_pipeline_tables.sql`).
3. Activar y configurar políticas de Row Level Security (RLS) de menor privilegio (`0003_enable_rls_policies.sql`).
4. Sembrar el universo dorado verificado de 14 entidades en `contracting_entities` (`0004_seed_contracting_entities.sql`).
5. Verificar integridad referencial y restricciones CHECK (Artículos 6, 10, 14, 16 y 18).

## 2. Criterios de Aceptación
- [x] Migraciones `0001` a `0004` ejecutadas y verificadas en Supabase (`tiythjlrjhvwkiqsnvwq`).
- [x] 6 tablas canónicas creadas con RLS activo: `contracting_entities`, `procurement_records`, `budget_execution_records`, `red_flags`, `alerts`, `citizen_reports`.
- [x] Tabla `red_flags` sin columna mutable de estado (Art. 14 / CA-004-06).
- [x] Tabla `citizen_reports` con CHECK `legal_disclaimer_shown = TRUE` (CA-006-01).
- [x] Tabla `contracting_entities` sembrada con exactamente 14 entidades provinciales y regional de Cajamarca.

## 3. Evidencia
- Ejecución exitosa de `apply_migration` y `execute_sql` vía Supabase MCP.
- Validación relacional en SQLite y PostgreSQL documentada en `docs/architecture/003-supabase-persistence-architecture.md`.
