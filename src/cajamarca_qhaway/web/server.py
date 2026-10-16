"""Servidor HTTP, aplicacion WSGI y API REST ligera para Cajamarca Qhaway.

Sirve la plataforma web estatica y expone los endpoints JSON REST de la plataforma:
- GET /api/health
- GET /api/snapshot
- GET /api/entities
- GET /api/procurements
- GET /api/budget
- GET /api/alerts (solo status == 'published' en vista publica, Art. 14)
- GET /api/red-flags (solo banderas enlazadas a alertas publicadas)
- GET /api/review/queue (candidatos internos; requiere sesion de veedor)
- GET /api/reports
- POST /api/reports (valida legal_disclaimer_shown == True, CA-006-01)
- POST /api/review (valida reviewed_by no generico y review_notes si status == 'discarded', Art. 14)

Expone tanto `app(environ, start_response)` (estandar WSGI nativo para Vercel Python Runtime)
como `WebApiHandler(BaseHTTPRequestHandler)` para ejecucion local y serverless.
Cumple con politicas de seguridad (CSP, nosniff, DENY) y Antislop R-02 (cero em-dash).
"""

from __future__ import annotations

import hashlib
import json
import logging
import mimetypes
import os
import posixpath
import secrets
import time
import urllib.parse
import urllib.request
from datetime import UTC, datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from cajamarca_qhaway.capabilities.denuncia_intake import DenunciaIntakeService
from cajamarca_qhaway.capabilities.review_panel import ReviewPanelService
from cajamarca_qhaway.models import BudgetExecutionRecord
from cajamarca_qhaway.models.alert import GENERIC_REVIEWERS
from cajamarca_qhaway.models.budget_reconciliation import canonical_budget_records
from cajamarca_qhaway.web.exporter import (
    build_verified_web_snapshot,
)

logger = logging.getLogger(__name__)

try:
    from cajamarca_qhaway.persistence.connection import DatabaseManager
    from cajamarca_qhaway.persistence.repositories import (
        AlertRepository,
        CitizenReportRepository,
        RedFlagRepository,
    )
    _db_manager = DatabaseManager()
    _alert_repo = AlertRepository(_db_manager)
    _report_repo = CitizenReportRepository(_db_manager)
    _red_flag_repo = RedFlagRepository(_db_manager)
    from cajamarca_qhaway.persistence.repositories.case_analysis_repository import CaseAnalysisRepository
    _case_analysis_repo = CaseAnalysisRepository(_db_manager)
except Exception as error:
    logger.exception("Fallo controlado del adaptador web (%s)", type(error).__name__, exc_info=False)
    _db_manager = None
    _alert_repo = None
    _report_repo = None
    _red_flag_repo = None
    _case_analysis_repo = None

PROJECT_ROOT = Path(__file__).resolve().parents[3]

SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Content-Security-Policy": "default-src 'self' https: data: 'unsafe-inline' 'unsafe-eval';",
}

# La respuesta publica se construye mediante lista positiva: un campo nuevo
# (por ejemplo, expedientes de revision) no se publica por accidente.
PUBLIC_SNAPSHOT_FIELDS = (
    "contracting_entities", "procurement_records", "budget_execution_records",
    "alerts", "red_flags", "geospatial_works", "geospatial_signals",
)
PUBLIC_METADATA_FIELDS = (
    "version", "generated_at", "source", "region", "constitution_version",
    "articles_covered", "total_entities", "total_procurements",
    "total_budget_executions", "budget_coverage_by_year", "total_geospatial_works",
)

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
    "georreferenciacion": "georreferenciacion.html",
    "mapa": "georreferenciacion.html",
    "transparencia": "transparencia.html",
    "acerca": "acerca.html",
    "metodologia": "metodologia.html",
    "admin": "admin-revision.html",
    "admin/revision": "admin-revision.html",
    "login": "login.html",
    "acreditacion": "login.html",
}

class PublicProjectionUnavailable(RuntimeError):
    """Configured authoritative publication storage cannot be read safely."""


def _verify_veedor_token(token: str | None) -> dict[str, Any] | None:
    from cajamarca_qhaway.web.auth import AuthService
    return AuthService(_db_manager).verify(token)


def _durable_repository(repo: Any) -> bool:
    """Cloud/private writes require configured PostgreSQL, never volatile storage."""
    if repo is None:
        return False
    cloud = bool(os.environ.get("VERCEL") or os.environ.get("CAJAMARCA_QHAWAY_DATABASE_URL")
                 or os.environ.get("CAJAMARCA_QHAWAY_ENV", "").lower() == "production"
                 or os.environ.get("ENVIRONMENT", "").lower() == "production")
    return not cloud or bool(getattr(getattr(repo, "db", None), "is_postgres", False))


