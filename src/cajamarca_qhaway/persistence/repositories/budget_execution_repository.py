"""Repositorio para BudgetExecutionRecord en base de datos operativa (Pilar 2)."""

from __future__ import annotations

import json
from collections.abc import Sequence
from typing import Any

from cajamarca_qhaway.models import BudgetExecutionRecord
from cajamarca_qhaway.persistence.connection import DatabaseManager

JSON_COLUMNS = ("raw_payload", "breakdown_by_scope", "breakdown_by_funding_source", "comparison_cuts")
BUDGET_COLUMNS = tuple(BudgetExecutionRecord.model_fields)


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

        columns = ", ".join(BUDGET_COLUMNS)
        parameters = ", ".join("?" for _ in BUDGET_COLUMNS)
        updates = ", ".join(
            f"{column} = excluded.{column}" for column in BUDGET_COLUMNS
            if column not in ("execution_record_id", "entity_id", "fiscal_year")
        )
        sql = (
            f"INSERT INTO budget_execution_records ({columns}) VALUES ({parameters}) "
            f"ON CONFLICT (execution_record_id) DO UPDATE SET {updates}"
        )
        params = []
        for record in records:
            values = record.model_dump(mode="json")
            for column in JSON_COLUMNS:
                if values[column] is not None:
                    values[column] = json.dumps(values[column], ensure_ascii=False)
            params.append(tuple(values[column] for column in BUDGET_COLUMNS))

        with self.db.connection() as conn:
            cursor = conn.cursor()
            cursor.executemany(sql, params)
            conn.commit()
            return len(params)

    @staticmethod
    def _row_to_model(row: Any) -> BudgetExecutionRecord:
        values = {column: row[column] for column in BUDGET_COLUMNS}
        for column in JSON_COLUMNS:
            if isinstance(values[column], str):
                values[column] = json.loads(values[column])
        return BudgetExecutionRecord.model_validate(values)
