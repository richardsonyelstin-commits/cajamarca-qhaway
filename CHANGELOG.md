---
title: Changelog
source: ai
generator: codex-gpt-6
generated_at: 2026-10-15T02:57:17.357830Z
confidence: high
verified: false
---

# Changelog

Formato [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/).
Versionado [SemVer](https://semver.org/lang/es/).

Se escribe **en el PR**, no en el release: reconstruirlo después es inventarlo.

## [Unreleased]

### Added

- Motor 011 privado con seis reglas exactas, revisión temporal, evidencia y replay canónico.
- CLI exclusiva, shadow desde bytes preservados, pruebas de propiedades, mutación y cobertura CI.

- Propuesta SDD 011 del motor determinista, ADR 0015-0019 y enmienda constitucional para revisión.
- Contratos cerrados, ejemplos sintéticos y pruebas automáticas de coherencia del diseño propuesto.

- Presupuesto por momentos con corte diario, comparacion mensual y desgloses de ambito y rubro.
- Evidencia OECE Pentaho en tabla independiente, enlace exacto a OCDS y cliente JSF con brechas CAPTCHA.
- Identidad Qhaway aplicada a 16 vistas, 88 activos locales y fuentes sin dependencias de CDN.
- Selectores de ano, ambito, rubro y corte, visor de procedencia y filtros contractuales multianuales.
- Pruebas de ortogonalidad, persistencia anidada, fuente/rubro, sesiones JSF y conservacion del DOM.

- Exportación atómica del snapshot desde spools Supabase validados con Pydantic; las cifras iniciales MPA se sincronizan desde el snapshot y la auditoría las compara con metadatos.
- Cosecha verificada de una contratación SEACE del feed oficial, con upsert en Supabase y watermark protegido por RLS.
- Filtro de streaming del padrón reducido oficial SUNAT: solo 198 RUC objetivo (14 entidades y 184 proveedores de adjudicaciones) guardados en `data/sunat/` y sincronizados con `sunat_ruc_profiles`, con filas fuente trazables.
- Migraciones de Supabase para `harvest_watermarks`, perfiles SUNAT filtrados y evaluación única de `auth.jwt()` en políticas de revisores.
- **Arquitectura Cloud Híbrida (ADR 0009):** workflow de GitHub Actions para el harvester y persistencia de watermarks en PostgreSQL.

### Changed

- Documentación vigente reconciliada con MPA/WSGI, persistencia y motores 004/011.
- Índices, roadmap, comandos y estados documentales actualizados; ADR históricos conservados.

- Herramientas 011 agrupadas en scripts/deterministic-engine/ con CI y comandos actualizados.
- Instrucciones canónicas en AGENTS.md; CLAUDE.md queda como entrada de compatibilidad.
- Retirados catorce placeholders .gitkeep y los metadatos Gemini del scaffolding.

- El catálogo primario del conector MEF se trasladó a PNDA; descubre los recursos de gasto 2024-2026 y prioriza sus CSV oficiales. DataStore queda como fallback y los HTTP 404 se registran como brechas sin contar la cosecha vacía como éxito.
- La cola de alertas admite `generated`/`in_review` sin firma; seis publicaciones anteriores sin acta/dictamen verificable en Supabase se regresaron a `in_review`.
- El catálogo geoespacial de producción queda vacío hasta verificar CUI, coordenadas y OCID de obras; se retiraron los sitios ilustrativos.
- La cosecha MEF deja de usar recursos/URLs anuales no comprobados y rechaza importes ausentes en vez de asumir cero.
- El spool del harvester se actualiza por ID determinista y las fallas de PostgreSQL configurado ya no se ocultan con fallback a SQLite.

### Fixed

- Consolidación local de las ramas en main, conservando OAuth, revocaciones y capacidades v2.
- Tipos canónicos, campos SUNAT opcionales y listas de persistencia corregidos; lint sin incidencias.
- Snapshot público filtrado también en contingencia, sin expedientes ni contadores privados.
- Validación JSON uniforme, guardado único de decisiones y moderación condicional durable.
- Tokens malformados rechazados y redirecciones del panel verificadas con el módulo real de sesión.

- El paquete de despliegue instala el driver PostgreSQL necesario para autenticacion, revocaciones y escrituras confirmadas en Vercel.
- La API acredita revisores con Supabase Auth y rol administrado, elimina cuentas de demostracion y registra revocaciones compartidas sin guardar tokens en claro.
- Las respuestas privadas y autenticadas impiden cache compartida, incluso con rewrites de Vercel.
- Denuncias, moderacion y decisiones confirman persistencia antes de actualizar el estado visible; el cliente rechaza fallos del backend sin anunciar exito local.
- El listado de denuncias consulta el repositorio privado con paginacion y filtros; cloud exige almacenamiento PostgreSQL configurado.
- Los cuerpos JSON que no son objetos reciben errores controlados y los recursos estaticos ausentes responden 404.

- El daemon conserva el cursor remoto cuando PostgreSQL falla y deriva registros al spool.
- El worker selecciona el secreto del entorno Production y comprueba destino sin revelar valores.
- El worker expone las brechas de fuente y exige PostgreSQL confirmado y cero spool pendiente.
- El catalogo geoespacial vacio se informa como SIN COBERTURA y omite la evaluacion.
- El dispatch admite runners Linux y Windows; SEACE devuelve 403 en ambos, MEF cloud aprobado.
- Se concilian los 42 presupuestos y 473 candidatos con SQL tras la ultima extraccion MEF cloud.
- El oraculo MPA compara las cifras del ultimo ejercicio y respeta la ausencia de alertas publicadas.
- El extractor MEF rechaza valores ausentes, no finitos o negativos, orden presupuestal invalido y avances porcentuales incoherentes.

- El CLI de cosecha devuelve error cuando MEF no entrega `records` verificables o una solicitud
  histórica no cubre los años solicitados; el cron deja de ocultar estos fallos como éxito.
- El parser MEF ya no asigna unidades ejecutoras distritales a municipalidades provinciales por compartir provincia; exige evidencia explícita del tipo provincial cuando falta un RUC oficial.
- Se corrigió el cruce SIAF de municipalidades provinciales con SEC_EJEC oficiales y UBIGEO de capital; se retiraron de Supabase 15 filas sintéticas y 8 filas distritales, sin modificar las contrataciones SEACE.
- El cursor de cosecha falla de forma explícita ante errores de PostgreSQL y la paginación SEACE sigue `links.next` del paquete OCDS.
- Los perfiles SUNAT dejan de asignar estados “ACTIVO/HABIDO” sintéticos cuando falta una respuesta verificable.
- Se eliminó una credencial Codart escrita en el código; la credencial expuesta requiere rotación en el proveedor.
- Se purgaron 56 filas MEF adicionales de ejecutoras distritales y se conservaron 10 filas MEF de fuente oficial junto a las 475 contrataciones SEACE sin modificarlas.
- El exportador dejó de generar datos de muestra, publicaciones y revisiones humanas simuladas. Las 473 señales calculadas se persistieron como candidatas; la copia pública no contiene alertas sin expediente humano comprobado.
- La nueva cosecha mensual MEF completa 42 filas oficiales: 14 entidades en cada ejercicio 2024-2026, con corte 2026-09-30.

### Removed

- Los spools de candidatos y los derivados del chat dejan de versionarse en el repositorio publico; las copias locales se conservan.

- Se retiro definitivamente el servidor secundario Express de Node.js (`server.js`) y su dependencia en `package.json`, consolidando el runtime canonico exclusivo en Python 3.12 (ADR 0001).

### Fixed

- Se corrigio la caida silenciosa a SQLite en memoria (`:memory:`) cuando se configuraba PostgreSQL/Supabase en los repositorios de persistencia.
- Se corrigio la perdida de denuncias y dictamenes en entornos serverless efimeros.

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
