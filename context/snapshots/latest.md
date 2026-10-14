---
title: Estado de cajamarca-qhaway
source: ai
generator: codex-gpt-6
generated_at: 2026-10-14T22:59:05Z
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
- Suite final CI: 201 pruebas Python y 3 pruebas Node aprobadas.
- Web audit: CONFORME; paridad MPA y accesibilidad estatica: PASS.
- Pyright y Ruff del extractor y oraculo MPA: PASS.
- CI de main y Vercel produccion Ready; PR 3, 4 y 5 integrados en commit 4764283.
- Pooler IPv4 confirmado; 25 pruebas locales de persistencia y WSGI aprobadas.
- Host confirmado y configurado: aws-1-ca-central-1.pooler.supabase.com.
- Worker vinculado al entorno GitHub Production del proyecto, cuyo secreto se actualizo hoy.
- Secreto de entorno actualizado el 2026-10-14T22:54:28Z; el marcador ya fue sustituido.
- Guardia cloud: proyecto, rol, pooler y base correctos; password_placeholder: false.
- Dos intentos posteriores fallan al autenticar; pendiente validacion privada de contrasena y URI.
- Vercel redesplegado Ready; el snapshot remoto sigue siendo identico al local.
- Persistencia: 27 pruebas locales aprobadas, incluidas cinco comprobaciones de la guardia.
- Hidratacion MPA: corregida la suma multianual, dos pruebas Node aprobadas.
- Navegador de produccion: PIM 5,980,488,974, devengado 3,926,357,702 y avance 65.7%.
- Denuncias cloud: HTTP 503 hasta disponer de persistencia confirmable en el adaptador.

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
