"""Ingestor para ejecucion presupuestal del MEF (capacidad 003-mef-ingestion).

Soporta ingesta desacoplada desde memoria y archivos locales (fixtures / dumps de datos abiertos).
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from cajamarca_qhaway.capabilities.mef_ingestion.parser import parse_mef_record
from cajamarca_qhaway.models import BudgetExecutionRecord, ContractingEntity


class MefIngester:
    """Servicio de ingesta de ejecucion presupuestal del MEF."""

    def __init__(self, entities: list[ContractingEntity]) -> None:
        self.entities = entities
        self.entities_by_ruc = {e.ruc: e for e in entities}
        self.entities_by_id = {e.entity_id: e for e in entities}

    def ingest_records(
        self, records: list[dict[str, Any]], retrieved_at: datetime | None = None
    ) -> list[BudgetExecutionRecord]:
        """Procesa una lista de registros crudos del MEF."""
        timestamp = retrieved_at or datetime.now(timezone.utc)
        results: list[BudgetExecutionRecord] = []
        for raw in records:
            rec = parse_mef_record(
                record=raw,
                entities_by_ruc=self.entities_by_ruc,
                entities_by_id=self.entities_by_id,
                retrieved_at=timestamp,
            )
            if rec is not None:
                results.append(rec)
        return results

    def ingest_payload(
        self, payload: dict[str, Any] | list[dict[str, Any]], retrieved_at: datetime | None = None
    ) -> list[BudgetExecutionRecord]:
        """Ingiere un paquete con registros del datastore del MEF."""
        if isinstance(payload, list):
            return self.ingest_records(payload, retrieved_at=retrieved_at)
        elif isinstance(payload, dict):
            # Formato estandar CKAN datastore: {"result": {"records": [...]}}
            if "result" in payload and "records" in payload["result"]:
                return self.ingest_records(payload["result"]["records"], retrieved_at=retrieved_at)
            elif "records" in payload and isinstance(payload["records"], list):
                return self.ingest_records(payload["records"], retrieved_at=retrieved_at)
        return []

    def ingest_file(self, path: Path | str, retrieved_at: datetime | None = None) -> list[BudgetExecutionRecord]:
        """Carga e ingiere un archivo JSON local con datos de ejecucion del MEF."""
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"Archivo MEF no encontrado: {path}")
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
        return self.ingest_payload(data, retrieved_at=retrieved_at)
