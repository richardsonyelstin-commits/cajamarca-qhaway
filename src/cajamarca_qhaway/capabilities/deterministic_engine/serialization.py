"""Codificación canónica y conversión de los DTO inmutables."""

from __future__ import annotations

import json
from dataclasses import fields, is_dataclass
from typing import cast

from .serialization_types import JSONValue


def document(value: object) -> JSONValue:
    if value is None or isinstance(value, (bool, int, str)):
        return value
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: document(getattr(value, field.name)) for field in fields(value)
        }
    if isinstance(value, (list, tuple)):
        return [document(item) for item in value]
    if isinstance(value, dict) and all(isinstance(key, str) for key in value):
        return {key: document(item) for key, item in value.items()}
    raise TypeError("El contrato admite únicamente valores JSON canónicos")


def canonical_bytes(value: JSONValue) -> bytes:
    validated = document(value)
    return json.dumps(
        validated,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def object_document(value: object) -> dict[str, JSONValue]:
    return cast(dict[str, JSONValue], document(value))
