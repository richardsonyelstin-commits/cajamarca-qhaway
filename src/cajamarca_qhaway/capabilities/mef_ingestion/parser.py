"""Parser de registros de ejecucion presupuestal del MEF (capacidad 003-mef-ingestion).

Mapea registros al contrato canonico BudgetExecutionRecord, cruzando por entity_id
y ano fiscal, preservando el raw_payload integro (Articulo 10).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from cajamarca_qhaway.capabilities.entity_mapping.entity_id import normalize_ruc
from cajamarca_qhaway.models import BudgetExecutionRecord, ContractingEntity, compute_execution_record_id


def parse_mef_record(
    record: dict[str, Any],
    entities_by_ruc: dict[str, ContractingEntity],
    entities_by_id: dict[str, ContractingEntity],
    retrieved_at: datetime | None = None,
) -> BudgetExecutionRecord | None:
    """Parsea un registro presupuestal del MEF a un BudgetExecutionRecord canonico."""
    # Extraer identificador de entidad (por entity_id directo o por ruc)
    matched_entity: ContractingEntity | None = None
    raw_entity_id = record.get("entity_id") or record.get("id_entidad")
    if raw_entity_id and raw_entity_id in entities_by_id:
        matched_entity = entities_by_id[raw_entity_id]
    else:
        raw_ruc = str(record.get("ruc") or record.get("sec_ejec") or "").strip()
        if raw_ruc:
            try:
                norm_ruc = normalize_ruc(raw_ruc)
                if norm_ruc in entities_by_ruc:
                    matched_entity = entities_by_ruc[norm_ruc]
            except ValueError:
                pass

    if not matched_entity:
        return None

    # Extraer ano fiscal
    raw_year = record.get("fiscal_year") or record.get("ano_eje") or record.get("ano")
    if not raw_year:
        return None
    try:
        fiscal_year = int(raw_year)
    except (ValueError, TypeError):
        return None

    # Extraer montos
    raw_budgeted = (
        record.get("budgeted_amount")
        or record.get("pim")
        or record.get("monto_pim")
        or record.get("presupuesto")
        or 0.0
    )
    raw_executed = (
        record.get("executed_amount")
        or record.get("devengado")
        or record.get("monto_devengado")
        or record.get("ejecutado")
        or 0.0
    )

    try:
        budgeted_amount = float(raw_budgeted)
        executed_amount = float(raw_executed)
    except (ValueError, TypeError):
        return None

    budget_category = record.get("budget_category") or record.get("generica") or record.get("categoria")
    if budget_category is not None:
        budget_category = str(budget_category).strip()

    timestamp = retrieved_at or datetime.now(timezone.utc)
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)

    exec_id = compute_execution_record_id(matched_entity.entity_id, fiscal_year, budget_category)

    return BudgetExecutionRecord(
        execution_record_id=exec_id,
        entity_id=matched_entity.entity_id,
        fiscal_year=fiscal_year,
        budgeted_amount=budgeted_amount,
        executed_amount=executed_amount,
        budget_category=budget_category,
        raw_payload=record,
        source="mef-datastore",
        retrieved_at=timestamp,
    )
