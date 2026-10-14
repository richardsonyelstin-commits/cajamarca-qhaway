---
title: Tareas 003 - mef-ingestion
spec: "003"
capability: mef-ingestion
status: draft
source: ai
generator: codex-gpt-6
generated_at: 2026-10-14T21:53:14.441784+00:00
confidence: high
verified: false
---

# Tareas 003 - mef-ingestion

Las pruebas siguientes cubren la ruta oficial mensual implementada.
Las aclaraciones pendientes CKAN se conservan sin declarar la spec aprobada.
La certificacion live exige cobertura 14/14 en cada ejercicio y paridad con Supabase.

| Tarea | Criterio | Prueba o consulta |
|---|---|---|
| T-003-01 | CA-003-01 | `test_postbacks_renew_hidden_state_and_preserve_session` |
| T-003-02 | CA-003-02 / CA-003-07 | `test_raw_payload_keeps_original_display_columns_and_route` |
| T-003-03 | CA-003-03 | `test_mapea_municipalidad_por_sec_ejec_oficial_y_evidencia_provincial` |
| T-003-04 | CA-003-04 | `test_extracts_official_cut_date_and_strips_em_dash` |
| T-003-05 | CA-003-05 | `test_mef_poller_marks_null_records_as_failed` |
| T-003-06 | CA-003-06 | Consulta por `fiscal_year`: 14 filas y 14 `entity_id` distintos |
| T-003-07 | CA-003-07 | `test_official_budget_order_and_advance_are_validated` |
| T-003-08 | CA-003-07 | `test_missing_or_invalid_amount_is_not_zero` |

## Comandos de comprobacion

`python -m pytest tests/test_mef_consulta_amigable.py tests/test_mef_ingestion.py -v`
verifica el parser, estado y mapa.
`harvest run --historical --years 2024,2025,2026 --source mef` ejecuta la cosecha live.
`select fiscal_year,count(*),count(distinct entity_id) from budget_execution_records
 group by fiscal_year;` verifica la cobertura persistida.
