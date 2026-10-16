"""Regresiones de integridad de la compuerta humana de publicacion."""

from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace

import pytest

pytestmark = pytest.mark.usefixtures("configured_test_veedor")

from cajamarca_qhaway.capabilities.review_panel import ReviewPanelService
from cajamarca_qhaway.models import RedFlag
from cajamarca_qhaway.web import server


@pytest.fixture
def review_context(monkeypatch):
    now = datetime.now(UTC)
    flag = RedFlag(
        red_flag_id="rf-review-persist",
        indicator_code="single-bidder",
        formula_description="Licitacion con unico postor",
        threshold=1,
        observed_value=1,
        procurement_ids=["p1"],
        evidence_source="seace-ocds",
        evidence_retrieved_at=now,
        generated_at=now,
    )
    service = ReviewPanelService()
    snapshot = {"alerts": []}
    monkeypatch.delenv("VERCEL", raising=False)
    monkeypatch.setattr(server.WebApiHandler, "review_service", service)
    monkeypatch.setattr(
        server.WebApiHandler, "get_snapshot", classmethod(lambda cls: snapshot)
    )
    monkeypatch.setattr(server, "_red_flag_repo", SimpleNamespace(get_by_id=lambda _id: flag))
    token = "synthetic-reviewer-token"
    data = {
        "entity_id": "ent-test",
        "red_flag_ids": [flag.red_flag_id],
        "status": "published",
        "review_notes": "Verificado con expediente oficial",
    }
    headers = {"authorization": f"Bearer {token}"}
    return service, snapshot, data, headers


@pytest.mark.parametrize("status", ["published", "discarded"])
def test_failed_decision_persistence_never_publishes(monkeypatch, review_context, status):
    service, snapshot, data, headers = review_context

    def fail_write(_alert):
        raise OSError("connection unavailable")

    monkeypatch.setattr(server, "_alert_repo", SimpleNamespace(save_decision=fail_write))
    code, _, body = server.WebApiHandler._dispatch_post_review(
        {**data, "status": status}, headers
    )

    assert code == 503
    assert service.list_alerts() == []
    assert snapshot["alerts"] == []
    assert b"connection unavailable" not in body


def test_decision_requires_durable_repository(monkeypatch, review_context):
    service, snapshot, data, headers = review_context
    monkeypatch.setattr(server, "_alert_repo", None)
    code, _, _ = server.WebApiHandler._dispatch_post_review(data, headers)
    assert code == 503
    assert service.list_alerts() == []
    assert snapshot["alerts"] == []


def test_duplicate_decision_conflict_does_not_overwrite(monkeypatch, review_context):
    service, snapshot, data, headers = review_context
    committed = []

    def insert_once(alert):
        if committed:
            raise ValueError("La alerta ya tiene una decision humana registrada")
        committed.append(alert)
        return alert

    monkeypatch.setattr(server, "_alert_repo", SimpleNamespace(save_decision=insert_once))
    code, _, _ = server.WebApiHandler._dispatch_post_review(data, headers)
    assert code == 201
    assert service.list_alerts("published") == committed
    assert len(snapshot["alerts"]) == 1

    code, _, _ = server.WebApiHandler._dispatch_post_review(
        {**data, "status": "discarded"}, headers
    )
    assert code == 409
    assert service.list_alerts("published") == committed
    assert len(snapshot["alerts"]) == 1
