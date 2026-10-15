---
title: Certificacion operativa del corte MEF 2024-2026
source: ai
generator: codex-gpt-6
generated_at: 2026-10-15T02:57:17.357830Z
confidence: high
verified: false
---

# Certificacion operativa del corte MEF 2024-2026

PostgreSQL autentica y el worker cloud MEF completa su ciclo con persistencia confirmada.
Supabase, spool y snapshot conservan 14 entidades, 475 contrataciones y 42 presupuestos.
SEACE devuelve HTTP 403 desde GitHub; la certificacion global permanece pendiente.

## Datos conciliados

| Predicado | Resultado | Evidencia ejecutada |
|---|---|---|
| Entidades | 14 | contracting_entities y perfiles oficiales SUNAT |
| Contrataciones preservadas | 475 | procurement_records y spool canonico |
| Presupuestos | 42 | budget_execution_records y spool validado |
| Cobertura por ano | 14/14 en 2024, 2025 y 2026 | GROUP BY fiscal_year |
| Paridad presupuestal | 0 diferencias | EXCEPT bidireccional de todos los campos |
| Candidatos privados | 473 | Motor local y UPSERT conservando todos los IDs |
| Paridad de candidatos | 0 diferencias | EXCEPT bidireccional de 473 filas completas |
| Alertas | 6 in_review, 2 discarded, 0 published | GROUP BY status |
| Publicacion automatica | 0 | Arrays publicos de candidatos, alertas y denuncias vacios |

La persona responsable confirmo los codigos observados en el MEF y el linaje de entidades.
Cajamarca provincial usa SEC_EJEC 300549; IDs y RUC canonicos se conservan.
Los 14 perfiles SUNAT conservan payload y fecha de consulta.
Las entidades usan verified_at y la procedencia YAML existente por decision confirmada.

| Ano | PIM (S/) | Devengado (S/) |
|---|---:|---:|
| 2024 | 5,088,605,186 | 4,618,558,165 |
| 2025 | 5,437,828,399 | 5,008,118,791 |
| 2026 | 5,980,488,974 | 3,926,357,702 |

El [modulo mensual MEF](https://apps5.mineco.gob.pe/transparencia/Mensual/)
publica el corte 2026-09-30 preservado en las filas del ejercicio abierto.
La extraccion cloud mas reciente conciliada tiene retrieved_at 2026-10-15T00:20:22.607943Z.
Los candidatos se recalcularon despues de incorporar esa extraccion.

## Worker cloud: resultados por fuente

La conexion usa el pooler confirmado aws-1-ca-central-1.pooler.supabase.com.
El job selecciona el secreto del entorno GitHub Production del proyecto.
El preflight comprueba destino y ausencia de marcadores mediante booleanos, sin revelar valores.

[MEF cloud aprobado](https://github.com/richardsonyelstin-commits/cajamarca-qhaway/actions/runs/38654058445):
14 presupuestos oficiales persistidos, PostgreSQL confirmado y cero archivos spool pendientes.
El catalogo geoespacial verificado contiene cero obras; la evaluacion se omite con SIN COBERTURA.
No se acredita observacion satelital ni se generan obras ilustrativas.

[SEACE en Linux](https://github.com/richardsonyelstin-commits/cajamarca-qhaway/actions/runs/38654365121)
y [SEACE en Windows](https://github.com/richardsonyelstin-commits/cajamarca-qhaway/actions/runs/38673139299)
fallan con HTTP 403 en cuatro intentos por ejecucion.
El mismo cliente identificado recibe localmente HTTP 200 y 20 releases, sin contratos nuevos.
La causa del rechazo remoto no esta determinada; los resultados no prueban un bloqueo geografico.
El cron combinado conserva salida fallida cuando alguna fuente falla.
No se sustituye una respuesta fallida por cobertura ni se avanza el cursor SEACE por ese fallo.

Ante PostgreSQL remoto y spool de emergencia, el daemon falla antes de confirmar el cursor.
Dos pruebas reproducen el error de repositorio y verifican que el cursor permanece intacto.
El workflow muestra brechas ante fallos y exige PostgreSQL y cero spool al verificar persistencia.

## Verificacion del corte

- CI ejecuta 203 pruebas Python y 3 pruebas Node con el snapshot real.
- Pyright y Ruff verifican los modulos modificados de cosecha y persistencia.
- web audit: CONFORME; audit_snapshot_parity.py: PASS.
- audit_accessibility_static.py: PASS en 16 paginas; audit_antislop.py: PASS.
- git diff --check verifica el diff antes de integrar.
- Las compuertas finales y el despliegue se reportan con las ejecuciones finales.

El cliente MPA inicia en 2026 y conserva selecciones historicas explicitas.
PIM y devengado se muestran completos; el avance regional es 65.7%.
Entidades conserva las 14 filas de 2026; San Pablo muestra 25.8% y el umbral critico es 30%.
Los porcentajes de financiamiento ausentes se muestran como Sin datos.

## Limites operativos

El adaptador cloud de denuncias devuelve HTTP 503 hasta disponer de persistencia confirmable.
Las revisiones requieren un adaptador autenticado y persistente.
La fuente SEACE desde GitHub y esas funciones impiden declarar operacion integral completa.

Los spools privados y derivados del chat estan fuera del arbol versionado y del despliegue.
El snapshot publico conserva solo sus conteos agregados.
El historial previo no se reescribio y conserva archivos anteriormente publicados.

Produccion: [Cajamarca Qhaway](https://cajamarca-qhaway.vercel.app).
