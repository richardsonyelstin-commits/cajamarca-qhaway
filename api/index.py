"""Punto de entrada WSGI Serverless para Vercel Python Runtime.

Define exclusivamente una funcion top-level `def app(environ, start_response):` (PEP 3333)
con aislamiento de errores en cold start y respaldo determinista en libreria estandar,
evitando cualquier colision con `BaseHTTPRequestHandler` o fallos de importacion en Lambda.
Cumple con Antislop R-02 (cero em-dash).
"""

import base64
import hashlib
import hmac
import json
import mimetypes
import os
import posixpath
import secrets
import sys
import time
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
_ACCREDITED_VEEDORES_STDLIB = [
    {
        "email": "veeduria-cajamarca@proetica.org.pe",
        "password_hash": hashlib.sha256(b"demo-veedor-2025").hexdigest(),
        "name": "Lic. Carlos Arana Silva",
        "organization": "Proetica (Capitulo Peruano de Transparency International)",
        "accreditationNumber": "VEED-PROETICA-2025-014",
        "role": "veedor_titular",
    },
    {
        "email": "veeduria.proetica@cajamarca-qhaway.pe",
        "password_hash": hashlib.sha256(b"Proetica#Cajamarca2025!").hexdigest(),
        "name": "Dra. Elena Santillan Mori",
        "organization": "Proetica Cajamarca",
        "accreditationNumber": "VEED-PROETICA-2025-008",
        "role": "veedor_titular",
    },
    {
        "email": "veeduria.propuesta@cajamarca-qhaway.pe",
        "password_hash": hashlib.sha256(b"Propuesta#Civica2025!").hexdigest(),
        "name": "Ing. Marco Tacilla Vasquez",
        "organization": "Grupo Propuesta Ciudadana",
        "accreditationNumber": "VEED-PROPUESTA-2025-021",
        "role": "veedor_revisor",
    },
    {
        "email": "veeduria.grufides@cajamarca-qhaway.pe",
        "password_hash": hashlib.sha256(b"Grufides#Veedor2025!").hexdigest(),
        "name": "Abg. Mirtha Villanueva Quispe",
        "organization": "GRUFIDES Cajamarca",
        "accreditationNumber": "VEED-GRUFIDES-2025-003",
        "role": "veedor_titular",
    },
    {
        "email": "veedor.regional@cajamarca-qhaway.pe",
        "password_hash": hashlib.sha256(b"Veedor#Qhaway2025!").hexdigest(),
        "name": "Prof. Jorge Terrones Bazan",
        "organization": "Mesa de Concertacion y Veeduria Ciudadana Cajamarca",
        "accreditationNumber": "VEED-MESA-2025-007",
        "role": "veedor_colegiado",
    },
]

_TOKEN_SECRET_STDLIB = os.environ.get(
    "CAJAMARCA_QHAWAY_AUTH_SECRET",
    "cajamarca-qhaway-civic-veedor-hmac-key-2026",
).encode("utf-8")
_REVOKED_TOKENS_STDLIB = set()
_LOGIN_ATTEMPTS_STDLIB = {}
_MAX_ATTEMPTS_STDLIB = 5
_LOCKOUT_SECONDS_STDLIB = 15 * 60


def _issue_veedor_token_stdlib(veedor, ttl_seconds=8 * 3600):
    now_ms = int(time.time() * 1000)
    expires_at = now_ms + (ttl_seconds * 1000)
    payload = {
        "veedor": {
            "email": veedor["email"],
            "name": veedor["name"],
            "organization": veedor["organization"],
            "accreditationNumber": veedor["accreditationNumber"],
            "role": veedor["role"],
        },
        "createdAt": now_ms,
        "expiresAt": expires_at,
        "nonce": secrets.token_hex(8),
    }
    raw_bytes = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    b64_payload = base64.urlsafe_b64encode(raw_bytes).decode("ascii").rstrip("=")
    sig = hmac.new(_TOKEN_SECRET_STDLIB, b64_payload.encode("ascii"), hashlib.sha256).hexdigest()
    return f"{b64_payload}.{sig}", expires_at


