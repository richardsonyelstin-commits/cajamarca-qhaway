"""Regressions for failed writes, private cache and malformed request boundaries."""
from __future__ import annotations

import copy
import io
import json
from datetime import UTC, datetime

import pytest

from cajamarca_qhaway.capabilities.denuncia_intake import DenunciaIntakeService
from cajamarca_qhaway.capabilities.review_panel import ReviewPanelService
from cajamarca_qhaway.models import RedFlag
from cajamarca_qhaway.persistence.config import DatabaseConfig
from cajamarca_qhaway.persistence.connection import DatabaseManager
from cajamarca_qhaway.persistence.repositories import (
    AlertRepository,
    CitizenReportRepository,
    RedFlagRepository,
)
from cajamarca_qhaway.web import server

SESSION = {"veedor": {"email": "reviewer@example.test", "name": "Synthetic Reviewer",
                     "organization": "Synthetic Team", "role": "reviewer"}, "expiresAt": 9999999999999}
AUTH = {"authorization": "Bearer synthetic-token"}


@pytest.fixture
def isolated(monkeypatch):
    for name in ("VERCEL", "CAJAMARCA_QHAWAY_DATABASE_URL", "CAJAMARCA_QHAWAY_ENV", "ENVIRONMENT"):
        monkeypatch.delenv(name, raising=False)
    db = DatabaseManager(DatabaseConfig(database_url=None, session_pooler_host=None))
    reports, alerts, flags = CitizenReportRepository(db), AlertRepository(db), RedFlagRepository(db)
    monkeypatch.setattr(server, "_db_manager", db)
    monkeypatch.setattr(server, "_report_repo", reports)
    monkeypatch.setattr(server, "_alert_repo", alerts)
    monkeypatch.setattr(server, "_red_flag_repo", flags)
    monkeypatch.setattr(server, "_verify_veedor_token", lambda token: SESSION if token == "synthetic-token" else None)
    snapshot = {"alerts": [], "citizen_reports": [], "red_flags": [], "metadata": {}}
    monkeypatch.setattr(server.WebApiHandler, "get_snapshot", classmethod(lambda cls: snapshot))
    monkeypatch.setattr(server.WebApiHandler, "denuncia_service", DenunciaIntakeService())
    monkeypatch.setattr(server.WebApiHandler, "review_service", ReviewPanelService())
    return db, reports, alerts, flags, snapshot


def dispatch(method, path, data=None, query=None, headers=None):
    status, _, body = server.WebApiHandler.dispatch(
        method, path, query or {}, json.dumps(data).encode() if data is not None else b"", headers,
    )
    return status, json.loads(body)


def wsgi(app, path, *, query="", token=None, method="GET", body=b""):
    captured = {}
    environ = {"REQUEST_METHOD": method, "PATH_INFO": path, "QUERY_STRING": query,
               "CONTENT_LENGTH": str(len(body)), "wsgi.input": io.BytesIO(body)}
    if token:
        environ["HTTP_AUTHORIZATION"] = "Bearer " + token
    def start(status, headers):
        captured.update(status=int(status.split()[0]), headers=dict(headers))
    response = b"".join(app(environ, start))
    return captured["status"], captured["headers"], response


@pytest.mark.parametrize("path", ["/api/auth/login", "/api/reports", "/api/review", "/api/reports/moderate"])
@pytest.mark.parametrize("payload", [[], 1, "text", None, True])
def test_json_non_objects_are_400_at_all_entrypoints(path, payload):
    from api import index
    body = json.dumps(payload).encode()
    for app in (server.app, index.app):
        status, _, _ = wsgi(app, path, method="POST", body=body)
        assert status == 400
    assert index._stdlib_fallback_dispatch("POST", path, {}, body=body)[0] == 400


