"""Aceptación 011: policy."""


def test_finite_versioned_heuristic_catalog(engine, evaluate, payload, corpus):
    assert set(engine.POLICY) == {
        "single-bidder",
        "contract-share",
        "hhi",
        "recurrent-direct",
        "budget-unspent",
        "budget-above-pim",
    }
    result = evaluate({**payload, "policy_version": "invented"})
    assert result["kind"] == "BatchInvalid"
    assert result["problems"] == [
        {"pointer": "/policy_version", "code": "UNSUPPORTED_VERSION"}
    ]
