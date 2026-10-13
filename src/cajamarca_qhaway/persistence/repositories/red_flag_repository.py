"""Repositorio para RedFlag en base de datos operativa (Pilar 2)."""

from __future__ import annotations

import json
from collections.abc import Sequence
from datetime import datetime, timezone
from typing import Any

from cajamarca_qhaway.models import RedFlag
from cajamarca_qhaway.persistence.connection import DatabaseManager


class RedFlagRepository:
    """Repositorio tipado para candidatos de bandera roja (CA-004-06: sin campo status)."""

    def __init__(self, db_manager: DatabaseManager) -> None:
        self.db = db_manager

    def get_by_id(self, red_flag_id: str) -> RedFlag | None:
        sql = "SELECT * FROM red_flags WHERE red_flag_id = ?"
        with self.db.connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (red_flag_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return self._row_to_model(row)

    def list_all(self) -> list[RedFlag]:
        sql = "SELECT * FROM red_flags ORDER BY generated_at DESC"
        with self.db.connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql)
            rows = cursor.fetchall()
            return [self._row_to_model(r) for r in rows]

    def insert_candidates(self, flags: Sequence[RedFlag]) -> int:
        if not flags:
            return 0

        sql = """
        INSERT INTO red_flags
            (red_flag_id, indicator_code, formula_description, threshold, threshold_value, observed_value,
             procurement_ids, execution_record_ids, evidence_source, evidence_retrieved_at,
             retrieved_at, generated_at)
        VALUES
            (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT (red_flag_id) DO NOTHING
        """

        params = [
            (
                f.red_flag_id,
                f.indicator_code,
                f.formula_description,
                f.threshold,
                str(f.threshold_value),
                f.observed_value,
                json.dumps(list(f.procurement_ids)),
                json.dumps(list(f.execution_record_ids)),
                f.evidence_source,
                f.evidence_retrieved_at.isoformat(),
                f.retrieved_at.isoformat(),
                f.generated_at.isoformat(),
            )
            for f in flags
        ]

        with self.db.connection() as conn:
            cursor = conn.cursor()
            cursor.executemany(sql, params)
            conn.commit()
            return len(params)

    @staticmethod
    def _row_to_model(row: Any) -> RedFlag:
        procurement_ids = row["procurement_ids"]
        if isinstance(procurement_ids, str):
            try:
                procurement_ids = tuple(json.loads(procurement_ids))
            except json.JSONDecodeError:
                procurement_ids = ()

        execution_record_ids = row["execution_record_ids"]
        if isinstance(execution_record_ids, str):
            try:
                execution_record_ids = tuple(json.loads(execution_record_ids))
            except json.JSONDecodeError:
                execution_record_ids = ()

        retrieved_at = row["retrieved_at"]
        if isinstance(retrieved_at, str):
            retrieved_at = datetime.fromisoformat(retrieved_at)
        if retrieved_at.tzinfo is None:
            retrieved_at = retrieved_at.replace(tzinfo=timezone.utc)

        generated_at = row["generated_at"]
        if isinstance(generated_at, str):
            generated_at = datetime.fromisoformat(generated_at)
        if generated_at.tzinfo is None:
            generated_at = generated_at.replace(tzinfo=timezone.utc)

        return RedFlag(
            red_flag_id=row["red_flag_id"],
            indicator_code=row["indicator_code"],
            formula_description=row["formula_description"],
            threshold_value=row["threshold_value"],
            observed_value=row["observed_value"],
            procurement_ids=procurement_ids,
            execution_record_ids=execution_record_ids,
            evidence_source=row["evidence_source"],
            retrieved_at=retrieved_at,
            generated_at=generated_at,
        )
