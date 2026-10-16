"""Regresiones de atomicidad y confidencialidad en operaciones de denuncias."""

from __future__ import annotations

import hashlib
import io
import json
from types import SimpleNamespace

import pytest

pytestmark = pytest.mark.usefixtures("configured_test_veedor")

from cajamarca_qhaway.capabilities.denuncia_intake.service import DenunciaIntakeService
from cajamarca_qhaway.models import CitizenReport
from cajamarca_qhaway.persistence.config import DatabaseConfig
from cajamarca_qhaway.persistence.connection import DatabaseManager
from cajamarca_qhaway.persistence.repositories.citizen_report_repository import (
    CitizenReportRepository,
)
from cajamarca_qhaway.web import server


def _raise_storage_error(_report):
    raise OSError("database connection failed")


def _prepare_handler(monkeypatch):
    handler = server.WebApiHandler
    service = DenunciaIntakeService()
    snapshot = {"citizen_reports": []}
    monkeypatch.delenv("VERCEL", raising=False)
    monkeypatch.setattr(handler, "denuncia_service", service)
    monkeypatch.setattr(handler, "get_snapshot", classmethod(lambda cls: snapshot))
    monkeypatch.setattr(server, "_report_repo", SimpleNamespace(
        save=_raise_storage_error,
        get_by_id=service.get_report,
        moderate_pending=_raise_storage_error,
    ))
    return handler, service, snapshot


def test_report_submission_failed_persistence_does_not_acknowledge_or_cache(monkeypatch):
    handler, service, snapshot = _prepare_handler(monkeypatch)
    code, _, body = handler._dispatch_post_reports({
        "raw_text": "Reporte ciudadano de prueba",
        "legal_disclaimer_shown": True,
    })

    assert code == 503
    assert "tracking_token" not in json.loads(body)
    assert service.list_reports() == []
    assert snapshot["citizen_reports"] == []


def test_report_moderation_failed_persistence_keeps_pending_status(monkeypatch):
    handler, service, snapshot = _prepare_handler(monkeypatch)
    report = service.submit_report(
        raw_text="Reporte pendiente",
        legal_disclaimer_shown=True,
        tracking_token_hash=hashlib.sha256(b"example-token").hexdigest(),
    )
    snapshot["citizen_reports"].append(report.model_dump(mode="json"))
    before = json.dumps(snapshot, sort_keys=True)
    token = "synthetic-reviewer-token"
    code, _, body = handler._dispatch_post_reports_moderate(
        {"report_id": report.report_id, "status": "accepted_as_lead"},
        {"authorization": f"Bearer {token}"},
    )

    assert code == 503
    assert "success" not in json.loads(body)
    assert service.get_report(report.report_id).moderation_status == "pending"
    assert json.dumps(snapshot, sort_keys=True) == before


def test_report_mutations_refuse_unavailable_repository(monkeypatch):
    handler, service, _ = _prepare_handler(monkeypatch)
    monkeypatch.setattr(server, "_report_repo", None)
    code, _, _ = handler._dispatch_post_reports({
        "raw_text": "Reporte ciudadano de prueba",
        "legal_disclaimer_shown": True,
    })
    assert code == 503
    assert service.list_reports() == []


def test_moderation_refuses_report_absent_from_database(monkeypatch):
    handler, service, snapshot = _prepare_handler(monkeypatch)
    report = service.submit_report(raw_text="Solo en memoria", legal_disclaimer_shown=True)
    snapshot["citizen_reports"].append(report.model_dump(mode="json"))
    monkeypatch.setattr(server._report_repo, "get_by_id", lambda _id: None)
    token = "synthetic-reviewer-token"

    code, _, _ = handler._dispatch_post_reports_moderate(
        {"report_id": report.report_id, "status": "rejected"},
        {"authorization": f"Bearer {token}"},
    )

    assert code == 404
    assert service.get_report(report.report_id).moderation_status == "pending"
    assert snapshot["citizen_reports"][0]["moderation_status"] == "pending"


def test_moderation_compare_and_swap_prevents_second_decision():
    from cajamarca_qhaway.capabilities.denuncia_intake.service import (
        DenunciaIntakeService,
    )

    repository = CitizenReportRepository(DatabaseManager(DatabaseConfig(database_url=None)))
    service = DenunciaIntakeService()
    report = service.submit_report(
        raw_text="Pendiente con una sola decision",
        legal_disclaimer_shown=True,
        persist=repository.save,
    )
    first = service.moderate_report(
        report.report_id, "rejected", "Veedor acreditado", persist=repository.moderate_pending,
    )
    assert repository.get_by_id(report.report_id).moderation_status == "rejected"

    stale = CitizenReport(**{**first.model_dump(), "moderation_status": "accepted_as_lead"})
    with pytest.raises(ValueError, match="ya moderado"):
        repository.moderate_pending(stale)
    assert repository.get_by_id(report.report_id).moderation_status == "rejected"


def test_wsgi_disables_api_shared_caching(monkeypatch):
    from api import index

    for app in (server.app, index.app):
        captured = {}

        def start_response(status, headers, captured=captured):
            captured["status"] = status
            captured["headers"] = dict(headers)

        response = app({
            "REQUEST_METHOD": "GET",
            "PATH_INFO": "/api/auth/session",
            "QUERY_STRING": "",
            "wsgi.input": io.BytesIO(),
            "CONTENT_LENGTH": "0",
        }, start_response)
        assert captured["headers"]["Cache-Control"] == "private, no-store"
        assert b"".join(response)

    monkeypatch.setattr(index, "_canonical_wsgi_app", None)
    captured = {}

    def fallback_response(status, headers):
        captured["headers"] = dict(headers)

    index.app({
        "REQUEST_METHOD": "GET",
        "PATH_INFO": "/api/snapshot",
        "QUERY_STRING": "",
        "wsgi.input": io.BytesIO(),
        "CONTENT_LENGTH": "0",
    }, fallback_response)
    assert captured["headers"]["Cache-Control"] == "private, no-store"
