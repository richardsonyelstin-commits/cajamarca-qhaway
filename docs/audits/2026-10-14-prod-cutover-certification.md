---
title: Certificacion operativa del corte MEF 2024-2026
source: ai
generator: codex-gpt-6
generated_at: 2026-10-14T22:10:05.581654+00:00
confidence: high
verified: false
---

# Certificacion operativa del corte MEF 2024-2026

El corte presupuestal y la paridad de datos estan verificados.
CI y el sitio de produccion estan en verde; el worker cloud requiere actualizar la credencial PostgreSQL guardada.
No se declara certificacion global PASS mientras esa compuerta siga fallida.

## Datos verificados

| Predicado | Resultado | Evidencia ejecutada |
|---|---|---|
| Entidades | 14 | Consulta contracting_entities y cruce con sunat_ruc_profiles |
| Contrataciones preservadas | 475 | COUNT procurement_records y spool canonico |
| Presupuestos | 42 | COUNT budget_execution_records |
| Cobertura por ano | 14/14 en 2024, 2025 y 2026 | GROUP BY fiscal_year |
| Paridad de presupuestos | 0 diferencias | EXCEPT bidireccional con jsonb_populate_recordset |
| Candidatos | 473 | Motor local, UPSERT y EXCEPT contra Supabase |
| Paridad de candidatos | 0 diferencias en 473 filas | Verificacion de todos los lotes |
| Huerfanos | 0 | Referencias presupuestales JSONB contra tabla fuente |
| Alertas | 6 in_review, 2 discarded, 0 published | GROUP BY status |
| Linaje de entidades | 14 perfiles oficiales completos | RUC, verified_at, raw_payload, queried_at |

La persona responsable confirmo el mapa oficial MEF y la procedencia existente de entidades.
Cajamarca provincial usa SEC_EJEC 300549; los IDs y RUC canonicos se conservan.
El [modulo mensual MEF](https://apps5.mineco.gob.pe/transparencia/Mensual/)
publica el corte 2026-09-30 conservado en cada fila.

## Verificacion local

- `pytest -v`: 190 pruebas aprobadas antes del ajuste optativo de pooler.
- Suite de corte en CI: 196 pruebas Python y 3 pruebas Node aprobadas.
- Guardia de conexion: 27 pruebas locales de persistencia, incluidas cinco nuevas comprobaciones.
- Persistencia y WSGI: 25 pruebas locales aprobadas tras corregir el parser libpq.
- Pyright: 0 errores en extractor, exportador, oraculo y configuracion/conexion de persistencia.
- Ruff: sin errores en esos modulos y las nuevas pruebas del extractor.
- `web audit`: CONFORME.
- `audit_snapshot_parity.py`: PASS para el ultimo ejercicio, sin sumar tres presupuestos anuales.
- `audit_accessibility_static.py`: PASS en 16 paginas.
- Antislop: 0 U+2014 en el arbol versionable; `git diff --check` limpio.

## GitHub y Vercel

[PR 3 integrado](https://github.com/richardsonyelstin-commits/cajamarca-qhaway/pull/3).
[CI de main aprobado](https://github.com/richardsonyelstin-commits/cajamarca-qhaway/actions/runs/38644855774).
Los PR 3, 4 y 5 estan integrados en main, commit 4764283.
[CI final aprobado](https://github.com/richardsonyelstin-commits/cajamarca-qhaway/actions/runs/38647722454).
Vercel publico el corte en produccion, deployment dpl_BZK5tPqHMT4VKTzwcHLfBhqAELJY, Ready.
[Plataforma publica](https://cajamarca-qhaway.vercel.app).
Las quince rutas MPA comprobadas devuelven HTTP 200 con nosniff y X-Frame-Options DENY.
El snapshot remoto coincide en conteos con la copia local y omite candidatos y denuncias.
Las tres ramas anteriores se retiraron despues de comprobar que sus commits estaban en main.

## Compuerta pendiente

[Worker fallido](https://github.com/richardsonyelstin-commits/cajamarca-qhaway/actions/runs/38644858333):
`psycopg.OperationalError`, conexion IPv6, Network is unreachable.
El fallo sucede antes de la cosecha; no se oculta ni se sustituye por SQLite.

La opcion `SUPABASE_SESSION_POOLER_HOST` usa el secreto DSN existente sin imprimirlo.
El host confirmado es `aws-1-ca-central-1.pooler.supabase.com`.
Ya esta configurado en GitHub y Vercel Production.
El worker alcanza el pooler IPv4 y Supabase rechaza la credencial guardada.
[Evidencia de autenticacion](https://github.com/richardsonyelstin-commits/cajamarca-qhaway/actions/runs/38646425183).
La persona responsable debe actualizar el secreto en ambos destinos sin compartirlo por chat.
[Supabase documenta la alternativa IPv4](https://supabase.com/docs/guides/database/connecting-to-postgres).
Tras configurarlo se debe ejecutar otra vez el worker y cotejar sus cursores y conteos SQL.

### Credencial de entorno y diagnostico seguro

El 2026-10-14T22:40:17Z se actualizo el secreto del entorno GitHub Production del proyecto.
El secreto del repositorio permanecia actualizado al 2026-10-13T19:38:12Z.
El worker ahora referencia el entorno existente para seleccionar la credencial vigente.
Vercel se redesplego con su configuracion de produccion y termino Ready.

[La guardia cloud](https://github.com/richardsonyelstin-commits/cajamarca-qhaway/actions/runs/38649917865)
confirma proyecto, usuario, pooler y base de datos correctos, con `password_placeholder: true`.
La ejecucion se detiene antes de autenticarse mientras la URL conserve el marcador de ejemplo.
El responsable debe sustituirlo por la contrasena PostgreSQL real y codificarla para URI.
La guardia imprime exclusivamente booleanos; cinco pruebas comprueban el bloqueo y la no exposicion.

## Hidratacion del cliente MPA

El navegador mostro un cambio de 65.7% a 82.1% al sumar tres ejercicios.
El cliente ahora selecciona 2026 por defecto y conserva consultas historicas explicitas.
Dos pruebas Node con el snapshot real verifican PIM 5,980,488,974 y devengado 3,926,357,702.
El formato de los KPIs conserva importes completos antes y despues de la hidratacion.
El navegador de produccion confirma ambos importes, 65.7% y las 14 filas del ejercicio 2026.
San Pablo conserva 25.8%; el filtro de subejecucion usa el umbral de 30%.
La vista Entidades inicia en 2026 y permite consultar los ejercicios anteriores explicitamente.
Se retiraron porcentajes de canon constantes sin evidencia y la mencion a SEDACAJ del universo.
El comparativo describe el presupuesto total disponible, sin atribuirlo solo a obras o canon.
El fallback cloud rechaza denuncias sin persistencia confirmable con HTTP 503.

## Limite del saneamiento de Git

Los spools de candidatos y los derivados del chat dejaron de estar en el arbol versionado.
Las copias locales se conservan e ignoran; el snapshot publico contiene solo metadatos de conteo.
El historial previo no se reescribio y sigue conservando los archivos antes publicados.
