"""Prepara expedientes privados reproducibles sin decidir ni atribuir autoría humana."""

from __future__ import annotations

import json
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

from cajamarca_qhaway.capabilities.review_panel.ai_copilot import LocalForensicReasoner, case_priority
from cajamarca_qhaway.models import Alert, AlertEvidence, BudgetExecutionRecord, ProcurementRecord, RedFlag, compute_alert_id
from cajamarca_qhaway.models.case_analysis import ReviewCaseAnalysis
from cajamarca_qhaway.models.procurement_source_record import ProcurementSourceRecord
from cajamarca_qhaway.persistence.repositories.red_flag_repository import RedFlagRepository
from cajamarca_qhaway.web.exporter import _read_jsonl


def main() -> None:
    directory = Path('data/harvested/recalibration-v2')
    flags = _read_jsonl(directory/'red_flags.jsonl', RedFlag)
    procurements = _read_jsonl(directory/'procurements.jsonl', ProcurementRecord)
    budgets = _read_jsonl(Path('data/harvested/budget_executions_all.jsonl'), BudgetExecutionRecord)
    owners = {p.procurement_id: p.entity_id for p in procurements}
    owners.update({b.execution_record_id: b.entity_id for b in budgets})
    for path in Path('data/harvested/official-source-staging').glob('*.jsonl'):
        for line in path.read_text(encoding='utf-8').splitlines():
            record = ProcurementSourceRecord.model_validate_json(line)
            owners[record.source_evidence_id] = record.entity_id
    grouped: dict[str, list[RedFlag]] = defaultdict(list)
    for flag in flags:
        entities = {owners[i] for i in [*flag.procurement_ids, *flag.execution_record_ids,
                                       *flag.source_evidence_ids] if i in owners}
        if len(entities) != 1:
            raise ValueError('La bandera no tiene una entidad inequívoca: '+flag.red_flag_id)
        grouped[next(iter(entities))].append(flag)
    cases = []
    for entity_id, evidence in sorted(grouped.items()):
        ids = [f.red_flag_id for f in evidence]
        cases.append(Alert(alert_id=compute_alert_id(entity_id, ids), entity_id=entity_id,
            red_flag_ids=ids, status='in_review', evidence=[AlertEvidence.model_validate({
                key: f.model_dump()[key] for key in AlertEvidence.model_fields}) for f in evidence]))
    prior = json.loads((directory/'prior-cases.json').read_text(encoding='utf-8'))
    prior_cases = [Alert.model_validate({k: v for k, v in a.items() if k in Alert.model_fields})
                   for a in prior['alerts'] if a['status'] == 'in_review']
    flag_map = {f.red_flag_id: f for f in flags}
    for value in prior['flags']:
        f = RedFlagRepository._row_to_model(value)
        if f.red_flag_id not in flag_map:
            flag_map[f.red_flag_id] = f.model_copy(update={'is_active': False})
    reasoner = LocalForensicReasoner()
    dossiers = []
    stamp = datetime.now(UTC)
    for alert in [*cases, *prior_cases]:
        evidence = [flag_map[i] for i in alert.red_flag_ids if i in flag_map]
        records = [p for p in procurements if p.procurement_id in {i for f in evidence for i in f.procurement_ids}]
        executions = [b for b in budgets if b.entity_id == alert.entity_id]
        priority = case_priority(evidence, records, executions)
        analysis = (reasoner.analyze(alert, evidence, records, executions, now=stamp)
            if len(evidence) == len(alert.red_flag_ids) else reasoner.analyze_archived_gap(alert, stamp))
        dossiers.append(ReviewCaseAnalysis(alert_id=alert.alert_id, entity_id=alert.entity_id,
            case_priority_score=priority.score, priority_components=priority,
            ai_copilot_analysis=analysis, generated_at=stamp))
    payload = {'new_cases': [a.model_dump(mode='json') for a in cases],
               'dossiers': [d.model_dump(mode='json') for d in dossiers]}
    (directory/'private-cases.json').write_text(json.dumps(payload, ensure_ascii=True), encoding='utf-8')
    print(json.dumps({'new_cases': len(cases), 'dossiers': len(dossiers),
        'unresolved_historical_cases': sum('original ausente' in ' '.join(d.ai_copilot_analysis.limitations)
                                         for d in dossiers)}))


if __name__ == '__main__':
    main()
