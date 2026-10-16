"""Emite lotes SQL tipados para el canal MCP, sin credenciales ni ejecución implícita."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('kind', choices=('flags', 'cases', 'analyses', 'activate'))
    parser.add_argument('--offset', type=int, default=0)
    options = parser.parse_args()
    directory = Path('data/harvested/recalibration-v2')
    flags = [json.loads(line) for line in (directory/'red_flags.jsonl').read_text().splitlines()]
    if options.kind == 'activate':
        ids = ','.join("'"+f['red_flag_id'].replace("'", "''")+"'" for f in flags)
        print('UPDATE public.red_flags SET is_active=(red_flag_id IN ('+ids+'));')
        return
    if options.kind == 'flags':
        rows = flags[options.offset:options.offset+40]
        for row in rows:
            row['threshold'] = json.dumps(row['threshold_value'])
            row['threshold_value'] = json.dumps(row['threshold_value'])
            row['observed_value'] = json.dumps(row['observed_value'])
            row['evidence_retrieved_at'] = row['retrieved_at']
        table = 'red_flags'
        columns = ('red_flag_id,indicator_code,formula_description,threshold,threshold_value,observed_value,'
            'procurement_ids,execution_record_ids,evidence_source,evidence_retrieved_at,retrieved_at,'
            'generated_at,source_evidence_ids,is_active')
        updates = ','.join(column+'=excluded.'+column for column in columns.split(',')[1:])
        conflict = 'ON CONFLICT(red_flag_id) DO UPDATE SET '+updates
    else:
        value = json.loads((directory/'private-cases.json').read_text())
        if options.kind == 'cases':
            rows = value['new_cases']
            table = 'alerts'
            for row in rows:
                row['disclaimer'] = row['legal_disclaimer']
            columns = ('alert_id,entity_id,red_flag_ids,status,reviewed_by,reviewed_at,review_notes,'
                'disclaimer,legal_disclaimer,evidence,published_at')
            conflict = 'ON CONFLICT(alert_id) DO NOTHING'
        else:
            rows = value['dossiers'][options.offset:options.offset+4]
            table = 'review_case_analyses'
            columns = ('alert_id,entity_id,case_priority_score,priority_components,ai_copilot_analysis,generated_at')
            conflict = ('ON CONFLICT(alert_id) DO UPDATE SET '
                + ','.join(c+'=excluded.'+c for c in columns.split(',')[1:]))
    encoded = json.dumps(rows, ensure_ascii=True).replace("'", "''")
    print(f'INSERT INTO public.{table} ({columns}) SELECT {columns} '
          f"FROM jsonb_populate_recordset(NULL::public.{table},'{encoded}'::jsonb) {conflict};")


if __name__ == '__main__':
    main()
