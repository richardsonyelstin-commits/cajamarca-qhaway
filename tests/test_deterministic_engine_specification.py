"""Compuertas del diseño propuesto; no certifican la implementación del motor futuro."""

from __future__ import annotations

import hashlib
import json
import operator
import re
from collections import Counter
from collections.abc import Iterator
from copy import deepcopy
from fractions import Fraction
from math import gcd
from pathlib import Path
from typing import Any

import pytest
import yaml
from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

ROOT = Path(__file__).resolve().parents[1]
DESIGN = ROOT / "specs" / "011-deterministic-engine"


def _schemas() -> dict[str, dict[str, Any]]:
    paths = sorted((DESIGN / "contracts").glob("*.schema.json"))
    assert paths, "El SDD debe entregar contratos JSON Schema ejecutables"
    return {path.name: json.loads(path.read_text(encoding="utf-8")) for path in paths}


def _registry(schemas: dict[str, dict[str, Any]]) -> Registry:
    return Registry().with_resources(
        (schema["$id"], Resource.from_contents(schema)) for schema in schemas.values()
    )


def _nodes(value: Any) -> Iterator[dict[str, Any]]:
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _nodes(child)
    elif isinstance(value, list):
        for child in value:
            yield from _nodes(child)


def _golden_vectors() -> list[dict[str, Any]]:
    document = json.loads((DESIGN / "fixtures" / "golden-vectors.json").read_text(encoding="utf-8"))
    assert document["synthetic"] is True
    assert document["verified"] is False
    vectors = document["vectors"]
    assert vectors, "Los contratos requieren ejemplos con resultados esperados"
    assert len({vector["id"] for vector in vectors}) == len(vectors)
    return vectors


def _validator(filename: str, fragment: str = "") -> Draft202012Validator:
    schemas = _schemas()
    schema = schemas[filename]
    return Draft202012Validator(
        {"$ref": schema["$id"] + fragment},
        registry=_registry(schemas),
        format_checker=FormatChecker(),
    )


def _full_fixture() -> dict[str, Any]:
    fixture = json.loads((DESIGN / "fixtures" / "full-result.json").read_text(encoding="utf-8"))
    assert fixture["synthetic"] is True
    assert fixture["verified"] is False
    return fixture


def _canonical(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False,
    ).encode("utf-8")


def _fraction(value: dict[str, str]) -> Fraction:
    return Fraction(int(value["numerator"]), int(value["denominator"]))


def test_design_has_complete_specification_and_test_plan() -> None:
    for filename in ("spec.md", "plan.md", "tasks.md", "test-plan.md"):
        path = DESIGN / filename
        assert path.is_file(), filename
        content = path.read_text(encoding="utf-8")
        assert content.startswith("---\n"), filename
        metadata = yaml.safe_load(content.split("---", 2)[1])
        assert metadata["source"] == "ai"
        assert metadata["verified"] is False
        assert metadata["generator"]
        assert metadata["generated_at"]
        assert re.findall(r"^# (.+)$", content, re.MULTILINE) == [metadata["title"]]
        assert "[NECESITA ACLARACIÓN" not in content, filename


def test_contracts_are_valid_versioned_and_resolve_without_network() -> None:
    schemas = _schemas()
    registry = _registry(schemas)
    ids = [schema["$id"] for schema in schemas.values()]
    assert len(ids) == len(set(ids)), "Los contratos deben tener identidades únicas"
    for filename, schema in schemas.items():
        assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema", filename
        Draft202012Validator.check_schema(schema)
        resolver = registry.resolver(base_uri=schema["$id"])
        for node in _nodes(schema):
            if "$ref" in node:
                resolver.lookup(node["$ref"])
        validator = Draft202012Validator(schema, registry=registry, format_checker=FormatChecker())
        assert validator.is_valid(None) is False, filename


def test_contract_objects_reject_undeclared_fields() -> None:
    for filename, schema in _schemas().items():
        for node in _nodes(schema):
            if node.get("type") == "object":
                assert (
                    node.get("additionalProperties") is False
                    or node.get("unevaluatedProperties") is False
                ), f"Objeto abierto en {filename}: {node.get('title', node.get('properties'))}"


