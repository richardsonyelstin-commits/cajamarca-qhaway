"""Aceptación 011: states."""


def test_exactly_one_state_per_requested_rule(engine, evaluate, payload, corpus):
    for vector in corpus:
        actual = evaluate(vector["input"])
        assert len(actual["evaluations"]) == sum(
            len(s["rules"]) for s in vector["input"]["scopes"]
        )
        for row in actual["evaluations"]:
            assert (row["observed"] is None) == (
                row["state"] in {"INVALID", "NOT_EVALUABLE"}
            )
