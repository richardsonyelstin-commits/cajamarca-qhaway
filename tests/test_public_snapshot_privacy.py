"""La API publica expone solo contratos expresamente autorizados."""

from __future__ import annotations

import json

from cajamarca_qhaway.web import server


def test_public_snapshot_uses_positive_allowlist_and_redacts_private_counts(monkeypatch):
    snapshot = {
        "metadata": {
            "version": "1.0.0",
            "region": "CAJAMARCA",
            "total_alerts": 2,
            "total_candidate_red_flags": 2,
            "total_citizen_reports": 8,
            "alert_status_counts": {"published": 1, "in_review": 1},
            "private_review_queue": "NO-PUBLICAR",
        },
        "contracting_entities": [],
        "procurement_records": [],
        "budget_execution_records": [],
        "alerts": [
            {"alert_id": "publica", "status": "published", "red_flag_ids": ["publica"]},
            {"alert_id": "privada", "status": "in_review", "red_flag_ids": ["privada"]},
        ],
        "red_flags": [
            {"red_flag_id": "publica"},
            {"red_flag_id": "privada", "raw_text": "NO-PUBLICAR"},
        ],
        "citizen_reports": [{"raw_text": "NO-PUBLICAR", "identity": "NO-PUBLICAR"}],
        "review_case_analyses": [{"private_dossier": "NO-PUBLICAR"}],
        "unknown_sensitive_field": "NO-PUBLICAR",
    }
    monkeypatch.setattr(
        server.WebApiHandler, "get_snapshot", classmethod(lambda cls: snapshot)
    )

    code, _, body = server.WebApiHandler._dispatch_api_get("/api/snapshot", {})

    assert code == 200
    assert b"NO-PUBLICAR" not in body
    payload = json.loads(body)
    assert set(payload) == set(server.PUBLIC_SNAPSHOT_FIELDS) | {"citizen_reports", "metadata"}
    assert payload["citizen_reports"] == []
    assert [a["alert_id"] for a in payload["alerts"]] == ["publica"]
    assert [f["red_flag_id"] for f in payload["red_flags"]] == ["publica"]
    assert payload["metadata"]["total_alerts"] == 1
    assert payload["metadata"]["total_published_alerts"] == 1
    assert payload["metadata"]["total_candidate_red_flags"] == 1
    assert payload["metadata"]["total_citizen_reports"] == 0
    assert payload["metadata"]["alert_status_counts"] == {"published": 1}
    assert len(snapshot["citizen_reports"]) == 1  # No mutar el snapshot interno.
