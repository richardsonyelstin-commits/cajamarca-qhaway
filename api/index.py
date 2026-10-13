"""Punto de entrada WSGI Serverless para Vercel Python Runtime.

Define exclusivamente una funcion top-level `def app(environ, start_response):` (PEP 3333)
con aislamiento de errores en cold start y respaldo determinista en libreria estandar,
evitando cualquier colision con `BaseHTTPRequestHandler` o fallos de importacion en Lambda.
Cumple con Antislop R-02 (cero em-dash).
"""

import json
import mimetypes
import posixpath
import sys
import traceback
import urllib.parse
from http import HTTPStatus
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_PATH = PROJECT_ROOT / "src"
WEB_DIR = PROJECT_ROOT / "web"

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

_IMPORT_ERROR = None
_canonical_wsgi_app = None

try:
    from cajamarca_qhaway.web.server import WebApiHandler, app as _srv_app

    WebApiHandler.web_dir = WEB_DIR
    _canonical_wsgi_app = _srv_app
except Exception:
    _IMPORT_ERROR = traceback.format_exc()

_STDLIB_SNAPSHOT_CACHE = None

_SECURITY_HEADERS = [
    ("X-Content-Type-Options", "nosniff"),
    ("X-Frame-Options", "DENY"),
    ("Referrer-Policy", "strict-origin-when-cross-origin"),
    ("Content-Security-Policy", "default-src 'self' https: data: 'unsafe-inline' 'unsafe-eval';"),
]


def _load_snapshot_stdlib():
    global _STDLIB_SNAPSHOT_CACHE
    if _STDLIB_SNAPSHOT_CACHE is not None:
        return _STDLIB_SNAPSHOT_CACHE
    snap_path = WEB_DIR / "src" / "data" / "verified-snapshot.json"
    if snap_path.exists():
        _STDLIB_SNAPSHOT_CACHE = json.loads(snap_path.read_text(encoding="utf-8"))
        return _STDLIB_SNAPSHOT_CACHE
    return {
        "metadata": {"generated_at": "2026-10-12T00:00:00Z"},
        "contracting_entities": [],
        "procurement_records": [],
        "budget_execution_records": [],
        "red_flags": [],
        "alerts": [],
        "citizen_reports": [],
    }


_STDLIB_SUNAT_CACHE = None


def _load_sunat_stdlib():
    global _STDLIB_SUNAT_CACHE
    if _STDLIB_SUNAT_CACHE is not None:
        return _STDLIB_SUNAT_CACHE
    sunat_path = PROJECT_ROOT / "data" / "sunat" / "ruc_registry.json"
    if sunat_path.exists():
        try:
            _STDLIB_SUNAT_CACHE = json.loads(sunat_path.read_text(encoding="utf-8"))
            return _STDLIB_SUNAT_CACHE
        except Exception:
            pass
    return {"metadata": {}, "registry": {}}