def test_synthetic_golden_vectors_conform_to_request_and_expected_projection() -> None:
    request = _validator("request.schema.json")
    expected = _validator("result.schema.json", "#/$defs/GoldenProjection")
    for vector in _golden_vectors():
        request.validate(vector["input"])
        expected.validate(vector["expected"])
        assert vector["derivation"], vector["id"]
        requested = {
            (scope["scope_id"], rule)
            for scope in vector["input"]["scopes"]
            for rule in scope["rules"]
        }
        actual = [
            (row["scope_id"], row["rule_code"]) for row in vector["expected"]["evaluations"]
        ]
        assert set(actual) == requested, vector["id"]
        assert all(count == 1 for count in Counter(actual).values()), vector["id"]


def test_golden_fractions_are_reduced_and_states_do_not_invent_values() -> None:
    coverage: dict[str, set[str]] = {}
    for vector in _golden_vectors():
        for result in vector["expected"]["evaluations"]:
            coverage.setdefault(result["rule_code"], set()).add(result["state"])
            if result["state"] in ("INVALID", "NOT_EVALUABLE"):
                assert result["observed"] is result["threshold"] is None, vector["id"]
                continue
            for field in ("observed", "threshold"):
                ratio = result[field]
                numerator, denominator = int(ratio["numerator"]), int(ratio["denominator"])
                assert denominator > 0, vector["id"]
                assert gcd(abs(numerator), denominator) == 1, vector["id"]
                assert ratio["numerator"] == str(numerator), vector["id"]
    rules = _schemas()["request.schema.json"]["$defs"]["scope"]["properties"]["rules"]
    assert set(coverage) == set(rules["items"]["enum"])
    for rule, states in coverage.items():
        assert {"PASS", "SIGNAL", "NOT_EVALUABLE"} <= states, rule


@pytest.mark.parametrize("mutation", ["unknown-field", "utc-alias", "invalid-date", "version"])
def test_request_contract_rejects_ambiguous_or_unsupported_input(mutation: str) -> None:
    request = deepcopy(_golden_vectors()[0]["input"])
    if mutation == "unknown-field":
        request["undeclared"] = True
    elif mutation == "utc-alias":
        request["as_of"] = "2025-01-02T00:00:00+00:00"
    elif mutation == "invalid-date":
        request["as_of"] = "2025-02-30T00:00:00Z"
    else:
        request["policy_version"] = "unknown-policy"
    assert not _validator("request.schema.json").is_valid(request)


def test_full_result_fixture_conforms_to_output_contract() -> None:
    fixture = _full_fixture()
    _validator("request.schema.json").validate(fixture["input"])
    _validator("result.schema.json").validate(fixture["output"])


def test_canonical_vectors_match_independent_json_serialization_and_sha256() -> None:
    path = DESIGN / "fixtures" / "canonical-vectors.json"
    document = json.loads(path.read_text(encoding="utf-8"))
    assert document["synthetic"] is True
    assert len(document["vectors"]) >= 3
    for vector in document["vectors"]:
        encoded = _canonical(vector["value"])
        assert encoded == vector["canonical_utf8"].encode("utf-8"), vector["id"]
        assert hashlib.sha256(encoded).hexdigest() == vector["sha256"], vector["id"]


def test_full_fixture_hashes_match_documented_nonrecursive_preimages() -> None:
    fixture = _full_fixture()
    request, output = fixture["input"], fixture["output"]
    assert output["run_id"] == hashlib.sha256(b"qhaway-run-v2\n" + _canonical(request)).hexdigest()
    for evaluation in output["evaluations"]:
        body = {key: value for key, value in evaluation.items() if key != "result_id"}
        preimage = {"run_id": output["run_id"], "evaluation": body}
        assert evaluation["result_id"] == hashlib.sha256(
            b"qhaway-result-v2\n" + _canonical(preimage),
        ).hexdigest()


