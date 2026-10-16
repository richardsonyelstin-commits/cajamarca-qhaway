"""Aceptación 011: arithmetic."""


def test_exact_cents_and_fraction_boundaries(engine, evaluate, payload, corpus):
    assert engine.cents("9007199254740993.01") == 900719925474099301
    assert engine.ratio(4, 10).numerator == "2"
    assert engine.ratio(0, 10).denominator == "1"
    assert engine.ratio(-4, 10).numerator == "-2"
