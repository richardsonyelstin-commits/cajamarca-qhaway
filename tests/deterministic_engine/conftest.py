"""Corpus sintético independiente del motor bajo prueba."""

import importlib
import importlib.util
import json
from pathlib import Path

import pytest

FIXTURES = (
    Path(__file__).resolve().parents[2] / "specs/011-deterministic-engine/fixtures"
)


@pytest.fixture
def engine():
    name = "cajamarca_qhaway.capabilities.deterministic_engine"
    assert importlib.util.find_spec(name) is not None, "Falta implementar el núcleo 011"
    return importlib.import_module(name)


@pytest.fixture
def corpus():
    return json.loads((FIXTURES / "golden-vectors.json").read_text(encoding="utf-8"))[
        "vectors"
    ]


@pytest.fixture
def payload(corpus):
    return corpus[0]["input"]


@pytest.fixture
def evaluate(engine):
    def run(value):
        raw = json.dumps(value, ensure_ascii=False).encode("utf-8")
        return json.loads(engine.evaluate_json(raw))

    return run


@pytest.fixture
def fixture_dir():
    return FIXTURES