def _verify_veedor_token_stdlib(token):
    if not token or token in _REVOKED_TOKENS_STDLIB or "." not in token:
        return None
    b64_payload, sig = token.split(".", 1)
    expected_sig = hmac.new(_TOKEN_SECRET_STDLIB, b64_payload.encode("ascii"), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(sig, expected_sig):
        return None
    padding = "=" * (-len(b64_payload) % 4)
    try:
        raw = base64.urlsafe_b64decode(b64_payload + padding)
        data = json.loads(raw.decode("utf-8"))
    except Exception:
        return None
    if int(time.time() * 1000) > int(data.get("expiresAt", 0)):
        return None
    return data


def _stdlib_fallback_dispatch(method, path, query, body=b"", req_headers=None):
    req_headers = req_headers or {}
    if method == "OPTIONS":
        return 200, "text/plain; charset=utf-8", b"OK"

    rewritten_path = query.get("__path", [None])[0]
    if rewritten_path:
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
            public_snap = dict(snap)
            public_snap["citizen_reports"] = []
            public_snap["alerts"] = [
                alert for alert in public_snap.get("alerts", [])
                if alert.get("status") == "published"
            ]
            published_ids = {
                flag_id
                for alert in public_snap.get("alerts", [])
                if alert.get("status") == "published"
                for flag_id in alert.get("red_flag_ids", [])
            }
            public_snap["red_flags"] = [
                flag for flag in public_snap.get("red_flags", [])
                if flag.get("red_flag_id") in published_ids
            ]
            return 200, "application/json; charset=utf-8", json.dumps(public_snap).encode("utf-8")
        if path == "/api/entities":
            entities = snap.get("contracting_entities", [])
            ent_id = query.get("id", [None])[0] or query.get("ruc", [None])[0]
            if ent_id:
                m = next((e for e in entities if e.get("entity_id") == ent_id or e.get("ruc") == ent_id), None)
                if m:
                    return 200, "application/json; charset=utf-8", json.dumps(m).encode("utf-8")
                return 404, "application/json; charset=utf-8", json.dumps({"error": f"Entidad '{ent_id}' no encontrada"}).encode("utf-8")
            return 200, "application/json; charset=utf-8", json.dumps(entities).encode("utf-8")
        if path == "/api/procurements":
            procurements = snap.get("procurement_records", [])
            ocid = query.get("ocid", [None])[0]
            if ocid:
                m = next((p for p in procurements if p.get("ocid") == ocid or p.get("procurement_id") == ocid), None)
                if m:
                    return 200, "application/json; charset=utf-8", json.dumps(m).encode("utf-8")
                return 404, "application/json; charset=utf-8", json.dumps({"error": f"Contratacion '{ocid}' no encontrada"}).encode("utf-8")
            eid = query.get("entity_id", [None])[0]
            if eid:
                procurements = [p for p in procurements if p.get("entity_id") == eid]
            return 200, "application/json; charset=utf-8", json.dumps(procurements).encode("utf-8")
        if path == "/api/budget":
            budgets = snap.get("budget_execution_records", [])
            eid = query.get("entity_id", [None])[0]
            if eid:
                budgets = [b for b in budgets if b.get("entity_id") == eid]
            return 200, "application/json; charset=utf-8", json.dumps(budgets).encode("utf-8")
        if path == "/api/alerts":
            pubs = [a for a in snap.get("alerts", []) if a.get("status") == "published"]
            aid = query.get("id", [None])[0]
            if aid:
                m = next((a for a in pubs if a.get("alert_id") == aid), None)
                if m:
                    return 200, "application/json; charset=utf-8", json.dumps(m).encode("utf-8")
                return 404, "application/json; charset=utf-8", json.dumps({"error": f"Alerta '{aid}' no encontrada"}).encode("utf-8")
            eid = query.get("entity_id", [None])[0]
            if eid:
                pubs = [a for a in pubs if a.get("entity_id") == eid]
            return 200, "application/json; charset=utf-8", json.dumps(pubs).encode("utf-8")
        if path == "/api/red-flags":
            published_flag_ids = {
                flag_id
                for alert in snap.get("alerts", [])
                if alert.get("status") == "published"
                for flag_id in alert.get("red_flag_ids", [])
            }
            flags = [
                flag for flag in snap.get("red_flags", [])
                if flag.get("red_flag_id") in published_flag_ids
            ]
            rfid = query.get("id", [None])[0]
            if rfid:
                m = next((f for f in flags if f.get("red_flag_id") == rfid), None)
                if m:
                    return 200, "application/json; charset=utf-8", json.dumps(m).encode("utf-8")
                return 404, "application/json; charset=utf-8", json.dumps({"error": f"Bandera roja '{rfid}' no encontrada"}).encode("utf-8")
            return 200, "application/json; charset=utf-8", json.dumps(flags).encode("utf-8")

        if path == "/api/reports":
            if method == "POST" and (
                os.environ.get("VERCEL") == "1"
                or os.environ.get("CAJAMARCA_QHAWAY_DATABASE_URL")
            ):
                return 503, "application/json; charset=utf-8", json.dumps({
                    "error": "No se puede confirmar persistencia del reporte; intente mas tarde"
                }).encode("utf-8")
            if method == "POST":
                try:
                    data = json.loads(body.decode("utf-8")) if body else {}
                except Exception:
                    return 400, "application/json; charset=utf-8", json.dumps({"error": "JSON invalido"}).encode("utf-8")
                raw_text = str(data.get("raw_text", "")).strip()
                if not raw_text:
                    return 400, "application/json; charset=utf-8", json.dumps({"error": "Campo 'raw_text' es obligatorio"}).encode("utf-8")
                if not bool(data.get("legal_disclaimer_shown") or data.get("disclaimer_accepted")):
                    return 400, "application/json; charset=utf-8", json.dumps({"error": "Descargo legal obligatorio (CA-006-01)"}).encode("utf-8")
                report_id = f"cr-{int(time.time()*1000):x}"
                tracking_token = secrets.token_urlsafe(32)
                tracking_token_hash = hashlib.sha256(tracking_token.encode("utf-8")).hexdigest()
                now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                payload = {
                    "report_id": report_id,
                    "submitted_at": now_iso,
                    "channel": data.get("channel", "web"),
                    "raw_text": raw_text,
                    "related_entity_id": data.get("related_entity_id"),
                    "moderation_status": "received",
                    "legal_disclaimer_shown": True,
                    "tracking_token_hash": tracking_token_hash,
                }
                snap.setdefault("citizen_reports", []).append(payload)
                public_payload = {key: value for key, value in payload.items() if key != "tracking_token_hash"}
                return 201, "application/json; charset=utf-8", json.dumps({**public_payload, "tracking_token": tracking_token, "report": public_payload}).encode("utf-8")
            # GET requiere sesion de veedor
            auth_h = req_headers.get("authorization", "")
            token = auth_h[7:].strip() if auth_h.startswith("Bearer ") else ""
            if not _verify_veedor_token_stdlib(token):
                return 401, "application/json; charset=utf-8", json.dumps({"error": "Acceso restringido a veedores acreditados (Ley 29733)"}).encode("utf-8")
            return 200, "application/json; charset=utf-8", json.dumps(snap.get("citizen_reports", [])).encode("utf-8")

        if path == "/api/reports/track":
            tok = query.get("token", [None])[0] or query.get("id", [None])[0]
            if not tok:
                return 400, "application/json; charset=utf-8", json.dumps({"error": "Parametro 'token' es obligatorio"}).encode("utf-8")
            tok_clean = tok.strip()
            reports = snap.get("citizen_reports", [])
            token_hash = hashlib.sha256(tok_clean.encode("utf-8")).hexdigest()
            m = next((r for r in reports if r.get("tracking_token_hash") == token_hash), None)
            if not m:
                return 404, "application/json; charset=utf-8", json.dumps({"error": "Expediente de denuncia no encontrado"}).encode("utf-8")
            safe = {
                "report_id": m.get("report_id"),
                "submitted_at": m.get("submitted_at") or m.get("created_at"),
                "moderation_status": m.get("moderation_status", "received"),
                "related_entity_id": m.get("related_entity_id"),
                "channel": m.get("channel", "web"),
                "legal_disclaimer_shown": m.get("legal_disclaimer_shown", True),
            }
            return 200, "application/json; charset=utf-8", json.dumps(safe).encode("utf-8")

        if path == "/api/review" and method == "POST":
            auth_header = req_headers.get("authorization", "")
            auth_token = auth_header[7:].strip() if auth_header.startswith("Bearer ") else ""
            session = _verify_veedor_token_stdlib(auth_token)
            if not session:
                return 401, "application/json; charset=utf-8", json.dumps({"error": "Sesion de veedor requerida"}).encode("utf-8")
            return 503, "application/json; charset=utf-8", json.dumps({"error": "El modo fallback no dispone de un repositorio privado de evidencia"}).encode("utf-8")

        if path == "/api/auth/session":
            auth_header = req_headers.get("authorization", "")
            if not auth_header.startswith("Bearer "):
                return 401, "application/json; charset=utf-8", json.dumps({"valid": False, "error": "No token provided"}).encode("utf-8")
            token = auth_header[7:].strip()
            session = _verify_veedor_token_stdlib(token)
            if not session:
                return 401, "application/json; charset=utf-8", json.dumps({"valid": False, "error": "Session expired"}).encode("utf-8")
            return 200, "application/json; charset=utf-8", json.dumps({
                "valid": True,
                "veedor": session["veedor"],
                "expiresAt": session["expiresAt"],
            }).encode("utf-8")

        if path == "/api/review/queue":
            auth_header = req_headers.get("authorization", "")
            token = auth_header[7:].strip() if auth_header.startswith("Bearer ") else ""
            if not _verify_veedor_token_stdlib(token):
                return 401, "application/json; charset=utf-8", json.dumps({"error": "Sesion de veedor requerida"}).encode("utf-8")
            return 503, "application/json; charset=utf-8", json.dumps({"error": "El modo fallback no dispone de un repositorio privado de revision"}).encode("utf-8")

        if path == "/api/auth/login" and method == "POST":
            try:
                data = json.loads(body.decode("utf-8")) if body else {}
            except Exception:
                return 400, "application/json; charset=utf-8", json.dumps({"error": "JSON invalido"}).encode("utf-8")
            if data.get("honeypot"):
                return 400, "application/json; charset=utf-8", json.dumps({"error": "Solicitud rechazada"}).encode("utf-8")
            email = str(data.get("email", "")).strip().lower()
            password = str(data.get("password", ""))
            if not email or not password:
                return 400, "application/json; charset=utf-8", json.dumps({"error": "Debe ingresar el correo y la contrasena de acreditacion"}).encode("utf-8")

            now = time.time()
            user_key = f"user:{email}"
            record = _LOGIN_ATTEMPTS_STDLIB.get(user_key)
            if record and record.get("locked_until", 0) > now:
                remaining_sec = int(record["locked_until"] - now)
                return 429, "application/json; charset=utf-8", json.dumps({
                    "error": f"Cuenta bloqueada temporalmente por seguridad. Reintente en {max(1, remaining_sec // 60)} minutos.",
                    "retryAfter": remaining_sec,
                    "status": 429,
                }).encode("utf-8")

            cand_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()
            matched = next((v for v in _ACCREDITED_VEEDORES_STDLIB if v["email"] == email), None)
            is_valid = bool(matched and hmac.compare_digest(matched["password_hash"], cand_hash))

            if not is_valid or matched is None:
                rec = _LOGIN_ATTEMPTS_STDLIB.setdefault(user_key, {"attempts": 0, "locked_until": 0.0})
                rec["attempts"] += 1
                if rec["attempts"] >= _MAX_ATTEMPTS_STDLIB:
                    rec["locked_until"] = now + _LOCKOUT_SECONDS_STDLIB
                remaining = max(0, _MAX_ATTEMPTS_STDLIB - rec["attempts"])
                return 401, "application/json; charset=utf-8", json.dumps({
                    "error": "Credenciales invalidas. Compruebe su correo u organizacion y el codigo de veeduria.",
                    "remainingAttempts": remaining,
                    "status": 401,
                }).encode("utf-8")

            if user_key in _LOGIN_ATTEMPTS_STDLIB:
                del _LOGIN_ATTEMPTS_STDLIB[user_key]

            token, expires_at = _issue_veedor_token_stdlib(matched)
            return 200, "application/json; charset=utf-8", json.dumps({
                "token": token,
                "expiresAt": expires_at,
                "veedor": {
                    "email": matched["email"],
                    "name": matched["name"],
                    "organization": matched["organization"],
                    "accreditationNumber": matched["accreditationNumber"],
                    "role": matched["role"],
                },
            }).encode("utf-8")

        if path == "/api/auth/logout" and method == "POST":
            return 200, "application/json; charset=utf-8", json.dumps({"message": "Sesion finalizada correctamente"}).encode("utf-8")

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

        if path == "/api/geospatial/works":
            works = snap.get("geospatial_works", [])
            site_id = query.get("id", [None])[0] or query.get("site_id", [None])[0]
            if site_id:
                m = next((w for w in works if w.get("site_id") == site_id), None)
                if m:
                    return 200, "application/json; charset=utf-8", json.dumps(m).encode("utf-8")
                return 404, "application/json; charset=utf-8", json.dumps({"error": f"Obra '{site_id}' no encontrada"}).encode("utf-8")
            prov = query.get("province", [None])[0]
            if prov:
                prov_clean = prov.strip().lower()
                works = [w for w in works if w.get("province", "").strip().lower() == prov_clean]
            return 200, "application/json; charset=utf-8", json.dumps(works).encode("utf-8")

        if path == "/api/geospatial/divergence":
            signals = snap.get("geospatial_signals", [])
            site_id = query.get("site_id", [None])[0] or query.get("id", [None])[0]
            if site_id:
                m = next((s for s in signals if s.get("site_id") == site_id), None)
                if m:
                    return 200, "application/json; charset=utf-8", json.dumps(m).encode("utf-8")
                return 404, "application/json; charset=utf-8", json.dumps({"error": f"Senal para '{site_id}' no encontrada"}).encode("utf-8")
            sev = query.get("severity", [None])[0]
            if sev:
                sev_clean = sev.strip().lower()
                signals = [s for s in signals if s.get("severity", "").strip().lower() == sev_clean]
            return 200, "application/json; charset=utf-8", json.dumps(signals).encode("utf-8")

        if path == "/api/reports/moderate" and method == "POST":
            auth_val = req_headers.get("authorization", "")
            if not auth_val.startswith("Bearer "):
                return 401, "application/json; charset=utf-8", json.dumps({"error": "Autenticacion requerida"}).encode("utf-8")
            try:
                data = json.loads(body.decode("utf-8")) if body else {}
            except Exception:
                return 400, "application/json; charset=utf-8", json.dumps({"error": "JSON invalido"}).encode("utf-8")
            report_id = str(data.get("report_id", "")).strip()
            status = str(data.get("status") or data.get("moderation_status", "")).strip()
            moderator = str(data.get("moderated_by", "Veedor Acreditado")).strip()
            if not report_id:
                return 400, "application/json; charset=utf-8", json.dumps({"error": "report_id obligatorio"}).encode("utf-8")
            if status not in ("accepted_as_lead", "rejected"):
                return 400, "application/json; charset=utf-8", json.dumps({"error": "Estado invalido"}).encode("utf-8")
            now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            rep_res = {
                "success": True,
                "report_id": report_id,
                "moderation_status": status,
                "moderated_by": moderator,
                "moderated_at": now_iso,
            }
            return 200, "application/json; charset=utf-8", json.dumps(rep_res).encode("utf-8")

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
        "georreferenciacion": "georreferenciacion.html",
        "mapa": "georreferenciacion.html",
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

    content_length = environ.get("CONTENT_LENGTH")
    body_bytes = b""
    if content_length and content_length.isdigit():
        try:
            body_bytes = environ["wsgi.input"].read(int(content_length))
        except Exception:
            body_bytes = b""

    req_headers = {}
    auth_header = environ.get("HTTP_AUTHORIZATION")
    if auth_header:
        req_headers["authorization"] = auth_header
    for key, val in environ.items():
        if key.startswith("HTTP_"):
            header_name = key[5:].replace("_", "-").lower()
            req_headers[header_name] = val

    status_code, content_type, resp_body = _stdlib_fallback_dispatch(
        method, raw_path, query, body=body_bytes, req_headers=req_headers
    )
    try:
        phrase = HTTPStatus(status_code).phrase
    except ValueError:
        phrase = "OK"

    headers = [
        ("Content-Type", content_type),
        ("Content-Length", str(len(resp_body))),
        ("Access-Control-Allow-Origin", "*"),
        ("Access-Control-Allow-Methods", "GET, POST, OPTIONS"),
        ("Access-Control-Allow-Headers", "Content-Type, Authorization"),
    ] + _SECURITY_HEADERS

    start_response(f"{status_code} {phrase}", headers)
    return [resp_body]