def _stdlib_fallback_dispatch(method, path, query):
    if method == "OPTIONS":
        return 200, "text/plain; charset=utf-8", b"OK"

    rewritten_path = query.get("__path", [None])[0]
    if rewritten_path and path in ("/api/index.py", "/api/index", "/api", "/python"):
        path = rewritten_path if rewritten_path.startswith("/") else f"/{rewritten_path}"

    if path in ("/api/index.py", "/api/index", "/api"):
        path = "/index.html"

    if path.startswith("/api/"):
        snap = _load_snapshot_stdlib()
        if path == "/api/health":
            payload = {
                "status": "healthy",
                "service": "cajamarca-qhaway-web",
                "version": "1.0.0",
                "timestamp": snap.get("metadata", {}).get("generated_at"),
                "region": "CAJAMARCA",
                "runtime_mode": "stdlib_fallback",
                "import_error": _IMPORT_ERROR,
                "invariants": {
                    "art_10_sources": ["seace-ocds", "mef-datastore"],
                    "art_14_human_review": True,
                    "art_16_no_person_scoring": True,
                    "art_18_universe_size": 14,
                },
            }
            return 200, "application/json; charset=utf-8", json.dumps(payload).encode("utf-8")
        if path == "/api/snapshot":
            return 200, "application/json; charset=utf-8", json.dumps(snap).encode("utf-8")
        if path == "/api/entities":
            return 200, "application/json; charset=utf-8", json.dumps(snap.get("contracting_entities", [])).encode("utf-8")
        if path == "/api/procurements":
            return 200, "application/json; charset=utf-8", json.dumps(snap.get("procurement_records", [])).encode("utf-8")
        if path == "/api/budget":
            return 200, "application/json; charset=utf-8", json.dumps(snap.get("budget_execution_records", [])).encode("utf-8")
        if path == "/api/alerts":
            pubs = [a for a in snap.get("alerts", []) if a.get("status") == "published"]
            return 200, "application/json; charset=utf-8", json.dumps(pubs).encode("utf-8")
        if path == "/api/red-flags":
            return 200, "application/json; charset=utf-8", json.dumps(snap.get("red_flags", [])).encode("utf-8")
        if path == "/api/reports":
            return 200, "application/json; charset=utf-8", json.dumps(snap.get("citizen_reports", [])).encode("utf-8")
        if path == "/api/sunat/ruc":
            dni_param = query.get("dni", [None])[0]
            if dni_param is not None:
                return (
                    403,
                    "application/json; charset=utf-8",
                    json.dumps(
                        {
                            "error": (
                                "Articulo 16 (Prohibicion de perfilamiento de personas naturales): "
                                "Queda terminantemente prohibido consultar, almacenar o procesar "
                                "solicitudes de DNI o RENIEC. El sistema opera exclusivamente sobre "
                                "entidades publicas y proveedores contratistas del Estado mediante RUC."
                            ),
                            "code": "CONSTITUTIONAL_PRIVACY_GUARD_ART_16",
                        }
                    ).encode("utf-8"),
                )

            ruc_param = query.get("ruc", [None])[0]
            if ruc_param is not None:
                cleaned_val = ruc_param.strip().replace("PE-RUC-", "")
                if len(cleaned_val) == 8 and cleaned_val.isdigit():
                    return (
                        403,
                        "application/json; charset=utf-8",
                        json.dumps(
                            {
                                "error": (
                                    "Articulo 16 (Prohibicion de perfilamiento de personas naturales): "
                                    f"El identificador '{ruc_param}' corresponde a un DNI de 8 digitos. "
                                    "Se rechaza la operacion para salvaguardar la privacidad de personas naturales."
                                ),
                                "code": "CONSTITUTIONAL_PRIVACY_GUARD_ART_16",
                            }
                        ).encode("utf-8"),
                    )

                if len(cleaned_val) != 11 or not cleaned_val.isdigit():
                    return (
                        400,
                        "application/json; charset=utf-8",
                        json.dumps({"error": "RUC invalido: debe contener 11 digitos numericos."}).encode("utf-8"),
                    )

                sunat_data = _load_sunat_stdlib()
                reg = sunat_data.get("registry", {})
                profile = reg.get(cleaned_val)
                if profile:
                    return 200, "application/json; charset=utf-8", json.dumps(profile).encode("utf-8")
                return (
                    404,
                    "application/json; charset=utf-8",
                    json.dumps({"error": f"RUC '{cleaned_val}' no encontrado en el padron verificado."}).encode("utf-8"),
                )

            sunat_data = _load_sunat_stdlib()
            meta = sunat_data.get("metadata", {})
            return 200, "application/json; charset=utf-8", json.dumps(meta).encode("utf-8")

        return 404, "application/json; charset=utf-8", json.dumps({"error": f"Ruta no encontrada: {path}", "status": 404}).encode("utf-8")

    clean_routes = {
        "entidades": "entidades.html",
        "entidad": "entidad-detalle.html",
        "alertas": "alertas.html",
        "contrataciones": "contrataciones.html",
        "contrato": "contrato-detalle.html",
        "presupuesto": "presupuesto.html",
        "proveedores": "proveedores.html",
        "concentracion": "proveedores.html",
        "denuncia": "denuncia.html",
        "transparencia": "transparencia.html",
        "acerca": "acerca.html",
        "admin/revision": "admin-revision.html",
        "login": "login.html",
        "acreditacion": "login.html",
    }
    clean_path = posixpath.normpath(path).lstrip("/")
    if clean_path == "web":
        clean_path = "index.html"
    elif clean_path.startswith("web/"):
        clean_path = clean_path[4:]
    if not clean_path or clean_path == ".":
        clean_path = "index.html"
    if clean_path in clean_routes:
        clean_path = clean_routes[clean_path]

    base_path = WEB_DIR.resolve()
    file_path = (base_path / clean_path).resolve()
    if not file_path.exists() and not file_path.suffix:
        cand = (base_path / f"{clean_path}.html").resolve()
        if cand.exists():
            file_path = cand
    if not file_path.exists() or file_path.is_dir():
        file_path = base_path / "index.html"
    if not file_path.exists():
        return 404, "text/plain; charset=utf-8", b"Not Found"

    ctype, _ = mimetypes.guess_type(str(file_path))
    ctype = ctype or "application/octet-stream"
    if ctype.startswith("text/") or ctype in ("application/javascript", "application/json", "image/svg+xml"):
        ctype = f"{ctype}; charset=utf-8"
    return 200, ctype, file_path.read_bytes()


def app(environ, start_response):
    """Entrypoint WSGI estandar (PEP 3333) para Vercel Python Runtime."""
    if _canonical_wsgi_app is not None:
        try:
            return _canonical_wsgi_app(environ, start_response)
        except Exception:
            pass

    method = environ.get("REQUEST_METHOD", "GET").upper()
    raw_path = environ.get("PATH_INFO", "/") or "/"
    query_string = environ.get("QUERY_STRING", "")
    query = urllib.parse.parse_qs(query_string)

    status_code, content_type, body = _stdlib_fallback_dispatch(method, raw_path, query)
    try:
        phrase = HTTPStatus(status_code).phrase
    except ValueError:
        phrase = "OK"

    headers = [
        ("Content-Type", content_type),
        ("Content-Length", str(len(body))),
        ("Access-Control-Allow-Origin", "*"),
        ("Access-Control-Allow-Methods", "GET, POST, OPTIONS"),
        ("Access-Control-Allow-Headers", "Content-Type, Authorization"),
    ] + _SECURITY_HEADERS

    start_response(f"{status_code} {phrase}", headers)
    return [body]
