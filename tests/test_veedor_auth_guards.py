"""Regresiones de identidad adaptadas al proveedor acreditado vigente."""
from __future__ import annotations

import hashlib
import json
from types import SimpleNamespace

import pytest
from test_web_auth import synthetic_token

from cajamarca_qhaway.web import server
from cajamarca_qhaway.web.auth import AuthService, InvalidCredentials


def test_sesion_rechaza_credencial_revocada(auth_setup):
    db, user, _, client = auth_setup
    auth = AuthService(db, client=client)
    token = synthetic_token()
    assert auth.verify(token)
    user["app_metadata"] = {}
    assert auth.verify(token) is None


def test_sesion_rechaza_suplantacion_aun_con_proveedor_valido(auth_setup):
    db, user, _, client = auth_setup
    auth = AuthService(db, client=client)
    user["app_metadata"]["role"] = "administrador"
    assert auth.verify(synthetic_token()) is None
    user["app_metadata"]["role"] = "reviewer"
    assert auth.verify(synthetic_token(sub="otro-sujeto")) is None


@pytest.mark.parametrize("payload", [[], {}, {"veedor": []}, {"veedor": {}}])
def test_sesion_rechaza_estructuras_invalidas(auth_setup, payload):
    db, _, _, client = auth_setup
    with pytest.raises(InvalidCredentials):
        AuthService(db, client=client).login({"access_token": json.dumps(payload)})


@pytest.mark.parametrize("expiry", [0, "no-es-fecha", True])
def test_sesion_rechaza_caducidad_invalida(auth_setup, expiry):
    db, _, _, client = auth_setup
    assert AuthService(db, client=client).verify(synthetic_token(exp=expiry)) is None


@pytest.mark.parametrize("token", ["ñ." + "a" * 64, "!" * 50 + "." + "a" * 64,
                                  "%%%", "header.%%%.signature"])
def test_sesion_rechaza_base64_invalido_sin_error_de_servidor(auth_setup, token):
    db, _, _, client = auth_setup
    assert AuthService(db, client=client).verify(token) is None


def test_logout_no_almacena_tokens_arbitrarios(auth_setup):
    db, _, _, client = auth_setup
    auth = AuthService(db, client=client)
    with pytest.raises(InvalidCredentials):
        auth.logout("token-falso")
    with db.connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM auth_revocations").fetchone()[0] == 0
    token = synthetic_token()
    auth.logout(token)
    assert auth.verify(token) is None
    with db.connection() as conn:
        assert conn.execute("SELECT token_hash FROM auth_revocations").fetchone()[0] == (
            hashlib.sha256(token.encode()).hexdigest())


def test_moderacion_rechaza_nombre_suplantado(monkeypatch, configured_test_veedor):
    monkeypatch.setattr(server, "_report_repo", SimpleNamespace())
    status, _, _ = server.WebApiHandler._dispatch_post_reports_moderate(
        {"report_id": "cualquier-reporte", "status": "accepted_as_lead",
         "moderated_by": "Otra persona acreditada"},
        {"authorization": "Bearer synthetic-reviewer-token"})
    assert status == 400
