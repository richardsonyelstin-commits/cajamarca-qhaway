"""Validador matematico y guardas constitucionales para RUC / SUNAT (Art. 16).

Invariante constitucional:
Articulo 16 de la Constitucion de Cajamarca Qhaway (Prohibicion de perfilamiento de personas naturales):
El sistema analiza exclusivamente entidades publicas y contratistas/proveedores del Estado
mediante RUC de 11 digitos. Queda terminantemente prohibido consultar, almacenar o perfilar
DNI / RENIEC de personas naturales.
"""

from __future__ import annotations

import re

# Pesos oficiales establecidos por SUNAT para el calculo del digito verificador modulo 11
SUNAT_RUC_WEIGHTS: tuple[int, ...] = (5, 4, 3, 2, 7, 6, 5, 4, 3, 2)

DNI_PATTERN = re.compile(r"^\d{8}$")
RUC_PATTERN = re.compile(r"^\d{11}$")


class ConstitutionalPrivacyGuardError(ValueError):
    """Excepcion constitucional bajo el Articulo 16 de Cajamarca Qhaway.

    Prohibe el perfilamiento, almacenamiento o consulta de DNI / RENIEC de personas naturales.
    """


def assert_ruc_not_dni(identifier: str) -> str:
    """Aplica la guarda constitucional del Articulo 16.

    Rechaza terminantemente cualquier identificador con patron de DNI de 8 digitos
    o invocaciones dirigidas al subsistema RENIEC o consultas sobre personas naturales.
    """
    if not isinstance(identifier, str):
        raise ConstitutionalPrivacyGuardError(
            "Identificador debe ser una cadena de texto valida."
        )

    cleaned = identifier.strip()
    lower = cleaned.lower()

    if "dni" in lower or "reniec" in lower:
        raise ConstitutionalPrivacyGuardError(
            "Articulo 16 (Prohibicion de perfilamiento de personas naturales): "
            "Queda terminantemente prohibido consultar, almacenar o procesar "
            "solicitudes de DNI o RENIEC. El sistema opera exclusivamente sobre "
            "entidades publicas y proveedores contratistas del Estado mediante RUC."
        )

    digits_only = re.sub(r"\D", "", cleaned)
    if len(digits_only) == 8 or DNI_PATTERN.match(cleaned):
        raise ConstitutionalPrivacyGuardError(
            "Articulo 16 (Prohibicion de perfilamiento de personas naturales): "
            f"El identificador '{identifier}' corresponde a un DNI de 8 digitos. "
            "Se rechaza la operacion para salvaguardar la privacidad de personas naturales."
        )

    return cleaned


def validate_ruc_checksum(ruc: str) -> bool:
    """Valida el digito verificador de un RUC peruano usando el algoritmo oficial Modulo 11 de SUNAT.

    Pesos SUNAT: (5, 4, 3, 2, 7, 6, 5, 4, 3, 2).
    Suma ponderada = d0*5 + d1*4 + d2*3 + d3*2 + d4*7 + d5*6 + d6*5 + d7*4 + d8*3 + d9*2.
    Resto = 11 - (Suma ponderada % 11).
    Si Resto == 10: digito verificador esperado es 0.
    Si Resto == 11: digito verificador esperado es 1.
    De lo contrario: digito verificador esperado es Resto.
    """
    if not isinstance(ruc, str):
        return False

    cleaned = ruc.strip().replace("PE-RUC-", "")
    if len(cleaned) != 11 or not cleaned.isdigit():
        return False

    digits = [int(c) for c in cleaned]
    weighted_sum = sum(d * w for d, w in zip(digits[:10], SUNAT_RUC_WEIGHTS))
    rem = 11 - (weighted_sum % 11)

    if rem == 10:
        expected_check_digit = 0
    elif rem == 11:
        expected_check_digit = 1
    else:
        expected_check_digit = rem

    return digits[10] == expected_check_digit


def assert_constitutional_ruc_only(identifier: str) -> str:
    """Valida y normaliza un RUC asegurando cumplimiento constitucional (Art. 16) y checksum Modulo 11.

    Lanza ConstitutionalPrivacyGuardError si se detecta un DNI o invocacion RENIEC.
    Lanza ValueError si el formato o digito verificador no es valido.
    Retorna el RUC limpio de 11 digitos numericos.
    """
    cleaned = assert_ruc_not_dni(identifier)
    ruc_cleaned = cleaned.replace("PE-RUC-", "").strip()

    if len(ruc_cleaned) != 11 or not ruc_cleaned.isdigit():
        raise ValueError(
            f"Identificador '{identifier}' invalido: se requiere un RUC de 11 digitos numericos."
        )

    if not validate_ruc_checksum(ruc_cleaned):
        raise ValueError(
            f"RUC '{ruc_cleaned}' invalido: no supera la verificacion de digito de control SUNAT Modulo 11."
        )

    return ruc_cleaned
