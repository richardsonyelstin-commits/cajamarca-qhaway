"""Repositorio para ProcurementRecord en base de datos operativa (Pilar 2)."""

from __future__ import annotations

import json
from collections.abc import Sequence
from datetime import datetime, timezone
from typing import Any

from cajamarca_qhaway.models import ProcurementRecord
from cajamarca_qhaway.persistence.connection import DatabaseManager


class ProcurementRepository:
    """Repositorio tipado para registros de contratacion publica SEACE/OCDS."""

    def __init__(self, db_manager: DatabaseManager) -> None:
        self.db = db_manager

    def get_by_id(self, procurement_id: str) -> ProcurementRecord | None:
        sql = "SELECT * FROM procurement_records WHERE procurement_id = ?"
        with self.db.connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (procurement_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return self._row_to_model(row)

    def get_by_ocid(self, ocid: str) -> ProcurementRecord | None:
        sql = "SELECT * FROM procurement_records WHERE ocid = ?"
        with self.db.connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (ocid,))
            row = cursor.fetchone()
            if not row:
                return None
            return self._row_to_model(row)

    def list_by_entity(self, entity_id: str) -> list[ProcurementRecord]:
        sql = "SELECT * FROM procurement_records WHERE entity_id = ?"
        with self.db.connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (entity_id,))
            rows = cursor.fetchall()
            return [self._row_to_model(r) for r in rows]

    def count(self) -> int:
        sql = "SELECT count(*) as cnt FROM procurement_records"
        with self.db.connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql)
            row = cursor.fetchone()
            return int(row["cnt"]) if row else 0

    def upsert_many(self, records: Sequence[ProcurementRecord]) -> int:
        if not records:
            return 0

        sql = """
        INSERT INTO procurement_records
            (procurement_id, ocid, entity_id, title, procurement_method, awarded_amount,
             executed_amount, number_of_bidders, supplier_name, supplier_ruc, raw_payload,
             source, retrieved_at)
        VALUES
            (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT (procurement_id) DO UPDATE SET
            awarded_amount = excluded.awarded_amount,
            executed_amount = excluded.executed_amount,
            number_of_bidders = excluded.number_of_bidders,
            supplier_name = excluded.supplier_name,
            supplier_ruc = excluded.supplier_ruc,
            raw_payload = excluded.raw_payload,
            retrieved_at = excluded.retrieved_at
        """

        params = [
            (
                r.procurement_id,
                r.ocid,
                r.entity_id,
                r.title,
                r.procurement_method,
                r.awarded_amount,
                r.executed_amount,
                r.number_of_bidders,
                r.supplier_name,
                r.supplier_ruc,
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
    def _row_to_model(row: Any) -> ProcurementRecord:
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

        return ProcurementRecord(
            procurement_id=row["procurement_id"],
            ocid=row["ocid"],
            entity_id=row["entity_id"],
            title=row["title"],
            procurement_method=row["procurement_method"],
            awarded_amount=row["awarded_amount"],
            executed_amount=row["executed_amount"],
            number_of_bidders=row["number_of_bidders"],
            supplier_name=row["supplier_name"],
            supplier_ruc=row["supplier_ruc"],
            raw_payload=raw_payload,
            source=row["source"],
            retrieved_at=retrieved_at,
        )
