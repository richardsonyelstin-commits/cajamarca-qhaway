"""Aceptación 011: revisions."""


def test_revision_selection_and_source_conflicts(
    engine, evaluate, payload, corpus, fixture_dir
):
    import json

    vectors = json.loads(
        (fixture_dir / "selection-vectors.json").read_text(encoding="utf-8")
    )["vectors"]
    for vector in vectors:
        result = evaluate(vector["input"])
        assert result["kind"] == "BatchResult", vector["id"]
        for actual, expected in zip(
            result["evaluations"], vector["expected"]["evaluations"], strict=True
        ):
            assert {key: actual[key] for key in expected} == expected, vector["id"]
