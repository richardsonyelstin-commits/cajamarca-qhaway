"""Oráculos independientes del indicador hhi."""


def test_hhi_golden_boundaries(evaluate, corpus):
    for vector in corpus:
        if vector["expected"]["evaluations"][0]["rule_code"] != "hhi":
            continue
        result = evaluate(vector["input"])
        assert result["kind"] == "BatchResult", vector["id"]
        for actual, expected in zip(
            result["evaluations"], vector["expected"]["evaluations"], strict=True
        ):
            assert {key: actual[key] for key in expected} == expected, vector["id"]
