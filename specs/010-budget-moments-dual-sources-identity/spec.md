---
title: Presupuesto reconciliado, fuentes duales e identidad
status: draft
source: ai
generator: codex
generated_at: 2026-10-16T07:18:34.441452+00:00
confidence: high
verified: false
updated: 2026-10-16
---

# Presupuesto reconciliado, fuentes duales e identidad

## Estado contrastado (2026-10-16)

La implementación local correspondiente está en [código](../../src/cajamarca_qhaway/models/).
El estado draft se conserva: tener implementación no constituye aprobación documental.
Las reglas siguientes son requisitos y diseño; no certifican cobertura o servicios remotos.

El encargo humano define el alcance y autoriza implementar modelo, conectores y vistas.
La propuesta ADR 0013 registra las decisiones sin alterar ADR aceptados.
Cada criterio siguiente se verifica antes de declarar cobertura o desplegar.

## Reglas y criterios

RN-010-01: un maestro institucional por entidad y ejercicio, sin sumar hijos.
CA-010-01: PIM total coincide con Proyecto + Actividad, tolerancia S/ 1.
Prueba: tests/test_budget_reconciliation_v2.py::test_scope_orthogonality_rejects_mismatch.
Prueba: tests/test_budget_reconciliation_v2.py::test_canonical_selection_rejects_duplicate_total.

RN-010-02: momentos finitos y consistentes; modificaciones=PIM-PIA.
CA-010-02: se rechazan NaN, orden invalido, avance inconsistente y fechas divergentes.
Prueba: tests/test_budget_reconciliation_v2.py::test_moments_and_funding_reconcile.

RN-010-03: solo Quien gasta y fecha real de cada modulo.
CA-010-03: nunca se usa BtnDepartamentoMeta aunque aparezca antes de BtnDepartamento.
Prueba: tests/test_budget_reconciliation_v2.py::test_geographic_department_is_never_posted.

RN-010-04: Fuente y Rubro son jerarquias, con filas originales preservadas.
CA-010-04: la suma de fuentes y la de sus rubros reconcilian con su padre.
Prueba: tests/test_budget_reconciliation_v2.py::test_moments_and_funding_reconcile.

RN-010-05: adaptadores oficiales conservan sesion y no inventan identificadores.
CA-010-05: Pentaho descubre recursos reales, filtra RUC en streaming y deduplica por ID oficial.
Prueba: tests/test_dual_procurement_sources.py::test_pentaho_session_discovery_and_ruc_filter.
CA-010-06: JSF renueva ViewState por respuesta XML y registra CAPTCHA o expiracion como brecha.
Prueba: tests/test_dual_procurement_sources.py::test_jsf_rotates_viewstate_and_reports_challenge.

RN-010-06: las 475 contrataciones y sus payload OCDS se preservan.
CA-010-07: evidencia dual se vincula por RUC e ID de proceso, sin coincidencia difusa.
Prueba: tests/test_dual_procurement_sources.py::test_cross_source_identity_preserves_procurement.

RN-010-07: identidad oficial y todos los anclajes funcionales se conservan.
CA-010-08: se verifican los 330 IDs de las 16 vistas y los atributos data-* de la linea base.
Prueba: tests/test_identity_dom_contract.py::test_dom_anchor_baseline_is_preserved.
CA-010-09: fuentes, tokens y activos locales servidos, sin fuentes de Google o Tailwind remoto.
Prueba: tests/test_identity_dom_contract.py::test_official_brand_assets_are_self_hosted.

RN-010-08: HTML inicial, datos SQL, snapshot e hidratacion usan el mismo maestro, ano y corte.
CA-010-10: cambiar ano, ambito y corte no suma particiones ni confunde devengado con girado.
Prueba: tests/budget-period.test.mjs.
Prueba: tests/budget-breakdown.test.mjs.
Prueba: scripts/audit_snapshot_parity.py.

## Oraculos operativos

Los cuadros de control provienen del sondeo institucional real.
Los presupuestos no se sustituyen en produccion hasta validar las 42 filas completas.
La igualdad SQL se comprueba en todos los campos con EXCEPT bidireccional.
Los conectores no declaran salud por cargar una portada vacia o encontrar un CAPTCHA.
Ninguna candidata se publica como alerta sin revision humana real.
