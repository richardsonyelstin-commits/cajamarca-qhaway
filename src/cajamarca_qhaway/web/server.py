"""Servidor HTTP y API REST ligera para Cajamarca Qhaway.

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

Cumple con politicas de seguridad (CSP, nosniff, DENY) y Antislop R-02 (cero em-dash).
"""

from __future__ import annotations

import json
import mimetypes
import os
import posixpath
import urllib.parse
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from cajamarca_qhaway.capabilities.denuncia_intake import DenunciaIntakeService
from cajamarca_qhaway.capabilities.review_panel import ReviewPanelService
from cajamarca_qhaway.models.alert import GENERIC_REVIEWERS
from cajamarca_qhaway.web.exporter import build_verified_web_snapshot, export_verified_snapshot

SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Content-Security-Policy": "default-src 'self' https: data: 'unsafe-inline' 'unsafe-eval';",
}


class WebApiHandler(SimpleHTTPRequestHandler):
    """Manejador HTTP que combina servicio de estaticos con API REST."""

    # Directorio base para servir estaticos
    web_dir: Path = Path("web")
    snapshot_cache: dict[str, Any] | None = None
    denuncia_service: DenunciaIntakeService = DenunciaIntakeService()
    review_service: ReviewPanelService = ReviewPanelService()

    @classmethod
    def get_snapshot(cls) -> dict[str, Any]:
        """Obtiene el snapshot canónico, leyendolo del disco o generandolo."""
        snapshot_file = cls.web_dir / "src" / "data" / "verified-snapshot.json"
        if snapshot_file.exists():
            try:
                data = json.loads(snapshot_file.read_text(encoding="utf-8"))
                cls.snapshot_cache = data
                return data
            except Exception:
                pass

        # Si no existe en disco, generar inmediatamente
        data = build_verified_web_snapshot()
        cls.snapshot_cache = data
        return data

    def _set_headers(self, status_code: int = 200, content_type: str = "application/json") -> None:
        self.send_response(status_code)
        self.send_header("Content-Type", f"{content_type}; charset=utf-8")
        for header, val in SECURITY_HEADERS.items():
            self.send_header(header, val)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def _send_json(self, data: Any, status_code: int = 200) -> None:
        self._set_headers(status_code, "application/json")
        body = json.dumps(data, ensure_ascii=False, indent=2)
        self.wfile.write(body.encode("utf-8"))

    def _send_error(self, message: str, status_code: int = 400) -> None:
        self._send_json({"error": message, "status": status_code}, status_code=status_code)

    def do_OPTIONS(self) -> None:
        """Maneja preflight requests para CORS."""
        self._set_headers(200, "text/plain")
        self.wfile.write(b"OK")

    def do_GET(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        # Enrutamiento de API
        if path.startswith("/api/"):
            self._handle_api_get(path, query)
            return

        # Servicio de archivos estaticos desde web_dir
        self._serve_static(path)

    def _handle_api_get(self, path: str, query: dict[str, list[str]]) -> None:
        snapshot = self.get_snapshot()

        if path == "/api/health":
            self._send_json({
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
            return

        if path == "/api/snapshot":
            self._send_json(snapshot)
            return

        if path == "/api/entities":
            entities = snapshot.get("contracting_entities", [])
            entity_id = query.get("id", [None])[0]
            if entity_id:
                matched = next((e for e in entities if e.get("entity_id") == entity_id or e.get("ruc") == entity_id), None)
                if matched:
                    self._send_json(matched)
                else:
                    self._send_error(f"Entidad no encontrada con ID: {entity_id}", 404)
                return
            self._send_json(entities)
            return

        if path == "/api/procurements":
            procurements = snapshot.get("procurement_records", [])
            entity_id = query.get("entity_id", [None])[0]
            ocid = query.get("ocid", [None])[0]
            if ocid:
                matched = next((p for p in procurements if p.get("ocid") == ocid or p.get("procurement_id") == ocid), None)
                if matched:
                    self._send_json(matched)
                else:
                    self._send_error(f"Contratacion no encontrada con OCID: {ocid}", 404)
                return
            if entity_id:
                procurements = [p for p in procurements if p.get("entity_id") == entity_id]
            self._send_json(procurements)
            return

        if path == "/api/budget":
            budget = snapshot.get("budget_execution_records", [])
            entity_id = query.get("entity_id", [None])[0]
            if entity_id:
                budget = [b for b in budget if b.get("entity_id") == entity_id]
            self._send_json(budget)
            return

        if path == "/api/alerts":
            # Invariante Art. 14: Solo alertas con status == 'published' para vista publica
            all_alerts = snapshot.get("alerts", [])
            published_only = [a for a in all_alerts if a.get("status") == "published"]
            alert_id = query.get("id", [None])[0]
            if alert_id:
                matched = next((a for a in published_only if a.get("alert_id") == alert_id), None)
                if matched:
                    self._send_json(matched)
                else:
                    self._send_error(f"Alerta publicada no encontrada con ID: {alert_id}", 404)
                return
            entity_id = query.get("entity_id", [None])[0]
            if entity_id:
                published_only = [a for a in published_only if a.get("entity_id") == entity_id]
            self._send_json(published_only)
            return

        if path == "/api/red-flags":
            # Banderas rojas tecnicas para el panel interno de revision (CU5)
            flags = snapshot.get("red_flags", [])
            flag_id = query.get("id", [None])[0]
            if flag_id:
                matched = next((f for f in flags if f.get("red_flag_id") == flag_id), None)
                if matched:
                    self._send_json(matched)
                else:
                    self._send_error(f"Bandera roja no encontrada con ID: {flag_id}", 404)
                return
            self._send_json(flags)
            return

        if path == "/api/reports":
            reports = snapshot.get("citizen_reports", [])
            self._send_json(reports)
            return

        self._send_error(f"Ruta API no encontrada: {path}", 404)

    def do_POST(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        content_length = int(self.headers.get("Content-Length", 0))
        if content_length <= 0:
            self._send_error("Cuerpo de solicitud vacio", 400)
            return

        try:
            body = self.rfile.read(content_length).decode("utf-8")
            data = json.loads(body)
        except Exception as exc:
            self._send_error(f"JSON invalido: {str(exc)}", 400)
            return

        if path == "/api/reports":
            self._handle_post_reports(data)
            return

        if path == "/api/review":
            self._handle_post_review(data)
            return

        self._send_error(f"Ruta POST no encontrada: {path}", 404)

    def _handle_post_reports(self, data: dict[str, Any]) -> None:
        """Procesa una denuncia ciudadana cumpliendo CA-006-01."""
        raw_text = data.get("raw_text", "").strip()
        legal_disclaimer = data.get("legal_disclaimer_shown", False)
        channel = data.get("channel", "web")
        entity_id = data.get("related_entity_id")

        if not raw_text:
            self._send_error("El campo 'raw_text' es obligatorio", 400)
            return

        # Invariante CA-006-01: descargo legal obligatorio
        if not legal_disclaimer:
            self._send_error(
                "La denuncia no puede ser aceptada sin previa confirmacion del descargo legal (CA-006-01)",
                400,
            )
            return

        try:
            report = self.denuncia_service.submit_report(
                raw_text=raw_text,
                legal_disclaimer_shown=True,
                channel=channel,
                related_entity_id=entity_id,
            )
            # Actualizar memoria del snapshot
            snapshot = self.get_snapshot()
            snapshot.setdefault("citizen_reports", []).append(report.model_dump(mode="json"))
            self._send_json(report.model_dump(mode="json"), status_code=201)
        except Exception as exc:
            self._send_error(f"Error al procesar denuncia: {str(exc)}", 400)

    def _handle_post_review(self, data: dict[str, Any]) -> None:
        """Procesa una decision de revision humana cumpliendo Art. 14 y CA-005-02."""
        entity_id = data.get("entity_id", "").strip()
        red_flag_ids = data.get("red_flag_ids", [])
        status = data.get("status", "").strip()
        reviewed_by = data.get("reviewed_by", "").strip()
        review_notes = data.get("review_notes", "").strip() or None

        if not entity_id or not red_flag_ids or not status or not reviewed_by:
            self._send_error("Campos requeridos: entity_id, red_flag_ids, status, reviewed_by", 400)
            return

        # CA-005-02: rechazar revisores genericos
        cleaned_reviewer = reviewed_by.lower()
        if cleaned_reviewer in GENERIC_REVIEWERS or not cleaned_reviewer:
            self._send_error(f"reviewed_by no puede ser generico o vacio: '{reviewed_by}'", 400)
            return

        # CA-005-04: review_notes obligatorio si status == 'discarded'
        if status == "discarded" and not review_notes:
            self._send_error("review_notes es obligatorio cuando el estado es 'discarded' (CA-005-04)", 400)
            return

        try:
            if status == "published":
                alert = self.review_service.publish_alert(
                    entity_id=entity_id,
                    red_flags=red_flag_ids,
                    reviewer_id=reviewed_by,
                    review_notes=review_notes,
                )
            elif status == "discarded":
                alert = self.review_service.discard_alert(
                    entity_id=entity_id,
                    red_flags=red_flag_ids,
                    reviewer_id=reviewed_by,
                    review_notes=review_notes or "Descarte documentado",
                )
            else:
                self._send_error(f"Estado invalido: {status}. Debe ser 'published' o 'discarded'", 400)
                return

            snapshot = self.get_snapshot()
            snapshot.setdefault("alerts", []).append(alert.model_dump(mode="json"))
            self._send_json(alert.model_dump(mode="json"), status_code=201)
        except Exception as exc:
            self._send_error(f"Error al procesar decision: {str(exc)}", 400)

    def _serve_static(self, path: str) -> None:
        """Sirve archivos estaticos desde web_dir respetando la raiz del proyecto."""
        # Limpiar ruta
        clean_path = posixpath.normpath(path).lstrip("/")
        if not clean_path or clean_path == ".":
            clean_path = "index.html"

        file_path = (self.web_dir / clean_path).resolve()
        base_path = self.web_dir.resolve()

        # Evitar directory traversal
        try:
            file_path.relative_to(base_path)
        except ValueError:
            self._send_error("Acceso denegado", 403)
            return

        if not file_path.exists() or file_path.is_dir():
            # Fallback a index.html para soportar rutas del router si se solicitan directamente
            index_path = self.web_dir / "index.html"
            if index_path.exists():
                file_path = index_path
            else:
                self._send_error("Recurso no encontrado", 404)
                return

        ctype, _ = mimetypes.guess_type(str(file_path))
        if not ctype:
            ctype = "application/octet-stream"

        try:
            content = file_path.read_bytes()
            self._set_headers(200, ctype)
            self.wfile.write(content)
        except Exception as exc:
            self._send_error(f"Error al leer archivo: {str(exc)}", 500)


def run_server(port: int = 8080, web_dir: Path | str = "web") -> ThreadingHTTPServer:
    """Inicia el servidor HTTP en el puerto indicado."""
    WebApiHandler.web_dir = Path(web_dir)
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
