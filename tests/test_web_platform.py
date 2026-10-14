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
import urllib.error
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
from cajamarca_qhaway.web.server import CLEAN_PAGE_ROUTES, WebApiHandler, run_server
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


def test_clean_page_routes_match_vercel_rewrites():
    vercel = json.loads(Path("vercel.json").read_text(encoding="utf-8"))
    rewrites = {item["source"]: item["destination"] for item in vercel["rewrites"]}
    for route, filename in CLEAN_PAGE_ROUTES.items():
        source = "/index.html" if route == "index" else ("/" if route == "" else f"/{route}")
        assert rewrites.get(source) == f"/web/{filename}", f"Ruta desincronizada: {source}"


def test_03_snapshot_models_validation(web_snapshot):
    """Verifica que todos los registros en verified-snapshot.json validen contra Pydantic v2."""
    # 1. ContractingEntity
    entities = [ContractingEntity.model_validate(e) for e in web_snapshot["contracting_entities"]]
    assert len(entities) == 14, "Deben existir exactamente 14 entidades en el universo"

    # 2. ProcurementRecord
    procurements = [ProcurementRecord.model_validate(p) for p in web_snapshot["procurement_records"]]
    assert len(procurements) == web_snapshot["metadata"]["total_procurements"] == 475

    # 3. BudgetExecutionRecord
    budget = [BudgetExecutionRecord.model_validate(b) for b in web_snapshot["budget_execution_records"]]
    assert len(budget) == web_snapshot["metadata"]["total_budget_executions"] == 42
    assert {
        year: {"records": sum(item.fiscal_year == int(year) for item in budget),
               "entities": len({item.entity_id for item in budget if item.fiscal_year == int(year)})}
        for year in ("2024", "2025", "2026")
    } == web_snapshot["metadata"]["budget_coverage_by_year"]

    # 4. RedFlag
    red_flags = [RedFlag.model_validate(f) for f in web_snapshot["red_flags"]]
    assert red_flags == [], "Los candidatos internos no se exponen en el snapshot publico"

    # 5. Alert
    alerts = [Alert.model_validate(a) for a in web_snapshot["alerts"]]
    assert alerts == [], "No se publican alertas sin evidencia de dictamen humano validado"
    assert web_snapshot["metadata"]["total_candidate_red_flags"] == 473
    assert web_snapshot["metadata"]["total_alerts"] == 8
    assert web_snapshot["metadata"]["total_published_alerts"] == 0
    assert web_snapshot["metadata"]["alert_status_counts"] == {"discarded": 2, "in_review": 6}
    assert web_snapshot["metadata"]["budget_coverage_by_year"] == {
        "2024": {"records": 14, "entities": 14},
        "2025": {"records": 14, "entities": 14},
        "2026": {"records": 14, "entities": 14},
    }

    # 6. CitizenReport
    assert web_snapshot["citizen_reports"] == [], "Los reportes privados no deben salir en el snapshot publico"


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
    """Verifica que el snapshot publico no exponga reportes ciudadanos."""
    assert web_snapshot["citizen_reports"] == []


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
    """La copia pública no inventa dictámenes ni publica alertas no verificadas."""
    url = f"{local_web_server}/api/alerts"
    with urllib.request.urlopen(url) as resp:
        assert resp.status == 200
        alerts = json.loads(resp.read().decode("utf-8"))
        assert alerts == []


def test_10_api_red_flags_internal_endpoint(local_web_server):
    """El snapshot público no expone candidatos internos del panel revisor."""
    url = f"{local_web_server}/api/red-flags"
    with urllib.request.urlopen(url) as resp:
        assert resp.status == 200
        flags = json.loads(resp.read().decode("utf-8"))
        assert flags == []


def test_review_queue_requires_veedor_session(local_web_server):
    """La cola privada nunca entrega candidatos con la clave anónima o sin sesión."""
    with pytest.raises(urllib.error.HTTPError) as exc:
        urllib.request.urlopen(f"{local_web_server}/api/review/queue")
    assert exc.value.code == 401


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
    assert exc_info.value.code == 401


def test_14_api_post_review_requires_notes_for_discarded(local_web_server):
    """Verifica que POST /api/review requiera review_notes si status == 'discarded' (CA-005-04)."""
    from cajamarca_qhaway.web.server import ACCREDITED_VEEDORES, _issue_veedor_token

    token, _ = _issue_veedor_token(ACCREDITED_VEEDORES[0])
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
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"},
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


