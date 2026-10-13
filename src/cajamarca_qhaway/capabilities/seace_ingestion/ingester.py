"""Ingestor para SEACE/OCDS (capacidad 002-seace-ingestion).

Soporta ingesta desacoplada de payloads en memoria, archivos locales y respuestas HTTP,
garantizando operacion determinista sin depender de conectividad externa.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from cajamarca_qhaway.capabilities.seace_ingestion.parser import parse_ocds_release
from cajamarca_qhaway.models import ContractingEntity, ProcurementRecord


class SeaceIngester:
    """Servicio de ingesta de contrataciones publicas desde el feed OCDS de OECE."""

    def __init__(self, entities: list[ContractingEntity]) -> None:
        self.entities = entities
        self.entities_by_ruc = {e.ruc: e for e in entities}
        self.entities_by_consucode = {e.consucode_id: e for e in entities if e.consucode_id}

    def ingest_releases(
        self, releases: list[dict[str, Any]], retrieved_at: datetime | None = None
    ) -> list[ProcurementRecord]:
        """Procesa una lista de releases OCDS y retorna los records que pertenecen a Cajamarca."""
        timestamp = retrieved_at or datetime.now(timezone.utc)
        records: list[ProcurementRecord] = []
        for rel in releases:
            rec = parse_ocds_release(
                release=rel,
                entities_by_ruc=self.entities_by_ruc,
                entities_by_consucode=self.entities_by_consucode,
                retrieved_at=timestamp,
            )
            if rec is not None:
                records.append(rec)
        return records

    def ingest_payload(
        self, payload: dict[str, Any], retrieved_at: datetime | None = None
    ) -> list[ProcurementRecord]:
        """Ingiere un paquete OCDS (que puede contener una clave 'releases' o ser un release unico)."""
        if "releases" in payload and isinstance(payload["releases"], list):
            return self.ingest_releases(payload["releases"], retrieved_at=retrieved_at)
        elif "ocid" in payload:
            return self.ingest_releases([payload], retrieved_at=retrieved_at)
        return []

    def ingest_file(self, path: Path | str, retrieved_at: datetime | None = None) -> list[ProcurementRecord]:
        """Carga e ingiere un archivo JSON local con releases OCDS."""
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"Archivo OCDS no encontrado: {path}")
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
        return self.ingest_payload(data, retrieved_at=retrieved_at)
