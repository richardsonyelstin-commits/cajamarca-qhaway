---
title: Spec 011 - Motor determinista reproducible
status: proposed
spec: '011'
source: ai
generator: codex
generated_at: 2026-10-16T07:18:34.441452+00:00
confidence: medium
verified: false
updated: 2026-10-16
---

# Spec 011 - Motor determinista reproducible

Implementación privada disponible en src/cajamarca_qhaway/capabilities/deterministic_engine/.
El estado proposed expresa aprobación documental pendiente, no ausencia del runtime.
No se declara promoción productiva ni calibración humana de la política exploratoria.

Diseño propuesto de un núcleo nuevo separado del motor heredado, con implementación privada.
Seis indicadores descriptivos producen resultados auditables sobre expedientes institucionales.
Las señales requieren revisión humana y no prueban corrupción ni incumplimiento normativo.

## Alcance y contrato

El mandato humano autoriza diseño e implementación, sin aprobar estos umbrales por anticipado.
Los contratos propuestos llevan `schema_version=engine-2` y no mutan contratos heredados.
La implementación privada vive en `src/cajamarca_qhaway/capabilities/deterministic_engine/`.
Su evidencia de ejecución está registrada en `docs/audits/2026-10-16-deterministic-engine-implementation.md`.
La implementación no convierte la propuesta en política aprobada ni habilita uso operativo.
No publica Alert, conecta fuentes, decide causalidad ni ejecuta migraciones productivas.
No entran denuncias, DJI, nombres personales, LLM, vectores ni inferencias patrimoniales.
El RUC agrupa adjudicaciones, nunca recibe puntuación ni ranking.
La prioridad compuesta queda fuera del núcleo 011 mediante ADR 0019.
Las fixtures son sintéticas y sus URL example.invalid jamás acreditan evidencia oficial.

`request` declara as_of, versiones, scopes, evidence y observations.
Cada scope identifica entidad oficial, cohorte e intervalo UTC semiabierto [start,end).
Para procurement, end<=as_of; presupuesto admite año abierto representable pero no evaluable.
`entity_id` usa identificador calificado por esquema; `region=CAJAMARCA` es obligatorio.
La acreditación geográfica del identificador pertenece al adaptador y su manifiesto conservado.
`cohort` es clasificación oficial o `all` explícito, nunca inferencia textual.
Cada observación representa un award o maestro presupuestal, no una mezcla de granularidades.
`record_key` es identidad oficial (OCID y award.id para contrataciones).
`process_id` es OCID y permite distinguir lotes de procesos completos.
`revision` entero monotónico lo certifica el adaptador, no se deduce del release.id textual.
`event_at`, `effective_at` y `retrieved_at` distinguen hecho, vigencia y extracción.
`coverage` no se acredita por HTTP 200: requiere manifiesto preservado y conteos reconciliados.
El núcleo comprueba consistencia interna; no puede probar completitud del portal externo.

## Reglas transversales y aceptación

**RN-011-01. Contrato cerrado y ejecución pura.**
La petición estructuralmente inválida produce BatchInvalid sin evaluaciones parciales.
Campos desconocidos, duplicados JSON, floats monetarios, NaN y timestamps sin Z se rechazan.
No se usa reloj, DB, red, entorno ni aleatoriedad.
**CA-011-01:** error uniforme con problemas ordenados por pointer/code y cero evaluaciones.

**RN-011-02. Selección temporal y revisiones.**
Se elige revisión mayor elegible por (scope_id,source_id,record_key).
Elegible exige effective_at y retrieved_at <=as_of; las futuras quedan en diagnóstico.
Duplicados idénticos colapsan; igual revisión con contenido distinto invalida ese scope.
Fuentes distintas para una record_key deben coincidir en todos los campos del hecho elegido.
Se une su evidencia; no se selecciona fuente ganadora cuando discrepan.
Un tombstone deleted=true retira el hecho y no borra historia externa.
Desacuerdo entre fuentes sobre deleted también invalida el scope.
**CA-011-02:** permutar y duplicar no altera salida; revisiones conflictivas dan INVALID.

**RN-011-03. Exactitud.**
Dinero PEN no negativo usa string con hasta 18 dígitos enteros y dos decimales obligatorios.
Se opera en céntimos enteros arbitrarios y se compara por productos cruzados exactos.
Ratios y HHI salen como numerator/denominator coprimos; cero se representa 0/1.
El numerador admite negativo para saldo presupuestal; denominador siempre positivo.
**CA-011-03:**40/100 no supera 2/5 y montos mayores que 2^53 céntimos no pierden precisión.