def test_golden_arithmetic_matches_independent_rational_oracles() -> None:
    thresholds = {
        "single-bidder": (Fraction(1), operator.eq),
        "contract-share": (Fraction(2, 5), operator.gt),
        "hhi": (Fraction(2500), operator.ge),
        "recurrent-direct": (Fraction(3), operator.ge),
        "budget-unspent": (Fraction(1, 2), operator.ge),
        "budget-above-pim": (Fraction(11, 10), operator.gt),
    }
    checked: set[str] = set()
    for vector in _golden_vectors():
        for result in vector["expected"]["evaluations"]:
            if result["state"] not in ("PASS", "SIGNAL"):
                continue
            facts = [
                observation["fact"] for observation in vector["input"]["observations"]
                if observation["scope_id"] == result["scope_id"] and not observation["deleted"]
            ]
            rule = result["rule_code"]
            if rule == "single-bidder":
                observed = Fraction(facts[0]["bidders"])
            elif rule in ("contract-share", "hhi"):
                shares: dict[str, Fraction] = {}
                for fact in facts:
                    supplier = fact["supplier_ruc"]
                    shares[supplier] = shares.get(supplier, Fraction(0)) + Fraction(fact["amount"])
                total = sum(shares.values(), Fraction(0))
                observed = (
                    max(shares.values()) / total if rule == "contract-share"
                    else 10000 * sum((value / total) ** 2 for value in shares.values())
                )
            elif rule == "recurrent-direct":
                direct: dict[str, set[str]] = {}
                for fact in facts:
                    if fact["method"] == "direct":
                        direct.setdefault(fact["supplier_ruc"], set()).add(fact["process_id"])
                process_count = max((len(processes) for processes in direct.values()), default=0)
                observed = Fraction(process_count)
            else:
                assert len(facts) == 1, vector["id"]
                pim, devengado = Fraction(facts[0]["pim"]), Fraction(facts[0]["devengado"])
                observed = (pim - devengado) / pim if rule == "budget-unspent" else devengado / pim
            threshold, compare = thresholds[rule]
            assert _fraction(result["observed"]) == observed, vector["id"]
            assert _fraction(result["threshold"]) == threshold, vector["id"]
            state = "SIGNAL" if compare(observed, threshold) else "PASS"
            assert result["state"] == state, vector["id"]
            checked.add(rule)
    assert checked == set(thresholds)


@pytest.mark.parametrize("value", [1.0, True, "1", "01.00", "1.0", "NaN", "-0.00"])
def test_money_contract_rejects_float_and_noncanonical_spelling(value: Any) -> None:
    facts = [
        observation["fact"]
        for vector in _golden_vectors()
        for observation in vector["input"]["observations"]
        if observation["fact"]["kind"] == "award"
    ]
    assert facts
    fact = deepcopy(facts[0])
    fact["amount"] = value
    assert not _validator("request.schema.json", "#/$defs/award").is_valid(fact)


@pytest.mark.parametrize(
    "mutation", ["unknown-field", "missing-value", "negative-zero", "zero-divisor"],
)
def test_result_contract_rejects_inconsistent_or_noncanonical_output(mutation: str) -> None:
    result = _full_fixture()["output"]
    evaluation = result["evaluations"][0]
    assert evaluation["state"] in ("PASS", "SIGNAL")
    if mutation == "unknown-field":
        evaluation["private_person_score"] = 99
    elif mutation == "missing-value":
        evaluation["observed"] = None
    elif mutation == "negative-zero":
        evaluation["observed"]["numerator"] = "-0"
    else:
        evaluation["observed"]["denominator"] = "0"
    assert not _validator("result.schema.json").is_valid(result)


def test_result_contract_forbids_observed_value_when_not_evaluable() -> None:
    result = _full_fixture()["output"]
    evaluation = result["evaluations"][0]
    evaluation["state"] = "NOT_EVALUABLE"
    evaluation["reason_code"] = "MISSING_FIELD"
    assert evaluation["observed"] is not None
    assert not _validator("result.schema.json").is_valid(result)


