"""Suite de pruebas unitarias para la capacidad de integracion SUNAT RUC.

Cubre:
1. Validacion matematica Modulo 11 de RUC reales de Cajamarca y deteccion de digito invalido.
2. Guarda constitucional Art. 16 rechazando DNI de 8 digitos y bloqueando consultas RENIEC.
3. Parseo de respuestas JSON devueltas por Codart API.
4. Deteccion de senales de alerta tributaria (NO HABIDO, BAJA DE OFICIO, digito invalido).
5. Despacho HTTP del endpoint /api/sunat/ruc en WebApiHandler (200 OK y 403 Forbidden).

Cumple estrictamente con Antislop R-02 (cero em-dash en todo el codigo y datos).
"""

from __future__ import annotations

import json
import pytest

from cajamarca_qhaway.capabilities.sunat_enrichment import (
    CodartSunatClient,
    ConstitutionalPrivacyGuardError,
    SunatEnrichmentService,
    SunatRucProfile,
    assert_constitutional_ruc_only,
    assert_ruc_not_dni,
    validate_ruc_checksum,
)
from cajamarca_qhaway.web.server import WebApiHandler


# --- 1. Validacion matematica Modulo 11 SUNAT ---


def test_modulo_11_golden_universe_cajamarca() -> None:
    """Verifica que las 14 entidades publicas del universo de Cajamarca superen el Modulo 11."""
    real_cajamarca_rucs = [
        "20453744168",  # GOBIERNO REGIONAL DE CAJAMARCA (check digit: 8)
        "20143623042",  # MP CAJAMARCA (check digit: 2)
        "20148288853",  # MP CELENDIN (check digit: 3)
        "20148289825",  # MP CHOTA (check digit: 5)
        "20220499767",  # MP CONTUMAZA (check digit: 7)
        "20191657447",  # MP CUTERVO (check digit: 7)
        "20174691267",  # MP HUALGAYOC (check digit: 7)
        "20148260843",  # MP JAEN (check digit: 3)
        "20201987297",  # MP SAN IGNACIO (check digit: 7)
        "20148261572",  # MP SAN MARCOS (check digit: 2)
        "20175083937",  # MP SAN MIGUEL (check digit: 7)
        "20143625843",  # MP SAN PABLO (check digit: 3)
        "20172446800",  # MP SANTA CRUZ (check digit: 0)
        "20200367376",  # MP CAJABAMBA (check digit: 6)
    ]
    for ruc in real_cajamarca_rucs:
        assert validate_ruc_checksum(ruc) is True, f"Fallo validacion para RUC real {ruc}"
        assert assert_constitutional_ruc_only(ruc) == ruc


def test_modulo_11_invalid_checksum_detection() -> None:
    """Verifica que RUCs con digito verificador alterado o invalido sean rechazados."""
    # 20453744168 alterado en el ultimo digito a 9
    assert validate_ruc_checksum("20453744169") is False

    # 20136951524 (digito esperado es 2, no 4)
    assert validate_ruc_checksum("20136951524") is False

    # 20496420671 (digito esperado es 6, no 1)
    assert validate_ruc_checksum("20496420671") is False

    # Corregidos con su digito real deben dar True
    assert validate_ruc_checksum("20136951522") is True
    assert validate_ruc_checksum("20496420676") is True

    # Entradas invalidas no numericas o con longitud incorrecta
    assert validate_ruc_checksum("") is False
    assert validate_ruc_checksum("204537441") is False
    assert validate_ruc_checksum("2045374416800") is False
    assert validate_ruc_checksum("2045374416A") is False


# --- 2. Guarda Constitucional Articulo 16 ---


def test_constitutional_guard_rejects_dni() -> None:
    """Verifica que cualquier intento de consultar o pasar un DNI de 8 digitos lance ConstitutionalPrivacyGuardError."""
    dni_samples = ["70238666", "12345678", "45678901", " 08765432 "]

    for dni in dni_samples:
        with pytest.raises(ConstitutionalPrivacyGuardError) as exc_info:
            assert_ruc_not_dni(dni)
        assert "Articulo 16" in str(exc_info.value)
        assert "personas naturales" in str(exc_info.value)

        with pytest.raises(ConstitutionalPrivacyGuardError):
            assert_constitutional_ruc_only(dni)


