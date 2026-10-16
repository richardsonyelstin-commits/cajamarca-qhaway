"""Aceptación 011: scopes."""


def test_grain_and_denominator_no_double_count(engine, evaluate, payload, corpus):
    import copy

    vector = next(v for v in corpus if v["id"] == "share-positive")
    value = copy.deepcopy(vector["input"])
    value["scopes"][0]["expected_count"] += 1
    assert evaluate(value)["evaluations"][0]["reason_code"] == "COVERAGE_MISMATCH"
