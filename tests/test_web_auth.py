"""Regresiones de identidad nominal y cierre de sesion entre instancias."""

import base64
import hashlib
import json
import sqlite3
import time
from contextlib import contextmanager

import httpx
import pytest

from cajamarca_qhaway.persistence.config import DatabaseConfig
from cajamarca_qhaway.persistence.connection import DatabaseManager
from cajamarca_qhaway.web.auth import AuthService, AuthUnavailable, InvalidCredentials


def synthetic_token(**changes):
    payload = {"sub": "synthetic-reviewer-id", "exp": int(time.time()) + 600, **changes}
    encoded = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
    return f"synthetic-header.{encoded}.synthetic-signature"


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


def test_identity_requires_provider_verified_accreditation(auth_setup):
    db, user, calls, client = auth_setup
    auth = AuthService(db, client=client)
    token = synthetic_token()
    assert auth.login({"access_token": token})["veedor"]["email"] == user["email"]
    assert calls[0].url.path == "/auth/v1/user"
    assert calls[0].headers["authorization"] == f"Bearer {token}"
    user["app_metadata"] = {}
    user["user_metadata"] = {"role": "reviewer"}
    assert auth.verify(token) is None
    with pytest.raises(InvalidCredentials):
        auth.login({"email": user["email"], "password": "synthetic-password"})


@pytest.mark.parametrize("changes", [{"exp": 1}, {"exp": "tomorrow"}, {"exp": True},
                                     {"sub": "different-subject"}])
def test_token_requires_valid_expiry_and_subject(auth_setup, changes):
    db, _, _, client = auth_setup
    assert AuthService(db, client=client).verify(synthetic_token(**changes)) is None


def test_logout_is_shared_by_independent_service_instances(auth_setup):
    db, _, calls, client = auth_setup
    first = AuthService(db, client=client)
    second = AuthService(db, client=client)
    token = synthetic_token()
    assert second.verify(token) is not None
    first.logout(token)
    before = len(calls)
    assert second.verify(token) is None
    assert len(calls) == before  # No proveedor mock que simule la revocacion.
    first.logout(token)  # Idempotente.
    with db.connection() as conn:
        row = conn.execute("SELECT token_hash FROM auth_revocations").fetchone()
    assert row["token_hash"] == hashlib.sha256(token.encode()).hexdigest()
    assert row["token_hash"] != token


def test_revocation_survives_new_connections_and_service_recreation(auth_setup, tmp_path):
    _, _, _, client = auth_setup
    database_path = tmp_path / "synthetic-revocations.sqlite"

    class SyntheticFileDatabase:
        is_postgres = False

        @contextmanager
        def connection(self):
            connection = sqlite3.connect(database_path)
            try:
                yield connection
            finally:
                connection.close()

    with SyntheticFileDatabase().connection() as conn:
        conn.execute("CREATE TABLE auth_revocations (token_hash TEXT PRIMARY KEY, expires_at BIGINT)")
        conn.commit()
    first = AuthService(SyntheticFileDatabase(), client=client)
    other_worker = AuthService(SyntheticFileDatabase(), client=client)
    token = synthetic_token()
    assert other_worker.verify(token) is not None
    first.logout(token)
    assert other_worker.verify(token) is None
    del first, other_worker
    restarted = AuthService(SyntheticFileDatabase(), client=client)
    assert restarted.verify(token) is None


def test_missing_configuration_or_shared_storage_fails_closed(auth_setup, monkeypatch):
    db, _, _, client = auth_setup
    with pytest.raises(AuthUnavailable):
        AuthService(client=client).verify(synthetic_token())
    monkeypatch.setenv("VERCEL", "1")
    with pytest.raises(AuthUnavailable):
        AuthService(db, client=client).verify(synthetic_token())
    monkeypatch.delenv("VERCEL")
    monkeypatch.delenv("SUPABASE_ANON_KEY")
    with pytest.raises(AuthUnavailable):
        AuthService(db, client=client).verify(synthetic_token())


def test_provider_errors_and_unconfirmed_identity_are_rejected(auth_setup):
    db, user, _, client = auth_setup
    user["email_confirmed_at"] = None
    assert AuthService(db, client=client).verify(synthetic_token()) is None
    with httpx.Client(transport=httpx.MockTransport(
        lambda request: httpx.Response(503))) as unavailable:
        with pytest.raises(AuthUnavailable):
            AuthService(db, client=unavailable).verify(synthetic_token())
    with httpx.Client(transport=httpx.MockTransport(
        lambda request: httpx.Response(401))) as denied:
        assert AuthService(db, client=denied).verify(synthetic_token()) is None


def test_revocation_read_and_write_failure_never_confirms_logout(auth_setup, monkeypatch):
    db, _, _, client = auth_setup
    service = AuthService(db, client=client)
    token = synthetic_token()
    service.verify(token)
    with db.connection() as conn:
        conn.execute("DROP TABLE auth_revocations")
    with pytest.raises(AuthUnavailable):
        service.verify(token)
    monkeypatch.setattr(service, "verify", lambda _: {"expiresAt": int(time.time() * 1000) + 60000})
    with pytest.raises(AuthUnavailable):
        service.logout(token)
