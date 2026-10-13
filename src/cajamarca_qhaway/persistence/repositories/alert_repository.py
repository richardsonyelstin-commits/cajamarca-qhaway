"""Repositorio para Alert en base de datos operativa (Pilar 2)."""

from __future__ import annotations

import json
from collections.abc import Sequence
from datetime import datetime, timezone
from typing import Any

from cajamarca_qhaway.models import Alert
from cajamarca_qhaway.persistence.connection import DatabaseManager


class AlertRepository:
    """Repositorio tipado para alertas decididas por comite humano."""

    def __init__(self, db_manager: DatabaseManager) -> None:
        self.db = db_manager

    def get_by_id(self, alert_id: str) -> Alert | None:
        sql = "SELECT * FROM alerts WHERE alert_id = ?"
        with self.db.connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (alert_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return self._row_to_model(row)

    def list_published(self) -> list[Alert]:
        """Retorna alertas publicadas (visibles publicamente bajo RLS)."""
        sql = "SELECT * FROM alerts WHERE status = 'published' ORDER BY published_at DESC"
        with self.db.connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql)
            rows = cursor.fetchall()
            return [self._row_to_model(r) for r in rows]

    def list_all(self) -> list[Alert]:
        sql = "SELECT * FROM alerts ORDER BY reviewed_at DESC"
        with self.db.connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql)
            rows = cursor.fetchall()
            return [self._row_to_model(r) for r in rows]

    def save(self, alert: Alert) -> None:
        sql = """
        INSERT INTO alerts
            (alert_id, red_flag_ids, entity_id, status, reviewed_by, reviewed_at,
             review_notes, disclaimer, legal_disclaimer, evidence, published_at)
        VALUES
            (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT (alert_id) DO UPDATE SET
            status = excluded.status,
            reviewed_by = excluded.reviewed_by,
            reviewed_at = excluded.reviewed_at,
            review_notes = excluded.review_notes,
            disclaimer = excluded.disclaimer,
            legal_disclaimer = excluded.legal_disclaimer,
            evidence = excluded.evidence,
            published_at = excluded.published_at
        """

        params = (
            alert.alert_id,
            json.dumps(list(alert.red_flag_ids)),
            alert.entity_id,
            alert.status,
            alert.reviewed_by,
            alert.reviewed_at.isoformat(),
            alert.review_notes,
            alert.legal_disclaimer,
            alert.legal_disclaimer,
            json.dumps([item.model_dump(mode="json") for item in alert.evidence]),
            alert.published_at.isoformat() if alert.published_at else None,
        )

        with self.db.connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            conn.commit()

    @staticmethod
    def _row_to_model(row: Any) -> Alert:
        red_flag_ids = row["red_flag_ids"]
        if isinstance(red_flag_ids, str):
            try:
                red_flag_ids = tuple(json.loads(red_flag_ids))
            except json.JSONDecodeError:
                red_flag_ids = ()

        reviewed_at = row["reviewed_at"]
        if isinstance(reviewed_at, str):
            reviewed_at = datetime.fromisoformat(reviewed_at)
        if reviewed_at.tzinfo is None:
            reviewed_at = reviewed_at.replace(tzinfo=timezone.utc)

        published_at = row["published_at"]
        if published_at:
            if isinstance(published_at, str):
                published_at = datetime.fromisoformat(published_at)
            if published_at.tzinfo is None:
                published_at = published_at.replace(tzinfo=timezone.utc)

        evidence = row["evidence"]
        if isinstance(evidence, str):
            try:
                evidence = json.loads(evidence)
            except json.JSONDecodeError:
                evidence = []

        return Alert(
            alert_id=row["alert_id"],
            red_flag_ids=red_flag_ids,
            entity_id=row["entity_id"],
            status=row["status"],
            reviewed_by=row["reviewed_by"],
            reviewed_at=reviewed_at,
            review_notes=row["review_notes"],
            legal_disclaimer=row["legal_disclaimer"],
            evidence=evidence,
            published_at=published_at,
        )
