"""Check that pre-rendered public HTML metrics match the verified snapshot."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def text_for_id(html: str, element_id: str) -> str:
    pattern = rf'<[^>]+\bid="{re.escape(element_id)}"[^>]*>(.*?)</[^>]+>'
    match = re.search(pattern, html, flags=re.DOTALL)
    if match is None:
        raise AssertionError(f"No se encontro el elemento #{element_id}")
    return re.sub(r"<[^>]+>", " ", match.group(1)).replace("&lt;", "<").strip()


def require_contains(html: str, element_id: str, expected: str) -> None:
    actual = text_for_id(html, element_id)
    normalized = re.sub(r"\s+", " ", actual)
    if expected not in normalized:
        raise AssertionError(f"#{element_id}: esperado {expected!r}; recibido {normalized!r}")


def format_millions(value: float) -> str:
    return f"S/ {value / 1_000_000:,.1f} M"


def run() -> None:
    snapshot = json.loads((ROOT / "web/src/data/verified-snapshot.json").read_text(encoding="utf-8"))
    metadata = snapshot["metadata"]
    entities = snapshot["contracting_entities"]
    procurements = snapshot["procurement_records"]
    budgets = snapshot["budget_execution_records"]
    alerts = [item for item in snapshot["alerts"] if item.get("status") == "published"]
    flags_by_id = {item["red_flag_id"]: item for item in snapshot["red_flags"]}
    procurements_by_id = {item["procurement_id"]: item for item in procurements}
    budgets_by_id = {item["execution_record_id"]: item for item in budgets}

    assert metadata["total_entities"] == len(entities)
    assert metadata["total_procurements"] == len(procurements)
    assert metadata["total_budget_executions"] == len(budgets)
    assert metadata["total_published_alerts"] == len(alerts)
    assert len(entities) == 14

    pim = sum(float(item.get("budgeted_amount") or 0) for item in budgets)
    executed = sum(float(item.get("executed_amount") or 0) for item in budgets)
    execution_rate = round(executed / pim * 100, 1) if pim else 0.0
    flagged_amount = 0.0
    for alert in alerts:
        for flag_id in alert.get("red_flag_ids", []):
            flag = flags_by_id.get(flag_id)
            if flag is None:
                raise AssertionError(f"La alerta publicada referencia bandera ausente: {flag_id}")
            for procurement_id in flag.get("procurement_ids", []):
                record = procurements_by_id.get(procurement_id)
                if record:
                    flagged_amount += float(record.get("awarded_amount") or 0)
            for budget_id in flag.get("execution_record_ids", []):
                record = budgets_by_id.get(budget_id)
                if record:
                    flagged_amount += float(record.get("executed_amount") or 0)

    index = (ROOT / "web/index.html").read_text(encoding="utf-8")
    entities_html = (ROOT / "web/entidades.html").read_text(encoding="utf-8")
    budget_html = (ROOT / "web/presupuesto.html").read_text(encoding="utf-8")
    alerts_html = (ROOT / "web/alertas.html").read_text(encoding="utf-8")
    for html, element_id in ((index, "kpi-procurements-total"), (index, "index-total-procurements-badge")):
        require_contains(html, element_id, str(len(procurements)))
    for html, element_id in ((index, "kpi-alerts-total"),):
        require_contains(html, element_id, f"{len(alerts)} Alertas")
    for html, element_id in ((index, "kpi-pim-total"), (entities_html, "entidades-kpi-pim"), (budget_html, "kpi-pim")):
        require_contains(html, element_id, format_millions(pim))
    for html, element_id in ((entities_html, "entidades-kpi-devengado"), (budget_html, "kpi-dev")):
        require_contains(html, element_id, format_millions(executed))
    for html, element_id in ((index, "kpi-devengado-pct"), (entities_html, "entidades-kpi-ejecucion"), (budget_html, "kpi-exec-rate")):
        require_contains(html, element_id, f"{execution_rate}%")
    require_contains(alerts_html, "alertas-kpi-total", str(len(alerts)))
    require_contains(alerts_html, "alertas-kpi-entidades", f"/ {len(entities)}")
    require_contains(alerts_html, "alertas-kpi-monto", format_millions(flagged_amount))
    print("Paridad HTML-snapshot: PASS")


if __name__ == "__main__":
    run()
