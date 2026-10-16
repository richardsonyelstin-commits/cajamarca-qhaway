"""Revisiones nuevas, corroboración y múltiples ámbitos independientes."""

import copy


def test_newest_revision_and_corroboration(payload, evaluate):
    value = copy.deepcopy(payload)
    newer = copy.deepcopy(value["observations"][0])
    newer["revision"] = 2
    newer["fact"]["bidders"] = 2
    value["observations"].append(newer)
    assert evaluate(value)["evaluations"][0]["state"] == "PASS"
    value["observations"].reverse()
    assert evaluate(value)["evaluations"][0]["state"] == "PASS"
    ref = copy.deepcopy(value["evidence"][1])
    ref["evidence_id"] = "corroboration"
    value["evidence"].append(ref)
    corroboration = copy.deepcopy(newer)
    corroboration["evidence_ids"] = ["corroboration"]
    value["observations"].append(corroboration)
    assert evaluate(value)["evaluations"][0]["evidence_ids"] == [
        "corroboration",
        "coverage-1",
        "evidence-1",
    ]


def test_two_independent_scopes(payload, evaluate):
    value = copy.deepcopy(payload)
    scope = copy.deepcopy(value["scopes"][0])
    scope["scope_id"] = "scope-2"
    row = copy.deepcopy(value["observations"][0])
    row["scope_id"] = "scope-2"
    row["fact"]["bidders"] = 2
    value["scopes"].append(scope)
    value["observations"].append(row)
    assert [r["state"] for r in evaluate(value)["evaluations"]] == ["SIGNAL", "PASS"]


def test_payload_identity_not_numerical_truth(payload, evaluate):
    value = copy.deepcopy(payload)
    original = evaluate(value)
    value["evidence"][1]["payload_sha256"] = "a" * 64
    changed = evaluate(value)
    assert original["run_id"] != changed["run_id"]
    assert (
        original["evaluations"][0]["observed"] == changed["evaluations"][0]["observed"]
    )


def test_conflicting_bidders_in_same_process_invalidates_market(corpus, evaluate):
    value = copy.deepcopy(corpus[4]["input"])
    other = copy.deepcopy(value["observations"][0])
    other["record_key"] += "-lot"
    other["fact"]["bidders"] = value["observations"][0]["fact"]["bidders"] + 1
    value["observations"].append(other)
    value["scopes"][0]["expected_count"] += 1
    assert evaluate(value)["evaluations"][0]["reason_code"] == "INVALID_FACT"
