"""Parser de registros de ejecucion presupuestal del MEF (capacidad 003-mef-ingestion).

Mapea filas originales del dataset oficial MEF listado en PNDA al contrato canónico
BudgetExecutionRecord, cruzando por entity_id y año fiscal, y preservando raw_payload
íntegro (Artículo 10). La página PNDA es catálogo; cada CSV se valida en su URL oficial
de distribución antes de aceptar filas.
"""

from __future__ import annotations

from datetime import datetime, timezone
import re
import unicodedata
from typing import Any

from cajamarca_qhaway.capabilities.entity_mapping.entity_id import normalize_ruc
from cajamarca_qhaway.models import BudgetExecutionRecord, ContractingEntity, compute_execution_record_id

PNDA_DATASET_URL = (
    "https://www.datosabiertos.gob.pe/dataset/"
    "presupuesto-y-ejecuci%C3%B3n-de-gasto"
)

GORE_CAJAMARCA_PLIEGO = "445"
MUNICIPAL_EXECUTOR_PROVINCES = {
    "300549": "CAJAMARCA",
    "300562": "CAJABAMBA",
    "300566": "CELENDIN",
    "300578": "CHOTA",
    "300597": "CONTUMAZA",
    "300605": "CUTERVO",
    "300620": "HUALGAYOC",
    "300623": "JAEN",
    "300635": "SAN IGNACIO",
    "300642": "SAN MARCOS",
    "300649": "SAN MIGUEL",
    "300662": "SAN PABLO",
    "300666": "SANTA CRUZ",
}


def _normalize_text(text: str) -> str:
    """Normaliza texto eliminando acentos y espacios superfluos."""
    text = text.replace("\u2014", "-")
    decomposed = unicodedata.normalize("NFKD", text)
    stripped = "".join(c for c in decomposed if not unicodedata.combining(c))
    return " ".join(stripped.upper().split())


def _normalize_siaf_code(value: Any) -> str:
    """Normaliza códigos enteros SIAF sin perder códigos alfanuméricos."""
    raw = str(value or "").strip()
    return raw.lstrip("0") or "0" if raw.isdigit() else raw


