"""Persiste evidencia oficial sin crear OCID ni duplicar procesos OCDS."""

from __future__ import annotations

import json
from collections.abc import Sequence

from cajamarca_qhaway.models.procurement_source_record import ProcurementSourceRecord
from cajamarca_qhaway.persistence.connection import DatabaseManager


class ProcurementSourceRepository:
    def __init__(self, database: DatabaseManager) -> None:
        self.database = database

    def upsert_many(self, records: Sequence[ProcurementSourceRecord]) -> int:
        if not records:
            return 0
        columns = tuple(ProcurementSourceRecord.model_fields)
        updates = ", ".join(f"{key}=excluded.{key}" for key in columns
                            if key not in ("source_evidence_id", "entity_id"))
        sql = (f"INSERT INTO procurement_source_records ({', '.join(columns)}) "
               f"VALUES ({', '.join('?' for _ in columns)}) "
               f"ON CONFLICT (source_evidence_id) DO UPDATE SET {updates}")
        values = []
        for record in records:
            row = record.model_dump(mode="json")
            row["raw_payload"] = json.dumps(row["raw_payload"], ensure_ascii=True)
            values.append(tuple(row[key] for key in columns))
        with self.database.connection() as connection:
            connection.cursor().executemany(sql, values)
            connection.commit()
        return len(values)

    def list_by_procurement(self, procurement_id: str) -> list[ProcurementSourceRecord]:
        with self.database.connection() as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT * FROM procurement_source_records WHERE procurement_id = ?",
                           (procurement_id,))
            records = []
            for result in cursor.fetchall():
                row = dict(result)
                if isinstance(row["raw_payload"], str):
                    row["raw_payload"] = json.loads(row["raw_payload"])
                records.append(ProcurementSourceRecord.model_validate(row))
            return records
