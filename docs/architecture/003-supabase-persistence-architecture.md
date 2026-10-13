# ARQUITECTURA TÉCNICA INTEGRAL: PERSISTENCIA RELACIONAL EN SUPABASE (PILAR 2)
**Documento Formal**: `docs/architecture/003-supabase-persistence-architecture.md`  
**Proyecto**: Cajamarca Qhaway (`c:\ws\projects\cajamarca-qhaway`)  
**Destino Supabase**: Proyecto `oglltrpvvifqvwmxmkjq` (`us-east-1`, URL: `https://oglltrpvvifqvwmxmkjq.supabase.co`)  
**Autor**: `sdd-architect`  
**Fecha**: 2026-10-12  
**Estado**: `APPROVED_DESIGN`  

---

## 1. Resumen Ejecutivo y Marco Constitucional

La persistencia operativa en Supabase (PostgreSQL 15+) materializa el **Pilar 2** de la arquitectura de Cajamarca Qhaway. Actúa como el sustrato transaccional centralizado para almacenar los 6 modelos canónicos (Artículo 19 de `docs/sdd/constitution.md`) asegurando idempotencia estricta, desacoplamiento de dependencias y resiliencia ante cortes de conectividad mediante spooling local transaccional.

### Invariantes Constitucionales Garantizados
1. **Artículo 10 (Evidencia íntegra y no modificada)**: Los modelos `ProcurementRecord` y `BudgetExecutionRecord` persisten el payload JSON de origen (`raw_payload`) de manera íntegra, byte a byte, en columnas de tipo `JSONB`.
2. **Artículo 14 (Cero alertas automáticas)**: Las tablas `red_flags` y `alerts` están estrictamente segregadas. Un candidato generado por los motores de reglas (`RedFlag`) carece de estado publicable (`CA-004-06`); únicamente la interacción humana formal registrada en `alerts` (`reviewed_by` y `reviewed_at`) habilita la visibilidad al público.
3. **Artículo 15 (Trazabilidad y marcas temporales UTC)**: Todas las marcas de tiempo (`retrieved_at`, `verified_at`, `generated_at`, `reviewed_at`, `published_at`, `submitted_at`, `moderated_at`) se almacenan como `TIMESTAMPTZ` con validación estricta de huso UTC.
4. **Artículo 16 (Prohibición de scoring a personas)**: Los repositorios y esquemas prohíben campos de agregación o scoring dirigidos a personas físicas.
5. **Artículo 18 (Ámbito exclusivo Cajamarca)**: Las restricciones relacionales (`REFERENCES contracting_entities(entity_id)`) y validaciones canónicas aseguran que los datos pertenezcan al universo dorado de 14 entidades verificado.
6. **ADR 0003 & ADR 0006 (PostgreSQL operativo y siembra desacoplada)**: Se desacopla la carga del universo dorado del pipeline operativo, implementando el patrón Repository tipado asíncrono/síncrono sobre `psycopg` v3 (pool de conexiones) sin acoplar módulos de dominio a bibliotecas externas pesadas.

---

## 2. Configuración Tipada de Persistencia (`DatabaseConfig`)

Se implementa en `src/cajamarca_qhaway/persistence/config.py` utilizando **Pydantic v2**:

```python
"""Configuración tipada del subsistema de persistencia en Supabase (Pilar 2)."""

from __future__ import annotations
from pathlib import Path
from pydantic import BaseModel, ConfigDict, Field, SecretStr


class DatabaseConfig(BaseModel):
    """Parámetros de conexión, pool, timeouts y resiliencia para Supabase / PostgreSQL."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    # Conexión a Supabase (Pooler Transaction mode en puerto 6543 o Directo en 5432)
    database_url: SecretStr = Field(
        ...,
        description="DSN de conexión a Supabase (PostgreSQL). Obligatorio vía env CAJAMARCA_QHAWAY_DATABASE_URL.",
    )
    
    # Parámetros del Pool de Conexiones
    min_pool_size: int = Field(default=1, ge=1, le=10, description="Conexiones mínimas en el pool")
    max_pool_size: int = Field(default=10, ge=2, le=30, description="Conexiones máximas en el pool")
    max_idle_seconds: float = Field(default=300.0, ge=10.0, description="Tiempo de vida en reposo")
    connection_timeout_seconds: float = Field(default=10.0, ge=1.0, description="Timeout para adquirir conexión")
    command_timeout_seconds: float = Field(default=30.0, ge=1.0, description="Timeout para sentencias SQL")

    # Resiliencia y Spooling Fallback Local
    spool_enabled: bool = Field(default=True, description="Habilitar fallback a disco local si la BD no responde")
    spool_dir: Path = Field(
        default=Path("data/harvested/spool"),
        description="Directorio de contingencia para registros cosechados pendientes de sincronizar",
    )
    spool_flush_batch_size: int = Field(default=100, ge=1, le=1000, description="Lote de inserción al vaciar spool")
```

