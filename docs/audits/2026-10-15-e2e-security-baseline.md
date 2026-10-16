---
title: "Auditoría base de extremo a extremo de Cajamarca Qhaway"
source: ai
generator: codex
generated_at: 2026-10-16T18:10:28.005038+00:00
confidence: medium
verified: false
metadata_reviewed_at: 2026-10-16
---

# Auditoría base de extremo a extremo de Cajamarca Qhaway

Fecha: 15 de octubre de 2026, America/Lima.
Commit: `20f4c5ab63efdb2c9d12f76b8b49ab802432bc20`.

Estado histórico: auditoría previa a las correcciones en `agent/codex/audit-remediation`. Los resultados siguientes describen el commit auditado, no el estado posterior a la remediación.

## Dictamen

La aplicación permite explorar la instantánea y sus pruebas de regresión pasan. Hay fallos reproducibles que impiden recomendar su uso en producción para recibir denuncias sensibles y publicar decisiones de revisión sin corregirlos primero. Esta auditoría no certifica el despliegue remoto.

Se identificaron **8 hallazgos: 1 crítico, 4 altos, 2 medios y 1 bajo**. Las comprobaciones de seguridad se ejecutaron exclusivamente contra procesos locales y repositorios sintéticos en memoria. No se publicaron alertas ni se enviaron denuncias a producción.

## Hallazgos priorizados

### F01. Crítico: autenticación con credenciales incorporadas y clave predeterminada conocida

Ubicación: [server.py:103](../../src/cajamarca_qhaway/web/server.py:103), [server.py:146](../../src/cajamarca_qhaway/web/server.py:146). El fallback duplica este patrón en `api/index.py`.

La lista de veedores incluye contraseñas literales transformadas mediante SHA-256 al cargar el módulo. El login de una cuenta incorporada devuelve HTTP 200 y un token, sin una comprobación externa de acreditación. Además, cuando falta `CAJAMARCA_QHAWAY_AUTH_SECRET`, se utiliza una constante del código. Una sesión sintética firmada con esa constante fue aceptada por `/api/auth/session` como válida, sin pasar por login.

Impacto: suplantación de revisores, acceso a funciones privadas y posibilidad de emitir decisiones en nombre de una identidad inventada. Configurar una clave de firma por sí solo no elimina las cuentas incorporadas. No se verificó qué configuración utiliza el despliegue remoto.

Corrección: eliminar las credenciales incorporadas; usar un proveedor de identidad o almacén de usuarios acreditados con derivación segura de contraseñas. Rechazar el arranque de producción sin una clave fuerte administrada y validar identidad, rol y estructura de cada sesión.

Evidencia: `probes.json`, `auth-and-cache.json`.

### F02. Alto: respuestas privadas anunciadas como caché pública

Ubicación: [server.py:1151](../../src/cajamarca_qhaway/web/server.py:1151).

Una solicitud WSGI autenticada a `/api/reports`, con contenido privado sintético, respondió HTTP 200 con `Cache-Control: public, max-age=0, s-maxage=60, stale-while-revalidate=300`. La clasificación solo excluye explícitamente `/api/red-flags` y `/api/auth/session`; también deja fuera la cola de revisión y el seguimiento de denuncias. Los rewrites con `__path` se deben considerar al clasificar la ruta efectiva.

Impacto: autoriza a cachés compartidas a almacenar contenido privado. No se demostró una filtración real a través del CDN; dependerá de su configuración y tratamiento de Authorization y de los parámetros de seguimiento.

Corrección: `private, no-store` para toda respuesta autenticada, denuncias, seguimiento y revisión; clasificar según la ruta efectiva y comprobar las cabeceras mediante el entrypoint de Vercel.

Evidencia: `probes.json`, `private_reports_cache`.

### F03. Alto: publicación visible aunque falle la persistencia

Ubicación: [server.py:995](../../src/cajamarca_qhaway/web/server.py:995), [server.py:1000](../../src/cajamarca_qhaway/web/server.py:1000).

La decisión se agrega a la instantánea compartida antes de ejecutar `_alert_repo.save`. Al inyectar un fallo en ese guardado, POST `/api/review` respondió 503 pero GET `/api/alerts` devolvió una alerta publicada. La decisión también se registra antes en la memoria de `ReviewPanelService`.

Impacto: una operación informada como fallida puede aparecer públicamente, carecer de persistencia y desaparecer después. Los reintentos pueden introducir decisiones duplicadas o contradictorias.

Corrección: persistir y confirmar la transacción antes de actualizar o invalidar la caché y el estado del servicio. Asegurar idempotencia y que una escritura fallida no tenga efectos visibles.

