---
title: Estado de cajamarca-qhaway
source: ai
generator: codex-gpt-6
generated_at: 2026-10-14T21:55:58.848146+00:00
confidence: high
verified: false
---

# Estado de cajamarca-qhaway

Rama de trabajo: `agent/codex/prod-cutover-v2`.
Supabase y spool conservan 14 entidades, 475 contrataciones y 42 presupuestos oficiales.
Cada ano 2024-2026 tiene 14 entidades; el corte oficial MEF es 2026-09-30.

## Estado de verificacion

- Cosecha historica MEF: 42 filas, codigo 0.
- Corrida puntual SEACE+MEF: 0 contratos nuevos y 14 presupuestos, codigo 0.
- Motor: 473 candidatos internos; alertas: 6 in_review, 2 discarded, 0 published.
- Supabase contra spool: 0 filas presupuestales faltantes o adicionales.
- Entidades: 14 perfiles SUNAT con payload y consulta, ademas de verified_at canonico.
- Suite final: 190 pruebas aprobadas; 3 pruebas de exportacion tras unificar el spool SEACE.
- Web audit: CONFORME; paridad MPA y accesibilidad estatica: PASS.
- Pyright y Ruff del extractor y oraculo MPA: PASS.
- CI de main y Vercel produccion Ready; PR 3 integrado en commit 83e6640.
- Worker cloud: bloqueado por host PostgreSQL directo IPv6 sin ruta en GitHub Actions.
- Opcion Session pooler implementada y comprobada con 21 pruebas de persistencia.
- Host confirmado y configurado: aws-1-ca-central-1.pooler.supabase.com.
- Worker: password authentication failed; falta actualizar la credencial en GitHub y Vercel.
- Hidratacion MPA: corregida la suma multianual, dos pruebas Node aprobadas.

## Decisiones confirmadas por la persona responsable

Se conservan los codigos MEF observados, incluido Cajamarca provincial SEC_EJEC 300549.
La procedencia de entidades se verifica con el contrato existente y perfiles SUNAT.
Las banderas internas quedan en Supabase y spool local ignorado por Git.
El snapshot publico omite candidatos, alertas sin dictamen y denuncias.

## Evidencia reproducible

`harvest run --historical --years 2024,2025,2026 --source mef`
`harvest run --once --source seace,mef`
`python -m cajamarca_qhaway.cli web audit`
`python scripts/audit_snapshot_parity.py`
`select fiscal_year,count(*),count(distinct entity_id) from budget_execution_records
 group by fiscal_year;`