---

## 3. Arquitectura del Patrón Repository Tipado

Se formalizan interfaces y repositorios desacoplados para los 6 modelos canónicos en `src/cajamarca_qhaway/persistence/repositories/`:

1. **`EntityRepository` (`contracting_entities`)**:
   - `get_by_id(entity_id: str) -> ContractingEntity | None`
   - `get_by_ruc(ruc: str) -> ContractingEntity | None`
   - `list_active() -> list[ContractingEntity]`
   - `upsert(entity: ContractingEntity) -> None` (Usa `ON CONFLICT (entity_id) DO UPDATE`).

2. **`ProcurementRepository` (`procurement_records`)**:
   - `get_by_id(procurement_id: str) -> ProcurementRecord | None`
   - `get_by_ocid(ocid: str) -> ProcurementRecord | None`
   - `list_by_entity(entity_id: str) -> list[ProcurementRecord]`
   - `upsert_many(records: Sequence[ProcurementRecord]) -> int`:
     - Sentencia SQL con `ON CONFLICT (procurement_id) DO UPDATE SET raw_payload = EXCLUDED.raw_payload, executed_amount = EXCLUDED.executed_amount, retrieved_at = EXCLUDED.retrieved_at`.
     - Preserva `raw_payload` byte a byte mediante serialización nativa JSONB.

3. **`BudgetExecutionRepository` (`budget_execution_records`)**:
   - `get_by_id(execution_record_id: str) -> BudgetExecutionRecord | None`
   - `list_by_entity_year(entity_id: str, fiscal_year: int) -> list[BudgetExecutionRecord]`
   - `upsert_many(records: Sequence[BudgetExecutionRecord]) -> int`:
     - Sentencia SQL con `ON CONFLICT (execution_record_id) DO UPDATE SET budgeted_amount = EXCLUDED.budgeted_amount, executed_amount = EXCLUDED.executed_amount, raw_payload = EXCLUDED.raw_payload, retrieved_at = EXCLUDED.retrieved_at`.

4. **`RedFlagRepository` (`red_flags`)**:
   - `get_by_id(red_flag_id: str) -> RedFlag | None`
   - `list_unreviewed() -> list[RedFlag]`: Cruza con tabla `alerts` para listar candidatos que aún no han sido evaluados en panel humano.
   - `insert_candidates(flags: Sequence[RedFlag]) -> int`: Inserción idempotente `ON CONFLICT (red_flag_id) DO NOTHING`. Jamás incluye columnas de decisión o publicación (`CA-004-06`).

5. **`AlertRepository` (`alerts`)**:
   - `get_by_id(alert_id: str) -> Alert | None`
   - `list_published() -> list[Alert]`: Filtro `status = 'published'` para alimentar visualizadores públicos o endpoints API.
   - `create_from_human_review(alert: Alert) -> None`:
     - Inserta validando que `reviewed_by` no sea genérico y que `disclaimer` coincida exactamente con `STANDARD_ALERT_DISCLAIMER`.

6. **`CitizenReportRepository` (`citizen_reports`)**:
   - `create_report(report: CitizenReport) -> str`: Requiere obligatoriamente `legal_disclaimer_shown = True`.
   - `list_pending_moderation() -> list[CitizenReport]`
   - `update_moderation(report_id: str, status: ModerationStatus, moderator_id: str) -> None`: Actualiza estado exigiendo moderador humano y marca temporal UTC.

---

## 4. Mecanismo de Sincronización, Idempotencia y Spooling Fallback

Para garantizar que el `HarvesterDaemon` (Pilar 1) nunca se bloquee ante latencia o indisponibilidad transitoria de Supabase, se implementa una unidad de sincronización de doble vía (`SyncManager`):

