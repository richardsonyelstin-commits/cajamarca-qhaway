"""Aceptación 011: replay."""


def test_canonical_replay_across_processes(
    engine, evaluate, payload, corpus, fixture_dir
):
    import json

    fixture = json.loads((fixture_dir / "full-result.json").read_text(encoding="utf-8"))
    assert evaluate(fixture["input"]) == fixture["output"]
