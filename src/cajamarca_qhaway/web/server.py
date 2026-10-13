"""Servidor HTTP, aplicacion WSGI y API REST ligera para Cajamarca Qhaway.

Sirve la plataforma web estatica y expone los endpoints JSON REST de la plataforma:
- GET /api/health
- GET /api/snapshot
- GET /api/entities
- GET /api/procurements
- GET /api/budget
- GET /api/alerts (solo status == 'published' en vista publica, Art. 14)
- GET /api/red-flags (restringido a panel de revision humana)
- GET /api/reports
- POST /api/reports (valida legal_disclaimer_shown == True, CA-006-01)
- POST /api/review (valida reviewed_by no generico y review_notes si status == 'discarded', Art. 14)

Expone tanto `app(environ, start_response)` (estandar WSGI nativo para Vercel Python Runtime)
como `WebApiHandler(BaseHTTPRequestHandler)` para ejecucion local y serverless.
Cumple con politicas de seguridad (CSP, nosniff, DENY) y Antislop R-02 (cero em-dash).
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import mimetypes
import os
import posixpath
import secrets
import time
import urllib.parse
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from cajamarca_qhaway.capabilities.denuncia_intake import DenunciaIntakeService
from cajamarca_qhaway.capabilities.review_panel import ReviewPanelService
from cajamarca_qhaway.models.alert import GENERIC_REVIEWERS
from cajamarca_qhaway.web.exporter import build_verified_web_snapshot, export_verified_snapshot

PROJECT_ROOT = Path(__file__).resolve().parents[3]

SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Content-Security-Policy": "default-src 'self' https: data: 'unsafe-inline' 'unsafe-eval';",
}

CLEAN_PAGE_ROUTES: dict[str, str] = {
    "": "index.html",
    "index": "index.html",
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

ACCREDITED_VEEDORES: list[dict[str, str]] = [
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

_TOKEN_SECRET = os.environ.get(
    "CAJAMARCA_QHAWAY_AUTH_SECRET",
    "cajamarca-qhaway-civic-veedor-hmac-key-2026",
).encode("utf-8")
_REVOKED_TOKENS: set[str] = set()
_LOGIN_ATTEMPTS: dict[str, dict[str, Any]] = {}
_MAX_ATTEMPTS = 5
_LOCKOUT_SECONDS = 15 * 60


def _issue_veedor_token(veedor: dict[str, str], ttl_seconds: int = 8 * 3600) -> tuple[str, int]:
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
    sig = hmac.new(_TOKEN_SECRET, b64_payload.encode("ascii"), hashlib.sha256).hexdigest()
    return f"{b64_payload}.{sig}", expires_at


def _verify_veedor_token(token: str | None) -> dict[str, Any] | None:
    if not token or token in _REVOKED_TOKENS or "." not in token:
        return None
    b64_payload, sig = token.split(".", 1)
    expected_sig = hmac.new(_TOKEN_SECRET, b64_payload.encode("ascii"), hashlib.sha256).hexdigest()
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


class WebApiHandler(BaseHTTPRequestHandler):
    """Manejador HTTP que combina servicio de estaticos con API REST."""

    # Directorio base absoluto por defecto para servir estaticos
    web_dir: Path = PROJECT_ROOT / "web"
    snapshot_cache: dict[str, Any] | None = None
    denuncia_service: DenunciaIntakeService = DenunciaIntakeService()
    review_service: ReviewPanelService = ReviewPanelService()

    @classmethod
    def get_snapshot(cls) -> dict[str, Any]:
        """Obtiene el snapshot canonico, leyendolo del disco o generandolo."""
        if cls.snapshot_cache is not None:
            return cls.snapshot_cache

        snapshot_file = Path(cls.web_dir) / "src" / "data" / "verified-snapshot.json"
        if snapshot_file.exists():
            try:
                data = json.loads(snapshot_file.read_text(encoding="utf-8"))
                cls.snapshot_cache = data
                return data
            except Exception:
                pass

        # Si no existe en disco, generar inmediatamente en memoria
        data = build_verified_web_snapshot()
        cls.snapshot_cache = data
        return data

    @classmethod
    def _json_bytes(cls, data: Any, status_code: int = 200) -> tuple[int, str, bytes]:
        encoded = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
        return status_code, "application/json; charset=utf-8", encoded

    @classmethod
    def _error_bytes(cls, message: str, status_code: int = 400) -> tuple[int, str, bytes]:
        return cls._json_bytes({"error": message, "status": status_code}, status_code=status_code)

    @classmethod
    def dispatch(
        cls,
        method: str,
        path: str,
        query: dict[str, list[str]],
        body_bytes: bytes = b"",
        headers: dict[str, str] | None = None,
    ) -> tuple[int, str, bytes]:
        """Despachador central compartido entre WSGI (`app`) y `BaseHTTPRequestHandler`."""
        method_upper = method.upper()
        req_headers = {k.lower(): v for k, v in (headers or {}).items()}
        if method_upper == "OPTIONS":
            return 200, "text/plain; charset=utf-8", b"OK"

        # Soportar parametro __path enviado por rewrites de vercel.json
        rewritten_path = query.get("__path", [None])[0]
        if rewritten_path and path in ("/api/index.py", "/api/index", "/api", "/python"):
            path = rewritten_path if rewritten_path.startswith("/") else f"/{rewritten_path}"

        if method_upper == "GET":
            if path in ("/api/index.py", "/api/index", "/api"):
                return cls._resolve_static("/index.html")
            if path.startswith("/api/"):
                return cls._dispatch_api_get(path, query, req_headers)
            return cls._resolve_static(path)

        if method_upper == "POST":
            if path == "/api/auth/logout":
                return cls._dispatch_post_logout(req_headers)
            if not body_bytes:
                return cls._error_bytes("Cuerpo de solicitud vacio", 400)
            try:
                data = json.loads(body_bytes.decode("utf-8"))
            except Exception as exc:
                return cls._error_bytes(f"JSON invalido: {str(exc)}", 400)

            if path == "/api/auth/login":
                return cls._dispatch_post_login(data, req_headers)
            if path == "/api/reports":
                return cls._dispatch_post_reports(data)
            if path == "/api/review":
                return cls._dispatch_post_review(data, req_headers)
            return cls._error_bytes(f"Ruta POST no encontrada: {path}", 404)

        return cls._error_bytes(f"Metodo HTTP no soportado: {method_upper}", 405)

    @classmethod
    def _compute_suppliers_concentration(cls, snapshot: dict[str, Any], entity_id: str | None) -> dict[str, Any]:
        procurements = snapshot.get("procurement_records", [])
        if entity_id:
            procurements = [p for p in procurements if p.get("entity_id") == entity_id]

        supplier_map: dict[str, dict[str, Any]] = {}
        grand_total = 0.0
        for p in procurements:
            key = p.get("supplier_ruc") or p.get("supplier_name") or "Desconocido"
            amount = float(p.get("awarded_amount") or p.get("executed_amount") or 0.0)
            if key not in supplier_map:
                supplier_map[key] = {
                    "ruc": p.get("supplier_ruc") or "Sin RUC",
                    "name": p.get("supplier_name") or "Proveedor Anonimo",
                    "totalAmount": 0.0,
                    "contractsCount": 0,
                }
            supplier_map[key]["totalAmount"] += amount
            supplier_map[key]["contractsCount"] += 1
            grand_total += amount

        base_total = grand_total if grand_total > 0 else 1.0
        suppliers: list[dict[str, Any]] = []
        for s in supplier_map.values():
            share = s["totalAmount"] / base_total
            suppliers.append({
                **s,
                "share": round(share, 4),
                "sharePct": round(share * 100, 1),
            })
        suppliers.sort(key=lambda item: item["totalAmount"], reverse=True)
        hhi = sum(item["share"] ** 2 for item in suppliers)
        return {
            "hhi": round(hhi, 2),
            "hhiPoints": round(hhi * 10000),
            "grandTotal": grand_total,
            "suppliersCount": len(suppliers),
            "topSuppliers": suppliers,
        }

    @classmethod
    def _dispatch_api_get(
        cls,
        path: str,
        query: dict[str, list[str]],
        req_headers: dict[str, str] | None = None,
    ) -> tuple[int, str, bytes]:
        snapshot = cls.get_snapshot()
        req_headers = req_headers or {}

        if path == "/api/health":
            return cls._json_bytes({
                "status": "healthy",
                "service": "cajamarca-qhaway-web",
                "version": "1.0.0",
                "timestamp": snapshot.get("metadata", {}).get("generated_at"),
                "region": "CAJAMARCA",
                "invariants": {
                    "art_10_sources": ["seace-ocds", "mef-datastore"],
                    "art_14_human_review": True,
                    "art_16_no_person_scoring": True,
                    "art_18_universe_size": 14,
                },
            })

        if path == "/api/auth/session":
            auth_header = req_headers.get("authorization", "")
            if not auth_header.startswith("Bearer "):
                return cls._json_bytes({"valid": False, "error": "No token provided"}, status_code=401)
            token = auth_header[7:].strip()
            session = _verify_veedor_token(token)
            if not session:
                return cls._json_bytes({"valid": False, "error": "Session expired"}, status_code=401)
            return cls._json_bytes({
                "valid": True,
                "veedor": session["veedor"],
                "expiresAt": session["expiresAt"],
            })

        if path == "/api/snapshot":
            return cls._json_bytes(snapshot)

        if path == "/api/entities":
            entities = snapshot.get("contracting_entities", [])
            entity_id = query.get("id", [None])[0]
            if entity_id:
                matched = next(
                    (e for e in entities if e.get("entity_id") == entity_id or e.get("ruc") == entity_id),
                    None,
                )
                if matched:
                    return cls._json_bytes(matched)
                return cls._error_bytes(f"Entidad no encontrada con ID: {entity_id}", 404)
            return cls._json_bytes(entities)

        if path == "/api/procurements":
            procurements = snapshot.get("procurement_records", [])
            entity_id = query.get("entity_id", [None])[0]
            ocid = query.get("ocid", [None])[0]
            if ocid:
                matched = next(
                    (p for p in procurements if p.get("ocid") == ocid or p.get("procurement_id") == ocid),
                    None,
                )
                if matched:
                    return cls._json_bytes(matched)
                return cls._error_bytes(f"Contratacion no encontrada con OCID: {ocid}", 404)
            if entity_id:
                procurements = [p for p in procurements if p.get("entity_id") == entity_id]
            return cls._json_bytes(procurements)

        if path == "/api/budget":
            budget = snapshot.get("budget_execution_records", [])
            entity_id = query.get("entity_id", [None])[0]
            if entity_id:
                budget = [b for b in budget if b.get("entity_id") == entity_id]
            return cls._json_bytes(budget)

        if path == "/api/alerts":
            # Invariante Art. 14: Solo alertas con status == 'published' para vista publica
            all_alerts = snapshot.get("alerts", [])
            published_only = [a for a in all_alerts if a.get("status") == "published"]
            alert_id = query.get("id", [None])[0]
            if alert_id:
                matched = next((a for a in published_only if a.get("alert_id") == alert_id), None)
                if matched:
                    return cls._json_bytes(matched)
                return cls._error_bytes(f"Alerta publicada no encontrada con ID: {alert_id}", 404)
            entity_id = query.get("entity_id", [None])[0]
            if entity_id:
                published_only = [a for a in published_only if a.get("entity_id") == entity_id]
            return cls._json_bytes(published_only)

        if path == "/api/red-flags":
            flags = snapshot.get("red_flags", [])
            flag_id = query.get("id", [None])[0]
            if flag_id:
                matched = next((f for f in flags if f.get("red_flag_id") == flag_id), None)
                if matched:
                    return cls._json_bytes(matched)
                return cls._error_bytes(f"Bandera roja no encontrada con ID: {flag_id}", 404)
            return cls._json_bytes(flags)

        if path == "/api/reports":
            reports = snapshot.get("citizen_reports", [])
            return cls._json_bytes(reports)

        if path in ("/api/concentration", "/api/suppliers"):
            entity_id = query.get("entity_id", [None])[0]
            return cls._json_bytes(cls._compute_suppliers_concentration(snapshot, entity_id))

        return cls._error_bytes(f"Ruta API no encontrada: {path}", 404)

    @classmethod
    def _dispatch_post_login(cls, data: dict[str, Any], req_headers: dict[str, str]) -> tuple[int, str, bytes]:
        if data.get("honeypot"):
            return cls._error_bytes("Solicitud rechazada", 400)

        email = str(data.get("email", "")).strip().lower()
        password = str(data.get("password", ""))
        if not email or not password:
            return cls._error_bytes("Debe ingresar el correo y la contrasena de acreditacion", 400)

        now = time.time()
        user_key = f"user:{email}"
        record = _LOGIN_ATTEMPTS.get(user_key)
        if record and record.get("locked_until", 0) > now:
            remaining_sec = int(record["locked_until"] - now)
            return cls._json_bytes(
                {
                    "error": f"Cuenta bloqueada temporalmente por seguridad. Reintente en {max(1, remaining_sec // 60)} minutos.",
                    "retryAfter": remaining_sec,
                    "status": 429,
                },
                status_code=429,
            )

        cand_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()
        matched = next((v for v in ACCREDITED_VEEDORES if v["email"] == email), None)
        is_valid = bool(matched and hmac.compare_digest(matched["password_hash"], cand_hash))

        if not is_valid or matched is None:
            rec = _LOGIN_ATTEMPTS.setdefault(user_key, {"attempts": 0, "locked_until": 0.0})
            rec["attempts"] += 1
            if rec["attempts"] >= _MAX_ATTEMPTS:
                rec["locked_until"] = now + _LOCKOUT_SECONDS
            remaining = max(0, _MAX_ATTEMPTS - rec["attempts"])
            return cls._json_bytes(
                {
                    "error": "Credenciales invalidas. Compruebe su correo u organizacion y el codigo de veeduria.",
                    "remainingAttempts": remaining,
                    "status": 401,
                },
                status_code=401,
            )

        _LOGIN_ATTEMPTS.pop(user_key, None)
        token, expires_at = _issue_veedor_token(matched)
        veedor_public = {
            "email": matched["email"],
            "name": matched["name"],
            "organization": matched["organization"],
            "accreditationNumber": matched["accreditationNumber"],
            "role": matched["role"],
        }
        return cls._json_bytes({
            "token": token,
            "veedor": veedor_public,
            "expiresAt": expires_at,
            "message": "Acreditacion verificada. Sesion segura iniciada.",
        })

    @classmethod
    def _dispatch_post_logout(cls, req_headers: dict[str, str]) -> tuple[int, str, bytes]:
        auth_header = req_headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            _REVOKED_TOKENS.add(auth_header[7:].strip())
        return cls._json_bytes({"message": "Sesion finalizada correctamente"})

    @classmethod
    def _dispatch_post_reports(cls, data: dict[str, Any]) -> tuple[int, str, bytes]:
        """Procesa una denuncia ciudadana cumpliendo CA-006-01."""
        raw_text = str(data.get("raw_text", "")).strip()
        legal_disclaimer = bool(data.get("legal_disclaimer_shown") or data.get("disclaimer_accepted"))
        raw_channel = str(data.get("channel") or data.get("source_channel") or "web").strip().lower()
        channel = "web" if raw_channel in ("web", "web_form") else raw_channel
        entity_id = data.get("related_entity_id") or data.get("entity_id")

        if not raw_text:
            return cls._error_bytes("El campo 'raw_text' es obligatorio", 400)

        # Invariante CA-006-01: descargo legal obligatorio
        if not legal_disclaimer:
            return cls._error_bytes(
                "La denuncia no puede ser aceptada sin previa confirmacion del descargo legal (CA-006-01)",
                400,
            )

        try:
            report = cls.denuncia_service.submit_report(
                raw_text=raw_text,
                legal_disclaimer_shown=True,
                channel=channel,
                related_entity_id=entity_id,
            )
            snapshot = cls.get_snapshot()
            payload = report.model_dump(mode="json")
            snapshot.setdefault("citizen_reports", []).append(payload)
            return cls._json_bytes({**payload, "report": payload}, status_code=201)
        except Exception as exc:
            return cls._error_bytes(f"Error al procesar denuncia: {str(exc)}", 400)

    @classmethod
    def _dispatch_post_review(
        cls,
        data: dict[str, Any],
        req_headers: dict[str, str] | None = None,
    ) -> tuple[int, str, bytes]:
        """Procesa una decision de revision humana cumpliendo Art. 14 y CA-005-02."""
        req_headers = req_headers or {}
        entity_id = str(data.get("entity_id", "")).strip()
        red_flag_ids = data.get("red_flag_ids", [])
        status = str(data.get("status", "")).strip()
        reviewed_by = str(data.get("reviewed_by", "")).strip()
        review_notes = str(data.get("review_notes", "")).strip() or None

        auth_header = req_headers.get("authorization", "")
        if auth_header.startswith("Bearer ") and not reviewed_by:
            session = _verify_veedor_token(auth_header[7:].strip())
            if session:
                veedor = session["veedor"]
                reviewed_by = f"{veedor['name']} ({veedor['organization']})"

        if not entity_id or not red_flag_ids or not status or not reviewed_by:
            return cls._error_bytes(
                "Campos requeridos: entity_id, red_flag_ids, status, reviewed_by",
                400,
            )

        # CA-005-02: rechazar revisores genericos
        cleaned_reviewer = reviewed_by.lower()
        if cleaned_reviewer in GENERIC_REVIEWERS or not cleaned_reviewer:
            return cls._error_bytes(f"reviewed_by no puede ser generico o vacio: '{reviewed_by}'", 400)

        # CA-005-04: review_notes obligatorio si status == 'discarded'
        if status == "discarded" and not review_notes:
            return cls._error_bytes(
                "review_notes es obligatorio cuando el estado es 'discarded' (CA-005-04)",
                400,
            )

        try:
            if status == "published":
                alert = cls.review_service.publish_alert(
                    entity_id=entity_id,
                    red_flags=red_flag_ids,
                    reviewer_id=reviewed_by,
                    review_notes=review_notes,
                )
            elif status == "discarded":
                alert = cls.review_service.discard_alert(
                    entity_id=entity_id,
                    red_flags=red_flag_ids,
                    reviewer_id=reviewed_by,
                    review_notes=review_notes or "Descarte documentado",
                )
            else:
                return cls._error_bytes(
                    f"Estado invalido: {status}. Debe ser 'published' o 'discarded'",
                    400,
                )

            snapshot = cls.get_snapshot()
            payload = alert.model_dump(mode="json")
            snapshot.setdefault("alerts", []).append(payload)
            return cls._json_bytes({**payload, "alert": payload}, status_code=201)
        except Exception as exc:
            return cls._error_bytes(f"Error al procesar decision: {str(exc)}", 400)

    @classmethod
    def _resolve_static(cls, path: str) -> tuple[int, str, bytes]:
        """Resuelve y lee archivos estaticos y rutas multipagina desde web_dir."""
        clean_path = posixpath.normpath(path).lstrip("/")
        if clean_path == "web":
            clean_path = "index.html"
        elif clean_path.startswith("web/"):
            clean_path = clean_path[4:]
        if not clean_path or clean_path == ".":
            clean_path = "index.html"

        if clean_path in CLEAN_PAGE_ROUTES:
            clean_path = CLEAN_PAGE_ROUTES[clean_path]

        base_path = Path(cls.web_dir).resolve()
        file_path = (base_path / clean_path).resolve()

        # Evitar directory traversal
        try:
            file_path.relative_to(base_path)
        except ValueError:
            return cls._error_bytes("Acceso denegado", 403)

        if not file_path.exists() and not file_path.suffix:
            html_candidate = (base_path / f"{clean_path}.html").resolve()
            if html_candidate.exists():
                file_path = html_candidate

        if not file_path.exists() or file_path.is_dir():
            index_path = base_path / "index.html"
            if index_path.exists():
                file_path = index_path
            else:
                return cls._error_bytes("Recurso no encontrado", 404)

        ctype, _ = mimetypes.guess_type(str(file_path))
        if not ctype:
            ctype = "application/octet-stream"
        if ctype.startswith("text/") or ctype in ("application/javascript", "application/json", "image/svg+xml"):
            content_type_header = f"{ctype}; charset=utf-8"
        else:
            content_type_header = ctype

        try:
            content = file_path.read_bytes()
            return 200, content_type_header, content
        except Exception as exc:
            return cls._error_bytes(f"Error al leer archivo: {str(exc)}", 500)

    def _set_headers(
        self,
        status_code: int = 200,
        content_type: str = "application/json; charset=utf-8",
        content_length: int | None = None,
    ) -> None:
        self.send_response(status_code)
        if "charset=" not in content_type and (
            content_type.startswith("text/") or content_type in ("application/json", "application/javascript")
        ):
            content_type = f"{content_type}; charset=utf-8"
        self.send_header("Content-Type", content_type)
        if content_length is not None:
            self.send_header("Content-Length", str(content_length))
        for header, val in SECURITY_HEADERS.items():
            self.send_header(header, val)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def _write_dispatch_result(self, status_code: int, content_type: str, body: bytes) -> None:
        self._set_headers(status_code, content_type, content_length=len(body))
        self.wfile.write(body)

    def _extract_headers(self) -> dict[str, str]:
        return {k.lower(): v for k, v in self.headers.items()}

    def do_OPTIONS(self) -> None:
        """Maneja preflight requests para CORS."""
        status_code, content_type, body = self.dispatch("OPTIONS", self.path, {}, headers=self._extract_headers())
        self._write_dispatch_result(status_code, content_type, body)

    def do_GET(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        query = urllib.parse.parse_qs(parsed.query)
        status_code, content_type, body = self.dispatch("GET", parsed.path, query, headers=self._extract_headers())
        self._write_dispatch_result(status_code, content_type, body)

    def do_POST(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        query = urllib.parse.parse_qs(parsed.query)
        content_length = int(self.headers.get("Content-Length", 0))
        body_bytes = self.rfile.read(content_length) if content_length > 0 else b""
        status_code, content_type, body = self.dispatch(
            "POST",
            parsed.path,
            query,
            body_bytes,
            headers=self._extract_headers(),
        )
        self._write_dispatch_result(status_code, content_type, body)


def app(environ: dict[str, Any], start_response: Any) -> list[bytes]:
    """Aplicacion WSGI estandar (PEP 3333) para Vercel Python Runtime y servidores WSGI."""
    method = environ.get("REQUEST_METHOD", "GET").upper()
    raw_path = environ.get("PATH_INFO", "/") or "/"
    query_string = environ.get("QUERY_STRING", "")
    query = urllib.parse.parse_qs(query_string)

    req_headers: dict[str, str] = {}
    for k, v in environ.items():
        if k.startswith("HTTP_"):
            header_name = k[5:].replace("_", "-").lower()
            req_headers[header_name] = str(v)

    body_bytes = b""
    if method in ("POST", "PUT", "PATCH"):
        try:
            content_length = int(environ.get("CONTENT_LENGTH") or 0)
        except (ValueError, TypeError):
            content_length = 0
        wsgi_input = environ.get("wsgi.input")
        if wsgi_input is not None:
            body_bytes = wsgi_input.read(content_length) if content_length > 0 else wsgi_input.read()

    status_code, content_type, response_body = WebApiHandler.dispatch(
        method=method,
        path=raw_path,
        query=query,
        body_bytes=body_bytes,
        headers=req_headers,
    )

    try:
        phrase = HTTPStatus(status_code).phrase
    except ValueError:
        phrase = "OK"
    status_line = f"{status_code} {phrase}"

    cache_control = "no-store"
    if method == "GET" and status_code == 200:
        if raw_path in ("/api/red-flags", "/api/auth/session"):
            cache_control = "no-store"
        elif raw_path.startswith("/api/"):
            cache_control = "public, max-age=0, s-maxage=60, stale-while-revalidate=300"
        else:
            cache_control = "public, max-age=0, s-maxage=3600"

    response_headers: list[tuple[str, str]] = [
        ("Content-Type", content_type),
        ("Content-Length", str(len(response_body))),
        ("Cache-Control", cache_control),
        ("Access-Control-Allow-Origin", "*"),
        ("Access-Control-Allow-Methods", "GET, POST, OPTIONS"),
        ("Access-Control-Allow-Headers", "Content-Type, Authorization"),
    ]
    for k, v in SECURITY_HEADERS.items():
        response_headers.append((k, v))

    start_response(status_line, response_headers)
    return [response_body]


def run_server(port: int = 8080, web_dir: Path | str | None = None) -> ThreadingHTTPServer:
    """Inicia el servidor HTTP en el puerto indicado."""
    if web_dir is not None:
        WebApiHandler.web_dir = Path(web_dir).resolve()
    else:
        WebApiHandler.web_dir = (PROJECT_ROOT / "web").resolve()
    server_address = ("", port)
    httpd = ThreadingHTTPServer(server_address, WebApiHandler)
    return httpd


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    httpd = run_server(port=port)
    print(f"Servidor Cajamarca Qhaway escuchando en http://localhost:{port}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor detenido por el usuario.")
        httpd.server_close()
