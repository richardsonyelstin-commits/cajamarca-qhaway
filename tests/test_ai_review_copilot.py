from datetime import UTC, datetime

import pytest

from cajamarca_qhaway.models import Alert, AlertEvidence, RedFlag


def case_and_flag():
    now = datetime(2026, 10, 15, tzinfo=UTC)
    flag = RedFlag(red_flag_id='rf-evidence', indicator_code='single-bidder',
        formula_description='Postor único en competencia', threshold_value=1, observed_value=1,
        procurement_ids=['pr-evidence'], evidence_source='seace-ocds', retrieved_at=now, generated_at=now)
    alert = Alert(alert_id='al-case', entity_id='ce-case', red_flag_ids=[flag.red_flag_id], status='in_review',
        evidence=[AlertEvidence(red_flag_id=flag.red_flag_id, formula_description=flag.formula_description,
            threshold_value=1, observed_value=1, evidence_source=flag.evidence_source, retrieved_at=now)])
    return alert, flag


def test_offline_copilot_explains_missing_sources_and_never_decides() -> None:
    from cajamarca_qhaway.capabilities.review_panel.ai_copilot import AIReviewCopilot
    alert, flag = case_and_flag()
    result = AIReviewCopilot().analyze(alert, [flag], [], [])
    assert result.mode == 'deterministic'
    assert result.executive_summary and result.risk_hypothesis and result.legal_counter_hypothesis
    assert result.verification_checklist
    assert 'rf-evidence' in result.evidence_refs
    assert any('SUNAT' in item for item in result.limitations)
    assert alert.status == 'in_review' and alert.reviewed_by is None


def test_copilot_rejects_unrelated_flags_and_decided_cases() -> None:
    from cajamarca_qhaway.capabilities.review_panel.ai_copilot import AIReviewCopilot
    alert, flag = case_and_flag()
    with pytest.raises(ValueError):
        AIReviewCopilot().analyze(alert, [], [], [])
    with pytest.raises(ValueError):
        AIReviewCopilot().analyze(alert.model_copy(update={'status': 'published'}), [flag], [], [])


def test_structured_copilot_falls_back_on_invalid_evidence_references() -> None:
    from cajamarca_qhaway.capabilities.review_panel.ai_copilot import AIReviewCopilot
    alert, flag = case_and_flag()
    class UngroundedClient:
        def generate(self, payload, schema):
            return {'executive_summary': 'Acusación sin fuente', 'evidence_refs': ['invented']}
    result = AIReviewCopilot(structured_client=UngroundedClient()).analyze(alert, [flag], [], [])
    assert result.mode == 'deterministic'
    assert 'invented' not in result.evidence_refs


def test_private_case_repository_preserves_unsigned_review_state() -> None:
    from cajamarca_qhaway.persistence.connection import DatabaseManager
    from cajamarca_qhaway.persistence.config import DatabaseConfig
    from cajamarca_qhaway.persistence.repositories.alert_repository import AlertRepository
    from cajamarca_qhaway.persistence.repositories.case_analysis_repository import CaseAnalysisRepository
    from cajamarca_qhaway.capabilities.review_panel.ai_copilot import AIReviewCopilot, case_priority
    from cajamarca_qhaway.models.case_analysis import ReviewCaseAnalysis
    alert, flag = case_and_flag()
    db = DatabaseManager(DatabaseConfig(database_url=None))
    AlertRepository(db).save(alert)
    priority = case_priority([flag], [], [])
    analysis = AIReviewCopilot().analyze(alert, [flag], [], [])
    value = ReviewCaseAnalysis(alert_id=alert.alert_id, entity_id=alert.entity_id,
        case_priority_score=priority.score, priority_components=priority,
        ai_copilot_analysis=analysis, generated_at=analysis.generated_at)
    repository = CaseAnalysisRepository(db)
    repository.save(value)
    assert repository.list_in_review() == [value]
    assert AlertRepository(db).list_all()[0].reviewed_at is None
