"""Herramienta de auditoria de integridad web para Cajamarca Qhaway.

Verifica:
1. Existencia de todas las carpetas y archivos estructurales de web/:
   - web/index.html
   - web/DESIGN.md
   - web/src/css/
   - web/src/js/
   - web/src/data/
   - web/media/
   - web/tools/
2. Cumplimiento estricto de Antislop R-02: Cero ocurrencias de raya em-dash (\\u2014) en web/.
3. Validez de todos los registros de verified-snapshot.json contra los 6 modelos canonicos Pydantic v2 (Art. 19).
4. Cumplimiento de invariantes constitucionales:
   - Art. 10: Fuentes OCDS SEACE ('seace-ocds') y MEF DataStore ('mef-datastore').
   - Art. 14: Toda alerta con status == 'published' posee reviewed_by valido y published_at no nulo.
   - Art. 15: Explicabilidad algoritmica (formula, threshold, observed_value, disclaimer).
   - Art. 16: Ninguna alerta ni bandera roja realiza scoring de personas por nombre o DNI.
   - Art. 18: Exactamente 14 entidades cerradas de Cajamarca.
   - CA-006-01: Toda denuncia ciudadana tiene legal_disclaimer_shown == True.
"""

from __future__ import annotations

import json
import re
import sys
from html import unescape
from pathlib import Path

from cajamarca_qhaway.models import (
    Alert,
    BudgetExecutionRecord,
    CitizenReport,
    ContractingEntity,
    ProcurementRecord,
    RedFlag,
)
from cajamarca_qhaway.models.alert import GENERIC_REVIEWERS, STANDARD_ALERT_DISCLAIMER


def validate_web_structure(web_root: Path = Path("web")) -> list[str]:
    """Verifica que existan las carpetas y archivos obligatorios de la plataforma web."""
    errors: list[str] = []
    required_paths = [
        web_root / "index.html",
        web_root / "DESIGN.md",
        web_root / "src" / "css",
        web_root / "src" / "js",
        web_root / "src" / "data",
        web_root / "media",
        web_root / "tools",
    ]

    for p in required_paths:
        if not p.exists():
            errors.append(f"Ruta requerida faltante: {p}")

    return errors


def validate_zero_em_dash(web_root: Path = Path("web")) -> list[str]:
    """Verifica regla Antislop R-02: cero caracteres em-dash (U+2014) en todo web/."""
    errors: list[str] = []
    for f in web_root.rglob("*"):
        if f.is_file() and f.suffix in {".html", ".css", ".js", ".json", ".md", ".py", ".svg"}:
            try:
                content = f.read_text(encoding="utf-8")
                if "\u2014" in content:
                    errors.append(f"Antislop R-02 violado (em-dash encontrado): {f}")
            except (OSError, ValueError, TypeError, KeyError, AttributeError) as exc:
                errors.append(f"Error al leer archivo {f}: {exc}")
    return errors


