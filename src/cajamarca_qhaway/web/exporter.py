"""Exporta una instantánea web desde spools de registros verificados.

Los spools de entrada se sincronizan desde Supabase. El exportador no crea datos,
no publica candidatos y no inventa decisiones de revisión humana.
"""

from __future__ import annotations

import json
import os
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from cajamarca_qhaway.capabilities.entity_mapping.dataset import load_universe
from cajamarca_qhaway.capabilities.red_flags_engine.engine import RedFlagsEngine
from cajamarca_qhaway.models import (
    Alert,
    BudgetExecutionRecord,
    CitizenReport,
    ContractingEntity,
    ProcurementRecord,
    RedFlag,
)
from cajamarca_qhaway.models.budget_reconciliation import canonical_budget_records

DEFAULT_SNAPSHOT_PATH = Path("web/src/data/verified-snapshot.json")
PROCUREMENT_SPOOL_CANDIDATES = (
    Path("data/harvested/procurements_all.jsonl"),
    Path("data/harvested/live-cutover-v2/procurements_all.jsonl"),
)
BUDGET_SPOOL_CANDIDATES = (
    Path("data/harvested/budget_executions_all.jsonl"),
    Path("data/harvested/budget_executions_2026-10-13.jsonl"),
    Path("data/harvested/live-cutover-v2/budget_executions_all.jsonl"),
)
REDFLAG_SPOOL_CANDIDATES = (
    Path("data/harvested/red_flags_all.jsonl"),
    Path("data/harvested/live-cutover-v2/red_flags.jsonl"),
)
ALERT_SUMMARY_CANDIDATES = (Path("data/harvested/alerts_summary.json"),)


def _first_existing(paths: tuple[Path, ...]) -> Path:
    for path in paths:
        if path.is_file():
            return path
    raise FileNotFoundError(f"No se encontro un spool requerido: {paths}")


def _read_jsonl[ModelT: BaseModel](path: Path, model: type[ModelT]) -> list[ModelT]:
    records: list[ModelT] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
            retrieved_at = value.get("retrieved_at")
            if isinstance(retrieved_at, str):
                parsed = datetime.fromisoformat(retrieved_at)
                if parsed.tzinfo is None:
                    raise ValueError("retrieved_at no incluye zona horaria")
                value["retrieved_at"] = parsed.astimezone(UTC)
            record = model.model_validate(value)
            if isinstance(record, BudgetExecutionRecord) and not record.raw_payload:
                raise ValueError("raw_payload esta vacio")
            records.append(record)
        except Exception as exc:
            raise ValueError(f"Registro invalido en {path}:{line_number}: {exc}") from exc
    return records


def _model_dump(records: Sequence[BaseModel]) -> list[dict[str, Any]]:
    return [record.model_dump(mode="json") for record in records]


