---
title: Guia de Despliegue Cloud (GitHub, Supabase y Vercel)
status: active
created: 2026-10-12
updated: 2026-10-13
source: ai
generator: infrastructure-architect
generated_at: 2026-10-13T14:26:00-05:00
confidence: high
verified: false
---

# Guia de Despliegue Cloud (GitHub, Supabase y Vercel)

Manual operativo para desplegar y operar Cajamarca Qhaway en la nube de forma 100% autonoma
y desacoplada de la maquina local del desarrollador (ADR 0009).
Combina GitHub Actions, Supabase PostgreSQL (`oglltrpvvifqvwmxmkjq`) y Vercel Serverless Python.

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
  2. Ejecuta la suite de pruebas completa (143 pruebas deterministas).
  3. Ejecuta la auditoria de integridad web (`python -m cajamarca_qhaway.cli web audit`).
- **Worker de Cosecha Continua (`.github/workflows/harvester-cron.yml`)**:
  1. Se ejecuta automaticamente cada 2 horas (`0 */2 * * *`) o por disparo manual.
  2. Conecta con Supabase usando `CAJAMARCA_QHAWAY_DATABASE_URL`.
  3. Realiza la cosecha de SEACE OCDS y MEF SIAF DataStore (`harvest run --once`).
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

Configure en la configuracion del repositorio GitHub y en el dashboard de Vercel:

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
3. El Harvester de GitHub Actions mantiene actualizada la base de datos cada 2 horas.
4. El observatorio opera con costo $0 USD de infraestructura mensual.
