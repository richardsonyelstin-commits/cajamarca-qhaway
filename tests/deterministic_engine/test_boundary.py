"""Aceptación 011: boundary."""


def test_closed_boundary_and_pure_execution(engine, evaluate, payload, corpus):
    value = {**payload, "unknown": "sensitive"}
    result = evaluate(value)
    assert result == {
        "schema_version": "engine-2",
        "kind": "BatchInvalid",
        "problems": [{"pointer": "/unknown", "code": "SCHEMA_VIOLATION"}],
    }
    assert b"sensitive" not in engine.evaluate_json(b'{"unknown":"sensitive"}')
    assert engine.evaluate_json(b'{"a":1,"a":2}') == engine.canonical_bytes(
        {
            "schema_version": "engine-2",
            "kind": "BatchInvalid",
            "problems": [{"pointer": "", "code": "DUPLICATE_JSON_KEY"}],
        }
    )
