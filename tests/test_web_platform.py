"""Suite de pruebas automatizadas y deterministas para la plataforma web de Cajamarca Qhaway.

Cubre:
1. Estructura de carpetas de web/ (index.html, DESIGN.md, src/css, src/js, src/data, media, tools).
2. Generacion y validacion Pydantic v2 de verified-snapshot.json contra los 6 modelos del Art. 19.
3. Cumplimiento del Articulo 14 (ninguna Alert publica sin reviewed_by valido, bloqueo de genericos).
4. Cumplimiento del Articulo 15 (explicabilidad algoritmica y STANDARD_ALERT_DISCLAIMER).
5. Cumplimiento de CA-006-01 (rechazo de denuncias con legal_disclaimer_shown=False en /api/reports).
6. Servidor HTTP / handler de API (/api/health, /api/entities, /api/alerts, /api/snapshot).
7. Comandos CLI cajamarca-qhaway web export-snapshot y cajamarca-qhaway web audit.
8. Verificacion estricta Antislop R-02 (cero rayas em-dash en archivos de la plataforma).
"""

from __future__ import annotations

import io
import json
import threading
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import pytest

from cajamarca_qhaway.models import (
    Alert,
    BudgetExecutionRecord,
    CitizenReport,
    ContractingEntity,
    ProcurementRecord,
    RedFlag,
)
from cajamarca_qhaway.models.alert import GENERIC_REVIEWERS, STANDARD_ALERT_DISCLAIMER
from cajamarca_qhaway.web.exporter import build_verified_web_snapshot, export_verified_snapshot
from cajamarca_qhaway.web.server import WebApiHandler, run_server
import importlib.util

_tool_path = Path("web/tools/validate_web_integrity.py").resolve()
_spec = importlib.util.spec_from_file_location("validate_web_integrity", _tool_path)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

validate_snapshot_integrity = _mod.validate_snapshot_integrity
validate_web_structure = _mod.validate_web_structure
validate_zero_em_dash = _mod.validate_zero_em_dash


@pytest.fixture(scope="module")
def web_snapshot() -> dict:
    """Fixture que provee la instantanea generada para validaciones."""
    return build_verified_web_snapshot()


@pytest.fixture(scope="module")
def local_web_server():
    """Inicia un servidor HTTP local en un puerto efimero para pruebas de endpoints."""
    # Usar puerto 8998 para pruebas
    server = run_server(port=8998, web_dir="web")
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield "http://localhost:8998"
    server.shutdown()
    server.server_close()


def test_01_web_folder_structure():
    """Verifica que la estructura de carpetas de web/ contenga todos los directorios requeridos."""
    errors = validate_web_structure(Path("web"))
    assert not errors, f"Errores en estructura de carpetas: {errors}"


def test_02_zero_em_dash_antislop_rule():
    """Verifica la regla Antislop R-02: cero em-dash (U+2014) en todo web/."""
    errors = validate_zero_em_dash(Path("web"))
    assert not errors, f"Violacion de regla Antislop R-02 (em-dash detectado): {errors}"


def test_03_snapshot_models_validation(web_snapshot):
    """Verifica que todos los registros en verified-snapshot.json validen contra Pydantic v2."""
    # 1. ContractingEntity
    entities = [ContractingEntity.model_validate(e) for e in web_snapshot["contracting_entities"]]
    assert len(entities) == 14, "Deben existir exactamente 14 entidades en el universo"

    # 2. ProcurementRecord
    procurements = [ProcurementRecord.model_validate(p) for p in web_snapshot["procurement_records"]]
    assert len(procurements) >= 5, "Debe haber registros OCDS de muestra"

    # 3. BudgetExecutionRecord
    budget = [BudgetExecutionRecord.model_validate(b) for b in web_snapshot["budget_execution_records"]]
    assert len(budget) >= 14, "Debe haber registros presupuestales MEF para las 14 entidades"

    # 4. RedFlag
    red_flags = [RedFlag.model_validate(f) for f in web_snapshot["red_flags"]]
    assert len(red_flags) >= 3, "Debe haber banderas rojas candidatas detectadas"

    # 5. Alert
    alerts = [Alert.model_validate(a) for a in web_snapshot["alerts"]]
    assert len(alerts) >= 3, "Debe haber alertas procesadas por el panel humano"

    # 6. CitizenReport
    reports = [CitizenReport.model_validate(r) for r in web_snapshot["citizen_reports"]]
    assert len(reports) >= 2, "Debe haber denuncias ciudadanas de prueba"