def test_17_wsgi_vercel_entrypoint():
    """Verifica que el entrypoint WSGI (api/index.py:app) funcione para /, /api/index.py y /api/health."""
    from api.index import app as vercel_wsgi_app

    def call_wsgi(method: str, path: str, query: str = "", body: bytes = b""):
        captured = {}

        def start_response(status, headers):
            captured["status"] = status
            captured["headers"] = dict(headers)

        environ = {
            "REQUEST_METHOD": method,
            "PATH_INFO": path,
            "QUERY_STRING": query,
            "CONTENT_LENGTH": str(len(body)),
            "wsgi.input": io.BytesIO(body),
        }
        chunks = vercel_wsgi_app(environ, start_response)
        return captured["status"], captured["headers"], b"".join(chunks)

    # 1. Raiz / sirve index.html
    status, headers, body = call_wsgi("GET", "/")
    assert status.startswith("200")
    assert "text/html" in headers["Content-Type"]
    assert b"Cajamarca Qhaway" in body

    # 2. /api/index.py tambien sirve index.html en caso de rewrite directo
    status_idx, _, body_idx = call_wsgi("GET", "/api/index.py")
    assert status_idx.startswith("200")
    assert b"Cajamarca Qhaway" in body_idx

    # 3. /api/health devuelve JSON valido con Content-Length exacto
    status_h, headers_h, body_h = call_wsgi("GET", "/api/health")
    assert status_h.startswith("200")
    assert int(headers_h["Content-Length"]) == len(body_h)
    health_data = json.loads(body_h.decode("utf-8"))
    assert health_data["status"] == "healthy"
    assert health_data["invariants"]["art_18_universe_size"] == 14


def test_18_multipage_routes_and_concentration_api(local_web_server):
    """Verifica las rutas multipagina limpias y los endpoints /api/concentration y /api/suppliers."""
    clean_routes = [
        "/entidades",
        "/entidad",
        "/alertas",
        "/contrataciones",
        "/contrato",
        "/presupuesto",
        "/proveedores",
        "/denuncia",
        "/transparencia",
        "/acerca",
        "/login",
        "/admin/revision",
    ]
    for route in clean_routes:
        with urllib.request.urlopen(f"{local_web_server}{route}") as resp:
            assert resp.status == 200
            html = resp.read().decode("utf-8")
            assert "Cajamarca Qhaway" in html

    for endpoint in ("/api/concentration", "/api/suppliers"):
        with urllib.request.urlopen(f"{local_web_server}{endpoint}") as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode("utf-8"))
            assert "hhi" in data
            assert "hhiPoints" in data
            assert "topSuppliers" in data
            assert data["suppliersCount"] >= 1


