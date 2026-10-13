"""Sincronizador integral de datos historicos y recientes a Supabase oglltrpvvifqvwmxmkjq.
Carga las 14 entidades, 474 contrataciones, 89 ejecuciones presupuestales,
439 banderas rojas, 4 alertas auditadas y 2 reportes ciudadanos con idempotencia total.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

from scripts.verification.supabase_admin import execute_sql


def sql_str(val: Any) -> str:
    if val is None:
        return "NULL"
    cleaned = str(val).replace("\x00", "").replace("'", "''")
    return f"'{cleaned}'"


def sql_num(val: Any) -> str:
    if val is None or (isinstance(val, float) and (math.isnan(val) or math.isinf(val))):
        return "NULL"
    return str(val)


def sql_int(val: Any) -> str:
    if val is None:
        return "NULL"
    try:
        return str(int(val))
    except (ValueError, TypeError):
        return "NULL"


def sql_bool(val: Any) -> str:
    if val is None:
        return "NULL"
    return "TRUE" if val else "FALSE"


def sql_jsonb(val: Any) -> str:
    if val is None:
        return "'{}'::jsonb"
    s = json.dumps(val, ensure_ascii=False).replace("\x00", "").replace("'", "''")
    return f"'{s}'::jsonb"


def sync_entities(entities: list[dict]) -> int:
    print(f"[*] Sincronizando {len(entities)} contracting_entities...")
    values = []
    for e in entities:
        v = (
            f"({sql_str(e['entity_id'])}, "
            f"{sql_str(e['official_name'])}, "
            f"{sql_str(e['entity_level'])}, "
            f"{sql_str(e.get('province'))}, "
            f"{sql_str(e['ruc'])}, "
            f"{sql_str(e.get('consucode_id'))}, "
            f"{sql_str(e.get('department', 'CAJAMARCA'))}, "
            f"{sql_str(e['verified_at'])}, "
            f"{sql_bool(e.get('active', True))})"
        )
        values.append(v)

    query = f"""
    INSERT INTO contracting_entities (
        entity_id, official_name, entity_level, province, ruc, consucode_id, department, verified_at, active
    ) VALUES
    {', '.join(values)}
    ON CONFLICT (entity_id) DO UPDATE SET
        official_name = EXCLUDED.official_name,
        entity_level = EXCLUDED.entity_level,
        province = EXCLUDED.province,
        ruc = EXCLUDED.ruc,
        consucode_id = EXCLUDED.consucode_id,
        department = EXCLUDED.department,
        verified_at = EXCLUDED.verified_at,
        active = EXCLUDED.active;
    """
    execute_sql(query)
    print(f"[+] {len(entities)} contracting_entities sincronizadas.")
    return len(entities)


def sync_procurements(procurements: list[dict], batch_size: int = 25) -> int:
    total = len(procurements)
    print(f"[*] Sincronizando {total} procurement_records en lotes de {batch_size}...")
    inserted = 0

    for i in range(0, total, batch_size):
        chunk = procurements[i : i + batch_size]
        values = []
        for p in chunk:
            v = (
                f"({sql_str(p['procurement_id'])}, "
                f"{sql_str(p['ocid'])}, "
                f"{sql_str(p['entity_id'])}, "
                f"{sql_str(p['title'])}, "
                f"{sql_str(p.get('procurement_method'))}, "
                f"{sql_num(p.get('awarded_amount'))}, "
                f"{sql_num(p.get('executed_amount'))}, "
                f"{sql_int(p.get('number_of_bidders'))}, "
                f"{sql_str(p.get('supplier_name'))}, "
                f"{sql_str(p.get('supplier_ruc'))}, "
                f"{sql_jsonb(p.get('raw_payload', {}))}, "
                f"{sql_str(p.get('source', 'seace-ocds'))}, "
                f"{sql_str(p['retrieved_at'])})"
            )
            values.append(v)

        query = f"""
        INSERT INTO procurement_records (
            procurement_id, ocid, entity_id, title, procurement_method,
            awarded_amount, executed_amount, number_of_bidders, supplier_name,
            supplier_ruc, raw_payload, source, retrieved_at
        ) VALUES
        {', '.join(values)}
        ON CONFLICT (procurement_id) DO UPDATE SET
            ocid = EXCLUDED.ocid,
            entity_id = EXCLUDED.entity_id,
            title = EXCLUDED.title,
            procurement_method = EXCLUDED.procurement_method,
            awarded_amount = EXCLUDED.awarded_amount,
            executed_amount = EXCLUDED.executed_amount,
            number_of_bidders = EXCLUDED.number_of_bidders,
            supplier_name = EXCLUDED.supplier_name,
            supplier_ruc = EXCLUDED.supplier_ruc,
            raw_payload = EXCLUDED.raw_payload,
            source = EXCLUDED.source,
            retrieved_at = EXCLUDED.retrieved_at;
        """
        execute_sql(query)
        inserted += len(chunk)
        print(f"  -> Lote {i // batch_size + 1}: {inserted}/{total} procesados...")

    print(f"[+] {inserted} procurement_records sincronizadas.")
    return inserted


def sync_budget_executions(budgets: list[dict], batch_size: int = 25) -> int:
    total = len(budgets)
    print(f"[*] Sincronizando {total} budget_execution_records en lotes de {batch_size}...")
    inserted = 0

    for i in range(0, total, batch_size):
        chunk = budgets[i : i + batch_size]
        values = []
        for b in chunk:
            v = (
                f"({sql_str(b['execution_record_id'])}, "
                f"{sql_str(b['entity_id'])}, "
                f"{sql_int(b['fiscal_year'])}, "
                f"{sql_num(b.get('budgeted_amount', 0.0))}, "
                f"{sql_num(b.get('executed_amount', 0.0))}, "
                f"{sql_str(b.get('budget_category'))}, "
                f"{sql_jsonb(b.get('raw_payload', {}))}, "
                f"{sql_str(b.get('source', 'mef-datastore'))}, "
                f"{sql_str(b['retrieved_at'])})"
            )
            values.append(v)

        query = f"""
        INSERT INTO budget_execution_records (
            execution_record_id, entity_id, fiscal_year, budgeted_amount,
            executed_amount, budget_category, raw_payload, source, retrieved_at
        ) VALUES
        {', '.join(values)}
        ON CONFLICT (execution_record_id) DO UPDATE SET
            entity_id = EXCLUDED.entity_id,
            fiscal_year = EXCLUDED.fiscal_year,
            budgeted_amount = EXCLUDED.budgeted_amount,
            executed_amount = EXCLUDED.executed_amount,
            budget_category = EXCLUDED.budget_category,
            raw_payload = EXCLUDED.raw_payload,
            source = EXCLUDED.source,
            retrieved_at = EXCLUDED.retrieved_at;
        """
        execute_sql(query)
        inserted += len(chunk)
        print(f"  -> Lote {i // batch_size + 1}: {inserted}/{total} procesados...")

    print(f"[+] {inserted} budget_execution_records sincronizadas.")
    return inserted


def sync_red_flags(flags: list[dict], batch_size: int = 50) -> int:
    total = len(flags)
    print(f"[*] Sincronizando {total} red_flags en lotes de {batch_size}...")
    inserted = 0

    for i in range(0, total, batch_size):
        chunk = flags[i : i + batch_size]
        values = []
        for f in chunk:
            v = (
                f"({sql_str(f['red_flag_id'])}, "
                f"{sql_str(f['indicator_code'])}, "
                f"{sql_str(f['formula_description'])}, "
                f"{sql_str(str(f['threshold']))}, "
                f"{sql_str(str(f['observed_value']))}, "
                f"{sql_jsonb(f.get('procurement_ids', []))}, "
                f"{sql_jsonb(f.get('execution_record_ids', []))}, "
                f"{sql_str(f['evidence_source'])}, "
                f"{sql_str(f['evidence_retrieved_at'])}, "
                f"{sql_str(f['generated_at'])})"
            )
            values.append(v)

        query = f"""
        INSERT INTO red_flags (
            red_flag_id, indicator_code, formula_description, threshold,
            observed_value, procurement_ids, execution_record_ids, evidence_source,
            evidence_retrieved_at, generated_at
        ) VALUES
        {', '.join(values)}
        ON CONFLICT (red_flag_id) DO UPDATE SET
            indicator_code = EXCLUDED.indicator_code,
            formula_description = EXCLUDED.formula_description,
            threshold = EXCLUDED.threshold,
            observed_value = EXCLUDED.observed_value,
            procurement_ids = EXCLUDED.procurement_ids,
            execution_record_ids = EXCLUDED.execution_record_ids,
            evidence_source = EXCLUDED.evidence_source,
            evidence_retrieved_at = EXCLUDED.evidence_retrieved_at,
            generated_at = EXCLUDED.generated_at;
        """
        execute_sql(query)
        inserted += len(chunk)
        print(f"  -> Lote {i // batch_size + 1}: {inserted}/{total} procesados...")

    print(f"[+] {inserted} red_flags sincronizadas.")
    return inserted


def sync_alerts(alerts: list[dict]) -> int:
    print(f"[*] Sincronizando {len(alerts)} alerts...")
    values = []
    for a in alerts:
        v = (
            f"({sql_str(a['alert_id'])}, "
            f"{sql_jsonb(a['red_flag_ids'])}, "
            f"{sql_str(a['entity_id'])}, "
            f"{sql_str(a['status'])}, "
            f"{sql_str(a['reviewed_by'])}, "
            f"{sql_str(a['reviewed_at'])}, "
            f"{sql_str(a.get('review_notes'))}, "
            f"{sql_str(a['disclaimer'])}, "
            f"{sql_str(a.get('published_at'))})"
        )
        values.append(v)

    query = f"""
    INSERT INTO alerts (
        alert_id, red_flag_ids, entity_id, status, reviewed_by,
        reviewed_at, review_notes, disclaimer, published_at
    ) VALUES
    {', '.join(values)}
    ON CONFLICT (alert_id) DO UPDATE SET
        red_flag_ids = EXCLUDED.red_flag_ids,
        entity_id = EXCLUDED.entity_id,
        status = EXCLUDED.status,
        reviewed_by = EXCLUDED.reviewed_by,
        reviewed_at = EXCLUDED.reviewed_at,
        review_notes = EXCLUDED.review_notes,
        disclaimer = EXCLUDED.disclaimer,
        published_at = EXCLUDED.published_at;
    """
    execute_sql(query)
    print(f"[+] {len(alerts)} alerts sincronizadas.")
    return len(alerts)


def sync_citizen_reports(reports: list[dict]) -> int:
    print(f"[*] Sincronizando {len(reports)} citizen_reports...")
    values = []
    for r in reports:
        v = (
            f"({sql_str(r['report_id'])}, "
            f"{sql_str(r['submitted_at'])}, "
            f"{sql_str(r['channel'])}, "
            f"{sql_str(r['raw_text'])}, "
            f"{sql_str(r.get('related_entity_id'))}, "
            f"{sql_str(r['moderation_status'])}, "
            f"{sql_str(r.get('moderated_by'))}, "
            f"{sql_str(r.get('moderated_at'))}, "
            f"{sql_bool(r.get('legal_disclaimer_shown', True))})"
        )
        values.append(v)

    query = f"""
    INSERT INTO citizen_reports (
        report_id, submitted_at, channel, raw_text, related_entity_id,
        moderation_status, moderated_by, moderated_at, legal_disclaimer_shown
    ) VALUES
    {', '.join(values)}
    ON CONFLICT (report_id) DO UPDATE SET
        submitted_at = EXCLUDED.submitted_at,
        channel = EXCLUDED.channel,
        raw_text = EXCLUDED.raw_text,
        related_entity_id = EXCLUDED.related_entity_id,
        moderation_status = EXCLUDED.moderation_status,
        moderated_by = EXCLUDED.moderated_by,
        moderated_at = EXCLUDED.moderated_at,
        legal_disclaimer_shown = EXCLUDED.legal_disclaimer_shown;
    """
    execute_sql(query)
    print(f"[+] {len(reports)} citizen_reports sincronizadas.")
    return len(reports)


def main() -> None:
    snapshot_path = Path("web/src/data/verified-snapshot.json")
    if not snapshot_path.exists():
        raise FileNotFoundError(f"No se encontro {snapshot_path}")

    with open(snapshot_path, encoding="utf-8") as f:
        data = json.load(f)

    print("=== INICIANDO SINCRONIZACION COMPLETA A SUPABASE (oglltrpvvifqvwmxmkjq) ===")
    sync_entities(data["contracting_entities"])
    sync_procurements(data["procurement_records"], batch_size=25)
    sync_budget_executions(data["budget_execution_records"], batch_size=25)
    sync_red_flags(data["red_flags"], batch_size=50)
    sync_alerts(data["alerts"])
    sync_citizen_reports(data["citizen_reports"])

    print("\n=== VERIFICANDO CONTEOS EN SUPABASE ===")
    tables = [
        "contracting_entities",
        "procurement_records",
        "budget_execution_records",
        "red_flags",
        "alerts",
        "citizen_reports",
    ]
    for t in tables:
        cnt = execute_sql(f"SELECT count(*) FROM {t};")
        print(f"  - {t}: {cnt[0]['count']} registros")

    print("\n=== DESGLOSE ANUAL EN SUPABASE ===")
    # Conteo de contrataciones por anio segun ocid o retrieved_at
    p_by_year = execute_sql(
        """
        SELECT
            CASE
                WHEN ocid ~ '-2024-' OR retrieved_at::text ~ '^2024' THEN '2024'
                WHEN ocid ~ '-2025-' OR retrieved_at::text ~ '^2025' THEN '2025'
                WHEN ocid ~ '-2026-' OR retrieved_at::text ~ '^2026' THEN '2026'
                ELSE 'otro'
            END as year,
            count(*) as count
        FROM procurement_records
        GROUP BY 1
        ORDER BY 1;
        """
    )
    print("Contrataciones por anio:")
    for row in p_by_year:
        print(f"  {row['year']}: {row['count']}")

    b_by_year = execute_sql(
        """
        SELECT fiscal_year, count(*) as count
        FROM budget_execution_records
        GROUP BY fiscal_year
        ORDER BY fiscal_year;
        """
    )
    print("Ejecuciones presupuestales por anio fiscal:")
    for row in b_by_year:
        print(f"  {row['fiscal_year']}: {row['count']}")


if __name__ == "__main__":
    main()
