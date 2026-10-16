---
title: Plan 011 - Arquitectura y semántica ejecutable
status: proposed
source: ai
generator: codex
generated_at: 2026-10-16T07:18:34.441452+00:00
confidence: medium
verified: false
updated: 2026-10-16
---

# Plan 011 - Arquitectura y semántica ejecutable

Arquitectura implementada de tipos congelados y funciones puras desde contratos 2020-12.
La entrada separa expediente, observación revisada y referencia de evidencia preservada.
La ejecución privada conserva fases verificables y no usa efectos externos en el núcleo.

## Arquitectura y firmas

El paquete `capabilities/deterministic_engine` es independiente de red_flags_engine.
Los tipos Request, Scope, Observation, Evidence y BatchResult se generan de JSON Schema.
Tuplas inmutables internas sustituyen listas mutables después de validar la frontera JSON.
No se importa módulo de infraestructura, modelos ORM, LLM, HTTP ni adaptadores desde el núcleo.
La API pública y las funciones internas actuales se encuentran en boundary.py y engine.py:

```python
def decode_request(raw: bytes) -> Request | BatchInvalid: ...
def normalize_request(request: Request) -> Request | BatchInvalid: ...
def evaluate(request: Request) -> BatchResult | BatchInvalid: ...
def evaluate_json(raw: bytes) -> bytes: ...
def canonical_bytes(value: JSONValue) -> bytes: ...
```

JSONValue es la unión recursiva de valores JSON tipados definida en serialization_types.py.
La conversión interna document admite los DTO congelados y sus tuplas.
Float nunca pertenece a esa unión; no se aceptan subclases bool como integer en frontera.
POLICY es catálogo inmutable `qhaway-exploratory-1`; no interpreta fórmulas como expresiones.
select devuelve hechos elegidos, claves, referencias, fallo opcional y diagnósticos.
calculate devuelve razón y racionales; evaluate construye las evaluaciones y sus identidades.
BatchInvalid siempre sigue result.schema.json, sin stacktrace ni texto libre sensible.
La semántica pura no prescribe framework, planificador ni almacenamiento.

```mermaid
flowchart LR
    A[Adaptador y ledger fuera del núcleo] --> B[Request validado]
    B --> C[Normalizar y seleccionar revisiones]
    C --> D[Validar scope y cobertura]
    D --> E[Comparadores exactos]
    E --> F[Evaluaciones y hashes]
    F --> G[Shadow privado y panel humano]
```

## Orden de validación y errores

Primero se decodifica UTF-8 estricto, sin BOM, con rechazo de claves JSON duplicadas.
Límite de entrada 32 MiB antes de parsear y profundidad máxima 32 niveles.
Exceso produce RESOURCE_LIMIT pointer vacío; sintaxis/UTF-8 inválido SCHEMA_VIOLATION vacío.
Luego schema 2020-12 con formatos activos, sin coerciones, sin resolver referencias en red.
Versiones ausentes son SCHEMA_VIOLATION; presentes no soportadas UNSUPPORTED_VERSION.
Código rule_code desconocido también es UNSUPPORTED_VERSION en su pointer de rules.
Esta clasificación se aplica antes de mapear a SCHEMA_VIOLATION el resto de errores del schema.
Cada infracción estructural genera pointer RFC 6901 y código SCHEMA_VIOLATION.
No se devuelve texto original ni valor fuente en errores.
Problemas se deduplican y ordenan lexicográficamente por (pointer,code).
Después: IDs de scopes/evidence únicos, refs resolubles y source_id consistente con evidencia.
scope_id duplicado es DUPLICATE_ID; observation.scope_id desconocido es DANGLING_REFERENCE.
evidence_id repetido idéntico colapsa; mismo ID con contenido distinto es DUPLICATE_ID.
Cada evidencia de observación debe tener su source_id y retrieved_at idénticos a la observación.
El manifiesto coverage_evidence_id debe resolver, y su extracción ser<=as_of.
adapter_version es obligatorio en cada referencia; el ledger conserva el artefacto de esa versión.
El núcleo identifica versiones de adaptador sin ejecutar sus normalizadores durante replay.
Ref ausente o source/fecha incompatible da DANGLING_REFERENCE en el campo de referencia.
observations.scope_id debe resolver; un scope no puede referir reglas del kind opuesto.
Regla/kind incompatible es SCHEMA_VIOLATION en /scopes/i/rules/j.
Estos errores de grafo producen BatchInvalid, sin resultados locales.

