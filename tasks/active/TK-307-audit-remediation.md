---
title: "TK-307: Corrección de hallazgos de auditoría de extremo a extremo"
source: ai
generator: codex
generated_at: 2026-10-16T18:10:28.005038+00:00
confidence: medium
verified: false
metadata_reviewed_at: 2026-10-16
---

# TK-307: Corrección de hallazgos de auditoría de extremo a extremo

**Estado:** READY_FOR_STAGING (implementación y verificación local completas; cierre integral pendiente)
**Agentes delegados:** ticket, arquitectura y constructor
**Épica:** E4 - Plataforma web, seguridad y persistencia
**Fecha de creación:** 2026-10-15 (America/Lima)
**Referencia auditada:** `20f4c5ab63efdb2c9d12f76b8b49ab802432bc20`
**Baseline portable:** `docs/audits/2026-10-15-e2e-security-baseline.md`
**Evidencia original de esta instancia:** `/workspace/audit-qhaway/INFORME.md`
**Rama de trabajo:** `agent/codex/audit-remediation`

**Diseño disponible:** [Arquitectura 007](../../docs/architecture/007-audit-remediation-security-consistency.md) y [ADR 0014 propuesto](../../docs/adr/0014-identidad-acreditada-y-consistencia-privada.md). Contratos revisados e implementados con verificación local completa.

**Evidencia de remediación:** [Validación local y límites](../../docs/audits/2026-10-15-remediation-validation.md), con resultados consolidados por coordinación. Esta evidencia no certifica producción ni sustituye staging.

## 1. Descripción y resultado esperado

Corregir los ocho hallazgos reproducidos por la auditoría local. La aplicación debe admitir únicamente identidades configuradas y acreditadas, proteger las respuestas privadas, confirmar escrituras duraderas antes de hacerlas visibles y mantener coherentes las denuncias y sesiones entre instancias.

La auditoría aprobó 216 pruebas Python y 12 Node, pero esas suites no cubrían los escenarios negativos documentados. Este ticket exige regresiones específicas y no considera que aprobar las pruebas anteriores cierre los hallazgos. La evidencia original es local y sintética; no demuestra una explotación ni una configuración concreta en producción.

El ticket no autoriza despliegues, publicación de alertas reales, denuncias reales, rotación de credenciales remotas ni cambios en servicios externos. No se deben copiar valores de credenciales, tokens ni claves a este archivo, las pruebas o sus resultados.

## 2. Hallazgos, evidencia y aceptación falsable

### F01. Crítico: autenticación y clave de firma predeterminadas

- Evidencia: `probes.json` y `auth-and-cache.json`, junto al informe. `src/cajamarca_qhaway/web/server.py` contiene cuentas incorporadas y una clave de firma predeterminada; `api/index.py` replica el patrón. Una cuenta incorporada obtuvo token y una sesión sintética firmada con la constante fue aceptada.
- **CA-307-01a:** sin configuración explícita de identidad, login no emite sesiones de revisor. Las cuentas y contraseñas incorporadas dejan de ser un mecanismo de acceso tanto en el handler canónico como en el fallback.
- **CA-307-01b:** se retiran la firma local y su clave predeterminada. Sin proveedor verificable/configurado, la autenticación devuelve un error controlado y no emite privilegios; no existe clave local alternativa ni se agrega un sistema propio de contraseñas.
- **CA-307-01c:** una identidad sintética acreditada mediante cliente HTTP de pruebas puede iniciar sesión; token rechazado por el proveedor, identidad desconocida, sesión vencida, sujeto discordante, correo sin confirmar, rol desconocido y estructura inválida se rechazan sin acceso privado. El rol editable por el usuario no acredita. Ninguna respuesta o log expone material de autenticación.
- **CA-307-01d:** queda documentado el contrato de Google OAuth mediante Supabase Auth, acreditación administrada y validación remota de cada token. Las pruebas con proveedor simulado se distinguen del flujo OAuth real pendiente de staging; no hay interruptor que habilite usuarios sintéticos en producción.

