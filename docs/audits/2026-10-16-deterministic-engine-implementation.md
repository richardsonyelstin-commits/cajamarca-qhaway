---
title: Implementación privada del motor determinista 011
source: ai
generator: codex-gpt-6
generated_at: 2026-10-16T05:18:45.198249+00:00
confidence: high
verified: false
---

# Implementación privada del motor determinista 011

Las seis reglas 011 están implementadas en un núcleo puro con entrada y salida cerradas.
La ejecución privada conserva identidad, procedencia y coexistencia con el motor 004.
Las pruebas técnicas pasan; la calibración y la adopción productiva requieren evidencia propia.

## Alcance aplicado

El propietario autorizó implementar el SDD y sus decisiones en la conversación del 2026-10-16.
El trabajo se realizó directamente en main, sin nuevas ramas, commit ni push.
Los ADR 0015-0019 conservan su estado documental proposed y verified:false.
La ejecución técnica no inventa una firma humana de aceptación ni una calibración de política.
Los ADR aceptados anteriores permanecen intactos.

| Decisión propuesta | Implementación observable |
|---|---|
| 0015, núcleo puro | capabilities/deterministic_engine/engine.py y contratos congelados |
| 0016, aritmética e identidad | policy.py y serialization.py; céntimos, gcd y SHA-256 separado |
| 0017, cobertura y revisiones | boundary.py y engine.py; consenso, tombstones y refs |
| 0018, catálogo finito | POLICY inmutable con seis fórmulas y versión explícita |
| 0019, coexistencia privada | deterministic_shadow.py y deterministic_cli.py |

Todas las rutas Python anteriores parten de src/cajamarca_qhaway/.
Los contratos fuente viven en specs/011-deterministic-engine/contracts/.
El generador scripts/deterministic-engine/generate-deterministic-contracts.py emite DTO y schemas empaquetables.
Su opción --check falla si el código generado diverge de los contratos fuente.
Los campos monetarios usan cadenas de dos decimales y las fórmulas usan enteros arbitrarios.
No hay conversión monetaria a float, redondeo, inferencia por nombre ni fecha implícita.

## Uso privado

Instalar el proyecto con sus dependencias de desarrollo desde la raíz del repositorio:

```powershell
uv sync --extra dev --frozen
```

Evaluar un Request engine-2 completo, separado del envoltorio de las fixtures:

```powershell
uv run cajamarca-qhaway-engine input.json private-result.json
```

La salida se crea de forma exclusiva; un destino existente produce código de salida 2.
BatchInvalid también produce código 2 y conserva su salida estructurada.
La API equivalente es evaluate_json(bytes)->bytes.
Para Request tipados ya validados existe evaluate(Request), sin límite de transporte JSON.
La frontera de bytes limita a 32 MiB y profundidad 32 antes de evaluar el lote.
El motor carece de importaciones de persistencia, HTTP, LLM y del motor 004.
La medición JSON separada aceptó 7,69 MB en 5,53 s y rechazó 76,92 MB con RESOURCE_LIMIT.

Shadow requiere un sobre shadow-1, más un mapa evidence_id a archivo preservado:

```powershell
uv run cajamarca-qhaway-engine shadow-input.json shadow-result.json `
  --shadow-payloads payload-files.json
