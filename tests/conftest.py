"""Identidades exclusivamente de prueba, nunca incluidas en el runtime del proyecto."""

from __future__ import annotations

import hashlib

import pytest


_TEST_SALT = b"test-salt-veedor-2026"
_TEST_HASH = hashlib.scrypt(
    b"demo-veedor-2025", salt=_TEST_SALT, n=2**14, r=8, p=1, dklen=64,
).hex()


@pytest.fixture
def configured_test_veedor(monkeypatch):
    from cajamarca_qhaway.web import server

    monkeypatch.setattr(server, "ACCREDITED_VEEDORES", [{
        "email": "veeduria-cajamarca@proetica.org.pe",
        "name": "Lic. Carlos Arana Silva",
        "organization": "Proetica Cajamarca (identidad ficticia de pruebas)",
        "accreditationNumber": "TEST-VEED-001",
        "role": "veedor_titular",
        "password_salt": _TEST_SALT.hex(),
        "password_scrypt_hash": _TEST_HASH,
    }])
    monkeypatch.setattr(server, "_TOKEN_SECRET", b"test-only-token-signing-key-2026-long")