Por scope se aplica la siguiente precedencia de fallos; gana el primero de esta lista:

1. INVALID_INTERVAL: start>=end, procurement con end>as_of o recurrencia con duración no 365 días.
2. CONFLICTING_REVISION: misma fuente/clave/revisión elegible con hechos distintos.
3. SOURCE_DISAGREEMENT: fuentes elegibles con hechos distintos para la misma clave.
4. MIXED_GRAIN: kind incompatible, entity/cohort distintos, partición presupuestal,
   más de un maestro presupuesto o más de un process_id en single-bidder.
5. INVALID_FACT: award no active, bidders contradictorios entre lotes del mismo proceso,
   event_at conocido fuera de [start,end), o fechas del presupuesto contradictorias.
6. INVALID_CUT: presupuesto cerrado con cut_at conocido distinto de 31 diciembre del fiscal_year,
   event_at distinto de cut_at o scope distinto de año fiscal completo.
7. EMPTY_SCOPE: no queda hecho después de revisiones/tombstones.
8. MISSING_FIELD: ausencia de campo requerido para esa regla, incluida fecha del hecho.
9. INCOMPLETE_COVERAGE: coverage no complete o expected_count null.
10. COVERAGE_MISMATCH: expected_count distinto de hechos activos seleccionados.
11. UNALLOCATED_SUPPLIERS: cualquier award sin asignación única para reglas de RUC.
12. INAPPLICABLE: single-bidder con método no competitivo o recurrent-direct con unknown.
13. OPEN_FISCAL_YEAR: fiscal_year>=as_of.year.
14. ZERO_DENOMINATOR: PIM=0 o cualquier monto de mercado=0.
15. INSUFFICIENT_SAMPLE: mínimos no satisfechos.

Los códigos 1-6 y 10 son INVALID;7-9 y 11-15 son NOT_EVALUABLE.
Los predicados 7-15 se comprueban por regla: un campo irrelevante ausente no la bloquea.
MISSING_FIELD de single-bidder exige event_at, process_id y bidders; no requiere amount/RUC.
MISSING_FIELD de mercado exige event_at, amount, supplier_ruc y currency=PEN.
MISSING_FIELD de recurrencia exige event_at y supplier_ruc; method unknown es INAPPLICABLE.
MISSING_FIELD presupuestal exige cut_at,event_at,pim,devengado y currency=PEN.
currency=unknown se considera campo monetario faltante, no afecta reglas sin importe.
bidders=0 es INVALID_FACT solo para single-bidder y no bloquea reglas que no lo requieren.
supplier_allocation=unallocated tiene precedencia sobre supplier_ruc null para reglas de RUC.
Single-bidder con bidders distintos por lotes da INVALID_FACT, no se toma el primero.
Mercado con amount=0 da ZERO_DENOMINATOR para todo el scope, aunque otros importes sean positivos.
Es una condición de admisión conservadora, no eliminación de filas del denominador.
INVALID_FACT y MIXED_GRAIN aplican al scope salvo bidders=0, exclusivo de single-bidder.
En presupuesto abierto INVALID_CUT no exige cierre anual; OPEN_FISCAL_YEAR sigue alcanzable.
Un corte conocido cuyo año difiere de fiscal_year sí es INVALID_FACT incluso en año abierto.
Los errores MISSING_FIELD y posteriores afectan solo a las reglas que requieren ese campo.
Cuando no hay fallo se calcula el valor y se devuelve THRESHOLD_MATCH o THRESHOLD_NOT_MATCH.

## Selección y evidencia