### F02. Alto: caché compartida de respuestas privadas

- Evidencia: `probes.json`, caso `private_reports_cache`. GET autenticado de `/api/reports` devolvió `Cache-Control: public` con ventana compartida de caché. La clasificación omitía otras rutas privadas y el rewrite `__path`.
- **CA-307-02a:** respuestas de autenticación, denuncias, seguimiento, candidatos y revisión, incluidos errores, usan `Cache-Control: private, no-store` o una política más restrictiva sin caché compartida.
- **CA-307-02b:** toda respuesta a una solicitud autenticada tiene esa protección, aunque la ruta también admita lectura pública.
- **CA-307-02c:** las mismas comprobaciones pasan por WSGI canónico y entrypoint `api/index.py`, con ruta directa y rewrite `__path`. Las rutas públicas sin autenticación conservan únicamente la política pública documentada.

### F03. Alto: publicación antes de confirmar persistencia

- Evidencia: `probes.json`, caso `failed_save_publication`. Un fallo inyectado en `_alert_repo.save` devolvió 503, pero GET `/api/alerts` ya mostraba la alerta. También existía mutación previa en `ReviewPanelService`.
- **CA-307-03a:** al fallar el guardado de una decisión, la API responde con error controlado y ni el servicio de revisión, la instantánea ni GET `/api/alerts` incorporan la decisión o publicación fallida.
- **CA-307-03b:** una decisión válida se hace visible solo después de confirmar su escritura. Una nueva instancia puede recuperar el resultado persistido.
- **CA-307-03c:** repetir la misma solicitud tras éxito o tras un fallo no crea dos alertas ni dos decisiones contradictorias. La arquitectura explicita la clave y el límite de idempotencia; se prueba al menos un reintento.
- **CA-307-03d:** el cambio conserva la revisión humana obligatoria y los campos de evidencia exigidos para publicar una alerta.
- **CA-307-03e:** ante 401/503 del backend, el cliente rechaza la promesa de revisión; no devuelve `success: true`, no agrega una alerta pública local y no comunica publicación exitosa. Una regresión del frontend verifica ambos estados de error.

### F04. Alto: denuncias confirmadas con almacenamiento efímero

- Evidencia: `probes.json`, caso `vercel_report_durability`. Con `VERCEL=1` y sin DSN, el handler canónico devolvió 201 usando SQLite en memoria y una segunda instancia no pudo recuperar la denuncia.
- **CA-307-04a:** en cloud/producción, sin almacenamiento duradero configurado, POST de denuncia devuelve 503 y no entrega una confirmación de recepción ni un código de seguimiento que implique persistencia.
- **CA-307-04b:** un fallo al confirmar escritura tampoco devuelve 201 ni una confirmación equivalente. Ambos entrypoints aplican la misma regla.
- **CA-307-04c:** SQLite en memoria solo se permite en pruebas o desarrollo explícitos. No se considera una base SQLite local garantía de durabilidad serverless.
- **CA-307-04d:** en integración con almacenamiento duradero, una denuncia sintética recibida por una instancia puede consultarse desde otra tras reinicio. La prueba con PostgreSQL real queda pendiente de staging si no hay servicio disponible localmente.

### F05. Alto: denuncias ausentes después de refrescar la instantánea

- Evidencia: `auth-and-cache.json`, caso `persisted_report_after_snapshot_refresh`. GET `/api/reports` quedó vacío al reconstruir el snapshot, aunque el repositorio conservaba la denuncia.
- **CA-307-05a:** el listado autorizado consulta el repositorio privado; una denuncia persistida sigue apareciendo después de reconstruir la instantánea pública y desde otra instancia.
- **CA-307-05b:** el listado permite paginación acotada y filtro por estados válidos con orden estable. Los parámetros inválidos producen un error controlado y no una consulta sin límites.
- **CA-307-05c:** usuarios sin rol autorizado no pueden enumerar denuncias. Ninguna denuncia privada se incorpora al snapshot público ni a su exportación como consecuencia del arreglo.

