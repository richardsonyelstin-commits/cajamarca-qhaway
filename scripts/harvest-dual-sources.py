"""Captura evidencia OECE por RUC y registra la disponibilidad real del buscador JSF."""

from __future__ import annotations

import argparse
import asyncio
import json
from datetime import UTC, datetime
from pathlib import Path

import httpx

from cajamarca_qhaway.capabilities.entity_mapping.dataset import load_universe
from cajamarca_qhaway.capabilities.live_harvest.coverage_logger import CoverageGapLogger
from cajamarca_qhaway.capabilities.live_harvest.official_source_probe import (
    probe_public_source,
)
from cajamarca_qhaway.capabilities.seace_ingestion.captcha_session import (
    BrowserCaptchaSolver,
)
from cajamarca_qhaway.capabilities.seace_ingestion.official_sources import (
    OECEPentahoClient,
    SEACEBuscadorPublicoClient,
    link_procurement_evidence,
)
from cajamarca_qhaway.models import ProcurementRecord
from cajamarca_qhaway.models.procurement_source_record import ProcurementSourceRecord
from cajamarca_qhaway.persistence.connection import DatabaseManager
from cajamarca_qhaway.persistence.repositories.procurement_source_repository import (
    ProcurementSourceRepository,
)
from cajamarca_qhaway.web.exporter import _read_jsonl


async def main() -> None:
    arguments = argparse.ArgumentParser()
    arguments.add_argument("--persist", action="store_true")
    arguments.add_argument("--current", action="store_true")
    arguments.add_argument("--browser", action="store_true")
    arguments.add_argument("--seace-only", action="store_true")
    options = arguments.parse_args()
    database = DatabaseManager() if options.persist else None
    if database and not database.is_postgres:
        raise SystemExit("Persistencia solicitada sin PostgreSQL")
    repository = ProcurementSourceRepository(database) if database else None
    directory = Path("data/harvested/official-source-staging")
    directory.mkdir(parents=True, exist_ok=True)
    gaps = CoverageGapLogger(Path("data/state/dual-source-gaps.jsonl"))
    entities = [entry.entity for entry in load_universe().entities]
    if database:
        from cajamarca_qhaway.persistence.repositories.procurement_repository import (
            ProcurementRepository,
        )
        with database.connection() as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT * FROM procurement_records")
            procurements = [ProcurementRepository._row_to_model(row) for row in cursor.fetchall()]
    else:
        procurements = _read_jsonl(Path("data/harvested/procurements_all.jsonl"), ProcurementRecord)
    failed: list[str] = []
    async with OECEPentahoClient() as client:
        resources = [] if options.seace_only else await client.discover(
            [datetime.now(UTC).year] if options.current else [2024, 2025, 2026],
        )
        if options.current:
            last_order = next((item for item in reversed(resources) if item.dataset == "ordenes"), None)
            resources = [item for item in resources if item.dataset != "ordenes" or item == last_order]
        for resource in resources:
            filename = resource.url.rsplit("/", 1)[-1].replace(".xlsx", ".jsonl")
            path = directory / filename
            if path.exists():
                if repository:
                    checkpoint = _read_jsonl(path, ProcurementSourceRecord)
                    repository.upsert_many(link_procurement_evidence(checkpoint, procurements))
                print(json.dumps({"file": filename, "status": "CHECKPOINT"}), flush=True)
                continue
            try:
                records = [record async for record in client.records(resource, entities)]
                linked = link_procurement_evidence(records, procurements)
                if repository:
                    repository.upsert_many(linked)
                temporary = path.with_suffix(".jsonl.tmp")
                temporary.write_text("".join(json.dumps(record.model_dump(mode="json"), ensure_ascii=True)
                                             + "\n" for record in linked), encoding="utf-8")
                temporary.replace(path)
                print(json.dumps({"file": filename, "records": len(linked),
                                  "linked": sum(record.procurement_id is not None for record in linked),
                                  "status": "OK"}), flush=True)
            except (httpx.HTTPError, ValueError) as error:
                failed.append(filename)
                gaps.log_incident(source="oece-pentaho-bi", attempt=1,
                                  status_code=getattr(getattr(error, "response", None), "status_code", None),
                                  endpoint=resource.url, error_message=str(error))
                print(json.dumps({"file": filename, "status": "FAILED", "type": type(error).__name__}), flush=True)
    solver = BrowserCaptchaSolver() if options.browser else None
    for entity in entities:
        for year in ([datetime.now(UTC).year] if options.current else [2024, 2025, 2026]):
            checkpoint = directory / f"seace-public-{entity.entity_id}-{year}.jsonl"
            if checkpoint.exists():
                records = _read_jsonl(checkpoint, ProcurementSourceRecord)
                if repository:
                    repository.upsert_many(link_procurement_evidence(records, procurements))
                print(json.dumps({"source": "seace-public", "entity_id": entity.entity_id,
                                  "fiscal_year": year, "status": "CHECKPOINT",
                                  "records": len(records)}), flush=True)
                continue
            async with SEACEBuscadorPublicoClient(coverage_logger=gaps, captcha_solver=solver) as client:
                probe = await probe_public_source(client, entity, year)
            if probe.status == "CAPTURED":
                linked = link_procurement_evidence(probe.records, procurements)
                temporary = checkpoint.with_suffix(".jsonl.tmp")
                temporary.write_text("".join(
                    json.dumps(record.model_dump(mode="json"), ensure_ascii=True) + "\n"
                    for record in linked
                ), encoding="utf-8")
                temporary.replace(checkpoint)
            if repository and probe.records:
                repository.upsert_many(link_procurement_evidence(probe.records, procurements))
            print(json.dumps({"source": "seace-public", "entity_id": entity.entity_id,
                              "fiscal_year": year, "status": probe.status,
                              "records": len(probe.records)}), flush=True)
    if database:
        with database.connection() as connection:
            cursor = connection.cursor()
            cursor.execute("""UPDATE procurement_records AS p SET source_evidence = COALESCE(
                (SELECT jsonb_agg(to_jsonb(e) ORDER BY e.source_evidence_id)
                 FROM procurement_source_records e WHERE e.procurement_id=p.procurement_id), '[]'::jsonb)""")
            cursor.execute("SELECT count(*) AS records, count(procurement_id) AS linked FROM procurement_source_records")
            print(json.dumps(dict(cursor.fetchone())), flush=True)
            connection.commit()
    if failed:
        raise SystemExit(f"Recursos OECE fallidos: {failed}")


if __name__ == "__main__":
    asyncio.run(main())