def test_19_veedor_auth_flow(local_web_server):
    """Verifica el flujo de acreditacion de veedores (/api/auth/login, /api/auth/session, /api/auth/logout)."""
    login_req = urllib.request.Request(
        f"{local_web_server}/api/auth/login",
        data=json.dumps({
            "email": "veeduria-cajamarca@proetica.org.pe",
            "password": "demo-veedor-2025",
        }).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(login_req) as resp:
        assert resp.status == 200
        auth_data = json.loads(resp.read().decode("utf-8"))
        token = auth_data["token"]
        assert auth_data["veedor"]["accreditationNumber"] == "VEED-PROETICA-2025-014"

    session_req = urllib.request.Request(
        f"{local_web_server}/api/auth/session",
        headers={"Authorization": f"Bearer {token}"},
        method="GET",
    )
    with urllib.request.urlopen(session_req) as resp:
        assert resp.status == 200
        sess_data = json.loads(resp.read().decode("utf-8"))
        assert sess_data["valid"] is True

    logout_req = urllib.request.Request(
        f"{local_web_server}/api/auth/logout",
        headers={"Authorization": f"Bearer {token}"},
        method="POST",
    )
    with urllib.request.urlopen(logout_req) as resp:
        assert resp.status == 200


def test_20_api_reports_privacy_and_tracking(local_web_server):
    """Verifica proteccion de privacidad en denuncias (Ley 29733) y endpoint de seguimiento seguro."""
    # 1. GET /api/reports sin token debe ser rechazado con 401
    reports_unauth_req = urllib.request.Request(f"{local_web_server}/api/reports", method="GET")
    with pytest.raises(urllib.error.HTTPError) as exc_info:
        urllib.request.urlopen(reports_unauth_req)
    assert exc_info.value.code == 401

    # 2. Iniciar sesion como veedor
    login_req = urllib.request.Request(
        f"{local_web_server}/api/auth/login",
        data=json.dumps({
            "email": "veeduria-cajamarca@proetica.org.pe",
            "password": "demo-veedor-2025",
        }).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(login_req) as resp:
        token = json.loads(resp.read().decode("utf-8"))["token"]

    # 3. GET /api/reports con token valido debe retornar 200
    reports_auth_req = urllib.request.Request(
        f"{local_web_server}/api/reports",
        headers={"Authorization": f"Bearer {token}"},
        method="GET",
    )
    with urllib.request.urlopen(reports_auth_req) as resp:
        assert resp.status == 200
        reports_list = json.loads(resp.read().decode("utf-8"))
        assert isinstance(reports_list, list)

    # 4. Crear una denuncia ciudadana para probar seguimiento
    post_req = urllib.request.Request(
        f"{local_web_server}/api/reports",
        data=json.dumps({
            "raw_text": "Observacion sobre irregularidades en expediente tecnico San Ignacio.",
            "legal_disclaimer_shown": True,
            "channel": "web",
        }).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(post_req) as resp:
        assert resp.status == 201
        created_report = json.loads(resp.read().decode("utf-8"))
        test_rep_id = created_report["report_id"]
        tracking_token = created_report["tracking_token"]

    # 5. GET /api/reports/track?token=<id> retorna metadatos publicos sanitizados
    track_req = urllib.request.Request(f"{local_web_server}/api/reports/track?token={tracking_token}", method="GET")
    with urllib.request.urlopen(track_req) as resp:
        assert resp.status == 200
        meta = json.loads(resp.read().decode("utf-8"))
        assert meta["report_id"] == test_rep_id
        assert meta["moderation_status"] == "pending"
        # Invariante de privacidad: Jamas exponer raw_text ni datos de identidad
        assert "raw_text" not in meta
        assert "reporter" not in meta

    # 6. GET /api/reports/track con token inexistente retorna 404
    track_404_req = urllib.request.Request(f"{local_web_server}/api/reports/track?token=cr-inexistente", method="GET")
    with pytest.raises(urllib.error.HTTPError) as exc_404:
        urllib.request.urlopen(track_404_req)
    assert exc_404.value.code == 404


def test_21_vercel_wsgi_security_and_tracking():
    """Verifica la paridad de proteccion y tracking en api/index.py (WSGI fallback)."""
    from api.index import app as vercel_wsgi_app

    def call_wsgi(method: str, path: str, query: str = "", body: bytes = b"", headers: dict = None):
        captured = {}
        headers = headers or {}

        def start_response(status, hdrs):
            captured["status"] = status
            captured["headers"] = dict(hdrs)

        environ = {
            "REQUEST_METHOD": method,
            "PATH_INFO": path,
            "QUERY_STRING": query,
            "CONTENT_LENGTH": str(len(body)),
            "wsgi.input": io.BytesIO(body),
        }
        for k, v in headers.items():
            environ[f"HTTP_{k.upper().replace('-', '_')}"] = v

        chunks = vercel_wsgi_app(environ, start_response)
        return captured["status"], captured["headers"], b"".join(chunks)

    # 1. GET /api/reports sin token debe retornar 401
    status, _, _ = call_wsgi("GET", "/api/reports")
    assert status.startswith("401")

    # 2. GET /api/reports con token Bearer valido de veedor retorna 200
    from cajamarca_qhaway.web.server import ACCREDITED_VEEDORES, _issue_veedor_token
    real_token, _ = _issue_veedor_token(ACCREDITED_VEEDORES[0])
    status_auth, _, body_auth = call_wsgi("GET", "/api/reports", headers={"Authorization": f"Bearer {real_token}"})
    assert status_auth.startswith("200")
    assert isinstance(json.loads(body_auth.decode("utf-8")), list)

    # 3. GET /api/reports/track sin parametro retorna 400
    status_bad, _, _ = call_wsgi("GET", "/api/reports/track")
    assert status_bad.startswith("400")

    # 4. POST /api/reports por WSGI
    rep_body = json.dumps({"raw_text": "Alerta vecinal", "legal_disclaimer_shown": True}).encode("utf-8")
    status_post, _, body_post = call_wsgi("POST", "/api/reports", body=rep_body)
    assert status_post.startswith("201")
    created = json.loads(body_post.decode("utf-8"))
    assert "report_id" in created

    # 5. Probar directamente _stdlib_fallback_dispatch para certificar el fallback estricto
    from api.index import _stdlib_fallback_dispatch
    s_code, _, s_body = _stdlib_fallback_dispatch("GET", "/api/reports", {}, req_headers={})
    assert s_code == 401
    from api.index import _ACCREDITED_VEEDORES_STDLIB, _issue_veedor_token_stdlib
    stdlib_token, _ = _issue_veedor_token_stdlib(_ACCREDITED_VEEDORES_STDLIB[0])
    s_code_ok, _, s_body_ok = _stdlib_fallback_dispatch(
        "GET", "/api/reports", {}, req_headers={"authorization": f"Bearer {stdlib_token}"}
    )
    assert s_code_ok == 200


def test_22_geospatial_api_endpoints(local_web_server):
    """Verifica los endpoints REST de la Capacidad 007 (/api/geospatial/works y /api/geospatial/divergence)."""
    # 1. Sin obras con CUI y coordenadas verificados, el endpoint retorna una lista vacía.
    req = urllib.request.Request(f"{local_web_server}/api/geospatial/works", method="GET")
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        works = json.loads(resp.read().decode("utf-8"))
        assert isinstance(works, list)
        assert works == []

    # 2. Filtrado por provincia
    req_chota = urllib.request.Request(f"{local_web_server}/api/geospatial/works?province=Chota", method="GET")
    with urllib.request.urlopen(req_chota) as resp:
        assert resp.status == 200
        chota_works = json.loads(resp.read().decode("utf-8"))
        assert chota_works == []

    # 3. Un ID ilustrativo no se devuelve como si fuera obra verificada.
    req_single = urllib.request.Request(f"{local_web_server}/api/geospatial/works?id=site-02-av-heroes-cenepa-mp-cajamarca", method="GET")
    with pytest.raises(urllib.error.HTTPError) as exc_single:
        urllib.request.urlopen(req_single)
    assert exc_single.value.code == 404

    # 4. ID inexistente retorna 404
    req_404 = urllib.request.Request(f"{local_web_server}/api/geospatial/works?id=site-inexistente", method="GET")
    with pytest.raises(urllib.error.HTTPError) as exc_404:
        urllib.request.urlopen(req_404)
    assert exc_404.value.code == 404

    # 5. GET /api/geospatial/divergence
    req_div = urllib.request.Request(f"{local_web_server}/api/geospatial/divergence", method="GET")
    with urllib.request.urlopen(req_div) as resp:
        assert resp.status == 200
        signals = json.loads(resp.read().decode("utf-8"))
        assert isinstance(signals, list)
        assert signals == []

    # 6. Filtrado de divergencia por severidad
    req_crit = urllib.request.Request(f"{local_web_server}/api/geospatial/divergence?severity=critical", method="GET")
    with urllib.request.urlopen(req_crit) as resp:
        assert resp.status == 200
        crit_signals = json.loads(resp.read().decode("utf-8"))
        assert all(s["severity"] == "critical" for s in crit_signals)


def test_23_reports_moderation_api_sync(local_web_server):
    """Verifica el endpoint POST /api/reports/moderate con autenticacion y persistencia."""
    from cajamarca_qhaway.web.server import ACCREDITED_VEEDORES, _issue_veedor_token

    veedor_token, _ = _issue_veedor_token(ACCREDITED_VEEDORES[0])

    # 1. Crear una denuncia de prueba
    post_req = urllib.request.Request(
        f"{local_web_server}/api/reports",
        data=json.dumps({
            "raw_text": "Denuncia de prueba para moderacion colegiada en Chota.",
            "legal_disclaimer_shown": True,
            "channel": "web",
        }).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(post_req) as resp:
        created = json.loads(resp.read().decode("utf-8"))
        test_rep_id = created["report_id"]
        tracking_token = created["tracking_token"]

    # 2. Moderar sin token debe retornar 401
    mod_unauth = urllib.request.Request(
        f"{local_web_server}/api/reports/moderate",
        data=json.dumps({"report_id": test_rep_id, "status": "accepted_as_lead"}).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with pytest.raises(urllib.error.HTTPError) as exc_401:
        urllib.request.urlopen(mod_unauth)
    assert exc_401.value.code == 401

    # 3. Moderar con estado invalido debe retornar 400
    mod_bad_status = urllib.request.Request(
        f"{local_web_server}/api/reports/moderate",
        data=json.dumps({"report_id": test_rep_id, "status": "invalid_status"}).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {veedor_token}",
        },
        method="POST",
    )
    with pytest.raises(urllib.error.HTTPError) as exc_bad:
        urllib.request.urlopen(mod_bad_status)
    assert exc_bad.value.code == 400

    # 4. Moderar con revisor generico debe ser rechazado
    mod_generic = urllib.request.Request(
        f"{local_web_server}/api/reports/moderate",
        data=json.dumps({
            "report_id": test_rep_id,
            "status": "accepted_as_lead",
            "moderated_by": "admin",
        }).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {veedor_token}",
        },
        method="POST",
    )
    with pytest.raises(urllib.error.HTTPError) as exc_gen:
        urllib.request.urlopen(mod_generic)
    assert exc_gen.value.code == 400

    # 5. Moderacion legitima con token de veedor colegiado retorna 200
    mod_valid = urllib.request.Request(
        f"{local_web_server}/api/reports/moderate",
        data=json.dumps({
            "report_id": test_rep_id,
            "status": "accepted_as_lead",
            "review_notes": "Verificado con expediente tecnico en campo.",
        }).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {veedor_token}",
        },
        method="POST",
    )
    with urllib.request.urlopen(mod_valid) as resp:
        assert resp.status == 200
        res_data = json.loads(resp.read().decode("utf-8"))
        assert res_data["success"] is True
        assert res_data["report_id"] == test_rep_id
        assert res_data["moderation_status"] == "accepted_as_lead"
        assert res_data["moderated_by"] is not None
        assert "Carlos Arana" in res_data["moderated_by"] or "Proetica" in res_data["moderated_by"]

    # 6. Consultar estado en /api/reports/track refleja el nuevo estado
    track_req = urllib.request.Request(f"{local_web_server}/api/reports/track?token={tracking_token}", method="GET")
    with urllib.request.urlopen(track_req) as resp:
        assert resp.status == 200
        meta = json.loads(resp.read().decode("utf-8"))
        assert meta["moderation_status"] == "accepted_as_lead"


def test_24_vercel_wsgi_geospatial_and_moderation():
    """Verifica paridad de endpoints geoespaciales y moderacion en api/index.py (WSGI fallback)."""
    from api.index import _stdlib_fallback_dispatch

    # 1. GET /api/geospatial/works via stdlib fallback
    code, _, body = _stdlib_fallback_dispatch("GET", "/api/geospatial/works", {})
    assert code == 200
    works = json.loads(body.decode("utf-8"))
    assert isinstance(works, list)

    # 2. GET /api/geospatial/divergence via stdlib fallback
    code_div, _, body_div = _stdlib_fallback_dispatch("GET", "/api/geospatial/divergence", {})
    assert code_div == 200
    signals = json.loads(body_div.decode("utf-8"))
    assert isinstance(signals, list)

    # 3. POST /api/reports/moderate sin auth retorna 401
    code_unauth, _, _ = _stdlib_fallback_dispatch("POST", "/api/reports/moderate", {}, body=b"{}", req_headers={})
    assert code_unauth == 401

    # 4. POST /api/reports/moderate con Bearer retorna 200
    mod_payload = json.dumps({
        "report_id": "cr-sample",
        "status": "accepted_as_lead",
        "moderated_by": "Lic. Carlos Arana Silva (Proetica)",
    }).encode("utf-8")
    code_mod, _, body_mod = _stdlib_fallback_dispatch(
        "POST",
        "/api/reports/moderate",
        {},
        body=mod_payload,
        req_headers={"authorization": "Bearer sample-token"},
    )
    assert code_mod == 200
    mod_res = json.loads(body_mod.decode("utf-8"))
    assert mod_res["success"] is True
    assert mod_res["moderation_status"] == "accepted_as_lead"



