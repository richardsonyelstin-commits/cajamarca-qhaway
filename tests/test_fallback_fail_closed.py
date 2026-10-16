"""Regresiones de seguridad del modo WSGI de contingencia."""

import json

import pytest

from api import index


@pytest.mark.parametrize(
    ("method", "path", "payload"),
    [
        ("POST", "/api/reports", {"raw_text": "Caso", "legal_disclaimer_shown": True}),
        ("POST", "/api/reports/moderate", {"report_id": "cr-1", "status": "rejected"}),
        ("POST", "/api/auth/login", {"email": "demo", "password": "demo"}),
        ("POST", "/api/auth/logout", {}),
        ("POST", "/api/review", {"alert_id": "alert-1"}),
        ("GET", "/api/auth/session", {}),
        ("GET", "/api/reports", {}),
        ("GET", "/api/reports/track", {}),
        ("GET", "/api/review/queue", {}),
    ],
)
def test_fallback_never_confirms_private_operations(method, path, payload, monkeypatch):
    monkeypatch.delenv("VERCEL", raising=False)
    monkeypatch.delenv("CAJAMARCA_QHAWAY_DATABASE_URL", raising=False)
    snapshot = {"citizen_reports": [{"report_id": "cr-1", "moderation_status": "received"}]}
    monkeypatch.setattr(index, "_STDLIB_SNAPSHOT_CACHE", snapshot)

    code, _, data = index._stdlib_fallback_dispatch(
        method,
        path,
        {"token": ["fake-token"]},
        body=json.dumps(payload).encode("utf-8"),
        req_headers={"authorization": "Bearer forged-token"},
    )

    assert code == 503
    assert "success" not in json.loads(data)
    assert snapshot["citizen_reports"][0]["moderation_status"] == "received"


def test_fallback_health_never_leaks_import_traceback(monkeypatch):
    monkeypatch.setattr(index, "_IMPORT_ERROR", "sensitive internal traceback")

    code, _, data = index._stdlib_fallback_dispatch("GET", "/api/health", {})

    assert code == 503
    assert b"sensitive internal traceback" not in data


def test_public_snapshot_remains_available_in_fallback():
    code, _, data = index._stdlib_fallback_dispatch("GET", "/api/snapshot", {})

    assert code == 200
    assert json.loads(data)["citizen_reports"] == []