@pytest.mark.parametrize("path", ["/api/reports", "/api/reports/track", "/api/review/queue", "/api/auth/session"])
@pytest.mark.parametrize("rewrite", [False, True])
def test_private_routes_never_advertise_shared_cache(isolated, path, rewrite):
    from api import index
    target = "/api/index.py" if rewrite else path
    query = "__path=" + path if rewrite else ""
    for app in (server.app, index.app):
        _, headers, _ = wsgi(app, target, query=query, token="synthetic-token")
        assert headers["Cache-Control"] == "private, no-store"
        assert "Authorization" in headers["Vary"]


def test_authorization_disables_cache_even_on_public_routes(isolated):
    status, headers, _ = wsgi(server.app, "/api/health", token="synthetic-token")
    assert status == 200
    assert headers["Cache-Control"] == "private, no-store"


@pytest.mark.parametrize("variable", ["VERCEL", "CAJAMARCA_QHAWAY_ENV", "ENVIRONMENT"])
def test_production_never_acknowledges_memory_reports(isolated, monkeypatch, variable):
    monkeypatch.setenv(variable, "1" if variable == "VERCEL" else "production")
    status, _ = dispatch("POST", "/api/reports", {"raw_text": "synthetic report", "legal_disclaimer_shown": True})
    assert status == 503
    assert isolated[1].list_page() == []
    assert server.WebApiHandler.denuncia_service.list_reports() == []
    assert isolated[4]["citizen_reports"] == []


def test_failed_report_save_leaves_no_confirmation_or_in_memory_report(isolated, monkeypatch):
    def failed(_):
        raise RuntimeError("synthetic write failure")
    monkeypatch.setattr(isolated[1], "save", failed)
    status, result = dispatch("POST", "/api/reports", {"raw_text": "synthetic", "legal_disclaimer_shown": True})
    assert status == 503
    assert "tracking_token" not in result
    assert server.WebApiHandler.denuncia_service.list_reports() == []
    assert isolated[4]["citizen_reports"] == []


def test_private_report_queue_survives_snapshot_refresh_and_paginates(isolated):
    for text in ("first", "second", "third"):
        assert dispatch("POST", "/api/reports", {"raw_text": text, "legal_disclaimer_shown": True})[0] == 201
    isolated[4].clear()
    status, first = dispatch("GET", "/api/reports", query={"limit": ["2"]}, headers=AUTH)
    assert status == 200 and len(first) == 2
    status, second = dispatch("GET", "/api/reports", query={"limit": ["2"], "offset": ["2"]}, headers=AUTH)
    assert status == 200 and len(second) == 1
    assert {row["report_id"] for row in first}.isdisjoint(row["report_id"] for row in second)
    assert dispatch("GET", "/api/reports", query={"limit": ["0"]}, headers=AUTH)[0] == 400
    assert dispatch("GET", "/api/reports", query={"status": ["rejected"]}, headers=AUTH) == (200, [])
    assert "citizen_reports" not in isolated[4]


def test_review_failure_and_retry_are_atomic_idempotent_and_conflicts_rejected(isolated, monkeypatch):
    flag = RedFlag(red_flag_id="rf-synthetic", indicator_code="single-bidder", formula_description="One bidder",
                   threshold=1, observed_value=1, procurement_ids=["pr-synthetic"],
                   evidence_source="seace-ocds", evidence_retrieved_at=datetime.now(UTC), generated_at=datetime.now(UTC))
    monkeypatch.setattr(isolated[3], "get_by_id", lambda _: flag)
    payload = {"entity_id": "ce-synthetic", "red_flag_ids": [flag.red_flag_id], "status": "published", "review_notes": "Synthetic evidence checked"}
    original = isolated[2].save_decision
    def failed(_):
        raise RuntimeError("synthetic write failure")
    monkeypatch.setattr(isolated[2], "save_decision", failed)
    assert dispatch("POST", "/api/review", payload, headers=AUTH)[0] == 503
    assert isolated[4]["alerts"] == []
    assert server.WebApiHandler.review_service.list_alerts() == []
    monkeypatch.setattr(isolated[2], "save_decision", original)
    status, committed = dispatch("POST", "/api/review", payload, headers=AUTH)
    assert status == 201
    assert dispatch("POST", "/api/review", payload, headers=AUTH) == (201, committed)
    assert len(isolated[4]["alerts"]) == len(isolated[2].list_published()) == 1
    assert dispatch("POST", "/api/review", {**payload, "status": "discarded"}, headers=AUTH)[0] == 409
    assert isolated[2].list_published()[0].alert_id == committed["alert_id"]


