---
title: Pruebas 011 - Oráculos y evidencias
status: proposed
source: ai
generator: codex
generated_at: 2026-10-16T07:18:34.441452+00:00
confidence: medium
verified: false
updated: 2026-10-16
---

# Pruebas 011 - Oráculos y evidencias

Plan de aceptación del núcleo y de su frontera de adopción.
Los vectores sintéticos contienen resultados matemáticos manuales independientes del runtime.
El informe de implementación registra ejecuciones locales; este plan no acredita por sí solo
calibración oficial, piloto, aprobación humana ni comportamiento en producción.

## Oráculos y corpus

golden-vectors.json contiene input completo y expected de proyección semántica definida por schema.
No es un BatchResult completo: omite IDs, refs y fórmula, comprobados por pruebas separadas.
Cada vector incluye derivation legible y synthetic=true en el sobre del corpus.
full-result.json contiene input y output completos con IDs concretos para validar serialización.
canonical-vectors.json contiene value, canonical_utf8 y SHA-256 estándar sin dependencia del motor.
selection-vectors.json añade seis casos manuales de revisiones, conflictos, retiro y duplicación.
Su expected es GoldenProjection y su entrada parte del caso completo de postor único.
La derivación declara los diagnósticos FUTURE_REVISION_EXCLUDED y TOMBSTONE_SELECTED esperados.
Una revisión futura conserva la señal, pero cambia run_id porque integra el conocimiento dado.
Un duplicado exacto tiene identity_matches_full_fixture=true: colapsa antes de canonizar y hashear.
invalid-result.json conserva el sobre de metadatos y output BatchInvalid completo, sin run_id.
Su problema SCHEMA_VIOLATION ejemplifica pointer estable y salida sin evaluaciones parciales.
Las fixtures nunca se cargan en pipelines de producción ni simulan cobertura oficial.
La URL example.invalid y los RUC sintéticos no representan instituciones o acusaciones reales.
Los umbrales de igualdad son los valores propuestos de política, nunca límites legales.
El oráculo racional usa Fraction de biblioteca estándar en test; el runtime usa céntimos/productos.
También se comprueban ejemplos manuales para evitar dos algoritmos con el mismo supuesto erróneo.
No se regenera expected a partir de evaluate ni se actualiza un snapshot por aceptar un fallo.

## Matriz de familias

Todas las funciones nominales de tasks.md parametrizan la familia completa correspondiente.
No basta con una aserción feliz por función; se enumeran aquí los casos exigibles.

1. Boundary: campos extra en todos los objetos, claves duplicadas, null versus omitido,
   int/bool/string, float/NaN/Infinity, UTF-8/BOM, límite 32 MiB y profundidad 32/33.
   URI inválida, fecha imposible, +00:00 rechazado frente a Z, fecha sin zona y leap seconds.
   Errores tienen pointer RFC 6901, orden estable, ningún payload sensible y BatchInvalid cerrado.
2. Revisiones: vieja/nueva invertidas, retirada, reaparición legítima con revisión superior,
   futura sin elegible, misma revisión contradictoria, corroboración por más evidencia,
   dos fuentes con distinta extracción pero mismo hecho y dos fuentes con hecho opuesto.
   effective_at o retrieved_at futuro excluye; no se usa extracción como fecha de adjudicación.
3. Aritmética:0.00,0.01,máximo 18 enteros, monto>2^53 céntimos, gcd, denominador positivo,
   -0 rechazado en racional normalizado, coeficiente repetitivo 1/3 y comparación sin round.
4. Estados: matriz de precedencia con dos defectos a la vez, scope vacío y 2 scopes independientes.
   Para cada regla PASS/SIGNAL/MISSING/INVALID; nunca PASS cuando falta denominador.
5. Scopes: padre/ejecutora, maestro/partición, mismo award corroborado por 2 fuentes,
   un proceso con varios awards y 2 scopes sin suma implícita.
   expected_count cuenta awards activos lógicos, no procesos/releases/fuentes.
6. Evidencia: refs colgantes, source_id distinto, extracción distinta, cobertura falsa por conteo,
   hash de payload cambiado, URL distinta, manifested partial y ninguna evidencia sin procedencia.
   Hashes no autentican por sí solos al publicador ni acreditan verdad del payload.
7. Replay:100 permutaciones, duplicado exacto, claves JSON reordenadas y 3 procesos separados.
   Entornos TZ y locale distintos, semillas distintas, sin red y con reloj congelado distinto.
   raw no se compara: se comparan bytes canónicos, run_id y result_id reconstruidos desde preimage.
8. Policy: catálogo exacto 6, versión no soportada, umbral no configurable, regla aplazada pedida.
9. Single:1,2,null,0; method direct/unknown; bids contradictorios por lote; proceso incompleto.
10. Share:40%,41%,0%,monopolio 100%,RUC faltante, monto 0,2 procesos y 3 procesos.
   40/30/30 son frontera;41/30/29 activa; nombre jamás reemplaza RUC ausente.
11. HHI: cuatro cuotas 25% dan 2500; cinco 20% dan 2000; monopolio da 10000.
   0<=HHI<=10000; repartir un proveedor en dos reduce o mantiene HHI si todo lo demás coincide.
12. Recurrencia:2/3 procesos,3 lotes de 1, ningún direct, método desconocido, RUC faltante.
    Inicio incluido; end excluido se prueba como observación de otro scope, no se descarta
   silenciosamente una observación mal asignada al intervalo actual.
   Duraciones 364,365,366 días y año bisiesto; la ventana siempre usa segundos, no año calendario.
