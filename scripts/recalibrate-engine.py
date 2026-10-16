"""Recalibra evidencia oficial local y produce artefactos privados reproducibles."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel

from cajamarca_qhaway.capabilities.red_flags_engine.engine import RedFlagsEngine
from cajamarca_qhaway.capabilities.seace_ingestion.official_sources import (
    _field,
    link_procurement_evidence,
)
from cajamarca_qhaway.models import BudgetExecutionRecord, ProcurementRecord
from cajamarca_qhaway.models.procurement_source_record import ProcurementSourceRecord
from cajamarca_qhaway.web.exporter import _read_jsonl


def atomic_jsonl(path: Path, rows: list[BaseModel]) -> None:
    temporary = path.with_suffix('.jsonl.tmp')
    temporary.write_text(''.join(json.dumps(row.model_dump(mode='json'), ensure_ascii=True)+'\n'
                                 for row in rows), encoding='utf-8')
    temporary.replace(path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--write', action='store_true')
    options = parser.parse_args()
    procurements = _read_jsonl(Path('data/harvested/procurements_all.jsonl'), ProcurementRecord)
    budgets = _read_jsonl(Path('data/harvested/budget_executions_all.jsonl'), BudgetExecutionRecord)
    original = {p.procurement_id: p.raw_payload for p in procurements}
    sources = [ProcurementSourceRecord.model_validate_json(line)
               for path in sorted(Path('data/harvested/official-source-staging').glob('*.jsonl'))
               for line in path.read_text(encoding='utf-8').splitlines() if line]
    sources = link_procurement_evidence(sources, procurements)
    by_procurement: dict[str, list[ProcurementSourceRecord]] = defaultdict(list)
    for record in sources:
        if record.procurement_id:
            by_procurement[record.procurement_id].append(record)
    enriched = []
    filled = 0
    for procurement in procurements:
        evidence = by_procurement.get(procurement.procurement_id, [])
        suppliers: dict[str, str] = {}
        for item in evidence:
            if item.dataset not in {'adjudicaciones', 'contratos'}:
                continue
            row = item.raw_payload.get('record', {})
            ruc = _field(row, 'RUC PROVEEDOR', 'RUC_CONTRATISTA')
            if len(ruc) == 11 and ruc.isdigit():
                suppliers[ruc] = _field(row, 'PROVEEDOR')
        changes: dict[str, object] = {'source_evidence': evidence}
        if procurement.supplier_ruc is None and len(suppliers) == 1:
            ruc, name = next(iter(suppliers.items()))
            changes['supplier_ruc'] = ruc
            if procurement.supplier_name is None and name:
                changes['supplier_name'] = name
            filled += 1
        enriched.append(ProcurementRecord.model_validate(procurement.model_copy(update=changes)))
    if any(p.raw_payload != original[p.procurement_id] for p in enriched):
        raise ValueError('Se alteró el payload OCDS original')
    now = datetime.now(UTC)
    engine = RedFlagsEngine()
    canonical_flags = engine.evaluate(enriched, budgets, now=now)
    flags = engine.evaluate(enriched, budgets, now=now, source_evidence=sources)
    summary = {'source': 'ai', 'generator': 'codex-gpt-6', 'generated_at': now.isoformat(),
        'confidence': 'high', 'verified': False, 'procurements': len(enriched),
        'source_rows': len(sources), 'source_counts': dict(Counter(str(s.source_system) for s in sources)),
        'supplier_rucs_filled': filled, 'canonical_flags': len(canonical_flags), 'total_flags': len(flags),
        'canonical_by_rule': dict(Counter(f.indicator_code for f in canonical_flags)),
        'all_by_rule': dict(Counter(f.indicator_code for f in flags)),
        'source_only_flags': sum(bool(f.source_evidence_ids) for f in flags),
        'original_payload_sha256': hashlib.sha256(json.dumps(original, sort_keys=True).encode()).hexdigest()}
    if options.write:
        directory = Path('data/harvested/recalibration-v2')
        directory.mkdir(parents=True, exist_ok=True)
        atomic_jsonl(directory/'procurements.jsonl', list(enriched))
        atomic_jsonl(directory/'red_flags.jsonl', list(flags))
        (directory/'summary.json').write_text(json.dumps(summary, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(summary, ensure_ascii=True), flush=True)


if __name__ == '__main__':
    main()