def test_moderation_failure_preserves_pending_state_and_nominal_identity(isolated, monkeypatch):
    _, created = dispatch("POST", "/api/reports", {"raw_text": "synthetic", "legal_disclaimer_shown": True})
    report_id = created["report_id"]
    original = isolated[1].moderate_pending
    before = copy.deepcopy(server.WebApiHandler.denuncia_service.get_report(report_id))
    def failed(_):
        raise RuntimeError("synthetic write failure")
    monkeypatch.setattr(isolated[1], "moderate_pending", failed)
    payload = {"report_id": report_id, "status": "accepted_as_lead", "moderated_by": "Impersonated Person"}
    assert dispatch("POST", "/api/reports/moderate", payload, headers=AUTH)[0] == 400
    payload.pop("moderated_by")
    assert dispatch("POST", "/api/reports/moderate", payload, headers=AUTH)[0] == 503
    assert server.WebApiHandler.denuncia_service.get_report(report_id) == before
    assert isolated[1].get_by_id(report_id).moderation_status == "pending"
    monkeypatch.setattr(isolated[1], "moderate_pending", original)
    status, result = dispatch("POST", "/api/reports/moderate", payload, headers=AUTH)
    assert status == 200
    assert result["moderated_by"] == "Synthetic Reviewer (Synthetic Team)"


@pytest.mark.parametrize("path", ["/src/js/absent.js", "/unknown-page", "/absent.html"])
def test_missing_resources_are_404_at_both_entrypoints(path):
    from api import index
    assert server.WebApiHandler._resolve_static(path)[0] == 404
    assert index._stdlib_fallback_dispatch("GET", path, {})[0] == 404
    assert wsgi(index.app, path)[0] == 404


def test_unavailable_auth_is_distinct_from_absent_token(monkeypatch):
    from cajamarca_qhaway.web.auth import AuthUnavailable
    def unavailable(_):
        raise AuthUnavailable("synthetic outage")
    monkeypatch.setattr(server, "_verify_veedor_token", unavailable)
    assert dispatch("GET", "/api/reports")[0] == 401
    assert dispatch("GET", "/api/reports", headers=AUTH)[0] == 503