**RN-011-04. Estados y cardinalidad.**
Cada par solicitado (scope_id,rule_code) genera exactamente un Evaluation.
INVALID representa contradicción semántica; NOT_EVALUABLE falta o insuficiencia de datos.
PASS y SIGNAL exigen todos los predicados de evaluabilidad y comparación calculada.
PASS solo significa no cruzar ese umbral sobre ese universo, nunca ausencia de riesgo.
Cada estado tiene reason_code; solo PASS/SIGNAL tienen observed y threshold no null.
**CA-011-04:** scope vacío da NOT_EVALUABLE/EMPTY_SCOPE por cada regla pedida.

**RN-011-05. Cohortes, cortes y doble conteo.**
Scope es cohorte atómica de entidad, clase, moneda PEN e intervalo; jamás se suman scopes.
Mercado requiere awards activos con fecha, monto positivo y RUC único confirmado.
Todo consorcio da NOT_EVALUABLE/UNALLOCATED_SUPPLIERS en este perfil sin reparto por award.
No se atribuye el valor íntegro a cada integrante ni se imputa al primero.
Presupuesto requiere exactamente un maestro ActProy por entidad, ejercicio y corte.
No entran particiones, fuentes/rubros ni ejecutoras sumadas con su padre.
**CA-011-05:** maestro 100 y partición 60 no suman 160: INVALID/MIXED_GRAIN.

**RN-011-06. Evidencia y explicación.**
Cada hecho refiere evidencia con URL, extracción y payload_sha256; ninguna referencia es huérfana.
Cada referencia declara adapter_version para reproducir la normalización, además de la fuente.
El ledger externo conserva bytes fuente; el núcleo no interpreta payload arbitrario.
Cada Evaluation expone fórmula fija, política, cohorte, ventana y cobertura vía scope_id y run_id.
record_keys incluye todo el denominador elegido, no solo hechos favorables a la señal.
evidence_ids incluye los hechos y el manifiesto de cobertura.
**CA-011-06:** alterar dato o política cambia run_id; toda referencia resuelve en request.

**RN-011-07. Identidad y reproducción.**
La canonización del plan ordena conjuntos y normaliza revisiones sin reloj implícito.
run_id identifica el request normalizado y result_id vincula run_id y Evaluation sin result_id.
Listas de identidad se ordenan y deduplican; evaluaciones se ordenan por scope_id/rule_code.
as_of es instante lógico; no existe generated_at tomado del sistema.
**CA-011-07:** replay en procesos separados produce bytes y SHA-256 completos idénticos.

**RN-011-08. Catálogo finito.**
qhaway-exploratory-1 contiene exactamente las seis reglas siguientes.
Todos sus umbrales son heurísticos propuestos pendientes de calibración humana; ninguno es ley.
Cambiar un umbral exige versión, fixtures y revisión humana; no se configura silenciosamente.
La evaluabilidad contractual no promete que la ingesta actual entregue todos los campos.
**CA-011-08:** código desconocido o versión distinta produce UNSUPPORTED_VERSION sin cálculo.

## Catálogo evaluable

Todo scope de procurement exige status=active y fechas del hecho dentro de [start,end).
No se obtiene muestra válida omitiendo observaciones incompletas.
El orden exacto de comprobaciones y sus motivos se define en plan.md.

**RN-011-09. single-bidder.**
Unidad: un proceso competitivo adjudicado; scope con exactamente un process_id.
Exige coverage=complete del proceso, method=competitive y bidders entero>=1 idéntico por lote.
Mínimo: un award; fórmula bidders; SIGNAL si=1, PASS si>=2, umbral 1/1 y operador eq.
No aplica UIT ni supone infracción; direct/unknown da NOT_EVALUABLE/INAPPLICABLE.
**CA-011-09:**1 activa,2 pasa,null no evaluable; varios lotes no duplican resultados.

**RN-011-10. contract-share.**
Unidad: cohorte institucional completa; mínimo 3 process_id distintos y 1 RUC válido.
El mínimo de procesos es filtro heurístico de diseño, no prueba de significancia estadística.
Cada award requiere monto>0 y RUC único; A_s suma montos por RUC y A suma todos.
Fórmula max_s(A_s)/A; SIGNAL estrictamente>2/5; igualdad pasa.
No se devuelve identidad del ganador ni puntuación por proveedor.
**CA-011-10:**40/100 pasa,41/100 activa; un RUC ausente invalida evaluabilidad global.