### F06. Medio: revocación y límites dependientes del proceso

- Evidencia: `auth-and-cache.json`, caso `logout_other_worker`. Tras logout el mismo proceso rechazó el token y otra instancia volvió a aceptarlo. El límite de login también usa memoria de proceso.
- **CA-307-06a:** logout invalida el access token actual en dos instancias que comparten el backend de revocaciones; sigue invalidado después de recrear el proceso hasta que expire. No se declara cierre global de dispositivos ni revocación de refresh tokens; el cliente no reutiliza un refresh token para eludir el cierre.
- **CA-307-06b:** revocaciones/sesiones tienen expiración coherente con el token. Si el backend necesario no está disponible, no se concede acceso basándose solo en un estado local vacío.
- **CA-307-06c:** eliminado el login por contraseñas y su contador local, los límites de inicio OAuth quedan delegados a Google/Supabase. Se documentan y verifican en staging sus límites efectivos alternando clientes/instancias; este criterio permanece pendiente hasta contar con evidencia del proveedor real y no se cierra con mocks.

### F07. Medio: cuerpos JSON con forma inesperada

- Evidencia: `probes.json`, casos `json_shape_list` y `json_shape_int`. POST `[]` y `1` a `/api/auth/login` provocó `AttributeError` en el handler canónico.
- **CA-307-07a:** todos los endpoints que esperan objeto rechazan arrays, números, booleanos, cadenas y `null` con 400/422 controlado antes de acceder a campos. JSON malformado también produce error de cliente.
- **CA-307-07b:** los casos anteriores no lanzan excepción hacia el servidor, no producen 500 ni cierre de conexión y no modifican el estado. Se prueban login, denuncia y revisión en ambos entrypoints.
- **CA-307-07c:** un objeto válido conserva el contrato existente; un cuerpo vacío o campos ausentes reciben la validación documentada.

### F08. Bajo: recursos ausentes con HTML y estado 200

- Evidencia: `probes.json`, caso `missing_static_asset`. GET `/src/js/absent-audit.js` devolvió portada HTML con estado 200 en el servidor Python.
- **CA-307-08a:** un asset inexistente y una página desconocida devuelven 404; un asset JavaScript ausente no recibe la portada con estado 200.
- **CA-307-08b:** las rutas MPA reconocidas, sus enlaces y assets existentes siguen respondiendo correctamente. Las reglas del entrypoint local y de Vercel se verifican por separado; ninguna prueba local se presenta como validación del CDN remoto.

## 3. Dependencias y fases

1. **Contrato y arquitectura:** fijar modo local/producción, provisión de identidad, backend compartido, orden de confirmación y semántica de reintentos. Revisar las specs 005/006 y los ADR vigentes; nuevas decisiones van en ADR `proposed`, sin editar ADR aceptados.
2. **Compuertas de seguridad:** F01 y F02 primero. F06 depende del mecanismo de sesión elegido para F01; no cerrar F01 como seguridad de despliegue si la sesión aún se acepta sin validación compartida necesaria.
3. **Consistencia de escritura y lectura:** F03, F04 y F05 como conjunto. Dependen de un repositorio privado operativo y de un contrato de transacción/confirmación. La paginación de F05 no debe consultar el snapshot público como respaldo.
4. **Entradas y rutas:** F07 y F08 se pueden implementar en paralelo al diseño de persistencia, manteniendo paridad entre handler canónico y fallback.
5. **Regresión local:** ejecutar escenarios negativos, pruebas de dos instancias y suites existentes con datos sintéticos; guardar evidencia reproducible y sin secretos.
6. **Integración de staging:** después del cierre local, usar PostgreSQL real y usuarios sintéticos para validar recepción, reinicio, seguimiento, revisión, logout y caché efectiva. La publicación/despliegue requiere una acción separada autorizada.

## 4. Alcance local y validación de staging

