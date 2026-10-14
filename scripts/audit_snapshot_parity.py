"""Audita cifras MPA del ultimo ejercicio y metadatos de candidatos privados."""

from __future__ import annotations

import importlib.util
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
    actual = re.sub(r"\s+", " ", text_for_id(html, element_id))
    if expected not in actual:
        raise AssertionError(f"#{element_id}: esperado {expected!r}; recibido {actual!r}")


def run() -> None:
    snapshot_path = ROOT / "web/src/data/verified-snapshot.json"
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    metadata = snapshot["metadata"]
    entities = snapshot["contracting_entities"]
    budgets = snapshot["budget_execution_records"]
    assert metadata["total_entities"] == len(entities) == 14
    assert metadata["total_procurements"] == len(snapshot["procurement_records"])
    assert metadata["total_budget_executions"] == len(budgets)
    assert snapshot["red_flags"] == [], "Los candidatos son privados"
    assert snapshot["citizen_reports"] == [], "Las denuncias son privadas"

    tool_path = ROOT / "web/tools/validate_web_integrity.py"
    spec = importlib.util.spec_from_file_location("validate_web_integrity", tool_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("No se pudo cargar la auditoria canonica MPA")
    tool = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tool)
    errors = tool.validate_static_snapshot_metrics(snapshot_path, ROOT / "web")
    if errors:
        raise AssertionError("\n".join(errors))

    published = metadata["total_published_alerts"]
    assert published == len(snapshot["alerts"])
    index = (ROOT / "web/index.html").read_text(encoding="utf-8")
    require_contains(index, "kpi-alerts-total", f"{published} alertas publicadas")
    latest_year = max(row["fiscal_year"] for row in budgets)
    latest = [row for row in budgets if row["fiscal_year"] == latest_year]
    pim = sum(float(row["budgeted_amount"]) for row in latest)
    executed = sum(float(row["executed_amount"]) for row in latest)
    rate = f"{executed / pim * 100:.1f}%" if pim else "No calculable"
    for filename, element_id in (
        ("entidades.html", "entidades-kpi-ejecucion"),
        ("presupuesto.html", "kpi-exec-rate"),
    ):
        require_contains(
            (ROOT / "web" / filename).read_text(encoding="utf-8"), element_id, rate
        )
    alerts_html = (ROOT / "web/alertas.html").read_text(encoding="utf-8")
    require_contains(alerts_html, "alertas-kpi-entidades", f"/ {len(entities)}")
    if published == 0:
        require_contains(alerts_html, "alertas-kpi-monto", "Sin monto publicado")
    for page in (ROOT / "web").glob("*.html"):
        if re.search(r"href=[\"']#/", page.read_text(encoding="utf-8")):
            raise AssertionError(f"Ruta hash SPA en {page.name}")
    print(f"Paridad HTML-snapshot ({latest_year}, candidatos privados): PASS")


if __name__ == "__main__":
    run()