**RN-011-11. hhi.**
Misma cohorte, requisitos y mínimo que contract-share.
Fórmula 10000*sum_s(A_s²)/A²; SIGNAL>=2500, igualdad activa.
Describe adjudicaciones institucionales declaradas, no el mercado económico completo.
**CA-011-11:** cuatro RUC de 25 dan 2500 y activan; cinco de 20 dan 2000 y pasan.

**RN-011-12. recurrent-direct.**
Unidad: cohorte institucional en ventana UTC 365*86400 segundos [start,end).
Exige coverage=complete, método conocido y RUC único por award; no requiere monto.
Cuenta process_id distintos direct por RUC, sin duplicar lotes del mismo proceso.
Fórmula máximo conteo; SIGNAL>=3; cero procesos direct da PASS/0 con universo no vacío.
Mínimo un proceso; competitive integra universo pero no numerador; unknown no evaluable.
**CA-011-12:** tres direct activan; tres lotes cuentan 1; start incluido y end excluido.

**RN-011-13. budget-unspent.**
Unidad: un maestro institucional anual cerrado, sin suma de filas.
Exige fiscal_year anterior al año UTC de as_of y cut_at=31 diciembre UTC del ejercicio.
scope.start es 1 enero del ejercicio y end es 1 enero siguiente; cut_at es medianoche UTC.
La fecha anual no acredita cierre contable certificado; el adaptador preserva el corte oficial.
Exige coverage=complete, PIM>0 y devengado no negativo conocido.
Fórmula(PIM-devengado)/PIM; SIGNAL>=1/2; igualdad activa.
Si devengado>PIM, el saldo negativo pasa; abierto da NOT_EVALUABLE/OPEN_FISCAL_YEAR.
**CA-011-13:**100/50 activa,100/50.01 pasa,PIM 0 no evaluable; abierto no evaluable.

**RN-011-14. budget-above-pim.**
Mismos requisitos y unidad que budget-unspent.
Fórmula devengado/PIM; SIGNAL estrictamente>11/10; igualdad pasa.
Etiqueta: diferencia financiera a verificar, nunca sobrecosto contractual o fraude probado.
**CA-011-14:**110/100 pasa,110.01/100 activa; devengado ausente no evaluable.

**RN-011-15. Reglas aplazadas.**
Plazos legales requieren régimen/modalidad, convocatoria y calendario hábil oficial versionado.
Fraccionamiento requiere identidad de necesidad y excepciones, además de perfil legal temporal.
Umbral directo requiere distinguir modalidades legales y UIT oficial por ejercicio.
Sobrecosto contractual requiere contrato, pagos y modificaciones en misma moneda y granularidad.
Alquiler, antigüedad, DJI y vectores carecen de contrato probatorio suficiente para este núcleo.
No se heredan reglas a partir de semejanza textual ni fechas de extracción.
**CA-011-15:** ninguna regla aplazada puede solicitarse ni aparecer en evaluaciones.

**RN-011-16. Adopción y migración.**
Shadow privado coexiste con 004 sin sustituir ni borrar su historia.
No se convierte float a Decimal ciegamente: se reconstruye desde payload monetario preservado.
Sin payload preciso se informa brecha; IDs heredados se enlazan por mapa versionado explícito.
Un ID previo puede corresponder a varios awards 011; ninguna aprobación humana se copia.
No se migra published ni priority_score; el panel vuelve a decidir antes de publicación 011.
**CA-011-16:** replay conserva 004; falta de mapa, payload o revisión impide promoción 011.

## Fuentes y límites verificados

OCDS describe awards, suppliers y numberOfTenderers; no acredita disponibilidad del feed peruano.
[OCDS 1.1.5](https://standard.open-contracting.org/1.1/en/schema/reference/).
MEF distingue PIM y fases de ejecución; la propuesta usa Devengado, no Girado.
[MEF Consulta Amigable][mef].

[mef]: <https://www.mef.gob.pe/index.php/es/?id=7605&option=com_content&view=article>
Consulta 2026-10-15; ninguna fuente prescribe los umbrales heurísticos propuestos.
El inventario de migración y las pruebas de diferencias están en plan.md y test-plan.md.
