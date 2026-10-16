---
title: "Despliegue y operación del proyecto"
status: active
updated: 2026-10-16
source: ai
generator: codex
generated_at: 2026-10-16T07:16:00.753518+00:00
confidence: high
verified: false
---

# Despliegue y operación del proyecto

Vercel sirve páginas y API; PostgreSQL conserva estado y GitHub Actions ejecuta cosecha.
Esta guía describe configuración y comprobaciones, no certifica un despliegue remoto nuevo.
El motor 011 permanece privado y no se promueve automáticamente al publicar el sitio.

## Fuentes de configuración

| Componente | Fuente comprobable |
|---|---|
| Python y dependencias | [pyproject.toml](../../pyproject.toml), [uv.lock](../../uv.lock) |
| API y recursos | [vercel.json](../../vercel.json), [api/index.py](../../api/index.py) |
| CI | [ci.yml](../../.github/workflows/ci.yml) |
| Worker cada dos horas y manual | [harvester-cron.yml](../../.github/workflows/harvester-cron.yml) |
| Conector oficial bajo demanda | [official-sources.yml](../../.github/workflows/official-sources.yml) |

CI fija Python 3.12 e instala desde uv.lock con --frozen.
Los workflows de cosecha conservan sus propios comandos de instalación y no se describen
como si ya utilizaran el mismo mecanismo que CI.
requirements.txt sigue en el repositorio como entrada de dependencias para herramientas existentes.
Ese archivo no incluye jsonschema, que sí forma parte del runtime 011 en pyproject.toml.
Para instalar el sistema completo usar el paquete con uv y su lock; no asumir sincronización
automática entre requirements.txt y pyproject.toml.

## Preparación local sin despliegue

```powershell
uv sync --extra dev --frozen
uv run cajamarca-qhaway web serve --port 8080
uv run cajamarca-qhaway web audit
uv run python -m pytest -q
node --test tests/*.test.mjs
uv run python scripts/audit_snapshot_parity.py
uv run python scripts/audit_accessibility_static.py
```

El acceso local es http://localhost:8080/.
Los entrypoints y extras están declarados en pyproject.toml.
La CLI privada 011 se instala como cajamarca-qhaway-engine.

## Configuración externa

CAJAMARCA_QHAWAY_DATABASE_URL contiene la conexión real a PostgreSQL.
SUPABASE_SESSION_POOLER_HOST es opcional y debe corresponder al pooler real si se utiliza.
La identidad usa CAJAMARCA_QHAWAY_SUPABASE_URL y CAJAMARCA_QHAWAY_SUPABASE_ANON_KEY;
[auth.py](../../src/cajamarca_qhaway/web/auth.py) admite también los nombres SUPABASE_URL
 y SUPABASE_ANON_KEY.
La variable pública de Supabase no sustituye la acreditación administrada de un revisor.
No imprimir DSN, tokens o claves en documentación, logs o comandos compartidos.

## Compuertas de operación

Antes de habilitar un entorno, comprobar autenticación real, rol acreditado y revocación.
Comprobar persistencia y reintento entre instancias; una prueba SQLite no cubre ese requisito.
Una denuncia o una decisión no puede confirmarse si no hay almacenamiento duradero.
Comprobar que el snapshot público no exponga candidatos ni denuncias privadas.
Registrar brechas de fuente y el estado del spool de cosecha antes de declarar cobertura.
Las pruebas locales no resuelven CAPTCHA ni garantizan acceso desde un runner remoto.
Los runs y verificaciones fechados anteriores permanecen en audits/ como antecedentes.

## Coexistencia y rollback 011

La publicación del sitio sigue usando el flujo existente y sus controles humanos.
El productor privado 011 puede dejar de invocarse sin borrar ledger ni resultados históricos.
Una promoción requiere las compuertas de spec y política; no se realiza mediante un cambio de README.
No se hizo deploy, migración ni modificación de secretos al actualizar esta documentación.
