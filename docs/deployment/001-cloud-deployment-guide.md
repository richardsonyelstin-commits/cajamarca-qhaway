---
title: Guia de Despliegue Cloud (GitHub, Supabase y Vercel)
status: active
created: 2026-10-12
updated: 2026-10-14
source: ai
generator: codex-gpt-6
generated_at: 2026-10-14T21:50:27.395040+00:00
confidence: high
verified: false
---

# Guia de Despliegue Cloud (GitHub, Supabase y Vercel)

Manual operativo para desplegar y operar Cajamarca Qhaway en la nube de forma 100% autonoma
y desacoplada de la maquina local del desarrollador (ADR 0009).
Combina GitHub Actions, Supabase PostgreSQL (`oglltrpvvifqvwmxmkjq`) y Vercel Serverless Python.
El cron automatiza los intentos de cosecha; la disponibilidad de cada fuente se monitorea aparte.

## 1. Arquitectura de Despliegue Desacoplada

```mermaid
flowchart TD
    GH["GitHub Repo: richardsonyelstin-commits/cajamarca-qhaway"] -->|"Push / PR"| GA_CI["GitHub Actions CI (.github/workflows/ci.yml)"]
    GH -->|"Cron cada 2h / Dispatch"| GA_WORKER["Harvester Worker (.github/workflows/harvester-cron.yml)"]
    GH -->|"CD Deploy automatico"| VC["Vercel Platform (vercel.json)"]
    
    GA_WORKER -->|"Cosecha SEACE/MEF + Sentinel-1/2"| SB["Supabase PostgreSQL (oglltrpvvifqvwmxmkjq)"]
    GA_WORKER -->|"Cursores de tiempo"| WM["Tabla harvest_watermarks"]
    
    VC -->|"Frontend MPA Estatico"| WEB["Vistas Web (web/*.html)"]
    VC -->|"Rutas /api/*"| PY["Vercel Python Function (api/index.py)"]
    
    WEB -->|"Lectura directa PostgREST (anon RLS)"| SB
    PY -->|"Persistencia transaccional de denuncias y revisiones"| SB
```

## 2. Repositorio y Automatizacion en GitHub

- **Repositorio oficial**: `https://github.com/richardsonyelstin-commits/cajamarca-qhaway`
- **Integracion Continua (`.github/workflows/ci.yml`)**:
  1. Instala el paquete en modo editable (`pip install -e ".[dev]"`).
  2. Ejecuta la suite de pruebas completa (suite de pruebas completa del repositorio).
  3. Ejecuta la auditoria de integridad web (`python -m cajamarca_qhaway.cli web audit`).
- **Worker de Cosecha Continua (`.github/workflows/harvester-cron.yml`)**:
  1. Se ejecuta automaticamente cada 2 horas (`0 */2 * * *`) o por disparo manual.
  2. Conecta con Supabase usando `CAJAMARCA_QHAWAY_DATABASE_URL`.
     El job usa el entorno GitHub Production del proyecto cajamarca-qhaway.
     Su secreto de entorno tiene precedencia sobre el secreto del repositorio.
  3. Realiza la cosecha de SEACE OCDS y MEF Consulta Amigable (`harvest run --once`).
  4. Realiza la evaluacion de divergencia fisico-financiera satelital (`geospatial evaluate --sar`).
  5. Persiste cursores de ingesta en la tabla `harvest_watermarks`.

## 3. Base de Datos y Persistencia en Supabase

- **Project ID**: `oglltrpvvifqvwmxmkjq`
- **Endpoint PostgREST**: `https://oglltrpvvifqvwmxmkjq.supabase.co/rest/v1`
- **Migraciones aplicadas (`scripts/migrations/`)**:
  - `0001_create_contracting_entities.sql`: Universo dorado de 14 entidades de Cajamarca.
  - `0002_create_pipeline_tables.sql`: Tablas operativas del pipeline (`procurement_records`,
    `budget_execution_records`, `red_flags`, `alerts`, `citizen_reports`).
  - `0003_enable_rls_policies.sql`: Politicas RLS de menor privilegio.
  - `0004_seed_contracting_entities.sql`: Siembra inicial de las 14 entidades.
  - `0005_harvest_watermarks.sql`: Estado persistente de cursores de recoleccion continua.

### Variables de Entorno de Produccion (GitHub Secrets y Vercel Environment)

