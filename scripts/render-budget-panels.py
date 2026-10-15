"""Sincroniza los paneles iniciales de presupuesto conservando los anclajes previos."""

from __future__ import annotations

import json
import re
from pathlib import Path

from cajamarca_qhaway.models import BudgetExecutionRecord
from cajamarca_qhaway.web.budget_view import render_budget_panel


def first_child_end(html: str, start: int) -> int:
    tokens = re.finditer(r'<!--.*?-->|<(/?)([A-Za-z][A-Za-z0-9]*)\b[^>]*>', html[start:], re.DOTALL)
    depth = 0
    opened = False
    void = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'param', 'source', 'track', 'wbr'}
    for token in tokens:
        if token.group(0).startswith('<!--'):
            continue
        tag = token.group(2).lower()
        if tag in void or token.group(0).endswith('/>'):
            continue
        depth += -1 if token.group(1) else 1
        opened = True
        if opened and depth == 0:
            return start + token.end()
    raise ValueError('No se pudo encontrar el encabezado de la vista')


def main() -> None:
    snapshot = json.loads(Path('web/src/data/verified-snapshot.json').read_text(encoding='utf-8'))
    records = [BudgetExecutionRecord.model_validate(record) for record in snapshot['budget_execution_records']]
    for name in ('index.html', 'presupuesto.html', 'entidades.html', 'entidad-detalle.html'):
        path = Path('web') / name
        html = path.read_text(encoding='utf-8')
        panel = render_budget_panel(records, name)
        pattern = r'<!-- qh-budget-panel:start -->.*?<!-- qh-budget-panel:end -->'
        html = re.sub(pattern, '', html, flags=re.DOTALL)
        main_tag = re.search(r'<main\b[^>]*>', html)
        if main_tag is None:
            raise ValueError(f'Vista sin main: {name}')
        position = first_child_end(html, main_tag.end())
        html = html[:position] + '\n' + panel + '\n' + html[position:]
        path.write_text(html, encoding='utf-8')
        print(path)


if __name__ == '__main__':
    main()
