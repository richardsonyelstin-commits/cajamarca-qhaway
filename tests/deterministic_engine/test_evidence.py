"""Aceptación 011: evidence."""


def test_evidence_graph_and_explanation_complete(engine, evaluate, payload, corpus):
    import copy

    value = copy.deepcopy(payload)
    value["observations"][0]["evidence_ids"] = ["absent"]
    assert evaluate(value)["kind"] == "BatchInvalid"
    assert evaluate(value)["problems"][0]["code"] == "DANGLING_REFERENCE"


import pytest


@pytest.mark.parametrize(
    "defect,code",
    [
        ("duplicate-scope", "DUPLICATE_ID"),
        ("duplicate-evidence", "DUPLICATE_ID"),
        ("scope-trim", "SCHEMA_VIOLATION"),
        ("evidence-trim", "SCHEMA_VIOLATION"),
        ("kind-rule", "SCHEMA_VIOLATION"),
        ("missing-coverage", "DANGLING_REFERENCE"),
        ("future-coverage", "DANGLING_REFERENCE"),
        ("missing-scope", "DANGLING_REFERENCE"),
        ("wrong-source", "DANGLING_REFERENCE"),
        ("wrong-retrieval", "DANGLING_REFERENCE"),
        ("version", "UNSUPPORTED_VERSION"),
    ],
)
def test_graph_failures_are_global(payload, evaluate, defect, code):
    import copy

    value = copy.deepcopy(payload)
    if defect == "duplicate-scope":
        value["scopes"].append(copy.deepcopy(value["scopes"][0]))
    if defect == "duplicate-evidence":
        duplicate = copy.deepcopy(value["evidence"][1])
        duplicate["source_url"] += "-changed"
        value["evidence"].append(duplicate)
    if defect == "scope-trim":
        value["scopes"][0]["scope_id"] += " "
    if defect == "evidence-trim":
        value["evidence"][1]["evidence_id"] += " "
    if defect == "kind-rule":
        value["scopes"][0]["kind"] = "budget"
    if defect == "missing-coverage":
        value["scopes"][0]["coverage_evidence_id"] = "missing"
    if defect == "future-coverage":
        value["evidence"][0]["retrieved_at"] = "2027-01-01T00:00:00Z"
    if defect == "missing-scope":
        value["observations"][0]["scope_id"] = "missing"
    if defect == "wrong-source":
        value["evidence"][1]["source_id"] = "other-source"
    if defect == "wrong-retrieval":
        value["evidence"][1]["retrieved_at"] = "2026-01-03T00:00:00Z"
    if defect == "version":
        value["engine_version"] = "deterministic-3.0.0"
    result = evaluate(value)
    assert result["kind"] == "BatchInvalid"
    assert "evaluations" not in result
    assert any(problem["code"] == code for problem in result["problems"])
