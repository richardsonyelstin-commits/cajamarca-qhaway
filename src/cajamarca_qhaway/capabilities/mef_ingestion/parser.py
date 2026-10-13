"""Parser de registros de ejecucion presupuestal del MEF (capacidad 003-mef-ingestion).

Mapea registros al contrato canonico BudgetExecutionRecord, cruzando por entity_id
y ano fiscal, preservando el raw_payload integro (Articulo 10).
"""

from __future__ import annotations

from datetime import datetime, timezone
import unicodedata
from typing import Any

from cajamarca_qhaway.capabilities.entity_mapping.entity_id import normalize_ruc
from cajamarca_qhaway.models import BudgetExecutionRecord, ContractingEntity, compute_execution_record_id


def _normalize_text(text: str) -> str:
    """Normaliza texto eliminando acentos y espacios superfluos."""
    decomposed = unicodedata.normalize("NFKD", text)
    stripped = "".join(c for c in decomposed if not unicodedata.combining(c))
    return " ".join(stripped.upper().split())


def _match_entity_from_mef(
    record: dict[str, Any],
    entities_by_ruc: dict[str, ContractingEntity],
    entities_by_id: dict[str, ContractingEntity],
) -> ContractingEntity | None:
    """Determina la entidad correspondiente para un registro presupuestal."""
    # 1. Cotejo directo por entity_id o id_entidad
    raw_entity_id = record.get("entity_id") or record.get("id_entidad")
    if raw_entity_id and raw_entity_id in entities_by_id:
        return entities_by_id[raw_entity_id]

    # 2. Cotejo por RUC explicito (variantes min/MAY)
    raw_ruc = str(
        record.get("ruc")
        or record.get("RUC")
        or record.get("ruc_entidad")
        or record.get("RUC_ENTIDAD")
        or record.get("sec_ejec")
        or record.get("SEC_EJEC")
        or ""
    ).strip()

    if raw_ruc:
        try:
            norm_ruc = normalize_ruc(raw_ruc)
            if norm_ruc in entities_by_ruc:
                return entities_by_ruc[norm_ruc]
        except ValueError:
            pass

    # 3. Cotejo institucional por departamento Cajamarca y pliego/ejecutora
    dep_code = str(record.get("DEPARTAMENTO_EJECUTORA") or record.get("departamento_ejecutora") or "").strip()
    dep_name = _normalize_text(str(record.get("DEPARTAMENTO_EJECUTORA_NOMBRE") or record.get("departamento") or ""))

    is_cajamarca = dep_code == "06" or "CAJAMARCA" in dep_name

    pliego = _normalize_text(str(record.get("PLIEGO_NOMBRE") or record.get("pliego_nombre") or record.get("PLIEGO") or ""))
    ejecutora = _normalize_text(str(record.get("EJECUTORA_NOMBRE") or record.get("ejecutora_nombre") or ""))
    nivel = str(record.get("NIVEL_GOBIERNO") or record.get("nivel_gobierno") or "").strip().upper()
    prov_name = _normalize_text(str(record.get("PROVINCIA_EJECUTORA_NOMBRE") or record.get("provincia") or ""))

    # GORE Cajamarca
    if is_cajamarca:
        if (
            nivel == "R"
            or "GOBIERNO REGIONAL" in pliego
            or "REGION CAJAMARCA" in pliego
            or "GOBIERNO REGIONAL" in ejecutora
            or "REGION CAJAMARCA" in ejecutora
        ):
            for ent in entities_by_id.values():
                if ent.entity_level == "regional" and ent.department.upper() == "CAJAMARCA":
                    return ent

    # Municipalidades Provinciales de Cajamarca
    if is_cajamarca or "CAJAMARCA" in pliego or "CAJAMARCA" in ejecutora:
        # Buscar coincidencia con alguna de las 13 provincias
        for ent in entities_by_id.values():
            if ent.province:
                norm_prov = _normalize_text(ent.province)
                if (
                    (nivel == "M" and norm_prov == prov_name)
                    or f"PROVINCIAL DE {norm_prov}" in pliego
                    or f"PROVINCIAL {norm_prov}" in pliego
                    or f"PROVINCIAL DE {norm_prov}" in ejecutora
                    or f"PROVINCIAL {norm_prov}" in ejecutora
                ):
                    return ent

    return None


def parse_mef_record(
    record: dict[str, Any],
    entities_by_ruc: dict[str, ContractingEntity],
    entities_by_id: dict[str, ContractingEntity],
    retrieved_at: datetime | None = None,
) -> BudgetExecutionRecord | None:
    """Parsea un registro presupuestal del MEF a un BudgetExecutionRecord canonico."""
    matched_entity = _match_entity_from_mef(record, entities_by_ruc, entities_by_id)
    if not matched_entity:
        return None

    # Extraer ano fiscal
    raw_year = (
        record.get("fiscal_year")
        or record.get("ano_eje")
        or record.get("ANO_EJE")
        or record.get("ano")
        or record.get("ANO")
    )
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
        or record.get("MONTO_PIM")
        or record.get("PIM")
        or record.get("MARCO_PRESUPUESTAL")
        or record.get("monto_asignado")
        or record.get("MONTO_ASIGNADO")
        or record.get("monto_pia")
        or record.get("MONTO_PIA")
        or record.get("PIA")
        or record.get("presupuesto")
        or 0.0
    )
    raw_executed = (
        record.get("executed_amount")
        or record.get("devengado")
        or record.get("monto_devengado")
        or record.get("MONTO_DEVENGADO")
        or record.get("DEVENGADO")
        or record.get("ejecutado")
        or 0.0
    )

    try:
        if isinstance(raw_budgeted, str):
            raw_budgeted = raw_budgeted.replace(",", "").strip()
        if isinstance(raw_executed, str):
            raw_executed = raw_executed.replace(",", "").strip()
        budgeted_amount = float(raw_budgeted)
        executed_amount = float(raw_executed)
    except (ValueError, TypeError):
        return None

    budget_category = (
        record.get("budget_category")
        or record.get("generica_nombre")
        or record.get("GENERICA_NOMBRE")
        or record.get("generica")
        or record.get("GENERICA")
        or record.get("categoria")
        or record.get("CATEGORIA_GASTO_NOMBRE")
    )
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