| Área | Verificación local requerida | Verificación pendiente de staging |
|---|---|---|
| Identidad y sesiones | Configuración negativa, rol/token/expiración, login con proveedor simulado, dos instancias y revocación del access token actual | OAuth Google/Supabase real, acreditación administrada, secretos administrados y límites del proveedor (CA-307-06c) |
| Caché | Cabeceras de rutas directas y `__path` en ambos entrypoints | Comportamiento efectivo de Vercel/CDN sin contenido sensible real |
| Persistencia | Fallos de guardado, confirmación, reintentos, repositorio compartido y refresco de snapshot | PostgreSQL real, migraciones/RLS efectivas, reinicio entre instancias |
| Entradas y rutas | JSON de tipo inválido, 404 y regresión MPA | Rewrites y recursos del despliegue de prueba |

La ausencia de credenciales o infraestructura de staging no impide corregir y probar localmente. Debe dejarse el criterio remoto como pendiente, con la operación que falta y su prerrequisito, sin declarar producción certificada. No leer `secrets/`, archivos `.env`, `.pem` o `.key`.

## 5. Matriz de seguimiento

Implementación y validación local completas según la ejecución final independiente de coordinación. La arquitectura 007 y el ADR 0014 continúan propuestos. Los resultados se detallan en el [informe de validación](../../docs/audits/2026-10-15-remediation-validation.md); los criterios remotos siguen abiertos.

| Hallazgo | Severidad | Criterios | Estado de validación | Cambio y evidencia local; pendiente remoto |
|---|---|---|---|---|
| F01 | Crítico | CA-307-01a a 01d | PASS local; OAuth real pendiente | Retiradas cuentas, passwords y firma local; autenticación delegada deniega sin proveedor verificable. `test_web_auth.py`: configuración, token, rol y proveedor simulado. Pendiente OAuth y acreditación reales. |
| F02 | Alto | CA-307-02a a 02c | PASS local; CDN pendiente | Política privada por ruta efectiva y autenticación. Regresiones y comprobación independiente canónica/Vercel/`__path` de caché privada PASS. Pendiente comportamiento efectivo del CDN. |
| F03 | Alto | CA-307-03a a 03e | PASS local; PostgreSQL real pendiente | Confirmación antes de proyecciones; fallo sin publicación, conflicto 409 y reintento idempotente. Reconstrucción de snapshot/nueva instancia recupera publicaciones del repositorio; PostgreSQL es autoritativo incluso vacío y su fallo responde 503. Cliente rechaza 401/503 sin éxito local. |
| F04 | Alto | CA-307-04a a 04d | PASS local; 04d PostgreSQL real pendiente | Cloud/producción sin DB duradera devuelve 503; comprobación independiente y fallback denegando operaciones PASS. Recuperación local probada con almacenamiento sintético; PostgreSQL real y reinicio remoto aún pendientes. |
| F05 | Alto | CA-307-05a a 05c | PASS local; integración PostgreSQL pendiente | Cola, seguimiento y moderación desde repositorio privado; refresco de snapshot no pierde denuncias, con paginación/filtro y autorización. No se exportan denuncias al snapshot público. |
| F06 | Medio | CA-307-06a a 06c | 06a/06b PASS local; 06c pendiente staging | Revocación del token actual entre servicios/conexiones independientes y reconstrucción verificada con SQLite de archivo de pruebas. Pendientes migración 0012 y PostgreSQL reales; límites OAuth no certificados por mocks. |
| F07 | Medio | CA-307-07a a 07c | PASS local | Formas JSON inesperadas y JSON malformado reciben error controlado antes de efectos; regresiones y comprobación independiente canónica/Vercel/`__path` PASS. |
| F08 | Bajo | CA-307-08a a 08b | PASS local; rutas remotas pendientes | Asset/página desconocidos devuelven 404; entrada canónica/Vercel verificada. Chromium carga las 16 rutas conocidas sin errores JavaScript. CDN remoto no verificado. |

### Resultados locales consolidados