```

Las rutas del mapa se resuelven respecto del archivo payload-files.json.
Cada evidencia del Request, incluido el manifiesto de cobertura, necesita bytes con hash exacto.
links registra legacy_id, scope_id, record_key y evidence_id.
Admite relaciones múltiples explícitas entre identificadores sin fusionar dictámenes.
Cada importe no nulo necesita un binding por scope, clave, fuente, revisión y campo.
El pointer RFC 6901 identifica el valor en el payload preservado, por ejemplo
/awards/0/value/amount para OCDS o /DEVENGADO para un objeto MEF normalizado y preservado.
Decimal se usa solo en este adaptador externo para leer el número original sin pérdida.
Un importe con precisión incompatible se bloquea en vez de redondearse.
La salida shadow contiene inventario de diez reglas 004 y prioridad, enlaces y resultado 011.
El contrato shadow-result-1 fija promotion=disabled y prohíbe copiar approved o published.
No existe operación de escritura al ledger, DB, panel ni resultado histórico desde esta CLI.
Rollback consiste en dejar de invocar este productor privado; no requiere deshacer datos 004.

Los campos no monetarios y la cobertura deben ser normalizados explícitamente por el llamador.
El adaptador no descubre feeds, no acredita por sí solo la verdad de un manifiesto y no
reconstruye un payload original a partir de los floats de los modelos heredados.
La procedencia exacta hace auditable una declaración; no convierte una heurística en prueba legal.

## Verificación ejecutada

La primera prueba del paquete falló por ausencia del núcleo antes de implementarlo.
Los vectores esperados se conservaron; no se regeneraron desde el resultado del runtime.
Los resultados siguientes se observaron en comandos locales, sin servicios oficiales en tests.

| Comprobación | Resultado observado |
|---|---|
| pytest completo, Python 3.12 | 479 passed, 155,08 segundos |
| Corrida previa completa, Python 3.13 | 466 passed antes de los 13 casos finales |
| Pruebas nuevas de runtime | 107, incluyendo grafo y presupuesto MEF |
| Pruebas de contratos y diseño | 34 passed |
| Pruebas Python heredadas | 338 preservadas |
| Node | 25 passed |
| Ruff y Pyright sobre src | Sin errores ni advertencias |
| Dependencias y lock | uv pip check y uv lock --check conformes |
| Auditorías web, paridad, accesibilidad y antislop | Conformes |
| Cobertura de núcleo, líneas y ramas combinadas | 98% |
| Ramas state_for y crossed | 100% ejecutadas |
| Mutación semántica aislada | 15 de 15 detectados |

Las propiedades usan semilla 20261015 y hasta 1000 ejemplos por propiedad.
Incluyen Fraction independiente, céntimos grandes, escala de mercado, monotonía presupuestal,
permutación, duplicado exacto y partición de lotes sin inflar el denominador.
Replay se ejecutó en tres procesos con TZ y PYTHONHASHSEED diferentes.
Un test bloquea sockets, reloj, random, open y getenv durante la evaluación tipada.
Las pruebas revisan bytes completos, hashes, razones, refs y validación de ambos resultados JSON.
El adaptador se prueba con payloads OCDS y MEF sintéticos, hashes y mappings ambiguos.
La CLI también comprueba que un destino existente no se sobrescriba.

```powershell
uv run python scripts/deterministic-engine/generate-deterministic-contracts.py --check
uv run python -m pytest -q
uv run python -m coverage run --branch `
  --source=cajamarca_qhaway.capabilities.deterministic_engine `
  -m pytest tests/deterministic_engine -q
uv run python -m coverage json -o coverage-engine.json
uv run python scripts/deterministic-engine/check-deterministic-coverage.py coverage-engine.json
uv run python scripts/deterministic-engine/mutate-deterministic-engine.py `
  --output context/snapshots/engine-mutations.json
```

CI instala uv 0.11.32 y resuelve exclusivamente uv.lock con --frozen.
Verifica contratos generados, suite completa, cobertura mínima 90%, ramas de estados y
comparadores, los quince mutantes, pruebas Node y las auditorías existentes.
Los mutantes se ejecutan en copias temporales del paquete y no editan el árbol de trabajo.
Un fallo de colección o infraestructura no se contabiliza como mutante detectado.

## Rendimiento y compuertas externas

El benchmark usa 100000 observaciones, 1000 scopes y 100000 evidencias sintéticas.
Cada scope solicita las cuatro reglas de procurement; single-bidder detecta varios procesos.
Share, HHI y recurrencia recorren los hechos y calculan sus fórmulas.
Se ejecuta un warmup, cinco mediciones y otra corrida con tracemalloc.
La medición de bytes se separa de la API tipada: el lote grande ocupa unos 76,9 MB,
por lo que su transporte JSON excede correctamente el límite de 32 MiB.
La mediana local fue 8,94 s y el pico tracemalloc 394371298 bytes, aproximadamente 376 MiB.
La razón 100 k/10 k fue 11,20; los objetivos locales de 10 s y 512 MiB se cumplieron.
La referencia contractual exige Python 3.12 y recursos dedicados; este host local no se certifica.
Los resultados brutos quedan en context/snapshots/2026-10-16-engine-benchmark.json.
Las mediciones no equivalen a un SLA ni a una prueba sobre datos oficiales.

```powershell
uv run python scripts/deterministic-engine/benchmark-deterministic-engine.py `
  --output context/snapshots/engine-benchmark.json
```

No se ejecutó el piloto de treinta días ni reconciliación oficial sobre catorce raíces.
No se promovió 011 a la publicación ni se alteraron aprobaciones, prioridad o alertas históricas.
Esas compuertas del SDD requieren corpus oficial autorizado, correspondencias acreditadas,
calibración humana y actas; los ejemplos sintéticos no las sustituyen.
