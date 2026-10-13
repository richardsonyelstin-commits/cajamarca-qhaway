"""Algoritmo determinista de `entity_id` (RN-001-04, `specs/001-entity-mapping/plan.md`).

`entity_id` se deriva **unicamente** del RUC normalizado. No depende del nombre, la
provincia ni la fecha de verificacion, porque esos campos pueden cambiar (CL-001-01:
una municipalidad cambia de nombre oficial) sin que la entidad deje de ser la misma
persona juridica. Dos ejecuciones sobre el mismo RUC producen siempre el mismo
`entity_id` (CA-001-03).
"""

from __future__ import annotations

import hashlib
import re

_DIGITS_ONLY = re.compile(r"\D")

# Longitud de RUC segun SUNAT: 11 digitos, sin excepcion.
_RUC_LENGTH = 11

# Prefijo legible: distingue un entity_id de cualquier otro identificador del sistema
# (p. ej. un `procurement_id`) con solo mirarlo, sin necesidad de un esquema aparte.
_PREFIX = "ce-"

# Cuantos caracteres hex del digest se conservan. 16 hex = 64 bits: suficiente para que
# una colision accidental sobre un universo de decenas a pocos cientos de entidades sea
# despreciable, sin producir un identificador incomodamente largo en logs o URLs.
_DIGEST_LENGTH = 16


def normalize_ruc(raw_ruc: str) -> str:
    """Normaliza un RUC a 11 digitos, sin espacios ni separadores.

    Lanza `ValueError` si, tras quitar todo lo que no sea digito, no quedan exactamente
    11 caracteres -- un RUC mas corto o mas largo no es un dato valido de SUNAT.
    """
    digits = _DIGITS_ONLY.sub("", raw_ruc)
    if len(digits) != _RUC_LENGTH:
        raise ValueError(
            f"RUC invalido: se esperaban {_RUC_LENGTH} digitos, "
            f"'{raw_ruc}' normaliza a {len(digits)} ('{digits}')"
        )
    return digits


def compute_entity_id(ruc: str) -> str:
    """Deriva el `entity_id` determinista de un RUC (RN-001-04).

    Mismo RUC (con o sin formato distinto de entrada) produce siempre el mismo
    `entity_id` -- es la propiedad que exige CA-001-03.
    """
    normalized = normalize_ruc(ruc)
    digest = hashlib.sha256(normalized.encode("ascii")).hexdigest()
    return f"{_PREFIX}{digest[:_DIGEST_LENGTH]}"


__all__ = ["compute_entity_id", "normalize_ruc"]