```
                   +----------------------------------+
                   | HarvesterDaemon / Pipeline Step  |
                   +----------------------------------+
                                     |
                                     v
                       +---------------------------+
                       |       SyncManager         |
                       +---------------------------+
                                     |
                       [¿Hay conexión con Supabase?]
                                     |
                    +----------------+----------------+
                    | SÍ                              | NO / Error Red
                    v                                 v
       +-------------------------+      +-------------------------+
       |   Supabase Postgres     |      | Spool Local Atómico     |
       | Transacción Idempotente |      | data/harvested/spool/   |
       +-------------------------+      +-------------------------+
                    ^                                 |
                    |           Daemon Desahogo       |
                    +---------------------------------+
                       (Flush Periódico en Reconexión)
```

---

## 5. Seguridad y Políticas Row Level Security (RLS) en Supabase

Las migraciones aplicadas `0001` a `0004` configuran Row Level Security (RLS) con el principio de mínimo privilegio:

| Tabla | Acceso Público / Anónimo (`anon`, `authenticated`) | Acceso Servicio / Ingesta (`service_role`) |
|---|---|---|
| `contracting_entities` | `SELECT` abierto (Transparencia activa). | `ALL` (Lectura y escritura completa). |
| `procurement_records` | `SELECT` abierto (Transparencia activa de compras). | `ALL` (Upserts idempotentes desde Daemon). |
| `budget_execution_records` | `SELECT` abierto (Transparencia presupuestal). | `ALL` (Upserts idempotentes desde Daemon). |
| `red_flags` | Restringido (`authenticated` solo analistas/revisores). | `ALL` (Ingesta desde Pipeline de Reglas). |
| `alerts` | `SELECT` filtrado estricto: `status = 'published'`. | `ALL` (Comité y panel de revisión). |
| `citizen_reports` | `INSERT` con `WITH CHECK (legal_disclaimer_shown = true)`. Lectura denegada. | `ALL` (Moderación y panel interno). |

---

## 6. Diagrama de Secuencia de Persistencia e Inserción Idempotente

```mermaid
sequenceDiagram
    autonumber
    participant HD as HarvesterDaemon
    participant SM as SyncManager
    participant SP as Local Spooler
    participant DB as Supabase PostgreSQL (oglltrpvvifqvwmxmkjq)

    HD->>SM: sync_procurements(records)
    activate SM
    SM->>DB: BEGIN Transaction (conn from pool)
    activate DB
    alt Conexión Supabase Exitosa
        SM->>DB: INSERT INTO procurement_records ... ON CONFLICT (procurement_id) DO UPDATE
        DB-->>SM: Rows Affected / Acknowledged
        SM->>DB: COMMIT Transaction
        deactivate DB
        SM-->>HD: SyncResult(status="synced", count=N)
    else Fallo de Red / Supabase No Disponible
        DB-->>SM: ConnectionTimeout / OperationalError
        deactivate DB
        SM->>SP: write_atomic_spool(records, path="data/harvested/spool/")
        activate SP
        SP-->>SM: Spooled to disk successfully
        deactivate SP
        SM-->>HD: SyncResult(status="spooled", count=N)
    end
    deactivate SM

    Note over HD,SP: En el siguiente ciclo o al restaurar red:
    HD->>SM: flush_spool()
    activate SM
    SM->>SP: get_pending_spool_files()
    SP-->>SM: [spool_20261012.jsonl]
    SM->>DB: BEGIN & INSERT ... ON CONFLICT DO UPDATE
    DB-->>SM: COMMIT OK
    SM->>SP: unlink(spool_20261012.jsonl)
    deactivate SM
```

---

## 7. Árbol de Módulos Canónico

```text
src/cajamarca_qhaway/
├── persistence/                    # NUEVO: Capa de Persistencia Supabase (Pilar 2)
│   ├── __init__.py
│   ├── config.py                   # DatabaseConfig (Pydantic v2)
│   ├── connection.py               # Pool de conexiones psycopg y context managers
│   ├── sync.py                     # SyncManager con estrategia Spooling Fallback
│   ├── spool.py                    # LocalSpooler (almacenamiento atómico en disco)
│   └── repositories/
│       ├── __init__.py
│       ├── entity_repository.py
│       ├── procurement_repository.py
│       ├── budget_execution_repository.py
│       ├── red_flag_repository.py
│       ├── alert_repository.py
│       └── citizen_report_repository.py
```