Evidencia: `probes.json`, `failed_save_publication`.

### F04. Alto: denuncias confirmadas sin almacenamiento duradero cuando falta el DSN

Ubicación: [connection.py:34](../../src/cajamarca_qhaway/persistence/connection.py:34), [server.py:768](../../src/cajamarca_qhaway/web/server.py:768).

Sin `CAJAMARCA_QHAWAY_DATABASE_URL`, `DatabaseManager` crea SQLite `:memory:`. Con `VERCEL=1` y ese repositorio local, el handler canónico respondió 201 al recibir una denuncia; otra instancia de DatabaseManager no pudo recuperarla. El control que devuelve 503 en cloud está en el fallback de `api/index.py`, pero no protege el handler canónico cuando importa correctamente.

Impacto: pérdida de denuncias al reciclar un proceso serverless o atender el seguimiento en otra instancia. Un DSN remoto correctamente configurado evita esta ruta concreta; no se verificó su presencia en producción.

Corrección: exigir almacenamiento duradero para confirmar recepción en producción y devolver 503 cuando no esté configurado o no pueda confirmar escritura. Reservar SQLite en memoria a pruebas y desarrollo explícitos.

Evidencia: `probes.json`, `vercel_report_durability`.

### F05. Alto: denuncias persistidas desaparecen del listado de revisión al refrescar la instantánea

Ubicación: [server.py:579](../../src/cajamarca_qhaway/web/server.py:579), [server.py:208](../../src/cajamarca_qhaway/web/server.py:208).

GET `/api/reports` devuelve exclusivamente `snapshot.citizen_reports`. La instantánea pública del disco no contiene denuncias y la caché se reconstruye al vencer su plazo de 30 segundos. Se guardó una denuncia sintética, se simuló esa reconstrucción y el listado devolvió cero elementos mientras el repositorio aún conservaba la denuncia. El seguimiento sí dispone de una búsqueda adicional en el repositorio; el listado no.

Impacto: los revisores dejan de ver denuncias realmente recibidas, incluso con el guardado resuelto.

Corrección: consultar el repositorio privado para el listado autorizado, con paginación y filtro de estados; mantener esa información fuera de la caché del snapshot público.

Evidencia: `auth-and-cache.json`, `persisted_report_after_snapshot_refresh`.

### F06. Medio: cierre de sesión limitado a un proceso

Ubicación: [server.py:150](../../src/cajamarca_qhaway/web/server.py:150), [server.py:761](../../src/cajamarca_qhaway/web/server.py:761).

La revocación vive en un set global. Tras logout, el token se rechazó en el mismo proceso; al simular otro trabajador con una lista de revocaciones vacía, volvió a aceptarse. El token tiene una vigencia predeterminada de ocho horas.

Impacto: logout no garantiza revocación en despliegues con múltiples instancias o después de un reinicio. El límite de intentos de login presenta una dependencia similar de memoria local.

Corrección: almacenar revocaciones/sesiones en un almacén compartido o utilizar el mecanismo del proveedor de identidad, con expiración y límites distribuidos.

Evidencia: `auth-and-cache.json`, `logout_other_worker`.

### F07. Medio: JSON válido con tipo inesperado rompe el handler canónico

Ubicación: [server.py:359](../../src/cajamarca_qhaway/web/server.py:359), [server.py:702](../../src/cajamarca_qhaway/web/server.py:702).

Se deserializa JSON sin exigir un objeto. POST de `[]` o `1` a `/api/auth/login` provoca AttributeError sin capturar al ejecutar `.get`. Esto se reprodujo invocando el handler WSGI canónico. El wrapper de `api/index.py` tiene su propio fallback y su respuesta ante esta excepción puede diferir; no se afirma que todos los despliegues respondan 500.

Impacto: entradas válidas a nivel JSON causan errores internos o cierres de conexión en el servidor local en lugar de respuestas controladas.

Corrección: validar el cuerpo mediante un modelo de entrada u objeto JSON y responder 400/422 ante tipos no admitidos antes del despacho.

Evidencia: `probes.json`, `json_shape_list`, `json_shape_int`.

### F08. Bajo: recursos inexistentes responden HTML con estado 200

Ubicación: [server.py:1038](../../src/cajamarca_qhaway/web/server.py:1038).

GET `/src/js/absent-audit.js` devolvió HTTP 200 y `text/html` con la portada. La resolución estática usa `index.html` para cualquier archivo ausente.

Impacto: oculta enlaces o assets rotos, dificulta la monitorización y produce errores de MIME en módulos. La comprobación se refiere al servidor Python local; las reglas estáticas de Vercel pueden comportarse de otra manera.

