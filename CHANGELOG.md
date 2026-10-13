# Changelog

Formato [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/).
Versionado [SemVer](https://semver.org/lang/es/).

Se escribe **en el PR**, no en el release: reconstruirlo después es inventarlo.

## [Unreleased]

### Fixed

- Se ejecutó auditoría WCAG 2.1 AA sobre las 15 páginas y se documentaron hallazgos pendientes
  de etiquetas de formulario, jerarquía de encabezados y contraste de estados.
- Se unificó la carga de tokens, estilos principales y componentes en las 15 páginas HTML.
- Se añadieron enlaces de salto, foco visible, objetivos táctiles mínimos, reducción de movimiento
  y una escala coherente de tipografía, color, bordes y superficies.
- Se eliminaron gradientes del skeleton y se corrigieron los estilos heredados para modo oscuro,
  estados de alerta y compatibilidad responsive.
- El frontend prioriza el snapshot servido por `/api`, con datos vivos de Supabase cuando
  `SUPABASE_URL` y `SUPABASE_ANON_KEY` están configuradas en el backend.
- Las denuncias y decisiones de revisión usan primero los endpoints del backend, y conservan
  el respaldo local únicamente ante fallos de red.
- Los KPI ya no muestran cifras sintéticas cuando la fuente real está vacía.

### Added

- **Pilar 3: Plataforma Web Integral, Auditoría y Despliegue Cloud (`web/` y `cajamarca_qhaway.web`)**:
  - Mapa de sitio y arquitectura de información (`docs/architecture/004-sitemap-cajamarca-qhaway.md`) y arquitectura técnica web (`docs/architecture/005-web-platform-architecture.md`, `docs/adr/0007-arquitectura-plataforma-web-hibrida.md`).
  - Dirección de diseño formal (`web/DESIGN.md`) bajo estándares `antislop` y `antislop-ui` (identidad Observatorio Cívico Andino, alto contraste WCAG 2.2 AA en modo claro y oscuro, tipografía con propósito y modo ligero rural).
  - Carpeta integral de plataforma `web/` conteniendo `index.html`, `src/css/` (`tokens.css`, `main.css`, `components.css`), `src/js/` (`config.js`, `supabase-client.js`, `state.js`, `router.js`, `views.js`, `explicabilidad.js`, `export-csv.js`, `denuncias.js`, `review-panel.js`, `app.js`), `src/data/verified-snapshot.json`, `media/` (`brand-mark.svg`, `cajamarca-map.svg` con las 13 provincias, `architecture-flow.svg`) y `tools/` (`sync_web_snapshot.py`, `validate_web_integrity.py`).
  - Puente backend Python (`src/cajamarca_qhaway/web/server.py` y `exporter.py`), comandos CLI `cajamarca-qhaway web` (`serve`, `export-snapshot`, `audit`) y configuración Serverless para Vercel (`vercel.json`, `api/index.py`).
  - Suite de pruebas deterministas de plataforma web en `tests/test_web_platform.py` (104/104 pruebas totales pasando).
  - Tickets `TK-301` a `TK-306` formalizados.
- **Pilar 2: Base de Datos Operativa Conectada a Supabase (`persistence`)**:
  - `DatabaseConfig` (`config.py`): Configuración tipada en Pydantic v2 con secreto protegido `SecretStr` para la URL de Supabase y validación de límites de pool y spooling.
  - `DatabaseManager` (`connection.py`): Gestor de conexiones desacoplado con soporte híbrido para PostgreSQL/Supabase en producción y SQLite en memoria para tests y contingencia sin red.
  - `LocalSpooler` (`spool.py`): Cola atómica en disco para desvío de registros en caso de desconexión o fallo en la base remota, con prevención estricta de `WinError 32` en Windows.
  - Repositorios tipados (`repositories/`): Implementación para los 6 modelos canónicos (`EntityRepository`, `ProcurementRepository`, `BudgetExecutionRepository`, `RedFlagRepository`, `AlertRepository`, `CitizenReportRepository`) con inserciones idempotentes (`ON CONFLICT`) y preservación byte a byte de `raw_payload` (Art. 10).
  - `SyncManager` (`sync.py`): Coordinador transaccional con siembra determinista (`seed_universe_entities`), desvío a spool local y función de desahogo (`flush_spool`).
  - Despliegue en Supabase: Migraciones `0001` a `0004` aplicadas vía Supabase MCP, políticas Row Level Security (RLS) de menor privilegio activadas en todas las tablas y 14 entidades sembradas.
  - Extensiones CLI en `cajamarca-qhaway db`: subcomandos `status`, `seed` y `sync`.
  - Integración del `HarvesterDaemon` con `SyncManager` para persistencia continua y contingencia transparente.
  - Suite de pruebas de persistencia en `tests/test_persistence.py` (88/88 pruebas globales pasando).
  - Documento arquitectónico `docs/architecture/003-supabase-persistence-architecture.md` y tickets completados `TK-201` a `TK-205` en `tasks/done/`.
- **Pilar 1: Cosecha Continua de Datos en Vivo (`live_harvest`)**:
  - `HarvesterDaemon` (`daemon.py`): Servicio asíncrono en segundo plano con soporte para ciclo continuo (`--daemon`) y corridas puntuales (`--once`), con gestión de señales `SIGINT` y `SIGTERM` para parada ordenada (graceful shutdown) en Windows y POSIX.
  - `SeacePoller` (`seace_poller.py`): Recolector asíncrono para OECE / SEACE OCDS (`/releases`), con semáforo acotado a 2 peticiones concurrentes, tasa de 3 req/s, reintentos exponenciales con Full Jitter (`backoff.py`), doble filtrado geográfico e institucional contra el universo 001, deduplicación idempotente por `ocid` y preservación íntegra de `raw_payload` (Art. 10).
  - `MefPoller` (`mef_poller.py`): Recolector asíncrono para el Portal de Datos Abiertos del MEF vía API CKAN DataStore (`datastore_search`), con filtro departamental `DEPARTAMENTO_EJECUTORA = '06'` y veto constitucional inquebrantable a Consulta Amigable (`apps5.mineco.gob.pe`, RN-003-01 / CA-003-01).
  - `WatermarkStore` (`watermark_store.py`): Persistencia atómica de cursores y marcas de agua mediante patrón Two-Phase Write (`.tmp` + `os.replace` con cierre previo de descriptores seguro para Windows).
  - `CoverageGapLogger` (`coverage_logger.py`): Registro auditable append-only en JSONL de ventanas temporales reales muestreadas (RN-002-06) e incidentes de red (RN-002-07 / RN-003-06) sin degradación silenciosa.
  - Extensiones CLI en `cajamarca-qhaway harvest`: subcomandos `run`, `status` y `gaps`.
  - Suite de pruebas de contrato y resiliencia en `tests/test_live_harvest.py`.
  - Documento de arquitectura técnica `docs/architecture/002-live-harvester-worker.md` y tickets completados `TK-101` a `TK-105` en `tasks/done/`.

## [0.1.0] - 2026-10-12

### Added

- Culminacion de la arquitectura y capacidades de Fase 1:
  - Seis contratos canonicos compartidos (Articulo 19 de `docs/sdd/constitution.md`):
    `ContractingEntity`, `ProcurementRecord`, `BudgetExecutionRecord`, `RedFlag`, `Alert`, `CitizenReport`.
  - Capacidad 002 `seace-ingestion`: Parser e ingesta de releases OCDS de OECE/SEACE con filtro de departamento Cajamarca y matching de universo de entidades.
  - Capacidad 003 `mef-ingestion`: Ingesta y normalizacion de ejecucion presupuestal del MEF (CKAN datastore).
  - Capacidad 004 `red-flags-engine`: Catalogo activo de 5 indicadores anticorrupcion (CA-004-01) y motor de deteccion con explicabilidad completa y prohibicion de scoring a personas.
  - Capacidad 005 `review-panel`: Compuerta humana infranqueable (Art. 14), servicio de publicacion y descarte de alertas con descargo inmutable y notas de descarte.
  - Capacidad 006 `denuncia-intake`: Servicio de recepcion de denuncias con obligatoriedad de confirmacion de aviso legal (CA-006-01) y maquina de estados de moderacion.
  - Pipeline orquestador (`pipeline.py`) y entrypoint de linea de comandos (`cajamarca-qhaway`).
  - Suite de 61 pruebas automatizadas (contrato, unitarias y end-to-end) con 100% determinismo.
- Implementacion inicial de `001-entity-mapping`: corpus dorado de 14 entidades en `data/entities/cajamarca-universe.yaml`, algoritmo de `entity_id` y script de siembra a PostgreSQL (ADR 0006).

### Changed

### Deprecated

### Removed

### Fixed

### Security