Se eliminan revisiones con extracción o vigencia futura antes de comparar revisiones elegibles.
Se registra FUTURE_REVISION_EXCLUDED por (scope_id,record_key), deduplicado.
En cada grupo fuente/clave gana max(revision), sin confiar en el orden de entrada.
Igual revisión con diferencias solo en evidence_ids es corroboración: se unen las refs.
Para conflicto se compara fact,deleted,effective_at,retrieved_at; revisión menor no lo oculta.
Entre fuentes se comparan solo fact y deleted, no sus relojes o números locales de revisión.
La igualdad de fact es igualdad estructural tras ordenar claves, incluidos null y codepoints.
expected_count cuenta record_key activos lógicos tras consenso, no releases, procesos o fuentes.
Una misma fuente/clave/revisión con distinta extracción es CONFLICTING_REVISION.
No se elige extracción más reciente; el adaptador debe emitir revisión superior o conservar bytes.
Las fuentes se resuelven antes de descartar tombstones, para detectar contradicción de borrado.
Una clave borrada concordante no cuenta en observed_count y produce TOMBSTONE_SELECTED.
No hay resurrección por fallback a revisión antigua tras tombstone.
evidence_ids del resultado une refs de revisiones elegidas, incluidas tombstones y manifiesto.
record_keys incluye solo hechos activos elegidos en el scope.
En INVALID por conflicto se incluyen todas las claves y refs elegibles involucradas.
Para EMPTY_SCOPE se preservan refs de tombstones y manifiesto, aunque no haya record_keys.
No se añade evidence no referenciada a la explicación, pero sí se conserva en identidad del request.

## Aritmética y fórmula

Dinero se parsea removiendo punto y usando entero, jamás float, y sin redondeo.
Fraction usa enteros arbitrarios y gcd(abs(n),d); d siempre>0 y signo solo en n.
Operadores y fórmula son constantes:

| rule_code | formula_id | observado | umbral | operador |
|---|---|---|---|---|
| single-bidder | bidders-eq-v1 | bidders/1 |1/1|eq|
| contract-share | max-award-share-v1 |max(A_s)/A|2/5|gt|
| hhi | award-hhi-v1 |10000*sum(A_s²)/A²|2500/1|ge|
| recurrent-direct | distinct-direct-processes-v1 |max(count_s)/1|3/1|ge|
| budget-unspent | annual-unspent-v1 |(PIM-D)/PIM|1/2|ge|
| budget-above-pim | annual-above-pim-v1 |D/PIM|11/10|gt|

Recurrencia con ningún direct usa máximo vacío=0; con hechos vacíos sigue EMPTY_SCOPE.
No hay rounding de visualización en el núcleo; cualquier formato decimal es capa posterior.
Concentración y HHI usan todos los métodos conocidos o unknown: modalidad no los condiciona.
Se exige amount>0, no se admiten concesiones de valor negativo en este perfil de gasto.
Una normalización externa no convierte valores negativos en cero: rechaza alcance incompatible.
Un award con varios proveedores solo es aceptable si el adaptador entrega distribución oficial.
El presente esquema single/unallocated no admite desdoblar un award en varios proveedores.
Por tanto, en esta versión también los consorcios con reparto publicado quedan no evaluables.
Extenderlos requiere versión nueva y semántica de asignación; no se inventa suffix de award.id.

## Canonización e identidad

Se acepta JSON sin normalización Unicode: strings conservan codepoints exactos.
No se hace trim, casefold, NFC ni se equiparan identificadores oficiales distintos.
Las claves oficiales no admiten espacios iniciales/finales por validación semántica INVALID_FACT.
Los IDs de scope/evidencia deben carecer de esos espacios o dan SCHEMA_VIOLATION.
Texto narrativo y nombres personales no son campos de este contrato.
canonical_bytes serializa null/bool/int/string con JSON UTF-8, ensure_ascii=False,
sort_keys=True, separators=(',',':'), sin slash escapado ni salto final.
El escape de controles, comillas y barra inversa sigue json.dumps de Python 3.12.
Solo entran enteros JSON de conteos/versiones; no hay float ni Decimal en ese serializador.
Antes de serializar request se ordenan scopes por scope_id y sus rules lexicográficamente.
evidence se deduplica por ID idéntico y ordena por evidence_id.
observations se deduplican por bytes exactos tras ordenar evidence_ids y se ordenan por
(scope_id,source_id,record_key,revision,canonical_bytes(observation)).
Se conservan revisiones antiguas/futuras en el request normalizado y por tanto en run_id.
Esto permite auditar el conocimiento suministrado, aunque no altere el valor observado.
Cambiar as_of cambia run_id aunque las señales coincidan.