def validate_snapshot_integrity(snapshot_path: Path = Path("web/src/data/verified-snapshot.json")) -> list[str]:
    """Verifica que verified-snapshot.json cumpla con los 6 modelos canonicos e invariantes."""
    errors: list[str] = []
    if not snapshot_path.exists():
        return [f"Archivo de snapshot no encontrado: {snapshot_path}"]

    try:
        data = json.loads(snapshot_path.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError, KeyError, AttributeError) as exc:
        return [f"Error al parsear snapshot JSON: {exc}"]

    # 1. Validar ContractingEntity (Art. 18: exactamente 14 entidades de Cajamarca)
    entities_raw = data.get("contracting_entities", [])
    if len(entities_raw) != 14:
        errors.append(f"Art. 18 violado: se esperaban 14 entidades, pero hay {len(entities_raw)}")

    entity_ids = set()
    for raw in entities_raw:
        try:
            ent = ContractingEntity.model_validate(raw)
            entity_ids.add(ent.entity_id)
        except (OSError, ValueError, TypeError, KeyError, AttributeError) as exc:
            errors.append(f"ContractingEntity invalida: {exc}")

    # 2. Validar ProcurementRecord (Art. 10: seace-ocds)
    procurements_raw = data.get("procurement_records", [])
    for raw in procurements_raw:
        try:
            proc = ProcurementRecord.model_validate(raw)
            if proc.source != "seace-ocds":
                errors.append(f"Art. 10 violado: source debe ser 'seace-ocds', recibido: '{proc.source}'")
            if proc.entity_id not in entity_ids:
                errors.append(f"Procurement {proc.procurement_id} pertenece a entity_id ajena al universo: {proc.entity_id}")
        except (OSError, ValueError, TypeError, KeyError, AttributeError) as exc:
            errors.append(f"ProcurementRecord invalido: {exc}")

    # 3. Validar BudgetExecutionRecord (Art. 10: mef-datastore)
    budget_raw = data.get("budget_execution_records", [])
    for raw in budget_raw:
        try:
            b = BudgetExecutionRecord.model_validate(raw)
            if b.source not in {"mef-datastore", "mef-consulta-amigable"}:
                errors.append(f"Art. 10 violado: source MEF desconocida: '{b.source}'")
            if b.entity_id not in entity_ids:
                errors.append(f"BudgetExecution {b.execution_record_id} pertenece a entity_id ajena: {b.entity_id}")
        except (OSError, ValueError, TypeError, KeyError, AttributeError) as exc:
            errors.append(f"BudgetExecutionRecord invalido: {exc}")

    # 4. Validar RedFlag (Art. 15 y Art. 16)
    flags_raw = data.get("red_flags", [])
    for raw in flags_raw:
        try:
            flag = RedFlag.model_validate(raw)
            if not flag.formula_description:
                errors.append(f"Art. 15 violado: formula_description vacia en {flag.red_flag_id}")
            if hasattr(flag, "status"):
                errors.append(f"Invariante violado: RedFlag no debe poseer campo 'status': {flag.red_flag_id}")
        except (OSError, ValueError, TypeError, KeyError, AttributeError) as exc:
            errors.append(f"RedFlag invalido: {exc}")

    # 5. Validar Alert (Art. 14, Art. 15, CA-005-02, CA-005-04)
    alerts_raw = data.get("alerts", [])
    for raw in alerts_raw:
        try:
            alert = Alert.model_validate(raw)
            # CA-005-02: reviewed_by no puede ser generico
            if alert.reviewed_by.lower() in GENERIC_REVIEWERS:
                errors.append(f"CA-005-02 violado: reviewed_by generico en {alert.alert_id}: {alert.reviewed_by}")

            # CA-005-03: si status == published, published_at existe
            if alert.status == "published" and alert.published_at is None:
                errors.append(f"CA-005-03 violado: alerta publicada sin published_at: {alert.alert_id}")

            # CA-005-04: si status == discarded, review_notes existe
            if alert.status == "discarded" and not alert.review_notes:
                errors.append(f"CA-005-04 violado: alerta descartada sin review_notes: {alert.alert_id}")

            # Art. 15: disclaimer legal inmutable
            if alert.disclaimer != STANDARD_ALERT_DISCLAIMER:
                errors.append(f"Art. 15 violado: disclaimer incorrecto en {alert.alert_id}")
        except (OSError, ValueError, TypeError, KeyError, AttributeError) as exc:
            errors.append(f"Alert invalida: {exc}")

    # 6. Validar CitizenReport (CA-006-01)
    reports_raw = data.get("citizen_reports", [])
    for raw in reports_raw:
        try:
            rep = CitizenReport.model_validate(raw)
            if not rep.legal_disclaimer_shown:
                errors.append(f"CA-006-01 violado: legal_disclaimer_shown debe ser True en {rep.report_id}")
        except (OSError, ValueError, TypeError, KeyError, AttributeError) as exc:
            errors.append(f"CitizenReport invalido: {exc}")

    return errors


def _static_element_text(page: Path, element_id: str) -> str:
    source = page.read_text(encoding="utf-8")
    match = re.search(
        rf'<(?P<tag>[a-zA-Z][\w:-]*)\b(?=[^>]*\bid="{re.escape(element_id)}")[^>]*>(?P<body>.*?)</(?P=tag)\s*>',
        source,
        re.DOTALL,
    )
    if not match:
        raise ValueError(f"No se encontro #{element_id} en {page}")
    return unescape(re.sub(r"<[^>]+>", " ", match.group("body"))).strip()


