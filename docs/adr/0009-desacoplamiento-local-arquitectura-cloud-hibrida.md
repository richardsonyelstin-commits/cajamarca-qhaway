---
id: adr-0009
title: Desacoplamiento del Entorno Local y Adopcion de Arquitectura Cloud Hibrida
type: adr
status: proposed
created: 2026-10-13
updated: 2026-10-13
date: 2026-10-13
deciders: [infrastructure-architect, cloud-engineer]
consulted: [security-officer, backend-lead]
supersedes: null
superseded_by: null
tags: [decision, cloud, infrastructure, vercel, supabase, github-actions, persistence]
source: ai
generator: infrastructure-architect
generated_at: 2026-10-13T14:25:00-05:00
confidence: high
verified: false
decides:
  - cloud-deployment-architecture
  - elimination-of-local-lock-in
  - scheduled-background-harvester-worker
  - relational-persistence-and-sql-dialect-adapter
  - retirement-of-secondary-node-server
---

# Desacoplamiento del Entorno Local y Adopcion de Arquitectura Cloud Hibrida

Se adopta una arquitectura en la nube hibrida desacoplada (Vercel Edge + Supabase PostgreSQL
+ GitHub Actions Harvester Worker) para eliminar definitivamente la dependencia de la maquina
local del desarrollador, retirando el servidor secundario Node.js (Express).

## Contexto y planteamiento del problema

La auditoria tecnica integral de produccion revelo que la plataforma Cajamarca Qhaway mantenia
un severo bloqueo local (*local lock-in*):
1. Los repositorios de persistencia relacional utilizaban exclusivamente comodines `?` de SQLite.
   Al conectarse a Supabase via `psycopg`, las consultas fallaban con error de sintaxis SQL,
   forzando una conmutacion silenciosa a SQLite en memoria (`:memory:`).
2. Las funciones serverless de Vercel son efimeras y carecen de persistencia durable en disco.
   Tanto las denuncias ciudadanas como las decisiones de revision quedaban en memoria volatil o
   en el `localStorage` del cliente.
3. El proceso de recoleccion continua (`HarvesterDaemon`) y la teledeteccion satelital de obras
   dependian 100% de ejecucion manual por CLI en local, y guardaban cursores de tiempo en
   ficheros de disco (`watermarks.json`).
4. Existia un servidor Express secundario (`server.js`) con sesiones en memoria y divergencia de
   endpoints respecto al backend oficial Python.

## Factores de decision

- **Autonomia operativa 24/7:** La cosecha de datos de SEACE, MEF y satelites debe ejecutarse
  de forma programada y autonoma sin requerir intervencion humana ni computadoras encendidas.
- **Persistencia durable y seguridad RLS:** Toda denuncia ciudadana y decision del panel de
  veedores debe quedar protegida y persistida en Supabase con politicas de menor privilegio.
- **Costo operativo cero ($0 USD):** Como observatorio civico regional sin fines de lucro, la
  plataforma debe operar dentro de las capas gratuitas de Vercel, Supabase y GitHub Actions.
- **Mantenibilidad y paridad tecnica:** Unico runtime backend en Python 3.12 (ADR 0001), eliminando
  servidores paralelos duplicados.

## Decision

Se adopta formalmente la arquitectura cloud hibrida (Opcion B):

1. **Frontend y CDN:** Servido globalmente en Vercel Edge con reglas de reescritura limpias y
   encabezados de seguridad HTTP (`X-Frame-Options: DENY`, `nosniff`, CSP).
2. **Backend Serverless API:** `api/index.py` (WSGI PEP 3333) reutiliza la logica canonica de
   `cajamarca_qhaway.web.server` y persiste transaccionalmente en Supabase.
3. **Persistencia Relacional y Adaptador SQL:** `DatabaseManager` incorpora wrappers proxy
   (`PostgresConnectionWrapper`, `PostgresCursorWrapper`) que adaptan transparentemente comodines
   `?` a `%s` y tipos booleanos segun el motor relacional activo (PostgreSQL o SQLite).
4. **Almacenamiento de Cursores en Nube:** Se crea la tabla `harvest_watermarks` en PostgreSQL
   (migracion 0005) para que `WatermarkStore` persista el estado de cosecha en base de datos.
5. **Worker Programado en Nube:** Se implementa un workflow en GitHub Actions
   (`.github/workflows/harvester-cron.yml`) con ejecucion programada cada 2 horas (`0 */2 * * *`)
   que ejecuta `harvest run --once` y `geospatial evaluate --sar` de forma autonoma.
6. **Retiro de `server.js`:** Se elimina definitivamente el servidor Express de Node.js y su
   dependencia en `package.json`, consolidando a Python como el backend unico del proyecto.

## Consecuencias

### Positivas
- Cero dependencia de computadoras locales para cosecha, calculos o almacenamiento.
- Resiliencia completa: datos de denuncias y alertas se conservan de forma permanente.
- Automatizacion desatendida de ingesta y evaluacion satelital cada 2 horas sin costo de servidor.
- Coherencia arquitectonica absoluta con ADR 0001 (Python unico) y ADR 0008 (MPA).

### Negativas
- El worker programado en GitHub Actions tiene una granularidad minima de ejecucion de minutos
  (no es un streaming en tiempo real a nivel de segundo, lo cual es admisible para contrataciones
  publicas que se actualizan diariamente).
