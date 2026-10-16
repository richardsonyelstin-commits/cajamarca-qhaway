---
title: Revisión del SDD del motor determinista
source: ai
generator: codex-gpt-6.1-sol
generated_at: 2026-10-16T04:53:54Z
confidence: high
verified: false
---

# Revisión del SDD del motor determinista
Un subagente elaboró la propuesta 011 y cinco ADR; el agente principal revisó sus contratos.
Las pruebas actuales verifican el diseño y sus ejemplos, sin sustituir el motor operativo.
Las decisiones de adopción y calibración quedan explícitas para la implementación posterior.

## Alcance y artefactos

El encargo humano del 2026-10-15 autorizó revisar motor, convenciones y Constitución.
La propuesta vive en `specs/011-deterministic-engine/`; 010 ya estaba asignado a presupuesto.
Se trabajó directamente en main, sin ramas, commits, push ni cambios del runtime.
Comprobación: `git branch --show-current` y `git diff --name-only -- src api web`.

- `spec.md`: 16 reglas de diseño y 16 criterios de aceptación.
- `plan.md`: contratos, selección temporal, aritmética, hashes y migración.
- `tasks.md` y `traceability.json`: 16 cadenas RN, CA, tarea y prueba futura.
- `test-plan.md`: contrato, propiedades, replay, integración, mutación y rendimiento.
- `contracts/`: Request y BatchResult/BatchInvalid con JSON Schema 2020-12.
- `fixtures/`: 28 casos de indicadores, seis de selección, tres canónicos y dos resultados completos.
- ADR 0015-0019: núcleo puro, exactitud, procedencia, política y coexistencia.

Estas referencias identifican propuestas de diseño, no fuentes de afirmaciones sobre producción.
Las seis reglas son descriptivas; sus umbrales no se presentan como obligaciones legales.
El plan dispone explícitamente de las diez reglas heredadas y separa prioridad de expedientes.
La propuesta constitucional v3 está junto a v2, que conserva su vigencia.

## Hallazgos resueltos durante la revisión

| ID | Defecto de diseño detectado | Resolución |
| --- | --- | --- |
| D01 | Número 010 ocupado | Se usa 011 sin duplicar capacidades |
| D02 | Dos proveedores mínimos ocultaban monopolios | Un proveedor y tres procesos; golden explícito |
| D03 | Validación temporal hacía inalcanzable OPEN_FISCAL_YEAR | End futuro se limita a procurement |
| D04 | El patrón de fracción aceptaba menos cero | Numerador canónico y pruebas negativas |
| D05 | El esquema permitía estados y valores contradictorios | Condicionales de estado y reason_code |
| D06 | Solo había ejemplos de indicadores | Se añaden selección, revisión y BatchInvalid |
| D07 | Benchmark grande podía superar el límite del decoder | Medir núcleo y frontera por separado |

Fuentes: cambios de `spec.md`, `plan.md`, schemas, fixtures y `test-plan.md`.
El motor futuro deberá reproducir estos casos; estas pruebas no ejecutan una implementación 011.

## Evidencia de verificación

Comandos Python ejecutados desde el proyecto con `.venv/Scripts/python.exe`.

| Compuerta | Comando | Resultado |
| --- | --- | --- |
| Diseño | `-m pytest tests/test_deterministic_engine_specification.py -q` | 34 pasan |
| Suite previa a la ampliación | `-m pytest -q --tb=short` | 365 pasan |
| Suite final | `-m pytest -q --tb=short` | 372 pasan en 103,37 segundos |
| Node | `node --test tests/*.test.mjs` | 25 pasan |
| Tipos | Pyright sobre src y pruebas del SDD | 0 errores |
| Lint | Ruff sobre src/tests/scripts/api/web/tools | 0 incidencias |
| Web, cifras y accesibilidad | CLI audit y scripts existentes | PASS |
| Dependencias | `-m pip check` y `uv lock --check` | PASS |
| Diff | `git diff --check` | PASS |

Los contratos se comprueban offline con FormatChecker y un registro local de referencias.
Los oráculos usan Fraction, JSON estándar y SHA-256, independientes del motor heredado.
Referencia de la herramienta: [documentación oficial de jsonschema](https://python-jsonschema.readthedocs.io/en/stable/validate/).
jsonschema se incorpora únicamente al extra dev y al lock; no es dependencia de producción.

## Criterio de entrega y siguiente fase

El diseño se entrega propuesto y sin afirmar que el nuevo motor esté implementado.
Sus pruebas futuras tienen nombres y archivos precisos, pero no se marcan como ejecutadas.
La implementación comienza con las tareas RED de 011, conserva el motor 004 en paralelo
y mide diferencias en un entorno privado antes de sustituir cualquier productor.
Las fuentes oficiales, umbrales y capacidades aplazadas requieren la revisión indicada en el SDD.