Corrección: devolver 404 para recursos y páginas desconocidos; conservar únicamente las rutas MPA reconocidas.

Evidencia: `probes.json`, `missing_static_asset`.

## Validación realizada

| Área | Resultado observado |
|---|---|
| pytest | 216 aprobadas, 0 fallos; XML de resultados adjunto |
| Node | 12 aprobadas, 0 fallos, 0 omitidas |
| Auditoría web del repositorio | CONFORME |
| Paridad HTML y snapshot | PASS |
| Accesibilidad estática | PASS, 16 páginas; no equivale a una certificación WCAG completa |
| Política Unicode del proyecto | PASS |
| Chromium | 16 rutas cargadas con HTTP 200, sin errores pageerror de JavaScript |
| Adaptación de pantalla | Sin desbordamiento horizontal en inicio, contrataciones, presupuesto y denuncias a 320/768 px; 16 rutas sin desbordamiento a 1440 px |
| Flujos interactivos | Directorio a ficha de entidad, contrato a expediente, búsqueda sin resultados y cambio a ejercicio 2024: verificados |
| Inyección DOM exploratoria | El título sintético con un img/onerror no ejecutó código en la vista de contrataciones probada; no prueba ausencia global de XSS |
| API e instantánea | 14 entidades, 475 contratos, 42 presupuestos, 0 alertas publicadas y 0 denuncias públicas |
| Integridad de datos | 0 contratos con entidad desconocida y 0 IDs de contratación duplicados |
| Distribución fiscal | 14 entidades únicas en cada año 2024, 2025 y 2026 |
| PIM/devengado 2026 | S/ 6,011,280,694 / S/ 4,006,118,779, coincide con el corte documentado |
| RLS versionada | Las migraciones 0006/0008 restringen la lectura de denuncias y candidatos al rol reviewer; no se verificó su aplicación remota |

El conjunto pytest incluye el pipeline de detección, revisión y moderación con datos sintéticos. Las pruebas que aprueban actualmente no cubren los casos negativos de autenticación, caché privada, fallos de persistencia y múltiples trabajadores descritos aquí. Los scripts exploratorios recopilan resultados; su exit code 0 no significa que el comportamiento de seguridad sea correcto.

## Límites y trabajo pendiente

- No se conectó a PostgreSQL/Supabase de producción ni se inspeccionaron secretos. No se verificaron las políticas efectivas, roles del DSN, restauración de copias de seguridad o migraciones contra un PostgreSQL real.
- No se invocó el harvester ni se extrajeron nuevos datos oficiales. El acceso actual a SEACE, MEF, OECE y la configuración de GitHub Actions/Vercel quedan sin validar en vivo.
- El navegador bloqueó destinos externos para mantener las pruebas locales. No se validaron autenticación federada, mapas remotos ni componentes dependientes de terceros.
- El catálogo de obras de la instantánea está vacío: no se acreditó monitoreo satelital operativo de obras.
- No se efectuó un análisis de CVE de dependencias, una prueba de carga o una auditoría legal. Las cifras verificadas son coherentes con los archivos del repositorio; no se cotejaron de nuevo con portales oficiales.
- El código, manifiestos y lockfiles permanecen sin cambios. La prueba de exportación regenera el snapshot; se preservaron y restauraron sus bytes originales mediante finally.

## Orden recomendado de remediación

1. Resolver F01 y F02 antes de habilitar acceso a datos sensibles.
2. Resolver conjuntamente F03, F04 y F05 para garantizar confirmaciones duraderas y colas de revisión consistentes.
3. Resolver F06 y F07 con pruebas de múltiples trabajadores y entradas inválidas.
4. Resolver F08 y validar de nuevo el entrypoint serverless, las cabeceras y la navegación.
5. Realizar después una prueba de integración en un entorno de staging con PostgreSQL real y usuarios sintéticos, verificando recepción, reinicio, seguimiento, revisión y persistencia sin publicar datos reales.

## Evidencias de la instancia de auditoría

Las evidencias exploratorias originales se conservan fuera del checkout, en `/workspace/audit-qhaway/`: `pytest.xml`, `pytest.txt`, `node.txt`, `probes.json`, `auth-and-cache.json`, `browser.json`, `flows.json`, los scripts correspondientes y capturas. Esos archivos son locales a esta instancia y no forman parte del repositorio ni de una garantía de restauración remota.

La corrección debe incorporar regresiones deterministas en `tests/` que cubran estos casos sin depender de esos artefactos locales. Las comprobaciones de publicación y denuncias solo utilizan datos sintéticos; no se ejecutan en producción.
