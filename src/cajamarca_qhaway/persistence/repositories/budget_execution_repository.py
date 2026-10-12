"""Repositorio para BudgetExecutionRecord en base de datos operativa (Pilar 2)."""

from __future__ import annotations

import json
from collections.abc import Sequence
from datetime import datetime, timezone
from typing import Any

from cajamarca_qhaway.models import BudgetExecutionRecord
from cajamarca_qhaway.persistence.connection import DatabaseManager


class BudgetExecutionRepository:
    """Repositorio tipado para registros de ejecucion presupuestal MEF."""

    def __init__(self, db_manager: DatabaseManager) -> None:
        self.db = db_manager

    def get_by_id(self, execution_record_id: str) -> BudgetExecutionRecord | None:
        sql = "SELECT * FROM budget_execution_records WHERE execution_record_id = ?"
        with self.db.connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (execution_record_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return self._row_to_model(row)

    def list_by_entity_year(self, entity_id: str, fiscal_year: int) -> list[BudgetExecutionRecord]:
        sql = "SELECT * FROM budget_execution_records WHERE entity_id = ? AND fiscal_year = ?"
        with self.db.connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (entity_id, fiscal_year))
            rows = cursor.fetchall()
            return [self._row_to_model(r) for r in rows]

    def count(self) -> int:
        sql = "SELECT count(*) as cnt FROM budget_execution_records"
        with self.db.connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql)
            row = cursor.fetchone()
            return int(row["cnt"]) if row else 0

    def upsert_many(self, records: Sequence[BudgetExecutionRecord]) -> int:
        if not records:
            return 0

        sql = """
        INSERT INTO budget_execution_records
            (execution_record_id, entity_id, fiscal_year, budgeted_amount, executed_amount,
             budget_category, raw_payload, source, retrieved_at)
        VALUES
            (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT (execution_record_id) DO UPDATE SET
            budgeted_amount = excluded.budgeted_amount,
            executed_amount = excluded.executed_amount,
            budget_category = excluded.budget_category,
            raw_payload = excluded.raw_payload,
            retrieved_at = excluded.retrieved_at
        """

        params = [
            (
                r.execution_record_id,
                r.entity_id,
                r.fiscal_year,
                r.budgeted_amount,
                r.executed_amount,
                r.budget_category,
                json.dumps(r.raw_payload, ensure_ascii=False) if isinstance(r.raw_payload, dict) else str(r.raw_payload),
                r.source,
                r.retrieved_at.isoformat(),
            )
            for r in records
        ]

        with self.db.connection() as conn:
            cursor = conn.cursor()
            cursor.executemany(sql, params)
            conn.commit()
            return len(params)

    @staticmethod
    def _row_to_model(row: Any) -> BudgetExecutionRecord:
        raw_payload = row["raw_payload"]
        if isinstance(raw_payload, str):
            try:
                raw_payload = json.loads(raw_payload)
            except json.JSONDecodeError:
                raw_payload = {}

        retrieved_at = row["retrieved_at"]
        if isinstance(retrieved_at, str):
            retrieved_at = datetime.fromisoformat(retrieved_at)
        if retrieved_at.tzinfo is None:
            retrieved_at = retrieved_at.replace(tzinfo=timezone.utc)

        return BudgetExecutionRecord(
            execution_record_id=row["execution_record_id"],
            entity_id=row["entity_id"],
            fiscal_year=row["fiscal_year"],
            budgeted_amount=row["budgeted_amount"],
            executed_amount=row["executed_amount"],
            budget_category=row["budget_category"],
            raw_payload=raw_payload,
            source=row["source"],
            retrieved_at=retrieved_at,
        )