13. Unspent:100/50,100/50.01,100/49.99,0/0,devengado null,abierto,corte incorrecto.
    Devengado 120/PIM 100 produce saldo-1/5 PASS y above-pim SIGNAL 11/10.
14. Above:110/100,110.01/100,109.99/100,PIM 0,moneda distinta,partición y corte futuro.
15. Deferred: cada uno de los códigos 004 aplazados rechazado y ninguna dependencia LLM/vector.
16. Migration: diez reglas 004 y prioridad con disposición visible y diferencias esperadas.
    Fecha de extracción ya no sustituye fecha del hecho; aprobación/published nunca se copian.
    Sin payload monetario preciso no se convierte float; mapa ambiguo bloquea promoción.

## Propiedades y metamorfismos

Usar generadores de scopes válidos y mutaciones singulares, con seed reproducible en reporte.
1000 ejemplos por propiedad y seed 20261015 en CI; guardar contraejemplo mínimo al fallar.
Permutación y duplicado exacto preservan salida y hashes tras normalización.
Multiplicar todo dinero de una cohorte por entero positivo preserva share/HHI y estados,
pero cambia run_id y refs al cambiar el request: invariancia semántica, no de identidad.
Cambiar evidencia/extraer más tarde conserva fórmula si hecho igual pero cambia run_id.
Añadir revisión futura conserva evaluación semántica y cambia run_id/diagnóstico.
Cambiar un lote por dos de mismo proceso/RUC y suma exacta conserva share/HHI/recurrencia,
conservando también cobertura declarada y ajustando expected_count.
Aumentar devengado con PIM fijo no aumenta saldo y no reduce above-pim.
Añadir award competitive a universo de recurrencia no incrementa conteo direct.
Duplicar fuentes corroborantes no duplica monto ni procesos.
No se exige monotonía SIGNAL al aumentar muestra/denominador o cambiar política.

## Integración, seguridad y mutación

Los adaptadores construyen contratos desde payload sintético OCDS/MEF preservado y su hash.
No se llaman servicios reales desde tests unitarios o golden; integración oficial es privada opt-in.
Un double de ledger detecta que 011 solo lee evidencia y nunca sobrescribe 004 o dictámenes.
Denegar acceso a sockets, reloj, random, entorno, DB e imports de infraestructura durante evaluate.
Permitir únicamente hashing, parseo, aritmética, normalización y serialización pura.
Mutation suite debe matar gt->ge de share/above, ge->gt de HHI/unspent/recurrencia,
eq 1->ge 1 en bidders, ventana end inclusivo, count awards en vez de procesos,
float en vez de entero, nombre en vez de RUC, revisión mínima, suma de maestro/partición,
falta de expected_count, inferir null 0 y conservar aprobación heredada.
Se exige 100% de esos 15 mutantes muertos, sin reclamar 100% de toda mutación imaginable.

## Rendimiento y límites

Complejidad objetivo O(n log n + r*n), r<=6 por scope; memoria O(n).
Ningún producto de pares de awards ni fitting de modelos sobre lote.
Benchmark privado fijo:100000 observaciones,1000 scopes,100000 refs,6 reglas compatibles.
Límite schema de 100000 observaciones se comprueba antes de agrupar.
En presupuesto usar una fila/scope; el corpus masivo principal usa procurement y 4 reglas.
El generador de benchmark no debe solicitar seis reglas incompatibles a un mismo scope.
Referencia: Python 3.12,4 núcleos lógicos dedicados,8 GiB RAM, sin red, semilla 20261015.
El benchmark grande mide `evaluate(Request)` tipado en memoria, separado del decoder de bytes.
`evaluate_json` se mide con corpus serializados de hasta 32 MiB y registra también su tamaño.
Si el corpus grande excede 32 MiB, la frontera JSON debe rechazarlo con RESOURCE_LIMIT.
Ese rechazo no constituye un fallo ni una certificación del rendimiento del núcleo puro.
Tras warmup 1, ejecutar 5 veces: mediana<=10 s y peak tracemalloc<=512 MiB es objetivo de
aceptación.
Si el host no cumple recursos, no se declara aprobación de rendimiento: usar runner fijado.
Comparar 10 k/100 k; razón de tiempos<=20 evita regresión cuadrática gruesa.
El reporte guarda commit, hardware, Python, corpus_sha256, tiempos y memoria, sin datos personales.

## Cierre y evidencia

Tests del SDD ejecutados ahora se reportan separados de futuros tests 011 y legacy.
La aprobación de adopción requiere firma humana de política/spec/ADR y trazabilidad sin huérfanos.
No se sustituye calibración sobre datos autorizados por ejemplos sintéticos que siempre pasan.

## Estado de ejecución 2026-10-16

El runtime y las pruebas están en tests/deterministic_engine/ y no se cargan desde las fixtures
como código de producción.
La última corrida completa observada tuvo 479 pruebas Python y 25 Node sin fallos.
El núcleo registró 98% de cobertura combinada y ramas completas en state_for y crossed.
Los quince mutantes se ejecutan con scripts/deterministic-engine/mutate-deterministic-engine.py.
El piloto de campo, la aprobación de política y el host de referencia siguen siendo compuertas
externas: las mediciones locales y las pruebas sintéticas no las completan.