`run_id = sha256(b'qhaway-run-v2\n' + canonical_bytes(normalized_request)).hexdigest()`.
Cada Evaluation incluye result_id calculado sobre sus demás campos y run_id en un envoltorio:
`sha256(b'qhaway-result-v2\n' + canonical_bytes({'run_id':run_id,'evaluation':body}))`.
body es el Evaluation sin result_id, incluso si estado INVALID o NOT_EVALUABLE.
run_id no depende del resultado, y result_id no entra en su propio preimage.
BatchInvalid no tiene run_id porque no representa una petición válida.
BatchResult completo se serializa con el mismo canonical_bytes.
diagnostics se ordena por scope_id,record_key,code y se deduplica.
No se afirma que hashes anonimizan datos; todas las salidas individuales siguen privadas.

## Evidencia de migración verificada en código

Referencias son observaciones del árbol consultado 2026-10-15; no autoridad normativa.
`engine.py:140` toma datetime.now si now es ausente;011 exige as_of.
`models/procurement_record.py:42` usa float monetario;011 exige payload decimal exacto.
`models/red_flag.py:20` trunca SHA-256 a 16 hex;011 conserva 64 y dominio explícito.
`engine.py:281` usa supplier_ruc o nombre;011 prohíbe fallback de identidad por nombre.
`semantic.py:38` deriva TF-IDF del lote;011 no usa texto ni vectores.
Rutas relativas a `src/cajamarca_qhaway/`, salvo engine.py/semantic.py dentro de
`capabilities/red_flags_engine/`; cada cambio de migración debe volver a verificar estas líneas.
`tests/test_red_flags_engine.py:34` fija catálogo 10; no se elimina esa prueba para fingir paridad.

| Regla 004 | Disposición 011 | Diferencia que prueba migración |
|---|---|---|
| single-bidder | Sustituida descriptivamente | Sin UIT; proceso completo y método confirmado |
| execution-overrun | Solo componente institucional sustituido | PIM nunca denomina un contrato |
| contract-concentration | contract-share | Cohorte completa, mínimo 3 procesos y 1 RUC |
| short-tender-window | Aplazada | Calendario y régimen no se infieren |
| direct-award-threshold | Aplazada | Sin UIT hardcodeada ni inferencia de ilegalidad |
| direct-administration-equipment-rent | Retirada del núcleo | Texto no prueba propiedad/necesidad |
| contract-splitting-orders | Aplazada | Sin similitud entrenada por lote ni conclusión legal |
| mef-underspending | Sustituida conservadoramente | Solo año cerrado, no avance intraanual |
| recurrent-direct-award | Sustituida | Ventana [start,end),365 días y procesos sin duplicar lotes |
| hhi-concentration | Sustituida | Cohorte declarada, muestras mínimas y fracción exacta |
| prioridad de expedientes | Fuera del núcleo | Sin score 011 ni copia de score 004 |

## Adopción propuesta

Crear adaptador 004->011 solo desde payloads y manifiestos preservados, sin leer secretos.
El mapa externo registra legacy_id, record_key, mapping_version y evidencia de correspondencia.
Permite one-to-many por lotes y many-to-one por revisiones, sin fusionar revisiones humanas.
Shadow conserva outputs separados y compara valores y razones, no exige igualdad artificial.
Promoción exige aprobar spec/ADR, corpus sintético completo, corpus oficial privado autorizado,
reconciliación del 100% de diferencias explicadas y ninguna señal sin evidencia resoluble.
Un piloto de 30 corridas diarias privadas con 14 raíces es propuesta de observación, no garantía.
Se registra aprobación humana de política y panel antes de conectar candidatos al flujo 005.
Rollback deshabilita productor 011 y mantiene ledger/mapas y candidatos históricos privados.
No hay borrado ni downgrade automático de published 004.