def test_04_article_14_human_review_invariants(web_snapshot):
    """Verifica que toda alerta publicada tenga revisor humano nominal y fecha de publicacion."""
    for raw in web_snapshot["alerts"]:
        alert = Alert.model_validate(raw)
        if alert.status == "published":
            assert alert.reviewed_by.lower() not in GENERIC_REVIEWERS
            assert "@" in alert.reviewed_by or "." in alert.reviewed_by, "El revisor debe ser una persona nominal"
            assert alert.published_at is not None
            assert alert.published_at.tzinfo is not None
        elif alert.status == "discarded":
            assert alert.review_notes is not None and len(alert.review_notes) > 0
            assert alert.published_at is None


def test_05_article_15_explainability_and_disclaimer(web_snapshot):
    """Verifica que todas las banderas y alertas cumplan los estandares de explicabilidad."""
    for raw in web_snapshot["red_flags"]:
        flag = RedFlag.model_validate(raw)
        assert flag.formula_description and len(flag.formula_description.strip()) > 10
        assert flag.threshold is not None
        assert flag.observed_value is not None
        assert flag.evidence_source in {"seace-ocds", "mef-datastore"}

    for raw in web_snapshot["alerts"]:
        alert = Alert.model_validate(raw)
        assert alert.disclaimer == STANDARD_ALERT_DISCLAIMER


def test_06_ca_006_01_legal_disclaimer_mandatory_on_reports(web_snapshot):
    """Verifica que los reportes ciudadanos registrados incluyan la aceptacion legal."""
    for raw in web_snapshot["citizen_reports"]:
        report = CitizenReport.model_validate(raw)
        assert report.legal_disclaimer_shown is True


def test_07_api_health_endpoint(local_web_server):
    """Verifica el endpoint GET /api/health."""
    url = f"{local_web_server}/api/health"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode("utf-8"))
        assert data["status"] == "healthy"
        assert data["service"] == "cajamarca-qhaway-web"
        assert data["region"] == "CAJAMARCA"
        assert data["invariants"]["art_18_universe_size"] == 14


def test_08_api_entities_endpoint(local_web_server):
    """Verifica el endpoint GET /api/entities y filtrado por ID."""
    url = f"{local_web_server}/api/entities"
    with urllib.request.urlopen(url) as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode("utf-8"))
        assert len(data) == 14

    # Filtrar por RUC del GORE Cajamarca
    url_filtered = f"{local_web_server}/api/entities?id=20453744168"
    with urllib.request.urlopen(url_filtered) as resp:
        assert resp.status == 200
        gore = json.loads(resp.read().decode("utf-8"))
        assert gore["ruc"] == "20453744168"
        assert gore["official_name"] == "GOBIERNO REGIONAL DE CAJAMARCA"


def test_09_api_alerts_public_only_published(local_web_server):
    """Verifica que GET /api/alerts solo exponga alertas con status == 'published' (Art. 14)."""
    url = f"{local_web_server}/api/alerts"
    with urllib.request.urlopen(url) as resp:
        assert resp.status == 200
        alerts = json.loads(resp.read().decode("utf-8"))
        assert len(alerts) > 0
        for alert in alerts:
            assert alert["status"] == "published", "Las alertas descartadas NO deben ser publicas"


