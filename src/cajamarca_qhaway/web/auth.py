"""Identidad acreditada por Supabase y revocacion compartida, sin cuentas locales."""

from __future__ import annotations

import base64
import hashlib
import json
import os
import time
from typing import Any
from urllib.parse import urlsplit

import httpx


class AuthUnavailable(RuntimeError):
    """No se puede comprobar identidad o revocacion de forma segura."""


class InvalidCredentials(ValueError):
    """La credencial no representa a un revisor acreditado vigente."""


class AuthService:
    """Valida cada credencial con el proveedor y una lista compartida de revocaciones.

    Las dependencias opcionales son para pruebas aisladas, no habilitan identidades
    sinteticas en el servidor. Nunca se confia en metadatos editables por el usuario.
    """

    def __init__(self, db: Any = None, *, client: Any = None) -> None:
        self.db = db
        self.client = client

    def _config(self) -> tuple[str, str]:
        url = (os.environ.get("CAJAMARCA_QHAWAY_SUPABASE_URL")
               or os.environ.get("SUPABASE_URL") or "").rstrip("/")
        key = (os.environ.get("CAJAMARCA_QHAWAY_SUPABASE_ANON_KEY")
               or os.environ.get("SUPABASE_ANON_KEY") or "")
        parsed = urlsplit(url)
        if (not key or parsed.scheme != "https" or not parsed.hostname
                or parsed.username or parsed.password or parsed.query or parsed.fragment
                or parsed.path):
            raise AuthUnavailable("Configure la URL HTTPS y la clave publica de Supabase Auth")
        cloud = (bool(os.environ.get("VERCEL"))
                 or os.environ.get("CAJAMARCA_QHAWAY_ENV", "").lower() == "production"
                 or os.environ.get("ENVIRONMENT", "").lower() == "production")
        if self.db is None or (cloud and not self.db.is_postgres):
            raise AuthUnavailable("La autenticacion requiere revocaciones compartidas duraderas")
        return url, key

    @staticmethod
    def _token_hash(token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    def _is_revoked(self, token: str) -> bool:
        try:
            with self.db.connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT token_hash FROM auth_revocations WHERE token_hash = ?",
                               (self._token_hash(token),))
                return cursor.fetchone() is not None
        except Exception as error:
            raise AuthUnavailable("No se pudo verificar la revocacion compartida") from error

    def verify(self, token: str | None) -> dict[str, Any] | None:
        if not token or not isinstance(token, str):
            return None
        url, key = self._config()
        if self._is_revoked(token):
            return None
        try:
            requester = self.client if self.client is not None else httpx
            response = requester.get(
                f"{url}/auth/v1/user",
                headers={"apikey": key, "Authorization": f"Bearer {token}"},
                timeout=5.0,
                follow_redirects=False,
            )
        except httpx.HTTPError as error:
            raise AuthUnavailable("El proveedor de identidad no esta disponible") from error
        if response.status_code in (401, 403):
            return None
        if response.status_code != 200:
            raise AuthUnavailable("El proveedor no pudo verificar la identidad")
        try:
            user = response.json()
            if not isinstance(user, dict):
                raise ValueError("Perfil invalido")
            metadata = user.get("app_metadata")
            email = user.get("email")
            if (not isinstance(metadata, dict) or metadata.get("role") != "reviewer"
                    or not user.get("email_confirmed_at") or not user.get("id")
                    or not isinstance(email, str) or "@" not in email):
                return None
            # El proveedor ya valido la firma y vigencia. La decodificacion local
            # solo extrae el vencimiento y la vinculacion del token validado.
            pieces = token.split(".")
            if len(pieces) != 3:
                return None
            payload = json.loads(base64.urlsafe_b64decode(pieces[1] + "=" * (-len(pieces[1]) % 4)))
            expires = payload.get("exp")
            if (not isinstance(expires, (int, float)) or isinstance(expires, bool)
                    or expires <= time.time() or payload.get("sub") != user["id"]):
                return None
            profile = {
                "email": email,
                "name": metadata.get("name") or email,
                "organization": metadata.get("organization") or "",
                "accreditationNumber": metadata.get("accreditationNumber") or "",
                "role": "reviewer",
            }
            if any(not isinstance(value, str) for value in profile.values()):
                return None
            return {"veedor": profile, "expiresAt": int(expires * 1000)}
        except (ValueError, TypeError, KeyError, AttributeError, OverflowError):
            return None

    def login(self, data: dict[str, Any]) -> dict[str, Any]:
        token = data.get("access_token")
        if not isinstance(token, str) or not token.strip():
            raise InvalidCredentials("Inicie sesion con Google mediante Supabase Auth")
        session = self.verify(token)
        if session is None:
            raise InvalidCredentials("Identidad no acreditada o sesion vencida")
        return {"token": token, **session}

    def logout(self, token: str | None) -> None:
        if not isinstance(token, str) or not token:
            raise InvalidCredentials("Sesion requerida")
        session = self.verify(token)
        if session is None:
            # Un logout repetido de un token ya revocado es idempotente.
            self._config()
            if self._is_revoked(token):
                return
            raise InvalidCredentials("Sesion invalida")
        try:
            with self.db.connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO auth_revocations (token_hash, expires_at) VALUES (?, ?) "
                    "ON CONFLICT (token_hash) DO NOTHING",
                    (self._token_hash(token), session["expiresAt"] // 1000),
                )
                conn.commit()
        except Exception as error:
            raise AuthUnavailable("No se pudo confirmar el cierre de sesion compartido") from error