def build_verified_web_snapshot(now: datetime | None = None) -> dict[str, Any]:
    """Construye un snapshot usando solo las filas reales disponibles en los spools."""
    generated_at = now or datetime.now(UTC)
    if generated_at.tzinfo is None:
        raise ValueError("generated_at debe incluir zona horaria")
    generated_at = generated_at.astimezone(UTC)

    entities = [ContractingEntity.model_validate(item) for item in load_universe().contracting_entities]
    if len(entities) != 14 or len({entity.entity_id for entity in entities}) != 14:
        raise ValueError("El universo debe contener exactamente 14 entity_id unicos")
    entity_ids = {entity.entity_id for entity in entities}

    procurements = _read_jsonl(_first_existing(PROCUREMENT_SPOOL_CANDIDATES), ProcurementRecord)
    budgets = canonical_budget_records(
        _read_jsonl(_first_existing(BUDGET_SPOOL_CANDIDATES), BudgetExecutionRecord)
    )
    if not procurements:
        raise ValueError("Circuit breaker: no hay contrataciones verificables")
    if not budgets:
        raise ValueError("Circuit breaker: no hay registros MEF verificables")
    for record in [*procurements, *budgets]:
        if record.entity_id not in entity_ids:
            raise ValueError(f"Registro fuera del universo canonico: {record.entity_id}")
    if len({record.procurement_id for record in procurements}) != len(procurements):
        raise ValueError("El spool SEACE contiene procurement_id duplicados")
    if len({record.execution_record_id for record in budgets}) != len(budgets):
        raise ValueError("El spool MEF contiene execution_record_id duplicados")

    red_flags: list[RedFlag] = []
    for path in REDFLAG_SPOOL_CANDIDATES:
        if path.is_file():
            red_flags = _read_jsonl(path, RedFlag)
            break
    else:
        red_flags = RedFlagsEngine().evaluate(procurements, budgets, now=generated_at)
    candidate_count = len(red_flags)
    alert_summary_path = next((path for path in ALERT_SUMMARY_CANDIDATES if path.is_file()), None)
    alert_summary = json.loads(alert_summary_path.read_text(encoding="utf-8")) if alert_summary_path else {}
    alert_status_counts = alert_summary.get("status_counts", {})
    total_alerts = sum(int(value) for value in alert_status_counts.values())
    total_published_alerts = int(alert_status_counts.get("published", 0))
    years = sorted({record.fiscal_year for record in budgets})
    if any({r.entity_id for r in budgets if r.fiscal_year == year} != entity_ids for year in years):
        raise ValueError("Cobertura MEF incompleta en un ejercicio fiscal")
    coverage = {
        str(year): {
            "records": sum(1 for record in budgets if record.fiscal_year == year),
            "entities": len({record.entity_id for record in budgets if record.fiscal_year == year}),
        }
        for year in years
    }

    snapshot: dict[str, Any] = {
        "metadata": {
            "version": "1.0.0",
            "generated_at": generated_at.isoformat().replace("+00:00", "Z"),
            "source": "supabase-synchronized-spool",
            "region": "CAJAMARCA",
            "constitution_version": "1.0",
            "articles_covered": [10, 14, 15, 16, 17, 18, 19],
            "total_entities": len(entities),
            "total_procurements": len(procurements),
            "total_budget_executions": len(budgets),
            "budget_coverage_by_year": coverage,
            "total_candidate_red_flags": candidate_count,
            "total_alerts": total_alerts,
            "total_published_alerts": total_published_alerts,
            "alert_status_counts": alert_status_counts,
            "total_citizen_reports": 0,
            "total_geospatial_works": 0,
        },
        "contracting_entities": _model_dump(entities),
        "procurement_records": _model_dump(procurements),
        "budget_execution_records": _model_dump(budgets),
        "red_flags": [],
        "alerts": [],
        "citizen_reports": [],
        "geospatial_works": [],
        "geospatial_signals": [],
    }
    _validate_snapshot(snapshot)
    return snapshot


def _validate_snapshot(snapshot: dict[str, Any]) -> None:
    entities = [ContractingEntity.model_validate(row) for row in snapshot["contracting_entities"]]
    procurements = [ProcurementRecord.model_validate(row) for row in snapshot["procurement_records"]]
    budgets = [BudgetExecutionRecord.model_validate(row) for row in snapshot["budget_execution_records"]]
    for row in snapshot["red_flags"]:
        RedFlag.model_validate(row)
    for row in snapshot["alerts"]:
        Alert.model_validate(row)
    for row in snapshot["citizen_reports"]:
        CitizenReport.model_validate(row)
    if len(entities) != snapshot["metadata"]["total_entities"]:
        raise ValueError("Conteo de entidades inconsistente")
    if len(procurements) != snapshot["metadata"]["total_procurements"]:
        raise ValueError("Conteo SEACE inconsistente")
    if len(budgets) != snapshot["metadata"]["total_budget_executions"]:
        raise ValueError("Conteo MEF inconsistente")
    if len(snapshot["red_flags"]) > snapshot["metadata"]["total_candidate_red_flags"]:
        raise ValueError("El snapshot expone mas candidatos que los contabilizados")


def export_verified_snapshot(output_path: Path | str = DEFAULT_SNAPSHOT_PATH) -> Path:
    """Valida y reemplaza atómicamente el snapshot solo después de pasar el circuito."""
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    snapshot = build_verified_web_snapshot()
    encoded = json.dumps(snapshot, separators=(",", ":"), ensure_ascii=True)
    _validate_snapshot(json.loads(encoded))
    temporary = out.with_name(out.name + ".tmp")
    try:
        with temporary.open("w", encoding="utf-8", newline="") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, out)
    finally:
        if temporary.exists():
            temporary.unlink()
    return out


if __name__ == "__main__":
    print(f"Snapshot verificado exportado: {export_verified_snapshot()}")
