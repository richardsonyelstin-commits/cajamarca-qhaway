import json
from datetime import UTC, datetime

import httpx

from cajamarca_qhaway.capabilities.review_panel.zero_cost_llm import ZeroCostLLMClient


def test_no_key_means_no_network_and_no_openai_support():
    client = ZeroCostLLMClient.from_environment({'OPENAI_API_KEY': 'not-permitted'})
    assert client is None


def test_free_router_is_pinned_and_rate_limit_returns_empty():
    requests = []
    def handle(request):
        requests.append(json.loads(request.content))
        return httpx.Response(429, json={'error': 'quota'})
    client = ZeroCostLLMClient.from_environment({'OPENROUTER_API_KEY': 'test-only'},
        transport=httpx.MockTransport(handle))
    assert client is not None
    assert client.generate({'evidence': []}, {}) == {}
    assert requests[0]['model'] == 'openrouter/free'
    assert len(requests) == 1


def test_paid_account_ambiguity_never_automatically_bills():
    for key in ('GEMINI_API_KEY', 'GROQ_API_KEY', 'HF_TOKEN'):
        assert ZeroCostLLMClient.from_environment({key: 'test-only'}) is None


def test_localhost_only_and_json_response():
    assert ZeroCostLLMClient.from_environment({'OLLAMA_BASE_URL': 'https://paid.example/v1'}) is None
    def handle(request):
        return httpx.Response(200, json={'choices': [{'message': {'content': '{"mode":"structured"}'}}]})
    client = ZeroCostLLMClient.from_environment({'OLLAMA_BASE_URL': 'http://localhost:11434/v1'},
        transport=httpx.MockTransport(handle))
    assert client is not None
    assert client.generate({}, {}) == {'mode': 'structured'}


def test_default_reasoner_is_local_and_graph_does_not_invent_sources():
    from test_ai_review_copilot import case_and_flag

    from cajamarca_qhaway.capabilities.review_panel.ai_copilot import (
        LocalForensicReasoner,
    )
    alert, flag = case_and_flag()
    result = LocalForensicReasoner().analyze(alert, [flag], [], [], now=datetime(2026, 10, 15, tzinfo=UTC))
    assert result.mode == 'deterministic'
    assert result.evidence_graph.nodes
    assert all(edge.source_id in {n.node_id for n in result.evidence_graph.nodes}
               and edge.target_id in {n.node_id for n in result.evidence_graph.nodes}
               for edge in result.evidence_graph.edges)
    assert '30225' in result.legal_counter_hypothesis and '32069' in result.legal_counter_hypothesis
    assert any('sin proceso' in item.lower() for item in result.limitations)


def test_private_case_endpoint_rejects_anonymous_access():
    from cajamarca_qhaway.web.server import WebApiHandler
    status, _, _ = WebApiHandler.dispatch('GET', '/api/review/cases', {})
    assert status == 401


def test_archived_signals_cannot_be_published_by_service():
    import pytest
    from test_ai_review_copilot import case_and_flag

    from cajamarca_qhaway.capabilities.review_panel.service import ReviewPanelService
    alert, flag = case_and_flag()
    with pytest.raises(ValueError, match='inactivas'):
        ReviewPanelService().publish_alert(alert.entity_id, [flag.model_copy(update={'is_active': False})],
            'revisor@civic.example', 'Revisión nominal documentada')
