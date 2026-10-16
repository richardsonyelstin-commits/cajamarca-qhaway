"""Frontera JSON cerrada; no consulta red, reloj ni configuración ambiental."""

from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import replace
from typing import Literal, cast

from jsonschema import Draft202012Validator, FormatChecker
from pydantic import TypeAdapter, ValidationError
from referencing import Registry

from .contracts import BatchInvalid, Problem, Request
from .policy import BUDGET_RULES, POLICY
from .schema_data import REQUEST_SCHEMA
from .serialization import canonical_bytes, object_document
from .serialization_types import JSONValue

MAX_BYTES = 32 * 1024 * 1024
MAX_DEPTH = 32
VALIDATOR = Draft202012Validator(
    REQUEST_SCHEMA, registry=Registry(), format_checker=FormatChecker()
)
REQUEST_ADAPTER = TypeAdapter(Request)
type ErrorCode = str


def invalid(problems: list[Problem]) -> BatchInvalid:
    return BatchInvalid(
        "engine-2",
        "BatchInvalid",
        tuple(
            sorted(
                set(problems),
                key=lambda item: (item.pointer, item.code),
            )
        ),
    )


def problem(pointer: str, code: str = "SCHEMA_VIOLATION") -> Problem:
    return Problem(pointer, cast("ProblemCode", code))


type ProblemCode = Literal[
    "SCHEMA_VIOLATION",
    "DUPLICATE_JSON_KEY",
    "UNSUPPORTED_VERSION",
    "DUPLICATE_ID",
    "DANGLING_REFERENCE",
    "RESOURCE_LIMIT",
]


class DuplicateKey(ValueError):
    pass


def _pairs(pairs: list[tuple[str, JSONValue]]) -> dict[str, JSONValue]:
    result = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKey()
        result[key] = value
    return result


def _float(_value: str) -> None:
    raise ValueError("Número no entero")


def _depth(raw: str) -> bool:
    depth = 0
    quoted = escaped = False
    for char in raw:
        if quoted:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                quoted = False
        elif char == '"':
            quoted = True
        elif char in "[{":
            depth += 1
            if depth > MAX_DEPTH:
                return False
        elif char in "]}":
            depth -= 1
    return True


def _pointer(parts: Iterable[str | int]) -> str:
    return "".join(
        "/" + str(part).replace("~", "~0").replace("/", "~1") for part in parts
    )


def decode_request(raw: bytes) -> Request | BatchInvalid:
    if len(raw) > MAX_BYTES:
        return invalid([problem("", "RESOURCE_LIMIT")])
    try:
        text = raw.decode("utf-8", errors="strict")
        if not _depth(text):
            return invalid([problem("", "RESOURCE_LIMIT")])
        value = json.loads(
            text, object_pairs_hook=_pairs, parse_float=_float, parse_constant=_float
        )
    except DuplicateKey:
        return invalid([problem("", "DUPLICATE_JSON_KEY")])
    except (ValueError, UnicodeError, RecursionError):
        return invalid([problem("")])
    if isinstance(value, dict):
        versions = {
            "schema_version": "engine-2",
            "engine_version": "deterministic-2.0.0",
            "policy_version": "qhaway-exploratory-1",
        }
        unsupported = [
            problem("/" + key, "UNSUPPORTED_VERSION")
            for key, expected in versions.items()
            if key in value and value[key] != expected
        ]
        scopes = value.get("scopes")
        if isinstance(scopes, list):
            for i, scope in enumerate(scopes):
                if isinstance(scope, dict) and isinstance(scope.get("rules"), list):
                    unsupported += [
                        problem(f"/scopes/{i}/rules/{j}", "UNSUPPORTED_VERSION")
                        for j, rule in enumerate(scope["rules"])
                        if isinstance(rule, str) and rule not in POLICY
                    ]
        if unsupported:
            return invalid(unsupported)
    errors = []
    for error in VALIDATOR.iter_errors(value):
        pointer = _pointer(error.absolute_path)
        if error.validator == "additionalProperties" and isinstance(
            error.instance, dict
        ):
            known = error.schema.get("properties", {})
            errors += [
                problem(pointer + "/" + str(key).replace("~", "~0").replace("/", "~1"))
                for key in error.instance
                if key not in known
            ]
        else:
            errors.append(problem(pointer))
    if errors:
        return invalid(errors)
    try:
        return normalize_request(
            REQUEST_ADAPTER.validate_json(canonical_bytes(value), strict=True)
        )
    except (ValueError, ValidationError, UnicodeError):
        return invalid([problem("")])


def normalize_request(request: Request) -> Request | BatchInvalid:
    errors = []
    scope_ids = set()
    for i, scope in enumerate(request.scopes):
        if scope.scope_id in scope_ids:
            errors.append(problem(f"/scopes/{i}/scope_id", "DUPLICATE_ID"))
        scope_ids.add(scope.scope_id)
        if scope.scope_id != scope.scope_id.strip():
            errors.append(problem(f"/scopes/{i}/scope_id"))
        for j, rule in enumerate(scope.rules):
            if (rule in BUDGET_RULES) != (scope.kind == "budget"):
                errors.append(problem(f"/scopes/{i}/rules/{j}"))
    evidence = {}
    for i, ref in enumerate(request.evidence):
        if ref.evidence_id != ref.evidence_id.strip():
            errors.append(problem(f"/evidence/{i}/evidence_id"))
        previous = evidence.get(ref.evidence_id)
        if previous is not None and previous != ref:
            errors.append(problem(f"/evidence/{i}/evidence_id", "DUPLICATE_ID"))
        evidence[ref.evidence_id] = ref
    for i, scope in enumerate(request.scopes):
        ref = evidence.get(scope.coverage_evidence_id)
        if ref is None or ref.retrieved_at > request.as_of:
            errors.append(
                problem(f"/scopes/{i}/coverage_evidence_id", "DANGLING_REFERENCE")
            )
    for i, observation in enumerate(request.observations):
        if observation.scope_id not in scope_ids:
            errors.append(problem(f"/observations/{i}/scope_id", "DANGLING_REFERENCE"))
        for j, ref_id in enumerate(observation.evidence_ids):
            ref = evidence.get(ref_id)
            if ref is None or (ref.source_id, ref.retrieved_at) != (
                observation.source_id,
                observation.retrieved_at,
            ):
                errors.append(
                    problem(f"/observations/{i}/evidence_ids/{j}", "DANGLING_REFERENCE")
                )
    if errors:
        return invalid(errors)
    observations = {
        replace(obs, evidence_ids=tuple(sorted(obs.evidence_ids)))
        for obs in request.observations
    }
    return replace(
        request,
        scopes=tuple(
            replace(scope, rules=tuple(sorted(scope.rules)))
            for scope in sorted(request.scopes, key=lambda scope: scope.scope_id)
        ),
        evidence=tuple(evidence[key] for key in sorted(evidence)),
        observations=tuple(
            sorted(
                observations,
                key=lambda obs: (
                    obs.scope_id,
                    obs.source_id,
                    obs.record_key,
                    obs.revision,
                    canonical_bytes(object_document(obs)),
                ),
            )
        ),
    )