@pytest.mark.parametrize(
    ("vector_id", "state", "reason", "observed"),
    [
        ("same-source-same-revision-conflict", "INVALID", "CONFLICTING_REVISION", None),
        ("cross-source-disagreement", "INVALID", "SOURCE_DISAGREEMENT", None),
        ("selected-tombstone-empty", "NOT_EVALUABLE", "EMPTY_SCOPE", None),
        ("future-revision-excluded", "SIGNAL", "THRESHOLD_MATCH", 1),
        ("latest-eligible-revision", "PASS", "THRESHOLD_NOT_MATCH", 2),
        ("exact-observation-duplicate", "SIGNAL", "THRESHOLD_MATCH", 1),
    ],
)
def test_revision_vectors_have_valid_contracts_and_independent_examples(
    vector_id: str, state: str, reason: str, observed: int | None,
) -> None:
    path = DESIGN / "fixtures" / "selection-vectors.json"
    document = json.loads(path.read_text(encoding="utf-8"))
    assert document["synthetic"] is True
    assert len(document["vectors"]) == 6
    vector = next(row for row in document["vectors"] if row["id"] == vector_id)
    request = vector["input"]
    _validator("request.schema.json").validate(request)
    _validator("result.schema.json", "#/$defs/GoldenProjection").validate(vector["expected"])
    evaluation, = vector["expected"]["evaluations"]
    assert (evaluation["state"], evaluation["reason_code"]) == (state, reason)
    if observed is None:
        assert evaluation["observed"] is evaluation["threshold"] is None
    else:
        assert _fraction(evaluation["observed"]) == observed
        assert _fraction(evaluation["threshold"]) == 1
    observations = request["observations"]
    eligible = [
        row for row in observations
        if row["retrieved_at"] <= request["as_of"] and row["effective_at"] <= request["as_of"]
    ]
    if vector_id == "same-source-same-revision-conflict":
        identities = {(row["source_id"], row["record_key"], row["revision"]) for row in eligible}
        assert len(identities) == 1
        assert len({_canonical(row["fact"]) for row in eligible}) == 2
    elif vector_id == "cross-source-disagreement":
        assert len({row["source_id"] for row in eligible}) == 2
        assert len({row["record_key"] for row in eligible}) == 1
        assert len({_canonical(row["fact"]) for row in eligible}) == 2
    elif vector_id == "selected-tombstone-empty":
        assert max(eligible, key=lambda row: row["revision"])["deleted"] is True
    elif vector_id == "future-revision-excluded":
        assert len(eligible) < len(observations)
        assert max(eligible, key=lambda row: row["revision"])["fact"]["bidders"] == observed
    elif vector_id == "latest-eligible-revision":
        assert max(eligible, key=lambda row: row["revision"])["fact"]["bidders"] == observed
    else:
        assert len(observations) > len({_canonical(row) for row in observations})
        assert vector["identity_matches_full_fixture"] is True
        request["observations"] = list({ _canonical(row): row for row in observations }.values())
        assert request == _full_fixture()["input"]


def test_batch_invalid_example_has_no_partial_results_or_run_identity() -> None:
    path = DESIGN / "fixtures" / "invalid-result.json"
    document = json.loads(path.read_text(encoding="utf-8"))
    assert document["synthetic"] is True
    output = document["output"]
    _validator("result.schema.json").validate(output)
    assert output["kind"] == "BatchInvalid"
    assert "evaluations" not in output and "run_id" not in output
    assert output["problems"] == [
        {"pointer": "/scopes/0/unknown", "code": "SCHEMA_VIOLATION"},
    ]


def test_traceability_has_no_orphan_rules_acceptance_criteria_or_tasks() -> None:
    trace = json.loads((DESIGN / "traceability.json").read_text(encoding="utf-8"))
    spec = (DESIGN / "spec.md").read_text(encoding="utf-8")
    tasks = (DESIGN / "tasks.md").read_text(encoding="utf-8")
    rule_ids = set(re.findall(r"\*\*(RN-011-\d+)\.", spec))
    acceptance_ids = set(re.findall(r"\*\*(CA-011-\d+):", spec))
    rows = trace["rules"]
    assert len(rows) == len({row["rule_id"] for row in rows})
    assert {row["rule_id"] for row in rows} == rule_ids
    mapped_acceptance = {identifier for row in rows for identifier in row["acceptance_ids"]}
    assert mapped_acceptance == acceptance_ids
    for row in rows:
        assert row["acceptance_ids"] and row["task_ids"] and row["tests"], row["rule_id"]
        for task in row["task_ids"]:
            assert task in tasks, task
        for test in row["tests"]:
            assert re.fullmatch(r"test_[a-z0-9_]+", test["function"]), test
            assert test["file"].startswith("tests/"), test
            assert test["function"] in tasks, test


def test_new_architecture_decisions_are_proposals_with_real_alternatives() -> None:
    paths = sorted((ROOT / "docs" / "adr").glob("00[1][5-9]-*.md"))
    assert len(paths) >= 3, "El rediseño requiere decisiones arquitectónicas explícitas"
    for path in paths:
        content = path.read_text(encoding="utf-8")
        metadata = yaml.safe_load(content.split("---", 2)[1])
        assert metadata["status"] == "proposed", path.name
        assert metadata["verified"] is False, path.name
        assert len(re.findall(r"^### Opción [0-9]", content, re.MULTILINE)) >= 2, path.name
