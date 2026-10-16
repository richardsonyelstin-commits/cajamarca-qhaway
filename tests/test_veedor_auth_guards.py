"""Regresiones de identidad y sesion para endpoints privados."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
from types import SimpleNamespace

import pytest

from cajamarca_qhaway.web import server


pytestmark = pytest.mark.usefixtures("configured_test_veedor")


def _signed_payload(payload: object) -> str:
    raw = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    encoded = base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")
    sig = hmac.new(server._TOKEN_SECRET, encoded.encode("ascii"), hashlib.sha256).hexdigest()
    return f"{encoded}.{sig}"


def _claims() -> dict:
    token, _ = server._issue_veedor_token(server.ACCREDITED_VEEDORES[0])
    encoded, _ = token.split(".", 1)
    return json.loads(base64.urlsafe_b64decode(encoded + "=" * (-len(encoded) % 4)))


def test_sesion_rechaza_credencial_revocada(monkeypatch):
    token, _ = server._issue_veedor_token(server.ACCREDITED_VEEDORES[0])
    assert server._verify_veedor_token(token)
    monkeypatch.setattr(server, "ACCREDITED_VEEDORES", [])
    assert server._verify_veedor_token(token) is None


def test_sesion_rechaza_suplantacion_aun_con_firma_valida():
    payload = _claims()
    payload["veedor"]["role"] = "administrador"
    assert server._verify_veedor_token(_signed_payload(payload)) is None
    payload = _claims()
    payload["veedor"]["email"] = "otro@ejemplo.org"
    assert server._verify_veedor_token(_signed_payload(payload)) is None


@pytest.mark.parametrize("payload", [[], {}, {"veedor": []}, {"veedor": {}}])
def test_sesion_rechaza_estructuras_invalidas(payload):
    assert server._verify_veedor_token(_signed_payload(payload)) is None


def test_sesion_rechaza_caducidad_y_duracion_manipuladas():
    payload = _claims()
    payload["expiresAt"] = payload["createdAt"] + 9 * 3600 * 1000
    assert server._verify_veedor_token(_signed_payload(payload)) is None
    payload["expiresAt"] = "no-es-fecha"
    assert server._verify_veedor_token(_signed_payload(payload)) is None


def test_sesion_rechaza_base64_invalido_sin_error_de_servidor():
    assert server._verify_veedor_token("ñ." + "a" * 64) is None
    assert server._verify_veedor_token("!" * 50 + "." + "a" * 64) is None
    assert server._verify_veedor_token("a" * 4097 + "." + "a" * 64) is None
    invalid = "%%%"
    signature = hmac.new(server._TOKEN_SECRET, invalid.encode("ascii"), hashlib.sha256).hexdigest()
    assert server._verify_veedor_token(f"{invalid}.{signature}") is None


def test_logout_no_almacena_tokens_arbitrarios(monkeypatch):
    monkeypatch.setattr(server, "_REVOKED_TOKENS", set())
    code, _, _ = server.WebApiHandler._dispatch_post_logout(
        {"authorization": "Bearer token-falso"}
    )
    assert code == 401
    assert not server._REVOKED_TOKENS
    token, _ = server._issue_veedor_token(server.ACCREDITED_VEEDORES[0])
    code, _, _ = server.WebApiHandler._dispatch_post_logout(
        {"authorization": f"Bearer {token}"}
    )
    assert code == 200
    assert server._verify_veedor_token(token) is None


def test_moderacion_rechaza_nombre_suplantado(monkeypatch):
    token, _ = server._issue_veedor_token(server.ACCREDITED_VEEDORES[0])
    monkeypatch.setattr(server, "_report_repo", SimpleNamespace())
    status, _, _ = server.WebApiHandler._dispatch_post_reports_moderate(
        {
            "report_id": "cualquier-reporte",
            "status": "accepted_as_lead",
            "moderated_by": "Otra persona acreditada",
        },
        {"authorization": f"Bearer {token}"},
    )
    assert status == 400