def _department_is_cajamarca(record: dict[str, Any]) -> bool:
    dep_code = _normalize_siaf_code(
        record.get("DEPARTAMENTO_EJECUTORA") or record.get("departamento_ejecutora")
    )
    dep_name = _normalize_text(
        str(
            record.get("DEPARTAMENTO_EJECUTORA_NOMBRE")
            or record.get("departamento_ejecutora_nombre")
            or record.get("departamento")
            or ""
        )
    )
    return dep_code == "6" or dep_name == "CAJAMARCA"


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

    # Un departamento explícito distinto de Cajamarca invalida los demás indicios.
    raw_department_code = record.get("DEPARTAMENTO_EJECUTORA") or record.get(
        "departamento_ejecutora"
    )
    raw_department_name = (
        record.get("DEPARTAMENTO_EJECUTORA_NOMBRE")
        or record.get("departamento_ejecutora_nombre")
        or record.get("departamento")
    )
    if (raw_department_code or raw_department_name) and not _department_is_cajamarca(record):
        return None

    # 2. Cotejo por RUC explícito de la ejecutora o entidad.
    raw_ruc = str(
        record.get("ruc")
        or record.get("RUC")
        or record.get("ruc_entidad")
        or record.get("RUC_ENTIDAD")
        or record.get("RUC_EJECUTORA")
        or record.get("ruc_ejecutora")
        or ""
    ).strip()

    if raw_ruc:
        try:
            norm_ruc = normalize_ruc(raw_ruc)
            if norm_ruc in entities_by_ruc:
                return entities_by_ruc[norm_ruc]
        except ValueError:
            pass

    # 3. En SIAF, 445 es PLIEGO regional. Las municipales se cotejan por el SEC_EJEC
    # provincial oficial del MEF; no se infiere provincia a partir de un rango.
    level = str(record.get("NIVEL_GOBIERNO") or record.get("nivel_gobierno") or "")
    level = level.strip().upper()
    pliego_code = _normalize_siaf_code(record.get("PLIEGO") or record.get("pliego"))
    if level == "R" and pliego_code == GORE_CAJAMARCA_PLIEGO:
        return next(
            (
                entity
                for entity in entities_by_id.values()
                if entity.entity_level == "regional"
                and entity.ruc == "20453744168"
            ),
            None,
        )

    executor_codes = (
        record.get("SEC_EJEC"),
        record.get("sec_ejec"),
        record.get("EJECUTORA"),
        record.get("ejecutora"),
    )
    province_code = next(
        (
            _normalize_siaf_code(code)
            for code in executor_codes
            if _normalize_siaf_code(code) in MUNICIPAL_EXECUTOR_PROVINCES
        ),
        None,
    )
    if level == "M" and province_code:
        expected_province = MUNICIPAL_EXECUTOR_PROVINCES[province_code]
        source_province = _normalize_text(
            str(
                record.get("PROVINCIA_EJECUTORA_NOMBRE")
                or record.get("provincia_ejecutora_nombre")
                or record.get("provincia")
                or ""
            )
        )
        source_executor_name = _normalize_text(
            str(
                record.get("EJECUTORA_NOMBRE")
                or record.get("ejecutora_nombre")
                or record.get("PLIEGO_NOMBRE")
                or record.get("pliego_nombre")
                or ""
            )
        )
        # SEC_EJEC alone is not enough to identify a provincial municipality:
        # the official SIAF extract also contains district municipalities whose
        # province happens to be one of the 13 provinces in scope. When RUC is
        # unavailable, require the official executor name to say "provincial".
        if (
            not source_province
            or not source_executor_name
            or "DISTRITAL" in source_executor_name
            or "PROVINCIAL" not in source_executor_name
        ):
            return None
        if source_province != expected_province:
            return None
        province = expected_province
        return next(
            (
                entity
                for entity in entities_by_id.values()
                if entity.entity_level == "provincial_municipality"
                and _normalize_text(entity.province or "") == province
            ),
            None,
        )

    # Rechazar códigos de unidad ejecutora fuera del universo canónico.
    if any(_normalize_siaf_code(code).startswith("3006") for code in executor_codes if code):
        return None

    # 4. Compatibilidad con versiones de conjuntos que traen departamento explicito.
    is_cajamarca = _department_is_cajamarca(record)

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
    budget_keys = (
        "budgeted_amount", "pim", "monto_pim", "MONTO_PIM", "PIM", "MARCO_PRESUPUESTAL",
        "monto_asignado", "MONTO_ASIGNADO", "monto_pia", "MONTO_PIA", "PIA", "presupuesto",
    )
    execution_keys = (
        "executed_amount", "devengado", "monto_devengado", "MONTO_DEVENGADO", "DEVENGADO", "ejecutado",
    )
    raw_budgeted = next((record[key] for key in budget_keys if key in record and record[key] is not None and record[key] != ""), None)
    raw_executed = next(
        (
            record[key]
            for key in execution_keys
            if key in record and record[key] is not None and record[key] != ""
        ),
        None,
    )
    if raw_executed is None:
        monthly_values = [
            value
            for key, value in record.items()
            if re.fullmatch(r"MONTO_DEVENGADO_(?:0?[1-9]|1[0-2])", str(key).upper())
            and value is not None
            and str(value).strip() != ""
        ]
        if monthly_values:
            try:
                raw_executed = sum(
                    float(value.replace(",", "").strip())
                    if isinstance(value, str)
                    else float(value)
                    for value in monthly_values
                )
            except (ValueError, TypeError):
                return None
    if raw_budgeted is None or raw_executed is None:
        return None

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