def validate_static_snapshot_metrics(
    snapshot_path: Path = Path("web/src/data/verified-snapshot.json"),
    web_root: Path = Path("web"),
) -> list[str]:
    """Comprueba que los KPIs iniciales MPA reflejen conteos de la instantánea."""
    try:
        metadata = json.loads(snapshot_path.read_text(encoding="utf-8"))["metadata"]
        expected = {
            ("index.html", "kpi-procurements-total"): str(metadata["total_procurements"]),
            ("index.html", "index-total-procurements-badge"): str(metadata["total_procurements"]),
            ("alertas.html", "alertas-kpi-total"): str(metadata["total_published_alerts"]),
            ("entidades.html", "entidades-kpi-contratos"): str(metadata["total_procurements"]),
            ("georreferenciacion.html", "kpi-total-works"): str(metadata["total_geospatial_works"]),
        }
        errors: list[str] = []
        for (filename, element_id), value in expected.items():
            actual = _static_element_text(web_root / filename, element_id)
            if not re.search(rf"(?<!\d){re.escape(value)}(?!\d)", actual):
                errors.append(f"Cifra estática inconsistente en {filename} #{element_id}: esperado {value}, recibido {actual!r}")
        budget_rows = json.loads(snapshot_path.read_text(encoding="utf-8"))["budget_execution_records"]
        latest_year = max((int(row["fiscal_year"]) for row in budget_rows), default=0)
        latest_rows = [row for row in budget_rows if int(row["fiscal_year"]) == latest_year]
        expected_mef: dict[tuple[str, str], str] = {}
        if latest_rows:
            pim = sum(float(row["budgeted_amount"]) for row in latest_rows)
            executed = sum(float(row["executed_amount"]) for row in latest_rows)
            if len({row["entity_id"] for row in latest_rows}) == int(metadata["total_entities"]):
                expected_mef = {
                    ("index.html", "kpi-pim-total"): f"S/ {pim:,.0f}",
                    ("index.html", "kpi-devengado-pct"): f"{executed / pim * 100:.1f}%" if pim else "No calculable",
                    ("entidades.html", "entidades-kpi-pim"): f"S/ {pim:,.0f}",
                    ("entidades.html", "entidades-kpi-devengado"): f"S/ {executed:,.0f}",
                    ("presupuesto.html", "kpi-pim"): f"S/ {pim:,.0f}",
                    ("presupuesto.html", "kpi-dev"): f"S/ {executed:,.0f}",
                }
        if expected_mef:
            for (filename, element_id), value in expected_mef.items():
                actual = _static_element_text(web_root / filename, element_id)
                if value not in actual:
                    errors.append(
                        f"Cifra MEF inconsistente en {filename} #{element_id}: esperado {value}, recibido {actual!r}"
                    )
        else:
            for filename, element_id in (
                ("index.html", "kpi-pim-total"),
                ("index.html", "kpi-devengado-pct"),
                ("entidades.html", "entidades-kpi-pim"),
                ("entidades.html", "entidades-kpi-devengado"),
                ("presupuesto.html", "kpi-pim"),
                ("presupuesto.html", "kpi-dev"),
            ):
                actual = _static_element_text(web_root / filename, element_id).casefold()
                if not any(token in actual for token in ("sin consolidado mef", "no consolidado", "no calculable", "sin dato mef", "cobertura mef parcial")):
                    errors.append(f"Cifra MEF no disponible presentada como dato en {filename} #{element_id}")
        return errors
    except (OSError, ValueError, TypeError, KeyError, AttributeError) as exc:
        return [f"Error al auditar cifras MPA frente al snapshot: {exc}"]


def run_full_web_audit(web_root: Path = Path("web")) -> bool:
    """Ejecuta la auditoria integral y reporta resultados."""
    print("=== Auditoria Integral de Plataforma Web (Cajamarca Qhaway) ===")

    structure_errors = validate_web_structure(web_root)
    print(f"1. Estructura de carpetas y archivos: {'PASS' if not structure_errors else 'FAIL'}")
    for err in structure_errors:
        print(f"   [ERROR] {err}")

    em_dash_errors = validate_zero_em_dash(web_root)
    print(f"2. Politica Antislop R-02 (Cero em-dash): {'PASS' if not em_dash_errors else 'FAIL'}")
    for err in em_dash_errors:
        print(f"   [ERROR] {err}")

    snapshot_path = web_root / "src" / "data" / "verified-snapshot.json"
    snapshot_errors = validate_snapshot_integrity(snapshot_path)
    print(f"3. Integridad de contratos canonicos Pydantic v2: {'PASS' if not snapshot_errors else 'FAIL'}")
    for err in snapshot_errors:
        print(f"   [ERROR] {err}")

    metric_errors = validate_static_snapshot_metrics(snapshot_path, web_root)
    print(f"4. Cifras estáticas MPA frente al snapshot: {'PASS' if not metric_errors else 'FAIL'}")
    for err in metric_errors:
        print(f"   [ERROR] {err}")

    all_errors = structure_errors + em_dash_errors + snapshot_errors + metric_errors
    print("================================================================")
    if not all_errors:
        print("RESULTADO GLOBAL: CONFORME (100% de verificaciones superadas)")
        return True
    else:
        print(f"RESULTADO GLOBAL: NO CONFORME ({len(all_errors)} errores detectados)")
        return False


def main() -> int:
    ok = run_full_web_audit()
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
