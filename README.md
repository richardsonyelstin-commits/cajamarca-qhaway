---
title: "Cajamarca Qhaway"
status: active
updated: 2026-10-16
source: ai
generator: codex
generated_at: 2026-10-16T07:14:27.989761+00:00
confidence: high
verified: false
---

# Cajamarca Qhaway

Plataforma cívica para revisar contrataciones y presupuestos de entidades de Cajamarca.
El servidor público y el panel privado conviven con el motor heredado 004 y el núcleo 011 privado.
Implementación local, aprobación documental y certificación productiva son estados distintos.

## Inicio local

Python 3.12 es la referencia de CI; el paquete declara Python >=3.12.
Instalar las dependencias fijadas y consultar los comandos disponibles:

```powershell
uv sync --extra dev --frozen
uv run cajamarca-qhaway --help
uv run cajamarca-qhaway web serve --port 8080
```

Abrir http://localhost:8080/.
El servidor y la aplicación WSGI se implementan en
[src/cajamarca_qhaway/web/server.py](src/cajamarca_qhaway/web/server.py).
Node se usa para las pruebas del cliente; no existe un router hash SPA activo.

## Estructura

| Ruta | Contenido |
|---|---|
| `src/cajamarca_qhaway/` | Modelos, capacidades, persistencia, servidor y CLI |
| `web/`, `api/` | Páginas HTML, recursos locales y entrada WSGI de Vercel |
| `tests/` | Pruebas Python, Node, contratos y regresiones |
| `specs/` | Requisitos, planes, contratos JSON y vectores sintéticos |
| `scripts/` | Herramientas; [índice de comandos](scripts/README.md) |
| `scripts/deterministic-engine/` | Generación, cobertura, mutación y benchmark 011 |
| `docs/` | [Documentación y registros históricos](docs/INDEX.md) |
| `data/` | Fuentes preservadas y datos operativos; parte del contenido es privado |
| `context/snapshots/` | Evidencia de corridas y contexto generado |
| `identidad-qhaway/` | Originales usados por las pruebas de integridad de marca |
| `tasks/` | Pendientes activos y antecedentes completados |

## Dos motores con usos diferentes

El catálogo heredado tiene diez reglas y sigue conectado al pipeline existente:
[catálogo 004](src/cajamarca_qhaway/capabilities/red_flags_engine/catalog.py).
El nuevo núcleo tiene seis reglas, dinero exacto, revisiones, cobertura e identidad reproducible:
[implementación 011](src/cajamarca_qhaway/capabilities/deterministic_engine/engine.py).

```powershell
uv run cajamarca-qhaway catalog
uv run cajamarca-qhaway-engine request.json private-result.json
```

request.json es un Request engine-2 completo, no el envoltorio de las fixtures.
La salida debe ser un archivo nuevo; la CLI no sobrescribe resultados existentes.
El modo shadow exige payloads preservados y un mapa explícito:
[contrato de entrada](specs/011-deterministic-engine/contracts/shadow.schema.json).
No se han migrado automáticamente aprobaciones, prioridad ni publicaciones de 004 a 011.
Los detalles de uso están en la [guía técnica 011](docs/audits/2026-10-16-deterministic-engine-implementation.md).

## Pruebas y verificaciones

```powershell
uv run python -m pytest -q
node --test tests/*.test.mjs
uv run cajamarca-qhaway web audit
uv run python scripts/audit_snapshot_parity.py
uv run python scripts/audit_accessibility_static.py
uv run python scripts/deterministic-engine/generate-deterministic-contracts.py --check
```

La última ejecución completa de esta conversación fue el 2026-10-16: 479 Python y 25 Node.
Es evidencia local; no acredita el estado actual de servicios remotos.
Los comandos y dependencias comprobables están en [pyproject.toml](pyproject.toml),
[uv.lock](uv.lock) y [CI](.github/workflows/ci.yml).

## Persistencia, despliegue y privacidad

PostgreSQL usa CAJAMARCA_QHAWAY_DATABASE_URL y el driver psycopg del paquete.
Configurar valores reales mediante el gestor de entorno del despliegue; no incluirlos en notas.
La autenticación usa Supabase Auth e identidades acreditadas.
Las escrituras privadas requieren durabilidad; un fallo no se confirma como guardado.
Consultar la [guía de despliegue](docs/deployment/001-cloud-deployment-guide.md).

Cada señal debe conservar fuente, fecha y fórmula, y pasar por revisión humana antes de publicarse.
Los umbrales exploratorios de 011 no se presentan como límites legales.
Los presupuestos de años, cortes y granularidades diferentes no se suman implícitamente.
No se puntúa a personas ni se transforma una denuncia ciudadana en evidencia verificada.

## Gobierno y estado

[AGENTS.md](AGENTS.md) es la entrada canónica; CLAUDE.md es su adaptador de compatibilidad.
Se trabaja directamente en main por instrucción del propietario.
La Constitución v2 permanece vigente y la enmienda v3 de 011 continúa propuesta.
Los ADR existentes conservan sus estados y firmas originales.
[Mapa de capacidades](specs/README.md), [arquitectura](docs/architecture/overview.md)
y [roadmap](docs/roadmap.md) separan código disponible y compuertas pendientes.
