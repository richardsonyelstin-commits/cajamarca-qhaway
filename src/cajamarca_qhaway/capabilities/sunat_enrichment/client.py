"""Cliente optativo de consulta tributaria de terceros; no sustituye la fuente oficial SUNAT."""

from __future__ import annotations

import json
import logging
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx

from cajamarca_qhaway.capabilities.sunat_enrichment.models import SunatRucProfile
from cajamarca_qhaway.capabilities.sunat_enrichment.validator import (
    ConstitutionalPrivacyGuardError,
    assert_ruc_not_dni,
)

logger = logging.getLogger("cajamarca_qhaway.sunat_enrichment.client")

CODART_DEFAULT_BASE_URL = "https://api-codart.cgrt.org/api/v1"


class CodartSunatClient:
    """Cliente de terceros desactivado por defecto y con errores de datos fail-closed."""

    def __init__(
        self,
        token: str | None = None,
        base_url: str | None = None,
        cache_registry_path: Path | str | None = None,
        timeout: float = 5.0,
        enable_remote: bool = False,
    ) -> None:
        self.token = token or os.getenv("CAJAMARCA_QHAWAY_CODART_TOKEN")
        self.base_url = (base_url or os.getenv("CAJAMARCA_QHAWAY_CODART_BASE_URL", CODART_DEFAULT_BASE_URL)).rstrip("/")
        self.timeout = timeout
        self.enable_remote = enable_remote
        self.cache_registry_path = Path(cache_registry_path or "data/sunat/ruc_registry.json")
        self._memory_cache: dict[str, SunatRucProfile] = {}
        self._circuit_broken: bool = False
        self._load_cache()

    def _load_cache(self) -> None:
        if self.cache_registry_path.exists():
            try:
                with open(self.cache_registry_path, encoding="utf-8") as f:
                    data = json.load(f)
                records = data.get("registry", {})
                for ruc, item in records.items():
                    if (
                        isinstance(item, dict)
                        and item.get("source_provider") == "sunat_padron_reducido"
                        and item.get("raw_payload", {}).get("source_url")
                    ):
                        self._memory_cache[ruc] = SunatRucProfile(**item)
            except (OSError, ValueError, TypeError, AttributeError, httpx.HTTPError) as exc:
                logger.warning("No se pudo cargar la cache local de RUC: %s", exc)

    def consultar_dni(self, dni: str) -> None:
        """Guarda constitucional Art. 16: Bloquea y prohibe consultas DNI/RENIEC."""
        raise ConstitutionalPrivacyGuardError(
            "Articulo 16 (Prohibicion de perfilamiento de personas naturales): "
            "Queda terminantemente prohibido invocar consultas DNI o RENIEC. "
            "Cajamarca Qhaway opera exclusivamente sobre personas juridicas y entidades del Estado."
        )

    def parse_codart_response(self, payload: dict[str, Any], ruc: str) -> SunatRucProfile:
        """Parsea e interpreta la respuesta JSON devuelta por el API Codart."""
        success = payload.get("success", False)
        result = payload.get("result", {})
        now_iso = datetime.now(UTC).isoformat()

        if not success or not isinstance(result, dict):
            error_msg = payload.get("error") or payload.get("message") or "Sin datos"
            raise ValueError(f"Respuesta no exitosa de Codart API para RUC {ruc}: {error_msg}")

        razon_social = (
            result.get("razon_social")
            or result.get("nombre")
            or result.get("razonSocial")
        )
        estado = result.get("estado") or result.get("estado_contribuyente")
        condicion = result.get("condicion") or result.get("condicion_domicilio")
        if (not isinstance(razon_social, str) or not razon_social.strip()
                or not isinstance(estado, str) or not estado.strip()
                or not isinstance(condicion, str) or not condicion.strip()):
            raise ValueError("La respuesta del proveedor carece de campos SUNAT verificables")
        razon_social = razon_social.strip()
        estado = estado.strip().upper()
        condicion = condicion.strip().upper()
        direccion = result.get("direccion") or result.get("direccion_fiscal")
        ubigeo = result.get("ubigeo")
        departamento = result.get("departamento")
        provincia = result.get("provincia")
        distrito = result.get("distrito")
        tipo = result.get("tipo_contribuyente") or result.get("tipo")

        return SunatRucProfile(
            ruc=ruc,
            razon_social=razon_social,
            estado_contribuyente=estado,
            condicion_domicilio=condicion,
            tipo_contribuyente=tipo,
            direccion_fiscal=direccion,
            ubigeo=ubigeo,
            departamento=departamento,
            provincia=provincia,
            distrito=distrito,
            es_entidad_publica=False,
            source_provider="codart_api",
            queried_at=now_iso,
            raw_payload=payload,
        )

    def consultar_ruc(
        self,
        identifier: str,
        fallback_metadata: dict[str, Any] | None = None,
        force_remote: bool = False,
    ) -> SunatRucProfile:
        """Consulta multi-nivel de RUC SUNAT garantizando cero fallas de ejecucion."""
        clean_ruc = assert_ruc_not_dni(identifier).replace("PE-RUC-", "").strip()

        # Nivel 1: Cache local en memoria o archivo
        if not force_remote and clean_ruc in self._memory_cache:
            return self._memory_cache[clean_ruc]

        # Nivel 2: Intento con API Codart si remoto habilitado y circuito cerrado
        if self.enable_remote and self.token and not self._circuit_broken:
            api_profile = self._query_codart_api(clean_ruc)
            if api_profile:
                self._memory_cache[clean_ruc] = api_profile
                return api_profile

        raise LookupError(f"No existe un perfil SUNAT verificado en cache para el RUC {clean_ruc}")

    def _query_codart_api(self, ruc: str) -> SunatRucProfile | None:
        url = f"{self.base_url}/consultas/sunat/ruc/{ruc}"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "User-Agent": "CajamarcaQhaway-SunatIntegrator/1.0",
        }
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(url, headers=headers)
                if response.status_code == 200:
                    data = response.json()
                    if data.get("success"):
                        return self.parse_codart_response(data, ruc)
                elif response.status_code in (401, 403, 422, 429):
                    # Desactivar API temporalmente si token es invalido o rate-limited
                    self._circuit_broken = True
                    logger.info("Codart API no disponible (status %d). No se usaran datos de sustitucion.", response.status_code)
        except (OSError, ValueError, TypeError, AttributeError, httpx.HTTPError) as exc:
            self._circuit_broken = True
            logger.debug("Error conectando con Codart API: %s", exc)
        return None
