"""Proveedores sintéticos inyectados exclusivamente en las pruebas."""
from __future__ import annotations

import httpx
import pytest

from cajamarca_qhaway.persistence.config import DatabaseConfig
from cajamarca_qhaway.persistence.connection import DatabaseManager


@pytest.fixture
def configured_test_veedor(monkeypatch):
    from cajamarca_qhaway.web import server
    profile = {"email": "reviewer@example.test", "name": "Revisora Sintetica",
               "organization": "Organizacion Sintetica", "role": "reviewer",
               "accreditationNumber": "TEST-REVIEWER-001"}
    monkeypatch.setattr(server, "_verify_veedor_token", lambda token: {
        "veedor": dict(profile), "expiresAt": 9999999999999
    } if token == "synthetic-reviewer-token" else None)

@pytest.fixture
def auth_setup(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "https://synthetic-project.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "synthetic-public-key")
    for name in ("VERCEL", "CAJAMARCA_QHAWAY_ENV", "ENVIRONMENT",
                 "CAJAMARCA_QHAWAY_SUPABASE_URL", "CAJAMARCA_QHAWAY_SUPABASE_ANON_KEY"):
        monkeypatch.delenv(name, raising=False)
    db = DatabaseManager(DatabaseConfig(database_url=None))
    user = {"id": "synthetic-reviewer-id", "email": "reviewer@example.test",
            "email_confirmed_at": "2026-01-01T00:00:00Z",
            "app_metadata": {"role": "reviewer", "name": "Persona Sintetica"}}
    calls = []

    def handle(request):
        calls.append(request)
        return httpx.Response(200, json=user)

    client = httpx.Client(transport=httpx.MockTransport(handle))
    yield db, user, calls, client
    client.close()
