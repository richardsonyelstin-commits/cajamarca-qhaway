"""Adaptación privada desde bytes preservados; nunca modifica modelos heredados."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import replace
from decimal import Decimal
from hashlib import sha256

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

from .capabilities.deterministic_engine.boundary import decode_request
from .capabilities.deterministic_engine.contracts import BatchInvalid, Request
from .capabilities.deterministic_engine.engine import evaluate
from .capabilities.deterministic_engine.schema_data import REQUEST_SCHEMA, SHADOW_SCHEMA
from .capabilities.deterministic_engine.serialization import (
    canonical_bytes,
    object_document,
)

LEGACY_DISPOSITIONS = {
    "single-bidder": "single-bidder: proceso completo y método confirmado",
    "execution-overrun": "budget-above-pim: solo maestro institucional anual",
    "contract-concentration": "contract-share: cobertura y mínimo tres procesos",
    "short-tender-window": "deferred: requiere calendario y régimen",
    "direct-award-threshold": "deferred: requiere régimen y umbral autorizado",
    "direct-administration-equipment-rent": "retired: texto insuficiente",
    "contract-splitting-orders": "deferred: sin similitud como prueba",
    "mef-underspending": "budget-unspent: solo ejercicio cerrado",
    "recurrent-direct-award": "recurrent-direct: procesos distintos en 365 días",
    "hhi-concentration": "hhi: fracción exacta y cohorte completa",
    "case-priority": "outside-core: prioridad y dictámenes no se migran",
}


class MigrationBlocked(ValueError):
    """El expediente no acredita una correspondencia o un importe exacto."""


def exact_money(raw: bytes, pointer: str) -> str:
    def reject(value):
        raise MigrationBlocked("Número no finito")

    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise MigrationBlocked("Clave duplicada")
            result[key] = value
        return result

    try:
        value = json.loads(
            raw.decode("utf-8"),
            parse_float=Decimal,
            parse_constant=reject,
            object_pairs_hook=pairs,
        )
        if not pointer.startswith("/"):
            raise MigrationBlocked("Pointer requerido")
        for token in pointer[1:].split("/"):
            key = token.replace("~1", "/").replace("~0", "~")
            value = value[int(key)] if isinstance(value, list) else value[key]
        if isinstance(value, bool) or not isinstance(value, (str, int, Decimal)):
            raise MigrationBlocked("Importe ausente")
        amount = Decimal(value)
        if (
            not amount.is_finite()
            or amount < 0
            or amount >= Decimal(1000000000000000000)
        ):
            raise MigrationBlocked("Importe fuera del perfil")
        if amount != amount.quantize(Decimal("0.01")):
            raise MigrationBlocked("Importe requiere redondeo")
        return format(amount, ".2f")
    except (ValueError, KeyError, IndexError, TypeError, ArithmeticError) as error:
        raise MigrationBlocked("Payload monetario incompatible") from error


def prepare_shadow(envelope: dict, payloads: Mapping[str, bytes]) -> Request:
    if not Draft202012Validator(
        SHADOW_SCHEMA,
        registry=Registry().with_resource(
            str(REQUEST_SCHEMA["$id"]), Resource.from_contents(REQUEST_SCHEMA)
        ),
    ).is_valid(envelope):
        raise MigrationBlocked("Mapa fuera de contrato shadow-1")
    request = decode_request(canonical_bytes(envelope["request"]))
    if isinstance(request, BatchInvalid):
        raise MigrationBlocked("Request inválido")
    evidence = {ref.evidence_id: ref for ref in request.evidence}
    if set(payloads) != set(evidence):
        raise MigrationBlocked("Cada evidencia requiere bytes preservados")
    for evidence_id, raw in payloads.items():
        ref = evidence.get(evidence_id)
        if ref is None or sha256(raw).hexdigest() != ref.payload_sha256:
            raise MigrationBlocked("Hash de payload no corresponde")
    targets = {(row.scope_id, row.record_key) for row in request.observations}
    linked = set()
    for link in envelope["links"]:
        target = (link["scope_id"], link["record_key"])
        if (
            target not in targets
            or link["evidence_id"] not in evidence
            or link["evidence_id"] not in payloads
        ):
            raise MigrationBlocked("Correspondencia no acreditada")
        if not any(
            row.scope_id == target[0]
            and row.record_key == target[1]
            and link["evidence_id"] in row.evidence_ids
            for row in request.observations
        ):
            raise MigrationBlocked("Correspondencia ajena al hecho")
        linked.add(target)
    if linked != targets:
        raise MigrationBlocked("Expedientes sin correspondencia explícita")
    bindings = {}
    for binding in envelope["money"]:
        key = tuple(
            binding[k]
            for k in ("scope_id", "record_key", "source_id", "revision", "field")
        )
        if key in bindings:
            raise MigrationBlocked("Correspondencia monetaria ambigua")
        bindings[key] = binding
    used = set()
    observations = []
    for row in request.observations:
        values = {}
        for field in ("amount",) if row.fact.kind == "award" else ("pim", "devengado"):
            if getattr(row.fact, field) is None:
                continue
            key = (row.scope_id, row.record_key, row.source_id, row.revision, field)
            binding = bindings.get(key)
            if (
                binding is None
                or binding["evidence_id"] not in row.evidence_ids
                or binding["evidence_id"] not in payloads
            ):
                raise MigrationBlocked("Falta payload monetario preciso")
            values[field] = exact_money(
                payloads[binding["evidence_id"]], binding["pointer"]
            )
            used.add(key)
        observations.append(replace(row, fact=replace(row.fact, **values)))
    if used != set(bindings):
        raise MigrationBlocked("Binding sin destino monetario")
    return replace(request, observations=tuple(observations))


def shadow_report(envelope: dict, payloads: Mapping[str, bytes]) -> bytes:
    request = prepare_shadow(envelope, payloads)
    return canonical_bytes(
        object_document(
            {
                "mapping_version": "shadow-1",
                "links": envelope["links"],
                "result": object_document(evaluate(request)),
                "promotion": "disabled",
                "migration_inventory": LEGACY_DISPOSITIONS,
            }
        )
    )
