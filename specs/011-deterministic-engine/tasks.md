---
title: Tareas 011 - Implementación y cierre verificable
status: proposed
source: ai
generator: codex
generated_at: 2026-10-16T07:18:34.441452+00:00
confidence: medium
verified: false
updated: 2026-10-16
---

# Tareas 011 - Implementación y cierre verificable

Las dieciséis tareas tienen implementación privada reportada y pruebas trazables.
El informe de implementación registra los resultados observados; no se reejecutaron aquí.
La calibración, adopción y aprobación humana siguen siendo compuertas separadas.

## Secuencia

Todos los archivos de prueba siguientes están bajo `tests/deterministic_engine/`.
Los tests actuales de documentación están separados en test_deterministic_engine_specification.py.
Un ingeniero de implementación realiza cada tarea y otro revisa su oráculo y evidencia.
Cada tarea depende de su predecesora excepto T-011-09 a T-011-14, paralelizables tras T-011-08.
No se utiliza paralelismo de escritura para cambiar el contrato ni para aprobar su política.

| Tarea | Regla/CA con mismo sufijo | Archivo | Función nominal de aceptación |
|---|---|---|---|
| T-011-01 | RN/CA-011-01 | test_boundary.py | test_closed_boundary_and_pure_execution |
| T-011-02 | RN/CA-011-02 | test_revisions.py | test_revision_selection_and_source_conflicts |
| T-011-03 | RN/CA-011-03 | test_arithmetic.py | test_exact_cents_and_fraction_boundaries |
| T-011-04 | RN/CA-011-04 | test_states.py | test_exactly_one_state_per_requested_rule |
| T-011-05 | RN/CA-011-05 | test_scopes.py | test_grain_and_denominator_no_double_count |
| T-011-06 | RN/CA-011-06 | test_evidence.py | test_evidence_graph_and_explanation_complete |
| T-011-07 | RN/CA-011-07 | test_replay.py | test_canonical_replay_across_processes |
| T-011-08 | RN/CA-011-08 | test_policy.py | test_finite_versioned_heuristic_catalog |
| T-011-09 | RN/CA-011-09 | test_single_bidder.py | test_single_bidder_golden_boundaries |
| T-011-10 | RN/CA-011-10 | test_share.py | test_contract_share_golden_boundaries |
| T-011-11 | RN/CA-011-11 | test_hhi.py | test_hhi_golden_boundaries |
| T-011-12 | RN/CA-011-12 | test_recurrence.py | test_recurrent_direct_golden_boundaries |
| T-011-13 | RN/CA-011-13 | test_unspent.py | test_budget_unspent_golden_boundaries |
| T-011-14 | RN/CA-011-14 | test_above_pim.py | test_budget_above_pim_golden_boundaries |
| T-011-15 | RN/CA-011-15 | test_deferred.py | test_deferred_rules_never_enter_core |
| T-011-16 | RN/CA-011-16 | test_migration.py | test_shadow_migration_preserves_history |

## Entregables y criterio por tarea

T-011-01: generar DTO cerrados y decoder uniforme; formatos, límites y efectos prohibidos pasan.
T-011-02: selector puro con tombstones y corroboración; conflictos no se resuelven por orden.
T-011-03: parseador de céntimos y racionales; comparación exacta y reducción verificadas.
T-011-04: unión de estados exhaustiva y precedencia de errores; no silencios ni PASS por ausencia.
T-011-05: validador de scopes; lotes, maestros y cobertura se reconcilian sin sumar granularidades.
T-011-06: refs íntegras y explicación; ningún candidato carece de dato/denominador/manifiesto.
T-011-07: serialización e identidad; hashes coinciden con vectores y replay multiproceso.
T-011-08: política finita compilada y bloqueada por versión; ningún parámetro oculto.
T-011-09 a T-011-14: implementar función pura por regla; vectores manuales y mutantes pasan.
T-011-15 depende además de las seis reglas: probar catálogo retirado y ausencia de efectos LLM.
T-011-16 depende de todas: adaptador privado, mapa, shadow y rollback sin mutar historia 004.

## Compuertas de cierre

Una tarea termina con su prueba inicialmente RED y finalmente GREEN sobre su aceptación.
No cuenta un test que compare el motor consigo mismo ni derive expected del código bajo prueba.
Se ejecutan pytest unitario/contrato, propiedades y replay sin red; cero skips/xfail ocultos.
El conjunto 011 debe conservar las 338 pruebas Python heredadas observadas en entrega anterior
[sin verificar en esta propuesta]; el número exacto se vuelve a medir antes de implementar.
Las pruebas Node existentes conservan su comprobación separada de las reglas 011.
La cobertura de ramas del núcleo debe ser 100% para estados y comparadores de umbral.
La cobertura global de líneas no sustituye los mutantes semánticos obligatorios del test-plan.
Debe cerrarse cada fila RN->CA->tarea->test y cada diferencia 004/011 del inventario.
Las aprobaciones humanas de spec, ADR y uso operativo de política son compuertas externas.
No se publica ninguna señal 011 durante esta secuencia técnica.


## Estado de implementación 2026-10-16

T-011-01 a T-011-16 tienen implementación privada y pruebas ejecutables con los nombres indicados.
El código vive en src/cajamarca_qhaway/capabilities/deterministic_engine/.
La CLI y shadow están en deterministic_cli.py y deterministic_shadow.py fuera del núcleo.
El informe docs/audits/2026-10-16-deterministic-engine-implementation.md identifica la evidencia.
Las compuertas de producción, calibración y piloto oficial siguen pendientes de datos y actas.
No se declara realizada una migración productiva ni verificación humana de documentos.