def test_publication_recovers_after_snapshot_rebuild_and_new_handler(isolated, monkeypatch):
    from cajamarca_qhaway.models import Alert
    db, _, alerts, flags, snapshot = isolated
    published_flag = RedFlag(
        red_flag_id="rf-published", indicator_code="single-bidder", formula_description="One bidder",
        threshold=1, observed_value=1, procurement_ids=["pr-published"], evidence_source="seace-ocds",
        evidence_retrieved_at=datetime.now(UTC), generated_at=datetime.now(UTC),
    )
    discarded_flag = published_flag.model_copy(update={"red_flag_id": "rf-discarded"})
    private_flag = published_flag.model_copy(update={"red_flag_id": "rf-private"})
    flags.insert_candidates([published_flag, discarded_flag, private_flag])
    payload = {"entity_id": "ce-synthetic", "red_flag_ids": [published_flag.red_flag_id],
               "status": "published", "review_notes": "Synthetic evidence checked"}
    assert dispatch("POST", "/api/review", payload, headers=AUTH)[0] == 201
    discarded = ReviewPanelService().discard_alert(
        entity_id="ce-synthetic", red_flags=[discarded_flag], reviewer_id="Synthetic Reviewer",
        review_notes="Synthetic discarded candidate",
    )
    alerts.save_decision(discarded)
    # Deliberately stale public snapshot must not resurrect a committed discard.
    stale_published = Alert.model_validate({
        **discarded.model_dump(mode="json"), "status": "published",
        "published_at": discarded.reviewed_at,
    }).model_dump(mode="json")
    snapshot.clear()
    snapshot.update(alerts=[stale_published], red_flags=[private_flag.model_dump(mode="json")],
                    citizen_reports=[{"raw_text": "private synthetic report"}], metadata={})
    fresh_snapshot = copy.deepcopy(snapshot)
    class FreshWorker(server.WebApiHandler):
        review_service = ReviewPanelService()
        snapshot_cache = None
        @classmethod
        def get_snapshot(cls):
            return copy.deepcopy(fresh_snapshot)
    # Independent repository objects share confirmed storage, not handler memory.
    monkeypatch.setattr(server, "_alert_repo", AlertRepository(db))
    monkeypatch.setattr(server, "_red_flag_repo", RedFlagRepository(db))
    for handler in (server.WebApiHandler, FreshWorker):
        public_alerts = json.loads(handler.dispatch("GET", "/api/alerts", {})[2])
        public_flags = json.loads(handler.dispatch("GET", "/api/red-flags", {})[2])
        public_snapshot = json.loads(handler.dispatch("GET", "/api/snapshot", {})[2])
        assert len(public_alerts) == 1
        assert public_alerts[0]["red_flag_ids"] == [published_flag.red_flag_id]
        assert [row["red_flag_id"] for row in public_flags] == [published_flag.red_flag_id]
        assert public_snapshot["alerts"] == public_alerts
        assert public_snapshot["red_flags"] == public_flags
        assert public_snapshot["citizen_reports"] == []
        assert public_snapshot["metadata"]["total_published_alerts"] == 1


def test_public_snapshot_fallback_remains_filtered_when_database_unavailable(isolated, monkeypatch):
    snapshot = isolated[4]
    snapshot.update(alerts=[{"alert_id": "confirmed-snapshot", "status": "published", "red_flag_ids": ["rf-visible"]},
                            {"alert_id": "private-discard", "status": "discarded", "red_flag_ids": ["rf-private"]}],
                    red_flags=[{"red_flag_id": "rf-visible"}, {"red_flag_id": "rf-private"}],
                    citizen_reports=[{"raw_text": "private"}])
    def unavailable():
        raise RuntimeError("synthetic database outage")
    monkeypatch.setattr(isolated[2], "list_published", unavailable)
    status, result = dispatch("GET", "/api/snapshot")
    assert status == 200
    assert [row["alert_id"] for row in result["alerts"]] == ["confirmed-snapshot"]
    assert result["red_flags"] == [{"red_flag_id": "rf-visible"}]
    assert result["citizen_reports"] == []


def test_authoritative_empty_repository_does_not_resurrect_snapshot(isolated, monkeypatch):
    monkeypatch.setattr(isolated[0], "_is_postgres", True)
    isolated[4]["alerts"] = [{"alert_id": "stale", "status": "published", "red_flag_ids": ["rf-stale"]}]
    isolated[4]["red_flags"] = [{"red_flag_id": "rf-stale"}]
    assert dispatch("GET", "/api/alerts") == (200, [])
    assert dispatch("GET", "/api/red-flags") == (200, [])


@pytest.mark.parametrize("path", ["/api/alerts", "/api/red-flags", "/api/snapshot"])
def test_authoritative_database_outage_never_falls_back_to_stale_decision(isolated, monkeypatch, path):
    monkeypatch.setattr(isolated[0], "_is_postgres", True)
    isolated[4]["alerts"] = [{"alert_id": "stale", "status": "published", "red_flag_ids": ["rf-stale"]}]
    def unavailable():
        raise RuntimeError("synthetic authoritative database outage")
    monkeypatch.setattr(isolated[2], "list_published", unavailable)
    status, result = dispatch("GET", path)
    assert status == 503
    assert "stale" not in json.dumps(result)