- Suite final: **272 pruebas pytest aprobadas** y **20 pruebas Node aprobadas**. Regresiones específicas: `tests/test_audit_remediation.py` (46), `tests/test_web_auth.py` (10) y `tests/audit-remediation.test.mjs` (8), incluidas en esos totales.
- Auditorías web, paridad, accesibilidad estática de 16 páginas, política Unicode y comprobación del diff: PASS.
- Chromium: 16 rutas con HTTP 200 y sin errores JavaScript; ocho comprobaciones móviles a 320/768 px sin desbordamiento horizontal.
- Comprobación independiente de coordinación: canónico, entrypoint Vercel, `__path`, caché privada, JSON inválido, 404, fallback denegando operaciones y producción sin base de datos: PASS.
- La baseline de DOM del login se ajustó únicamente para retirar IDs de campos password eliminados; se conservaron las demás aserciones.
- No se ejecutaron PostgreSQL real, OAuth real, CDN remoto ni aplicación remota de la migración 0012. CA-307-06c continúa pendiente de staging. No se realizaron commits ni despliegues para cerrar esta verificación local.

## 6. Definición de terminado

- [x] Los ocho hallazgos tienen estado explícito, cambio trazable y pruebas específicas; cualquier parte diferida se identifica como pendiente, con motivo y prerrequisito.
- [x] El cierre local cuenta con regresiones nuevas; no se basa únicamente en la suite anterior.
- [x] Suites Python/Node y auditorías web/paridad/accesibilidad/Unicode relevantes aprobadas, con 272/20 pruebas y resultados registrados en el informe enlazado.
- [x] Regresiones ejecutadas mediante handler canónico y fallback, incluida ruta efectiva `__path`, donde corresponde.
- [x] Conservados los invariantes de revisión humana, privacidad, geografía y evidencia; sin publicación ni envío de datos reales.
- [x] Documentación del mecanismo y configuración por nombres de variables actualizada, sin secretos; arquitectura/ADR propuestos enlazados.
- [x] Matriz separada entre cierre local y verificaciones de staging pendientes.
- [x] Comprobación del diff final aprobada según coordinación; sin commits de esta remediación.
- [ ] Verificar PostgreSQL real, migración 0012 y RLS efectiva, recepción/seguimiento/revisión y revocación tras reinicio entre instancias en staging.
- [ ] Verificar OAuth real, acreditación administrada y límites del proveedor (CA-307-06c) en staging.
- [ ] Verificar caché efectiva y rutas del CDN/Vercel remoto con datos sintéticos en staging.
- [ ] Cerrar integralmente el ticket solo después de adjuntar evidencia de los criterios remotos anteriores. READY_FOR_STAGING no significa producción certificada.

## 7. Entregables de coordinación

- Este ticket local es la referencia de aceptación; no se ha creado una issue remota.
- Arquitectura: [documento 007](../../docs/architecture/007-audit-remediation-security-consistency.md) y [ADR 0014 propuesto](../../docs/adr/0014-identidad-acreditada-y-consistencia-privada.md), disponibles para F01-F08 con límites y migración privada de revocaciones. Su existencia no implica aplicación remota de la migración.
- Construcción: implementación y regresiones completadas localmente; evidencia en el [informe de validación](../../docs/audits/2026-10-15-remediation-validation.md). Integración remota pendiente de staging.
- Coordinación final: informe al usuario con correcciones verificadas, resultados y pendientes de staging. El creador de este ticket no cambia código, tests, `docs/INDEX.md`, `CHANGELOG.md` ni realiza commits.

## Actualización documental del 2026-10-16

La última suite completa observada en esta conversación pasó 479 pruebas Python y 25 Node.
Esto reemplaza como estado local actual las cifras de corridas parciales anteriores.
No certifica OAuth, migraciones ni durabilidad entre instancias en staging.
El motor 011 dispone de implementación privada y no sustituye el flujo 004 ni sus dictámenes.
Las observaciones remotas fechadas de esta bitácora no se han vuelto a consultar en esta
actualización documental.