def _cache_control(method: str, path: str, query: dict[str, list[str]],
                   headers: dict[str, str], status: int) -> str:
    effective = query.get("__path", [path])[0]
    effective = "/" + effective.lstrip("/")
    private = headers.get("authorization") or any(
        effective.startswith(prefix) for prefix in
        ("/api/auth", "/api/reports", "/api/review", "/api/red-flags")
    )
    if private or method != "GET" or status != 200:
        return "private, no-store"
    if effective.startswith("/api/"):
        return "public, max-age=0, s-maxage=60, stale-while-revalidate=300"
    return "public, max-age=0, s-maxage=3600"


class WebApiHandler(BaseHTTPRequestHandler):
    """Manejador HTTP que combina servicio de estaticos con API REST."""

    # Directorio base absoluto por defecto para servir estaticos
    web_dir: Path = PROJECT_ROOT / "web"
    snapshot_cache: dict[str, Any] | None = None
    snapshot_cache_time: float = 0
    snapshot_cache_mtime: int = 0
    denuncia_service: DenunciaIntakeService = DenunciaIntakeService()
    review_service: ReviewPanelService = ReviewPanelService()

    @classmethod
    def get_snapshot(cls) -> dict[str, Any]:
        """Obtiene el snapshot canonico, leyendolo del disco o generandolo."""
        snapshot_file = Path(cls.web_dir) / "src" / "data" / "verified-snapshot.json"
        mtime = snapshot_file.stat().st_mtime_ns if snapshot_file.exists() else 0
        if (cls.snapshot_cache is not None and mtime == cls.snapshot_cache_mtime
                and time.monotonic() - cls.snapshot_cache_time < 30):
            return cls.snapshot_cache
        cls.snapshot_cache_time = time.monotonic()
        cls.snapshot_cache_mtime = mtime

        live_snapshot = cls._fetch_live_snapshot()
        if live_snapshot is not None:
            cls.snapshot_cache = live_snapshot
            return live_snapshot

        if snapshot_file.exists():
            try:
                data = json.loads(snapshot_file.read_text(encoding="utf-8"))
                cls.snapshot_cache = data
                return data
            except Exception as error:
                logger.exception("Fallo controlado del adaptador web (%s)", type(error).__name__, exc_info=False)

        # Si no existe en disco, generar inmediatamente en memoria
        data = build_verified_web_snapshot()
        cls.snapshot_cache = data
        return data

    @classmethod
    def _fetch_live_snapshot(cls) -> dict[str, Any] | None:
        """Consulta las tablas publicas de Supabase sin exponer credenciales al cliente."""
        base_url = (os.environ.get("CAJAMARCA_QHAWAY_SUPABASE_URL")
                    or os.environ.get("SUPABASE_URL", "")).rstrip("/")
        anon_key = (os.environ.get("CAJAMARCA_QHAWAY_SUPABASE_ANON_KEY")
                    or os.environ.get("SUPABASE_ANON_KEY", ""))
        if not base_url or not anon_key:
            return None

        tables = {
            "contracting_entities": "select=*&order=official_name.asc",
            "procurement_records": (
                "select=*&order=retrieved_at.desc&limit=1000"
            ),
            "budget_execution_records": (
                "select=*&order=fiscal_year.desc&limit=1000"
            ),
            "alerts": "select=*&status=eq.published&order=published_at.desc",
        }
        headers = {
            "apikey": anon_key,
            "Authorization": f"Bearer {anon_key}",
            "Accept": "application/json",
        }
        result: dict[str, Any] = {}
        try:
            for table, query in tables.items():
                url = f"{base_url}/rest/v1/{table}?{query}"
                request = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(request, timeout=8) as response:
                    rows = json.loads(response.read().decode("utf-8"))
                if not isinstance(rows, list):
                    return None
                result[table] = rows
            masters = canonical_budget_records([
                BudgetExecutionRecord.model_validate(row) for row in result["budget_execution_records"]
            ])
            entity_ids = {row["entity_id"] for row in result["contracting_entities"]}
            years = {row.fiscal_year for row in masters}
            if any({row.entity_id for row in masters if row.fiscal_year == year} != entity_ids
                   for year in years):
                return None
            result["budget_execution_records"] = [row.model_dump(mode="json") for row in masters]
        except Exception as error:
            logger.exception("Fallo controlado del adaptador web (%s)", type(error).__name__, exc_info=False)
            return None

        fallback = cls._snapshot_from_disk()
        result["red_flags"] = fallback.get("red_flags", [])
        result["citizen_reports"] = fallback.get("citizen_reports", [])
        result["metadata"] = {
            **fallback.get("metadata", {}),
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "source_mode": "supabase-live-via-backend",
            "total_entities": len(result["contracting_entities"]),
            "total_procurements": len(result["procurement_records"]),
            "total_budget_executions": len(result["budget_execution_records"]),
            "total_published_alerts": len(result["alerts"]),
        }
        return result

    @classmethod
    def _snapshot_from_disk(cls) -> dict[str, Any]:
        snapshot_file = Path(cls.web_dir) / "src" / "data" / "verified-snapshot.json"
        if snapshot_file.exists():
            try:
                return json.loads(snapshot_file.read_text(encoding="utf-8"))
            except Exception as error:
                logger.exception("Fallo controlado del adaptador web (%s)", type(error).__name__, exc_info=False)
        return {}

    @classmethod
    def _json_bytes(cls, data: Any, status_code: int = 200) -> tuple[int, str, bytes]:
        encoded = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
        return status_code, "application/json; charset=utf-8", encoded

    @classmethod
    def _error_bytes(cls, message: str, status_code: int = 400) -> tuple[int, str, bytes]:
        return cls._json_bytes({"error": message, "status": status_code}, status_code=status_code)

    _sunat_service: Any = None

    @classmethod
    def get_sunat_service(cls) -> Any:
        if cls._sunat_service is None:
            from cajamarca_qhaway.capabilities.sunat_enrichment.service import (
                SunatEnrichmentService,
            )
            cls._sunat_service = SunatEnrichmentService()
        return cls._sunat_service

    @classmethod
    def dispatch(cls, method: str, path: str, query: dict[str, list[str]],
                 body_bytes: bytes = b"", headers: dict[str, str] | None = None
                 ) -> tuple[int, str, bytes]:
        from cajamarca_qhaway.web.auth import AuthUnavailable
        try:
            return cls._dispatch(method, path, query, body_bytes, headers)
        except AuthUnavailable:
            return cls._error_bytes("Autenticacion segura no disponible", 503)
        except PublicProjectionUnavailable:
            return cls._error_bytes("Publicacion confirmada temporalmente no disponible", 503)

    @classmethod
    def _dispatch(
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
        if rewritten_path:
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
                logger.exception("Fallo controlado del adaptador web (%s)", type(exc).__name__, exc_info=False)
                return cls._error_bytes(f"JSON invalido: {exc!s}", 400)

            if not isinstance(data, dict):
                return cls._error_bytes("El cuerpo JSON debe ser un objeto", 400)

            if path == "/api/auth/login":
                return cls._dispatch_post_login(data, req_headers)
            if path == "/api/reports":
                return cls._dispatch_post_reports(data)
            if path == "/api/reports/moderate":
                return cls._dispatch_post_reports_moderate(data, req_headers)
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
    def _public_projection(cls, snapshot: dict[str, Any]) -> dict[str, Any]:
        """Recover committed publication independently of the process snapshot cache."""
        public = dict(snapshot)
        public["citizen_reports"] = []
        public["alerts"] = [row for row in snapshot.get("alerts", []) if row.get("status") == "published"]
        repository_active = False
        authoritative = bool(getattr(_db_manager, "is_postgres", False))
        if authoritative and _alert_repo is None:
            raise PublicProjectionUnavailable()
        if _durable_repository(_alert_repo):
            try:
                published = _alert_repo.list_published()
                # An explicitly configured PostgreSQL database is authoritative even
                # when empty. A pristine local in-memory DB retains snapshot reading.
                repository_active = bool(_alert_repo.db.is_postgres or published or _alert_repo.list_all())
                if repository_active:
                    public["alerts"] = [row.model_dump(mode="json") for row in published]
            except Exception as error:
                if authoritative:
                    raise PublicProjectionUnavailable() from error
                logger.warning("Repositorio local no disponible; se usa instantanea publica")
        published_ids = {flag_id for row in public["alerts"] for flag_id in row.get("red_flag_ids", [])}
        flags = {row["red_flag_id"]: row for row in snapshot.get("red_flags", [])
                 if row.get("red_flag_id") in published_ids}
        if repository_active and _red_flag_repo is not None:
            for flag_id in sorted(published_ids):
                try:
                    flag = _red_flag_repo.get_by_id(flag_id)
                    if flag is not None:
                        flags[flag_id] = flag.model_dump(mode="json")
                except Exception as error:
                    if authoritative:
                        raise PublicProjectionUnavailable() from error
                    logger.warning("Evidencia publicada no disponible para la proyeccion publica")
        public["red_flags"] = list(flags.values())
        public["metadata"] = {**snapshot.get("metadata", {}), "total_published_alerts": len(public["alerts"])}
        return public

    @classmethod
    def _dispatch_api_get(
        cls,
        path: str,
        query: dict[str, list[str]],
        req_headers: dict[str, str] | None = None,
    ) -> tuple[int, str, bytes]:
        snapshot = cls.get_snapshot()
        if path in ("/api/alerts", "/api/red-flags", "/api/snapshot"):
            snapshot = cls._public_projection(snapshot)
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

        if path in {"/api/review/queue", "/api/review/cases"}:
            auth_header = req_headers.get("authorization", "")
            if not auth_header.startswith("Bearer "):
                return cls._json_bytes({"error": "Sesion de veedor requerida"}, status_code=401)
            if not _verify_veedor_token(auth_header[7:].strip()):
                return cls._json_bytes({"error": "Sesion de veedor invalida o expirada"}, status_code=401)
            if _red_flag_repo is None or _alert_repo is None:
                return cls._json_bytes({"error": "Repositorio privado de revision no disponible"}, status_code=503)
            if path == "/api/review/cases":
                if _case_analysis_repo is None:
                    return cls._json_bytes({"error": "Dossiers privados no disponibles"}, status_code=503)
                return cls._json_bytes([case.model_dump(mode='json') for case in _case_analysis_repo.list_in_review()])
            reviewed_ids = _alert_repo.decided_flag_ids()
            cases = _case_analysis_repo.list_in_review() if _case_analysis_repo else []
            by_flag = {node.node_id: case for case in cases
                       for node in case.ai_copilot_analysis.evidence_graph.nodes if node.kind == 'signal'}
            queue = [
                {**flag.model_dump(mode="json"),
                 'entity_id': by_flag[flag.red_flag_id].entity_id if flag.red_flag_id in by_flag else None,
                 'case_priority_score': by_flag[flag.red_flag_id].case_priority_score if flag.red_flag_id in by_flag else 0,
                 'alert_id': by_flag[flag.red_flag_id].alert_id if flag.red_flag_id in by_flag else None}
                for flag in _red_flag_repo.list_all()
                if flag.is_active and flag.red_flag_id not in reviewed_ids
            ]
            queue.sort(key=lambda item: (-item['case_priority_score'], item['red_flag_id']))
            return cls._json_bytes(queue)

        if path == "/api/snapshot":
            public_snapshot = {
                key: snapshot.get(key, []) for key in PUBLIC_SNAPSHOT_FIELDS
            }
            public_snapshot["citizen_reports"] = []
            public_snapshot["alerts"] = [
                alert for alert in public_snapshot.get("alerts", [])
                if alert.get("status") == "published"
            ]
            published_ids = {
                flag_id
                for alert in public_snapshot.get("alerts", [])
                if alert.get("status") == "published"
                for flag_id in alert.get("red_flag_ids", [])
            }
            public_snapshot["red_flags"] = [
                flag for flag in public_snapshot.get("red_flags", [])
                if flag.get("red_flag_id") in published_ids
            ]
            raw_metadata = snapshot.get("metadata", {})
            if not isinstance(raw_metadata, dict):
                raw_metadata = {}
            public_metadata = {
                key: raw_metadata[key] for key in PUBLIC_METADATA_FIELDS
                if key in raw_metadata
            }
            published_count = len(public_snapshot["alerts"])
            public_metadata.update({
                "total_alerts": published_count,
                "total_published_alerts": published_count,
                "total_candidate_red_flags": len(public_snapshot["red_flags"]),
                "alert_status_counts": {"published": published_count},
                "total_citizen_reports": 0,
            })
            public_snapshot["metadata"] = public_metadata
            return cls._json_bytes(public_snapshot)

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
            published_flag_ids = {
                flag_id
                for alert in snapshot.get("alerts", [])
                if alert.get("status") == "published"
                for flag_id in alert.get("red_flag_ids", [])
            }
            flags = [
                flag for flag in snapshot.get("red_flags", [])
                if flag.get("red_flag_id") in published_flag_ids
            ]
            flag_id = query.get("id", [None])[0]
            if flag_id:
                matched = next((f for f in flags if f.get("red_flag_id") == flag_id), None)
                if matched:
                    return cls._json_bytes(matched)
                return cls._error_bytes(f"Bandera roja no encontrada con ID: {flag_id}", 404)
            return cls._json_bytes(flags)

        if path == "/api/reports":
            auth_header = req_headers.get("authorization", "")
            if not auth_header.startswith("Bearer "):
                return cls._json_bytes(
                    {"error": "Acceso restringido a veedores acreditados (Ley 29733 de Proteccion de Datos Personales)"},
                    status_code=401,
                )
            token = auth_header[7:].strip()
            session = _verify_veedor_token(token)
            if not session:
                return cls._json_bytes(
                    {"error": "Sesion de veedor invalida o expirada"},
                    status_code=401,
                )
            try:
                limit = int(query.get("limit", ["100"])[0])
                offset = int(query.get("offset", ["0"])[0])
                status = query.get("status", [None])[0]
                if not 1 <= limit <= 200 or offset < 0:
                    raise ValueError("Paginacion invalida")
                if status not in (None, "pending", "accepted_as_lead", "rejected"):
                    raise ValueError("Estado invalido")
            except ValueError:
                return cls._error_bytes("Paginacion o estado invalido", 400)
            if not _durable_repository(_report_repo):
                return cls._error_bytes("Repositorio privado no disponible", 503)
            try:
                reports = _report_repo.list_page(limit=limit, offset=offset, status=status)
            except Exception:
                return cls._error_bytes("No se pudo consultar las denuncias", 503)
            return cls._json_bytes([report.model_dump(mode="json") for report in reports])

        if path == "/api/reports/track":
            token = query.get("token", [None])[0] or query.get("id", [None])[0]
            if not token:
                return cls._error_bytes("Parametro 'token' es obligatorio", 400)
            token_clean = token.strip()
            reports = []
            token_hash = hashlib.sha256(token_clean.encode("utf-8")).hexdigest()
            matched = next(
                (r for r in reports if r.get("tracking_token_hash") == token_hash),
                None,
            )
            # Si no esta en snapshot en memoria, consultar repositorio de base de datos
            if not matched and _report_repo is not None:
                try:
                    db_report = _report_repo.get_by_tracking_token_hash(token_hash)
                    if db_report:
                        matched = db_report.model_dump(mode="json")
                except Exception as error:
                    logger.exception("Fallo controlado del adaptador web (%s)", type(error).__name__, exc_info=False)

            if not matched:
                return cls._error_bytes("Expediente de denuncia no encontrado", 404)

            # Exponer unicamente metadatos publicos de seguimiento, NUNCA raw_text ni identidades
            safe_summary = {
                "report_id": matched.get("report_id"),
                "submitted_at": matched.get("submitted_at") or matched.get("created_at"),
                "moderation_status": matched.get("moderation_status", "received"),
                "related_entity_id": matched.get("related_entity_id"),
                "channel": matched.get("channel", "web"),
                "legal_disclaimer_shown": matched.get("legal_disclaimer_shown", True),
            }
            return cls._json_bytes(safe_summary)

        if path in ("/api/concentration", "/api/suppliers"):
            entity_id = query.get("entity_id", [None])[0]
            return cls._json_bytes(cls._compute_suppliers_concentration(snapshot, entity_id))

        if path == "/api/sunat/ruc":
            # Guarda Constitucional Art. 16: Prohibicion de perfilamiento de personas naturales (DNI/RENIEC)
            dni_param = query.get("dni", [None])[0]
            if dni_param is not None:
                return cls._json_bytes(
                    {
                        "error": (
                            "Articulo 16 (Prohibicion de perfilamiento de personas naturales): "
                            "Queda terminantemente prohibido consultar, almacenar o procesar "
                            "solicitudes de DNI o RENIEC. El sistema opera exclusivamente sobre "
                            "entidades publicas y proveedores contratistas del Estado mediante RUC."
                        ),
                        "code": "CONSTITUTIONAL_PRIVACY_GUARD_ART_16",
                    },
                    status_code=403,
                )

            ruc_param = query.get("ruc", [None])[0]
            if ruc_param is not None:
                cleaned_val = ruc_param.strip().replace("PE-RUC-", "")
                # Guarda si se pasa un DNI de 8 digitos en el parametro ruc
                if len(cleaned_val) == 8 and cleaned_val.isdigit():
                    return cls._json_bytes(
                        {
                            "error": (
                                "Articulo 16 (Prohibicion de perfilamiento de personas naturales): "
                                f"El identificador '{ruc_param}' corresponde a un DNI de 8 digitos. "
                                "Se rechaza la operacion para salvaguardar la privacidad de personas naturales."
                            ),
                            "code": "CONSTITUTIONAL_PRIVACY_GUARD_ART_16",
                        },
                        status_code=403,
                    )

                if len(cleaned_val) != 11 or not cleaned_val.isdigit():
                    return cls._error_bytes("RUC invalido: debe contener 11 digitos numericos.", 400)

                service = cls.get_sunat_service()
                try:
                    profile = service.lookup_ruc(cleaned_val)
                except ValueError as exc:
                    return cls._error_bytes(str(exc), 400)

                if profile:
                    return cls._json_bytes(profile.model_dump())
                return cls._error_bytes(f"RUC '{cleaned_val}' no encontrado en el padron verificado.", 404)

            # Si no se especifica RUC ni DNI, devolver resumen del padron consolidado
            service = cls.get_sunat_service()
            return cls._json_bytes(service.get_registry_summary())

        if path == "/api/geospatial/works":
            works = snapshot.get("geospatial_works", [])
            site_id = query.get("id", [None])[0] or query.get("site_id", [None])[0]
            if site_id:
                matched = next((w for w in works if w.get("site_id") == site_id), None)
                if matched:
                    return cls._json_bytes(matched)
                return cls._error_bytes(f"Obra '{site_id}' no encontrada en el catalogo geoespacial", 404)
            prov = query.get("province", [None])[0]
            if prov:
                prov_clean = prov.strip().lower()
                works = [w for w in works if w.get("province", "").strip().lower() == prov_clean]
            return cls._json_bytes(works)

        if path == "/api/geospatial/divergence":
            signals = snapshot.get("geospatial_signals", [])
            site_id = query.get("site_id", [None])[0] or query.get("id", [None])[0]
            if site_id:
                matched = next((s for s in signals if s.get("site_id") == site_id), None)
                if matched:
                    return cls._json_bytes(matched)
                return cls._error_bytes(f"Senal de divergencia para obra '{site_id}' no encontrada", 404)
            sev = query.get("severity", [None])[0]
            if sev:
                sev_clean = sev.strip().lower()
                signals = [s for s in signals if s.get("severity", "").strip().lower() == sev_clean]
            return cls._json_bytes(signals)

        return cls._error_bytes(f"Ruta API no encontrada: {path}", 404)

    @classmethod
    def _dispatch_post_login(cls, data: dict[str, Any], req_headers: dict[str, str]) -> tuple[int, str, bytes]:
        from cajamarca_qhaway.web.auth import AuthService, AuthUnavailable, InvalidCredentials
        if data.get("honeypot"):
            return cls._error_bytes("Solicitud rechazada", 400)
        try:
            return cls._json_bytes(AuthService(_db_manager).login(data))
        except AuthUnavailable:
            return cls._error_bytes("Autenticacion no disponible", 503)
        except InvalidCredentials:
            return cls._error_bytes("Acreditacion invalida", 401)

    @classmethod
    def _dispatch_post_logout(cls, req_headers: dict[str, str]) -> tuple[int, str, bytes]:
        from cajamarca_qhaway.web.auth import AuthService, AuthUnavailable, InvalidCredentials
        auth = req_headers.get("authorization", "")
        if not auth.startswith("Bearer "):
            return cls._error_bytes("Sesion requerida", 401)
        try:
            AuthService(_db_manager).logout(auth[7:].strip())
        except AuthUnavailable:
            return cls._error_bytes("No se pudo confirmar el cierre de sesion", 503)
        except InvalidCredentials:
            return cls._error_bytes("Sesion invalida", 401)
        return cls._json_bytes({"message": "Sesion finalizada correctamente"})

    @classmethod
    def _dispatch_post_reports(cls, data: dict[str, Any]) -> tuple[int, str, bytes]:
        """Procesa una denuncia ciudadana cumpliendo CA-006-01."""
        if _report_repo is None or (
            os.environ.get("VERCEL") and (_db_manager is None or not _db_manager.is_postgres)
        ):
            return cls._error_bytes("Persistencia de denuncias no disponible", 503)
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
            tracking_token = secrets.token_urlsafe(32)
            tracking_token_hash = hashlib.sha256(tracking_token.encode("utf-8")).hexdigest()
            if not _durable_repository(_report_repo):
                return cls._error_bytes("Persistencia duradera de denuncias no disponible", 503)
            pending_service = DenunciaIntakeService()
            report = pending_service.submit_report(
                raw_text=raw_text,
                legal_disclaimer_shown=True,
                channel=channel,
                related_entity_id=entity_id,
                tracking_token_hash=tracking_token_hash,
                persist=_report_repo.save,
            )
            payload = report.model_dump(mode="json")

            # Persistencia en base de datos operativa (Pilar 2)
            if _report_repo is not None:
                try:
                    _report_repo.save(report)
                except Exception as exc:
                    logger.exception("Fallo controlado del adaptador web (%s)", type(exc).__name__, exc_info=False)
                    logger.exception("No se pudo persistir la denuncia antes de confirmar su recepcion")
                    return cls._error_bytes(
                        f"No se pudo guardar la denuncia: {type(exc).__name__}", 503
                    )

            cls.denuncia_service._reports[report.report_id] = report

            public_payload = {
                key: value for key, value in payload.items() if key != "tracking_token_hash"
            }
            return cls._json_bytes(
                {**public_payload, "tracking_token": tracking_token, "report": public_payload},
                status_code=201,
            )
        except Exception as exc:
            logger.exception("Fallo controlado del adaptador web (%s)", type(exc).__name__, exc_info=False)
            if isinstance(exc, ValueError):
                return cls._error_bytes(f"Error al procesar denuncia: {exc!s}", 400)
            return cls._error_bytes("No se pudo procesar la denuncia", 503)

    @classmethod
    def _dispatch_post_reports_moderate(
        cls,
        data: dict[str, Any],
        req_headers: dict[str, str] | None = None,
    ) -> tuple[int, str, bytes]:
        """Modera una denuncia ciudadana (Art. 14 y RN-006-03)."""
        if _report_repo is None or (
            os.environ.get("VERCEL") and (_db_manager is None or not _db_manager.is_postgres)
        ):
            return cls._error_bytes("Persistencia de denuncias no disponible", 503)
        req_headers = req_headers or {}
        auth_header = req_headers.get("authorization", "")
        if not auth_header.startswith("Bearer "):
            return cls._json_bytes({"error": "Autenticacion requerida: token de veedor ausente"}, status_code=401)

        token = auth_header[7:].strip()
        session = _verify_veedor_token(token)
        if not session:
            return cls._json_bytes({"error": "Sesion de veedor invalida o expirada"}, status_code=401)

        veedor = session["veedor"]
        moderator_nominal = f"{veedor['name']} ({veedor['organization']})"

        report_id = str(data.get("report_id", "")).strip()
        status = str(data.get("status") or data.get("moderation_status", "")).strip()
        custom_moderator = str(data.get("moderated_by", "")).strip()
        if custom_moderator and custom_moderator != moderator_nominal:
            return cls._error_bytes("moderated_by debe coincidir con la identidad acreditada", 400)

        moderator_id = moderator_nominal

        if not report_id:
            return cls._error_bytes("El campo 'report_id' es obligatorio", 400)

        if status not in ("accepted_as_lead", "rejected"):
            return cls._error_bytes(
                f"Estado invalido: '{status}'. Debe ser 'accepted_as_lead' o 'rejected'",
                400,
            )

        if not _durable_repository(_report_repo):
            return cls._error_bytes("Persistencia duradera no disponible", 503)
        try:
            existing = _report_repo.get_by_id(report_id)
        except Exception:
            return cls._error_bytes("No se pudo consultar la denuncia", 503)
        if existing is None:
            return cls._error_bytes("Denuncia no encontrada", 404)
        pending_service = DenunciaIntakeService()
        pending_service._reports[report_id] = existing
        try:
            updated = pending_service.moderate_report(
                report_id=report_id, new_status=status,
                moderator_id=moderator_nominal, moderated_at=datetime.now(UTC),
            )
        except (ValueError, KeyError) as exc:
            return cls._error_bytes(str(exc), 400)
        try:
            _report_repo.save(updated)
        except Exception:
            return cls._error_bytes("No se pudo persistir la moderacion", 503)
        cls.denuncia_service._reports[report_id] = updated
        payload = updated.model_dump(mode="json")
        return cls._json_bytes({
            "success": True, "report_id": updated.report_id,
            "moderation_status": updated.moderation_status,
            "moderated_by": updated.moderated_by,
            "moderated_at": payload["moderated_at"], "report": payload,
        })

    @classmethod
    def _dispatch_post_review(
        cls,
        data: dict[str, Any],
        req_headers: dict[str, str] | None = None,
    ) -> tuple[int, str, bytes]:
        """Procesa una decision de revision humana cumpliendo Art. 14 y CA-005-02."""
        if _alert_repo is None or _red_flag_repo is None or (
            os.environ.get("VERCEL") and (_db_manager is None or not _db_manager.is_postgres)
        ):
            return cls._error_bytes("Persistencia de decisiones no disponible", 503)
        req_headers = req_headers or {}
        entity_id = str(data.get("entity_id", "")).strip()
        red_flag_ids = data.get("red_flag_ids", [])
        status = str(data.get("status", "")).strip()
        reviewed_by = str(data.get("reviewed_by", "")).strip()
        review_notes = str(data.get("review_notes", "")).strip() or None

        auth_header = req_headers.get("authorization", "")
        if not auth_header.startswith("Bearer "):
            return cls._json_bytes({"error": "Sesion de veedor requerida"}, status_code=401)
        session = _verify_veedor_token(auth_header[7:].strip())
        if not session:
            return cls._json_bytes({"error": "Sesion de veedor invalida o expirada"}, status_code=401)
        veedor = session["veedor"]
        reviewed_by = f"{veedor['name']} ({veedor['organization']})"

        if (not isinstance(red_flag_ids, list) or not red_flag_ids
                or any(not isinstance(flag_id, str) or not flag_id.strip() for flag_id in red_flag_ids)):
            return cls._error_bytes("red_flag_ids debe ser una lista de identificadores", 400)
        red_flag_ids = list(dict.fromkeys(red_flag_ids))
        if not entity_id or not status or not reviewed_by:
            return cls._error_bytes(
                "Campos requeridos: entity_id, red_flag_ids, status, reviewed_by",
                400,
            )

        # CA-005-02: rechazar revisores genericos
        cleaned_reviewer = reviewed_by.lower()
        if cleaned_reviewer in GENERIC_REVIEWERS or not cleaned_reviewer:
            return cls._error_bytes(f"reviewed_by no puede ser generico o vacio: '{reviewed_by}'", 400)

        # Toda decision humana debe dejar una razon verificable.
        if not review_notes:
            return cls._error_bytes(
                "review_notes es obligatorio para toda decision de revision",
                400,
            )

        if not _durable_repository(_alert_repo):
            return cls._error_bytes("Persistencia duradera de alertas no disponible", 503)
        pending_review = ReviewPanelService()
        try:
            if status == "published":
                if _red_flag_repo is None:
                    return cls._error_bytes("Repositorio de evidencia no disponible", 503)
                complete_flags = [_red_flag_repo.get_by_id(flag_id) for flag_id in red_flag_ids]
                if any(flag is None or not flag.is_active for flag in complete_flags):
                    return cls._error_bytes("No se puede publicar sin evidencia completa de cada RedFlag", 409)
                alert = pending_review.publish_alert(
                    entity_id=entity_id,
                    red_flags=[flag for flag in complete_flags if flag is not None],
                    reviewer_id=reviewed_by,
                    review_notes=review_notes,
                    persist=_alert_repo.save,
                )
            elif status == "discarded":
                if _red_flag_repo is None:
                    return cls._error_bytes("Repositorio de evidencia no disponible", 503)
                complete_flags = [_red_flag_repo.get_by_id(flag_id) for flag_id in red_flag_ids]
                if any(flag is None for flag in complete_flags):
                    return cls._error_bytes("No se puede registrar la decision sin evidencia completa", 409)
                alert = pending_review.discard_alert(
                    entity_id=entity_id,
                    red_flags=[flag for flag in complete_flags if flag is not None],
                    reviewer_id=reviewed_by,
                    review_notes=review_notes,
                    persist=_alert_repo.save,
                )
            else:
                return cls._error_bytes(
                    f"Estado invalido: {status}. Debe ser 'published' o 'discarded'",
                    400,
                )

            payload = alert.model_dump(mode="json")

            # Persistencia en base de datos operativa (Pilar 2)
            if _alert_repo is not None:
                try:
                    alert = _alert_repo.save_decision(alert)
                    payload = alert.model_dump(mode="json")
                except ValueError:
                    return cls._error_bytes("El candidato ya tiene una decision distinta", 409)
                except Exception:
                    return cls._error_bytes("No se pudo persistir la alerta", 503)

            cls.review_service._decisions[alert.alert_id] = alert
            snapshot = cls.get_snapshot()
            alerts = snapshot.setdefault("alerts", [])
            alerts[:] = [row for row in alerts if row.get("alert_id") != alert.alert_id]
            alerts.append(payload)
            return cls._json_bytes({**payload, "alert": payload}, status_code=201)
        except Exception as exc:
            logger.exception("Fallo controlado del adaptador web (%s)", type(exc).__name__, exc_info=False)
            if isinstance(exc, ValueError) and "ya tiene una decision" in str(exc):
                return cls._error_bytes("Esta alerta ya fue revisada", 409)
            if isinstance(exc, (ValueError, TypeError)):
                return cls._error_bytes(f"Decision invalida: {exc!s}", 400)
            return cls._error_bytes("No se pudo persistir la decision", 503)

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
            logger.exception("Fallo controlado del adaptador web (%s)", type(exc).__name__, exc_info=False)
            return cls._error_bytes(f"Error al leer archivo: {exc!s}", 500)

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
        self.send_header("Cache-Control", "no-store" if self.path.startswith("/api/") else "public, max-age=0")
        if content_length is not None:
            self.send_header("Content-Length", str(content_length))
        for header, val in SECURITY_HEADERS.items():
            self.send_header(header, val)
        parsed = urllib.parse.urlparse(self.path)
        self.send_header("Cache-Control", _cache_control(
            self.command, parsed.path, urllib.parse.parse_qs(parsed.query), self._extract_headers(), status_code,
        ))
        self.send_header("Vary", "Authorization")
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

    cache_control = _cache_control(method, raw_path, query, req_headers, status_code)

    response_headers: list[tuple[str, str]] = [
        ("Content-Type", content_type),
        ("Content-Length", str(len(response_body))),
        ("Cache-Control", cache_control),
        ("Vary", "Authorization"),
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
    port = int(os.environ.get("PORT", "8080"))
    httpd = run_server(port=port)
    print(f"Servidor Cajamarca Qhaway escuchando en http://localhost:{port}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor detenido por el usuario.")
        httpd.server_close()
