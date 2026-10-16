"""Repositorio privado de dossiers; nunca se incorpora al snapshot público."""

from __future__ import annotations

import json

from cajamarca_qhaway.models.case_analysis import ReviewCaseAnalysis
from cajamarca_qhaway.persistence.connection import DatabaseManager


class CaseAnalysisRepository:
    def __init__(self, database: DatabaseManager) -> None:
        self.database = database

    def save(self, value: ReviewCaseAnalysis) -> None:
        sql = '''INSERT INTO review_case_analyses
            (alert_id, entity_id, case_priority_score, priority_components, ai_copilot_analysis, generated_at)
            VALUES (?, ?, ?, ?, ?, ?) ON CONFLICT(alert_id) DO UPDATE SET
            case_priority_score=excluded.case_priority_score,
            priority_components=excluded.priority_components,
            ai_copilot_analysis=excluded.ai_copilot_analysis,
            generated_at=excluded.generated_at'''
        with self.database.connection() as connection:
            connection.cursor().execute(sql, (
                value.alert_id, value.entity_id, value.case_priority_score,
                value.priority_components.model_dump_json(), value.ai_copilot_analysis.model_dump_json(),
                value.generated_at.isoformat(),
            ))
            connection.commit()

    def list_in_review(self) -> list[ReviewCaseAnalysis]:
        with self.database.connection() as connection:
            cursor = connection.cursor()
            cursor.execute('''SELECT c.* FROM review_case_analyses c JOIN alerts a
                ON a.alert_id=c.alert_id AND a.entity_id=c.entity_id
                WHERE a.status='in_review' ORDER BY c.case_priority_score DESC, c.alert_id''')
            result = []
            for row in cursor.fetchall():
                value = dict(row)
                for field in ('priority_components', 'ai_copilot_analysis'):
                    if isinstance(value[field], str):
                        value[field] = json.loads(value[field])
                result.append(ReviewCaseAnalysis.model_validate(value))
            return result
