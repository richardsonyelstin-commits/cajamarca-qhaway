"""Repositorio para ContractingEntity en base de datos operativa (Pilar 2)."""

from __future__ import annotations

import sqlite3
from collections.abc import Sequence
from datetime import datetime, timezone

from cajamarca_qhaway.models import ContractingEntity
from cajamarca_qhaway.persistence.connection import DatabaseManager


class EntityRepository:
    """Repositorio tipado para el universo de ContractingEntity."""

    def __init__(self, db_manager: DatabaseManager) -> None:
        self.db = db_manager

    def get_by_id(self, entity_id: str) -> ContractingEntity | None:
        sql = "SELECT * FROM contracting_entities WHERE entity_id = ?"
        with self.db.connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (entity_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return self._row_to_model(row)

    def get_by_ruc(self, ruc: str) -> ContractingEntity | None:
        sql = "SELECT * FROM contracting_entities WHERE ruc = ?"
        with self.db.connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (ruc,))
            row = cursor.fetchone()
            if not row:
                return None
            return self._row_to_model(row)

    def list_active(self) -> list[ContractingEntity]:
        sql = "SELECT * FROM contracting_entities WHERE active = TRUE"
        with self.db.connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql)
            rows = cursor.fetchall()
            return [self._row_to_model(r) for r in rows]

    def upsert(self, entity: ContractingEntity) -> None:
        self.upsert_many([entity])

    def upsert_many(self, entities: Sequence[ContractingEntity]) -> int:
        if not entities:
            return 0

        sql = """
        INSERT INTO contracting_entities
            (entity_id, official_name, entity_level, province, ruc, consucode_id, department, verified_at, active)
        VALUES
            (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT (entity_id) DO UPDATE SET
            official_name = excluded.official_name,
            entity_level = excluded.entity_level,
            province = excluded.province,
            ruc = excluded.ruc,
            consucode_id = excluded.consucode_id,
            department = excluded.department,
            verified_at = excluded.verified_at,
            active = excluded.active
        """

        params = [
            (
                e.entity_id,
                e.official_name,
                e.entity_level,
                e.province,
                e.ruc,
                e.consucode_id,
                e.department,
                e.verified_at.isoformat(),
                True if e.active else False,
            )
            for e in entities
        ]

        with self.db.connection() as conn:
            cursor = conn.cursor()
            cursor.executemany(sql, params)
            conn.commit()
            return len(params)

    @staticmethod
    def _row_to_model(row: Any) -> ContractingEntity:
        verified_at = row["verified_at"]
        if isinstance(verified_at, str):
            verified_at = datetime.fromisoformat(verified_at)
        if verified_at.tzinfo is None:
            verified_at = verified_at.replace(tzinfo=timezone.utc)

        return ContractingEntity(
            entity_id=row["entity_id"],
            official_name=row["official_name"],
            entity_level=row["entity_level"],
            province=row["province"],
            ruc=row["ruc"],
            consucode_id=row["consucode_id"],
            department=row["department"],
            verified_at=verified_at,
            active=bool(row["active"]),
        )