def test_constitutional_guard_blocks_reniec_invocations() -> None:
    """Verifica que invocaciones con palabras clave reniec o dni sean bloqueadas de inmediato."""
    with pytest.raises(ConstitutionalPrivacyGuardError):
        assert_ruc_not_dni("consulta_reniec_ciudadano")

    with pytest.raises(ConstitutionalPrivacyGuardError):
        assert_ruc_not_dni("dni_persona_natural")

    client = CodartSunatClient(enable_remote=False)
    with pytest.raises(ConstitutionalPrivacyGuardError) as client_exc:
        client.consultar_dni("70238666")
    assert "Articulo 16" in str(client_exc.value)


def test_sunat_ruc_profile_blocks_dni_construction() -> None:
    """Verifica que no sea posible construir un SunatRucProfile usando un DNI de 8 digitos."""
    from pydantic import ValidationError

    with pytest.raises(ValidationError) as exc_info:
        SunatRucProfile(
            ruc="70238666",
            razon_social="PERSONA NATURAL CON DNI",
            queried_at="2026-10-13T00:00:00Z",
        )
    assert "Articulo 16" in str(exc_info.value)
    assert "personas naturales" in str(exc_info.value)


# --- 3. Parseo de respuesta de Codart API ---


def test_codart_api_response_parsing() -> None:
    """Verifica el parseo correcto de la estructura JSON devuelta por el API Codart."""
    codart_payload = {
        "success": True,
        "result": {
            "ruc": "20453744168",
            "razon_social": "GOBIERNO REGIONAL CAJAMARCA",
            "estado": "ACTIVO",
            "condicion": "HABIDO",
            "direccion": "JR. SANTA TERESA DE JOURNET NRO. 351 URB. LA ALAMEDA",
            "ubigeo": "060101",
            "departamento": "CAJAMARCA",
            "provincia": "CAJAMARCA",
            "distrito": "CAJAMARCA",
            "tipo_contribuyente": "GOBIERNO REGIONAL",
            "actividad_economica": "ADMINISTRACION PUBLICA",
        },
    }

    client = CodartSunatClient(enable_remote=False)
    profile = client.parse_codart_response(codart_payload, "20453744168")

    assert profile.ruc == "20453744168"
    assert profile.razon_social == "GOBIERNO REGIONAL CAJAMARCA"
    assert profile.estado_contribuyente == "ACTIVO"
    assert profile.condicion_domicilio == "HABIDO"
    assert profile.departamento == "CAJAMARCA"
    assert profile.provincia == "CAJAMARCA"
    assert profile.distrito == "CAJAMARCA"
    assert profile.tipo_contribuyente == "GOBIERNO REGIONAL"
    assert profile.es_entidad_publica is False  # Este cliente no infiere el tipo de entidad por el nombre.
    assert profile.source_provider == "codart_api"
    assert profile.has_risks is False
    assert profile.raw_payload == codart_payload


def test_sunat_lookup_without_verified_source_fails_closed(tmp_path) -> None:
    client = CodartSunatClient(cache_registry_path=tmp_path / "empty.json", enable_remote=False)
    with pytest.raises(LookupError, match="perfil SUNAT verificado"):
        client.consultar_ruc("20453744168", fallback_metadata={"estado_contribuyente": "ACTIVO"})


def test_codart_api_error_response_raises_value_error() -> None:
    """Verifica que una respuesta de error de Codart API sea manejada con excepcion apropiada."""
    error_payload = {
        "success": False,
        "error": "No se encontraron resultados para el RUC ingresado",
    }
    client = CodartSunatClient(enable_remote=False)
    with pytest.raises(ValueError) as exc:
        client.parse_codart_response(error_payload, "20453744168")
    assert "Respuesta no exitosa de Codart API" in str(exc.value)


# --- 4. Deteccion de senales de alerta tributaria objetivas ---


