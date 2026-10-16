"""Shadow reconstruye importes desde bytes y conserva historia privada."""

import copy
import json
from hashlib import sha256

import pytest

from cajamarca_qhaway.deterministic_cli import main
from cajamarca_qhaway.deterministic_shadow import (
    MigrationBlocked,
    exact_money,
    shadow_report,
)


def envelope_for(payload):
    value = copy.deepcopy(payload)
    raw = b'{"awards":[{"value":{"amount":900719925474099.91}}]}'
    value["evidence"][1]["payload_sha256"] = sha256(raw).hexdigest()
    coverage = b'{"coverage":"complete","expected_count":1}'
    value["evidence"][0]["payload_sha256"] = sha256(coverage).hexdigest()
    return {
        "mapping_version": "shadow-1",
        "request": value,
        "links": [
            {
                "legacy_id": "legacy-1",
                "scope_id": "scope-1",
                "record_key": "ocds-synthetic-1/award-1",
                "evidence_id": "evidence-1",
            }
        ],
        "money": [
            {
                "scope_id": "scope-1",
                "record_key": "ocds-synthetic-1/award-1",
                "source_id": "synthetic",
                "revision": 1,
                "field": "amount",
                "evidence_id": "evidence-1",
                "pointer": "/awards/0/value/amount",
            }
        ],
    }, {"evidence-1": raw, "coverage-1": coverage}


def test_shadow_migration_preserves_history(payload, fixture_dir):
    envelope, payloads = envelope_for(payload)
    history = copy.deepcopy(envelope)
    result = json.loads(shadow_report(envelope, payloads))
    from jsonschema import Draft202012Validator
    from referencing import Registry, Resource

    schemas = [
        json.loads(path.read_text(encoding="utf-8"))
        for path in (fixture_dir.parent / "contracts").glob("*.schema.json")
    ]
    registry = Registry().with_resources(
        (schema["$id"], Resource.from_contents(schema)) for schema in schemas
    )
    schema = next(
        schema for schema in schemas if schema["$id"].endswith("shadow-result-1")
    )
    Draft202012Validator(schema, registry=registry).validate(result)
    assert result["promotion"] == "disabled"
    assert result["result"]["kind"] == "BatchResult"
    assert envelope == history
    assert "approved" not in result and "published" not in result
    assert (
        exact_money(payloads["evidence-1"], "/awards/0/value/amount")
        == "900719925474099.91"
    )


@pytest.mark.parametrize("defect", ["money", "links", "hash", "duplicate", "approval"])
def test_shadow_blocks_unproven_mapping(payload, defect):
    envelope, payloads = envelope_for(payload)
    if defect == "money":
        envelope["money"] = []
    if defect == "links":
        envelope["links"][0]["record_key"] = "unrelated"
    if defect == "hash":
        payloads["evidence-1"] += b" "
    if defect == "duplicate":
        envelope["money"] *= 2
    if defect == "approval":
        envelope["published"] = True
    with pytest.raises(MigrationBlocked):
        shadow_report(envelope, payloads)


@pytest.mark.parametrize(
    "raw",
    [
        b'{"x":0.001}',
        b'{"x":true}',
        b'{"x":-1}',
        b'{"x":null}',
        b'{"x":NaN}',
        b'{"x":1,"x":2}',
    ],
)
def test_no_lossy_money(raw):
    with pytest.raises(MigrationBlocked):
        exact_money(raw, "/x")


def test_cli_exclusive_private_output(payload, tmp_path):
    source, target = tmp_path / "input.json", tmp_path / "private.json"
    source.write_text(json.dumps(payload))
    assert main([str(source), str(target)]) == 0
    old = target.read_bytes()
    assert main([str(source), str(target)]) == 2
    assert target.read_bytes() == old


def test_mef_shadow_master(corpus):
    envelope = {
        "mapping_version": "shadow-1",
        "request": copy.deepcopy(corpus[17]["input"]),
        "links": [],
        "money": [],
    }
    row = envelope["request"]["observations"][0]
    ref_id = row["evidence_ids"][0]
    raw = b'{"PIM":100.00,"DEVENGADO":50.00}'
    payloads = {ref_id: raw}
    for ref in envelope["request"]["evidence"]:
        ref["payload_sha256"] = sha256(payloads[ref["evidence_id"]]).hexdigest()
    envelope["links"] = [
        {
            "legacy_id": "legacy-budget",
            "scope_id": row["scope_id"],
            "record_key": row["record_key"],
            "evidence_id": ref_id,
        }
    ]
    envelope["money"] = [
        {
            "scope_id": row["scope_id"],
            "record_key": row["record_key"],
            "source_id": row["source_id"],
            "revision": row["revision"],
            "field": field,
            "evidence_id": ref_id,
            "pointer": pointer,
        }
        for field, pointer in (("pim", "/PIM"), ("devengado", "/DEVENGADO"))
    ]
    result = json.loads(shadow_report(envelope, payloads))["result"]
    assert result["evaluations"][0]["observed"] == {
        "numerator": "1",
        "denominator": "2",
    }
