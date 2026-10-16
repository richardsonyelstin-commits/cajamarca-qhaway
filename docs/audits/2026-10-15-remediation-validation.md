# Verificacion local de TK-307

Fecha: 2026-10-15, America/Lima. Rama: `agent/codex/audit-remediation`.
Base auditada: `20f4c5ab63efdb2c9d12f76b8b49ab802432bc20`.
Estado: implementacion verificada localmente, **READY_FOR_STAGING**.

## Entregables

- [Ticket TK-307](../../tasks/active/TK-307-audit-remediation.md).
- [Arquitectura 007](../architecture/007-audit-remediation-security-consistency.md).
- [ADR 0014 propuesto](../adr/0014-identidad-acreditada-y-consistencia-privada.md).
- [Auditoria previa](2026-10-15-e2e-security-baseline.md).

Los tres agentes crearon el ticket, concretaron arquitectura/autenticacion e
implementaron la correccion. Coordinacion reviso contratos, integro documentacion
y ejecuto una validacion independiente. No se realizaron commits, despliegues,
rotaciones de credenciales ni escrituras contra servicios de produccion.

## Resultados finales

| Comprobacion | Resultado |
|---|---|
| `.venv/bin/python -m pytest -q` | 272 aprobadas, 0 fallos |
| `node --test tests/*.test.mjs` | 20 aprobadas, 0 fallos, 0 omitidas |
| `python -m cajamarca_qhaway.cli web audit` | CONFORME |
| `python scripts/audit_snapshot_parity.py` | PASS |
| `python scripts/audit_accessibility_static.py` | PASS, 16 paginas |
| `python scripts/audit_antislop.py` | PASS |
| `git diff --check` | PASS |
| Chromium, 16 rutas publicas y de acceso | HTTP 200, sin errores JavaScript |
| Inicio, contratos, presupuesto y denuncias a 320/768 px | 8 comprobaciones sin desbordamiento horizontal |
| Entrada WSGI canonica y Vercel, rutas directas y `__path` | Privadas sin cache compartida; JSON no objeto 400; assets ausentes 404 |
| Fallback sin dependencias operativas | No emite autenticacion ni confirma escrituras privadas |
| Produccion declarada sin almacenamiento duradero | Recepcion de denuncias responde 503 |
| Servidor reiniciado con el codigo final | Health, 14 entidades y login responden 200; modulo ausente responde 404 |

Los comandos Python se ejecutaron con `.venv/bin/python` desde el checkout.
Se preservaron los bytes del snapshot publico durante las pruebas. La propia
prueba de exportacion ahora restaura el archivo mediante `finally`.

## Evidencia de correccion

| Hallazgo | Cambio y regresion |
|---|---|
| F01 | Sin cuentas de demostracion, passwords locales ni HMAC predeterminado. Supabase verifica identidad, correo confirmado y rol administrado reviewer; metadatos editables por usuario no autorizan. |
| F02 | Politica `private, no-store` por ruta efectiva, escrituras, errores y Authorization; pruebas de ambos entrypoints y rewrites. |
| F03 | Preparacion sin mutacion global, commit previo a proyeccion, reintento idempotente y conflicto 409. Fallos no publican ni alteran el servicio. API recupera alertas y solo sus RedFlags desde DB despues de reconstruir cache/handler; PG es autoritativo incluso vacio y su fallo responde 503. |
| F04 | Cloud requiere PostgreSQL para confirmar; errores de guardado no entregan recibo. El navegador no confirma recepcion local tras fallos remotos. |
| F05 | Cola privada desde repositorio, orden estable, filtros y paginacion acotada. El panel carga las paginas sin depender del snapshot publico. |
| F06 | Hash del access token revocado en tabla compartida, commit antes de confirmar logout. Prueba con conexiones e instancias independientes y reconstruccion; fallos de backend no autorizan ni confirman cierre. |
| F07 | Validacion de objeto JSON antes de despacho; arrays, escalares, booleanos, null y JSON malformado reciben error controlado. |
| F08 | Recursos y paginas ausentes responden 404; rutas MPA validas conservadas. |

Las 56 pruebas Python adicionales se distribuyen entre
`tests/test_audit_remediation.py` (46) y `tests/test_web_auth.py` (10).
`tests/audit-remediation.test.mjs` agrega 8 casos de confirmaciones fallidas,
perfiles cacheados, logout y respuestas canonicas. Las pruebas no sustituyen
credenciales reales ni habilitan identidades sinteticas en el servidor.

El contrato DOM de login migra deliberadamente a OAuth: conserva formulario y
boton, incorpora mensaje de error y retira controles/atributos de credenciales
de demostracion. Se actualizo exclusivamente esa parte del baseline; la prueba
de anclas de las demas paginas sigue intacta.

## Limites antes de despliegue

- Aplicar la migracion privada `0012_auth_revocations.sql` en un entorno de prueba
  y verificar permisos del usuario operativo, RLS y mantenimiento por expiracion.
- Configurar Supabase Auth/Google, redireccion OAuth y rol reviewer administrado.
  El backend necesita URL HTTPS, clave publica y DSN PostgreSQL; solo se documentan
  nombres, no se crean valores ni usuarios acreditados automaticamente.
- Validar PostgreSQL real, persistencia tras reinicio, OAuth completo y revocacion
  entre trabajadores remotos. Las pruebas locales usan proveedor simulado y datos
  sinteticos; no certifican disponibilidad de servicios externos.
- Comprobar los limites de OAuth del proveedor y la cache efectiva de Vercel/CDN.
  CA-307-06c sigue pendiente de staging. Logout revoca el access token actual;
  no equivale a cierre global de dispositivos ni revocacion de refresh tokens.
- La API con PostgreSQL autoritativo falla con 503 ante lectura no verificable.
  La lectura offline del frontend conserva su fallback de snapshot publico;
  no se acredita frescura remota de ese snapshot ni un mecanismo nuevo de retiro.
- El ADR permanece proposed y el ticket no se cierra de forma integral hasta
  completar los criterios remotos. No se ha desplegado ni publicado el cambio.

Las salidas de esta instancia se conservan en
`/workspace/audit-qhaway/remediation/`: resultados JSON, JUnit, logs de comandos y
smoke de navegador. La comprobacion independiente de entrypoints esta en
`/workspace/audit-qhaway/remediation-entrypoints.json`. Son artefactos locales,
no requisitos para ejecutar las regresiones incorporadas al repositorio.

## Preparacion posterior para staging

Al preparar el despliegue se detecto que el driver PostgreSQL solo figuraba en
un extra opcional. Se incorporo a las dependencias de runtime y al manifiesto
Vercel, actualizando el lockfile sin cambiar versiones de paquetes. Una instalacion
base separada sin extras pudo importar psycopg y el handler canonico y servir
las 14 entidades. El entorno Supabase indicado comparte la referencia documentada
de produccion; la publicacion de un Preview no demuestra aislamiento ni permite
dar por ejecutadas las pruebas remotas pendientes.