Configure en el entorno GitHub Production del proyecto cajamarca-qhaway y en Vercel Production.
El nombre literal del entorno en YAML es `"Production \u2013 cajamarca-qhaway"`.
El escape Unicode evita caracteres prohibidos en el archivo y conserva el entorno existente.

- `CAJAMARCA_QHAWAY_DATABASE_URL`: Cadena transaccional de conexión directa o pooler de Supabase
  (`postgresql://postgres:[PASSWORD]@db.oglltrpvvifqvwmxmkjq.supabase.co:5432/postgres`).
- `SUPABASE_URL`: `https://oglltrpvvifqvwmxmkjq.supabase.co`
- `SUPABASE_ANON_KEY`: Llave publica `anon` protegida por politicas RLS.
- `CAJAMARCA_QHAWAY_AUTH_SECRET`: Secreto criptografico para tokens de veedores acreditados.

## 4. Despliegue en Vercel (`vercel.json` + `api/index.py`)

- **Capa Estatica (`web/`)**: Vistas MPA (`index.html`, `entidades.html`, `alertas.html`,
  `contrataciones.html`, `presupuesto.html`, `proveedores.html`, `denuncia.html`,
  `georreferenciacion.html`, `acerca.html`, `login.html`, `admin-revision.html`).
- **Capa Serverless (`api/index.py`)**: Endpoints WSGI (`/api/health`, `/api/snapshot`,
  `/api/entities`, `/api/procurements`, `/api/budget`, `/api/alerts`, `/api/red-flags`,
  `/api/reports`, `/api/review`, `/api/geospatial/works`, `/api/geospatial/divergence`).
- **Seguridad HTTP**: Encabezados `nosniff`, `X-Frame-Options: DENY` y `Referrer-Policy`.

## 5. Operacion y Monitoreo Desatendido

Al no depender del entorno local:
1. Las denuncias ciudadanas emitidas por la web se guardan de forma permanente en Supabase.
2. Las alertas aprobadas por veedores acreditados impactan inmediatamente en la nube.
3. El workflow del Harvester intenta cosechar cada 2 horas. Cada fuente debe devolver una
   respuesta estructuralmente válida; el CLI termina con código distinto de cero ante fallos,
   de modo que GitHub Actions marque el ciclo fallido.
4. La configuración del cron no demuestra que una fuente haya entregado filas. Consultar
   `harvest status` y `harvest gaps`; no presentar una respuesta sin filas como cobertura.
5. El modulo mensual oficial MEF entrega 42 filas para 2024-2026, con corte 2026-09-30.
   La cobertura se verifica por ejercicio y por entidad antes de sincronizar datos.
   Supabase conserva 475 contrataciones, 42 presupuestos y 473 candidatos privados.
   El snapshot publico muestra cero alertas publicadas y el total privado en metadatos.
   Comprobar `harvest status`, `web audit` y `python scripts/audit_snapshot_parity.py`.
   La fuente primaria verificable es
   [Consulta de Ejecucion del Gasto del MEF](https://apps5.mineco.gob.pe/transparencia/Mensual/Navegar_6.aspx?y=2026&ap=ActProy).

### Conexion del worker desde una red IPv4

El run de produccion del 2026-10-14 fallo antes de ingerir datos porque el runner no alcanza
la direccion IPv6 del host PostgreSQL directo.
[Evidencia del worker](https://github.com/richardsonyelstin-commits/cajamarca-qhaway/actions/runs/38644858333).

Supabase recomienda su Session pooler para redes IPv4.
[Documentacion oficial](https://supabase.com/docs/guides/database/connecting-to-postgres).
Obtener el hostname exacto en el panel Connect del proyecto; no deducirlo de la region.
Configurar la variable del repositorio GitHub `SUPABASE_SESSION_POOLER_HOST` con ese hostname.
El worker conserva el secreto `CAJAMARCA_QHAWAY_DATABASE_URL` y cambia solo host, puerto 5432
y el usuario con sufijo de proyecto para la conexion de sesion.
La validacion admite exclusivamente hosts oficiales `.pooler.supabase.com`.

Sin esa variable, la conexion conserva el DSN original y sus errores siguen siendo visibles.
Un despliegue Vercel Ready y CI verde no acreditan por si solos que el worker haya ingerido datos.
Despues de configurar el host, ejecutar el workflow y verificar cosecha, cursores y conteos SQL.
