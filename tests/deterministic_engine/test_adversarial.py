"""Frontera hostil, precedencia y aislamiento sin servicios externos."""

import copy
import json
import os
import subprocess
import sys
from fractions import Fraction

import pytest
from hypothesis import given, seed, settings
from hypothesis import strategies as st
from jsonschema import Draft202012Validator

from cajamarca_qhaway.capabilities.deterministic_engine import (
    cents,
    evaluate,
    evaluate_json,
    ratio,
)
from cajamarca_qhaway.capabilities.deterministic_engine.boundary import decode_request
from cajamarca_qhaway.capabilities.deterministic_engine.contracts import BatchResult
from cajamarca_qhaway.capabilities.deterministic_engine.schema_data import RESULT_SCHEMA


@pytest.mark.parametrize(
    "raw",
    [
        b"",
        b"[]",
        b"null",
        b"true",
        b"{}",
        b"{",
        b'"\xff"',
        b"\xef\xbb\xbf{}",
        b'{"a":1.0}',
        b'{"a":NaN}',
        b'{"a":Infinity}',
        b'{"a":-Infinity}',
    ],
)
def test_invalid_wire(raw):
    result = json.loads(evaluate_json(raw))
    Draft202012Validator(RESULT_SCHEMA).validate(result)
    assert result["kind"] == "BatchInvalid"


@pytest.mark.parametrize(
    "path,value",
    [
        (("as_of",), "2026-02-30T00:00:00Z"),
        (("as_of",), "2026-10-15T00:00:00+00:00"),
        (("as_of",), "2026-10-15T00:00:60Z"),
        (("as_of",), "2026-10-15"),
        (("observations", 0, "revision"), True),
        (("observations", 0, "revision"), "1"),
        (("observations", 0, "fact", "amount"), 100.0),
        (("observations", 0, "fact", "amount"), "01.00"),
        (("evidence", 0, "source_url"), "http://example.invalid"),
        (("observations", 0, "fact", "extra"), "secret-marker"),
        (("scopes", 0, "extra"), 1),
        (("evidence", 0, "extra"), 1),
        (("observations", 0, "extra"), 1),
    ],
)
def test_schema_mutations(payload, path, value):
    target = copy.deepcopy(payload)
    node = target
    for part in path[:-1]:
        node = node[part]
    node[path[-1]] = value
    raw = evaluate_json(json.dumps(target).encode())
    assert json.loads(raw)["kind"] == "BatchInvalid"
    assert b"secret-marker" not in raw


def test_limits():
    for raw in [b" " * (32 * 1024 * 1024 + 1), b"[" * 33 + b"]" * 33]:
        assert json.loads(evaluate_json(raw))["problems"] == [
            {"pointer": "", "code": "RESOURCE_LIMIT"}
        ]


@pytest.mark.parametrize(
    "defect,reason",
    [
        ("empty", "EMPTY_SCOPE"),
        ("coverage", "INCOMPLETE_COVERAGE"),
        ("count", "COVERAGE_MISMATCH"),
        ("interval", "INVALID_INTERVAL"),
        ("entity", "MIXED_GRAIN"),
        ("status", "INVALID_FACT"),
        ("end", "INVALID_FACT"),
        ("direct", "INAPPLICABLE"),
        ("missing", "MISSING_FIELD"),
    ],
)
def test_reason_precedence(payload, defect, reason):
    value = copy.deepcopy(payload)
    scope, fact = value["scopes"][0], value["observations"][0]["fact"]
    if defect == "empty":
        value["observations"] = []
    if defect == "coverage":
        scope["expected_count"] = None
    if defect == "count":
        scope["expected_count"] = 2
    if defect == "interval":
        scope["end"] = scope["start"]
        fact["bidders"] = None
    if defect == "entity":
        fact["entity_id"] = "PE-RUC:20999999990"
        fact["bidders"] = None
    if defect == "status":
        fact["status"] = "cancelled"
        fact["bidders"] = None
    if defect == "end":
        fact["event_at"] = scope["end"]
    if defect == "direct":
        fact["method"] = "direct"
    if defect == "missing":
        fact["bidders"] = None
        scope["coverage"] = "partial"
    assert (
        json.loads(evaluate_json(json.dumps(value).encode()))["evaluations"][0][
            "reason_code"
        ]
        == reason
    )


@seed(20261015)
@settings(max_examples=1000, deadline=None)
@given(st.integers(-(10**25), 10**25), st.integers(1, 10**25))
def test_rational_oracle(numerator, denominator):
    actual = ratio(numerator, denominator)
    oracle = Fraction(numerator, denominator)
    assert (actual.numerator, actual.denominator) == (
        str(oracle.numerator),
        str(oracle.denominator),
    )


@seed(20261015)
@settings(max_examples=1000, deadline=None)
@given(st.integers(0, 10**20 - 1))
def test_money_oracle(value):
    text = f"{value // 100}.{value % 100:02}"
    assert cents(text) == value


def test_replay_subprocesses(payload):
    raw = json.dumps(payload).encode()
    code = "import sys;from cajamarca_qhaway.capabilities.deterministic_engine import evaluate_json;sys.stdout.buffer.write(evaluate_json(sys.stdin.buffer.read()))"
    outputs = []
    for timezone, hashseed in [
        ("UTC", "1"),
        ("America/Lima", "2"),
        ("Asia/Tokyo", "333"),
    ]:
        environment = {
            **os.environ,
            "TZ": timezone,
            "PYTHONHASHSEED": hashseed,
            "LC_ALL": "C",
        }
        outputs.append(
            subprocess.run(
                [sys.executable, "-c", code],
                input=raw,
                capture_output=True,
                env=environment,
                check=True,
            ).stdout
        )
    assert outputs == [evaluate_json(raw)] * 3


def test_pure_execution(payload, monkeypatch):
    import builtins
    import random
    import socket
    import time

    request = decode_request(json.dumps(payload).encode())

    def forbidden(*args, **kwargs):
        raise AssertionError("Efecto externo en el núcleo")

    with monkeypatch.context() as patch:
        patch.setattr(socket, "socket", forbidden)
        patch.setattr(time, "time", forbidden)
        patch.setattr(random, "random", forbidden)
        patch.setattr(builtins, "open", forbidden)
        patch.setattr(os, "getenv", forbidden)
        assert isinstance(evaluate(request), BatchResult)


def test_all_outputs_follow_schema(corpus):
    for vector in corpus:
        Draft202012Validator(RESULT_SCHEMA).validate(
            json.loads(evaluate_json(json.dumps(vector["input"]).encode()))
        )


def test_normalized_permutations(payload):
    request = decode_request(json.dumps(payload).encode())
    expected = evaluate(request)
    value = copy.deepcopy(payload)
    for _ in range(100):
        value["evidence"].reverse()
        value["observations"] = list(reversed(value["observations"])) + [
            value["observations"][0]
        ]
        actual = evaluate(decode_request(json.dumps(value).encode()))
        assert actual == expected
