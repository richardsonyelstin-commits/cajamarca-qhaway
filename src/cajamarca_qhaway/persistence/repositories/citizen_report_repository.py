"""Repositorio para CitizenReport en base de datos operativa (Pilar 2)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from cajamarca_qhaway.models import CitizenReport, ModerationStatus
from cajamarca_qhaway.persistence.connection import DatabaseManager


class CitizenReportRepository:
    """Repositorio tipado para denuncias y reportes ciudadanos."""

    def __init__(self, db_manager: DatabaseManager) -> None:
        self.db = db_manager

    def get_by_id(self, report_id: str) -> CitizenReport | None:
        sql = "SELECT * FROM citizen_reports WHERE report_id = ?"
        with self.db.connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (report_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return self._row_to_model(row)

    def list_pending(self) -> list[CitizenReport]:
        sql = "SELECT * FROM citizen_reports WHERE moderation_status = 'pending' ORDER BY submitted_at ASC"
        with self.db.connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql)
            rows = cursor.fetchall()
            return [self._row_to_model(r) for r in rows]

    def save(self, report: CitizenReport) -> None:
        if not report.legal_disclaimer_shown:
            raise ValueError("Violacion de contrato CA-006-01: legal_disclaimer_shown debe ser True.")

        sql = """
        INSERT INTO citizen_reports
            (report_id, submitted_at, channel, raw_text, related_entity_id,
             moderation_status, moderated_by, moderated_at, legal_disclaimer_shown)
        VALUES
            (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT (report_id) DO UPDATE SET
            moderation_status = excluded.moderation_status,
            moderated_by = excluded.moderated_by,
            moderated_at = excluded.moderated_at
        """

        params = (
            report.report_id,
            report.submitted_at.isoformat(),
            report.channel,
            report.raw_text,
            report.related_entity_id,
            report.moderation_status,
            report.moderated_by,
            report.moderated_at.isoformat() if report.moderated_at else None,
            True if report.legal_disclaimer_shown else False,
        )

        with self.db.connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            conn.commit()

    @staticmethod
    def _row_to_model(row: Any) -> CitizenReport:
        submitted_at = row["submitted_at"]
        if isinstance(submitted_at, str):
            submitted_at = datetime.fromisoformat(submitted_at)
        if submitted_at.tzinfo is None:
            submitted_at = submitted_at.replace(tzinfo=timezone.utc)

        moderated_at = row["moderated_at"]
        if moderated_at:
            if isinstance(moderated_at, str):
                moderated_at = datetime.fromisoformat(moderated_at)
            if moderated_at.tzinfo is None:
                moderated_at = moderated_at.replace(tzinfo=timezone.utc)

        return CitizenReport(
            report_id=row["report_id"],
            submitted_at=submitted_at,
            channel=row["channel"],
            raw_text=row["raw_text"],
            related_entity_id=row["related_entity_id"],
            moderation_status=row["moderation_status"],
            moderated_by=row["moderated_by"],
            moderated_at=moderated_at,
            legal_disclaimer_shown=bool(row["legal_disclaimer_shown"]),
        )