def test_risk_signal_detection_no_habido_and_baja_oficio() -> None:
    """Verifica la deteccion objetiva de condiciones de riesgo: NO HABIDO, NO HALLADO y BAJA DE OFICIO."""
    # Caso 1: Proveedor dado de baja de oficio
    baja_profile = SunatRucProfile(
        ruc="20453744168",
        razon_social="PROVEEDOR DE BAJA SAC",
        estado_contribuyente="BAJA DE OFICIO",
        condicion_domicilio="HABIDO",
        source_provider="test_fixture",
        queried_at="2026-10-13T00:00:00Z",
        raw_payload={"fixture": True},
    )
    assert baja_profile.has_risks is True
    assert "ESTADO_NO_ACTIVO: BAJA DE OFICIO" in baja_profile.risk_signals

    # Caso 2: Proveedor no habido
    no_habido_profile = SunatRucProfile(
        ruc="20453744168",
        razon_social="PROVEEDOR NO HABIDO SRL",
        estado_contribuyente="ACTIVO",
        condicion_domicilio="NO HABIDO",
        source_provider="test_fixture",
        queried_at="2026-10-13T00:00:00Z",
        raw_payload={"fixture": True},
    )
    assert no_habido_profile.has_risks is True
    assert "CONDICION_IRREGULAR: NO HABIDO" in no_habido_profile.risk_signals

    # Caso 3: Proveedor no hallado
    no_hallado_profile = SunatRucProfile(
        ruc="20453744168",
        razon_social="CONSTRUCTORA NO HALLADA EIRL",
        estado_contribuyente="ACTIVO",
        condicion_domicilio="NO HALLADO",
        source_provider="test_fixture",
        queried_at="2026-10-13T00:00:00Z",
        raw_payload={"fixture": True},
    )
    assert no_hallado_profile.has_risks is True
    assert "CONDICION_IRREGULAR: NO HALLADO" in no_hallado_profile.risk_signals

    # Caso 4: Proveedor con digito verificador matematicamente invalido
    bad_check_profile = SunatRucProfile(
        ruc="20136951524",  # Digito esperado es 2, no 4
        razon_social="PROVEEDOR CON RUC MAL DIGITADO",
        estado_contribuyente="ACTIVO",
        condicion_domicilio="HABIDO",
        source_provider="test_fixture",
        queried_at="2026-10-13T00:00:00Z",
        raw_payload={"fixture": True},
    )
    assert bad_check_profile.has_risks is True
    assert "DIGITO_VERIFICADOR_INVALIDO" in bad_check_profile.risk_signals


# --- 5. Endpoint HTTP /api/sunat/ruc en WebApiHandler ---


def test_endpoint_sunat_ruc_valid_lookup() -> None:
    """Verifica que GET /api/sunat/ruc?ruc=<RUC_VALIDO> devuelva 200 OK con datos completos."""
    status, ctype, body = WebApiHandler.dispatch("GET", "/api/sunat/ruc", {"ruc": ["20453744168"]})
    assert status == 200
    assert "application/json" in ctype
    data = json.loads(body.decode("utf-8"))
    assert data["ruc"] == "20453744168"
    assert "GOBIERNO REGIONAL" in data["razon_social"]
    assert data["es_entidad_publica"] is True
    assert data["estado_contribuyente"] == "ACTIVO"


def test_endpoint_sunat_ruc_blocks_dni_with_403() -> None:
    """Verifica que GET /api/sunat/ruc?dni=... sea bloqueado con 403 Forbidden citando Art. 16."""
    status, ctype, body = WebApiHandler.dispatch("GET", "/api/sunat/ruc", {"dni": ["70238666"]})
    assert status == 403
    data = json.loads(body.decode("utf-8"))
    assert data["code"] == "CONSTITUTIONAL_PRIVACY_GUARD_ART_16"
    assert "Articulo 16" in data["error"]
    assert "personas naturales" in data["error"]


def test_endpoint_sunat_ruc_blocks_8_digit_identifier_with_403() -> None:
    """Verifica que pasar un DNI de 8 digitos en el parametro ruc tambien devuelva 403 Forbidden."""
    status, ctype, body = WebApiHandler.dispatch("GET", "/api/sunat/ruc", {"ruc": ["70238666"]})
    assert status == 403
    data = json.loads(body.decode("utf-8"))
    assert data["code"] == "CONSTITUTIONAL_PRIVACY_GUARD_ART_16"
    assert "Articulo 16" in data["error"]


def test_endpoint_sunat_ruc_summary() -> None:
    """Verifica que GET /api/sunat/ruc sin parametros devuelva el resumen del padron consolidado."""
    status, ctype, body = WebApiHandler.dispatch("GET", "/api/sunat/ruc", {})
    assert status == 200
    data = json.loads(body.decode("utf-8"))
    assert "total_records" in data
    assert "public_entities_count" in data
    assert data["total_records"] > 0
    assert data["public_entities_count"] >= 14