def test_10_api_red_flags_internal_endpoint(local_web_server):
    """Verifica que GET /api/red-flags devuelva los candidatos algoritmicos para el panel."""
    url = f"{local_web_server}/api/red-flags"
    with urllib.request.urlopen(url) as resp:
        assert resp.status == 200
        flags = json.loads(resp.read().decode("utf-8"))
        assert len(flags) > 0
        for f in flags:
            assert "indicator_code" in f
            assert "formula_description" in f


def test_11_api_post_report_accepts_valid_disclaimer(local_web_server):
    """Verifica que POST /api/reports acepte denuncias con legal_disclaimer_shown=True."""
    url = f"{local_web_server}/api/reports"
    payload = {
        "raw_text": "Observacion ciudadana sobre retraso injustificado en obra de Celendin.",
        "legal_disclaimer_shown": True,
        "channel": "web",
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 201
        created = json.loads(resp.read().decode("utf-8"))
        assert created["moderation_status"] == "pending"
        assert created["legal_disclaimer_shown"] is True


def test_12_api_post_report_rejects_missing_disclaimer(local_web_server):
    """Verifica que POST /api/reports rechace con HTTP 400 si legal_disclaimer_shown=False (CA-006-01)."""
    url = f"{local_web_server}/api/reports"
    payload = {
        "raw_text": "Denuncia sin aceptar terminos legales.",
        "legal_disclaimer_shown": False,
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with pytest.raises(urllib.error.HTTPError) as exc_info:
        urllib.request.urlopen(req)
    assert exc_info.value.code == 400


def test_13_api_post_review_rejects_generic_reviewers(local_web_server):
    """Verifica que POST /api/review rechace revisores genericos (admin, system, bot, etc.)."""
    url = f"{local_web_server}/api/review"
    payload = {
        "entity_id": "ce-f5f5d8fc32518855",
        "red_flag_ids": ["rf-123456"],
        "status": "published",
        "reviewed_by": "admin",
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with pytest.raises(urllib.error.HTTPError) as exc_info:
        urllib.request.urlopen(req)
    assert exc_info.value.code == 400


def test_14_api_post_review_requires_notes_for_discarded(local_web_server):
    """Verifica que POST /api/review requiera review_notes si status == 'discarded' (CA-005-04)."""
    url = f"{local_web_server}/api/review"
    payload = {
        "entity_id": "ce-f5f5d8fc32518855",
        "red_flag_ids": ["rf-123456"],
        "status": "discarded",
        "reviewed_by": "m.vasquez@proetica-cajamarca.org.pe",
        "review_notes": "",  # Vacio ilegal
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with pytest.raises(urllib.error.HTTPError) as exc_info:
        urllib.request.urlopen(req)
    assert exc_info.value.code == 400


def test_15_cli_export_snapshot_and_audit():
    """Verifica que los comandos CLI export-snapshot y audit se ejecuten con codigo de salida 0."""
    from cajamarca_qhaway.cli import main
    import sys

    # Simular: cajamarca-qhaway web export-snapshot
    test_args = ["cajamarca-qhaway", "web", "export-snapshot", "--output", "web/src/data/verified-snapshot.json"]
    orig_argv = sys.argv
    try:
        sys.argv = test_args
        code = main()
        assert code == 0
    finally:
        sys.argv = orig_argv

    # Simular: cajamarca-qhaway web audit
    test_args = ["cajamarca-qhaway", "web", "audit"]
    try:
        sys.argv = test_args
        code = main()
        assert code == 0
    finally:
        sys.argv = orig_argv


def test_16_snapshot_integrity_validation_suite():
    """Ejecuta la auditoria integral de contratos sobre el snapshot final en disco."""
    errors = validate_snapshot_integrity(Path("web/src/data/verified-snapshot.json"))
    assert not errors, f"Errores de integridad detectados en verified-snapshot.json: {errors}"
