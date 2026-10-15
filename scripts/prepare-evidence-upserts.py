"""Prepara lotes SQL verificables de evidencia filtrada para el conector Supabase."""

from __future__ import annotations

import json
from pathlib import Path

from cajamarca_qhaway.capabilities.entity_mapping.dataset import load_universe
from cajamarca_qhaway.capabilities.seace_ingestion.official_sources import (
    link_procurement_evidence,
)
from cajamarca_qhaway.models import ProcurementRecord
from cajamarca_qhaway.models.procurement_source_record import ProcurementSourceRecord
from cajamarca_qhaway.web.exporter import _read_jsonl


def main() -> None:
    procurements = _read_jsonl(Path("data/harvested/procurements_all.jsonl"), ProcurementRecord)
    entities = {entry.entity.entity_id for entry in load_universe().entities}
    output = Path("context/snapshots/mef-v2-staging/source-sync")
    output.mkdir(parents=True, exist_ok=True)
    manifest = []
    coverage = []
    for path in sorted(Path("data/harvested/official-source-staging").glob("*.jsonl")):
        rows = link_procurement_evidence(_read_jsonl(path, ProcurementSourceRecord), procurements)
        if any(row.entity_id not in entities for row in rows):
            raise ValueError("La evidencia contiene una entidad fuera del universo")
        coverage.append({"file": path.name, "records": len(rows)})
        columns = tuple(ProcurementSourceRecord.model_fields)
        for offset in range(0, len(rows), 500):
            batch = rows[offset:offset + 500]
            payload = json.dumps([row.model_dump(mode="json") for row in batch], ensure_ascii=True)
            if "$qh$" in payload:
                raise ValueError("El payload contiene el delimitador SQL reservado")
            updates = ", ".join(f"{key}=EXCLUDED.{key}" for key in columns
                                if key not in ("source_evidence_id", "entity_id"))
            sql = (f"WITH saved AS (INSERT INTO procurement_source_records ({', '.join(columns)}) "
                   f"SELECT {', '.join(columns)} FROM jsonb_populate_recordset("
                   f"NULL::public.procurement_source_records,$qh${payload}$qh$::jsonb) "
                   f"ON CONFLICT(source_evidence_id) DO UPDATE SET {updates} "
                   "RETURNING source_evidence_id) SELECT count(*) saved FROM saved;")
            target = output / f"{path.stem}-{offset // 500}.sql"
            target.write_text(sql, encoding="utf-8")
            manifest.append({"file": target.as_posix(), "rows": len(batch)})
    (output / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    (output / "coverage.json").write_text(json.dumps(coverage), encoding="utf-8")
    print(json.dumps({"batches": len(manifest), "rows": sum(item["rows"] for item in manifest),
                      "resources": len(coverage)}))


if __name__ == "__main__":
    main()
