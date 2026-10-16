"""Servicio de intake y moderacion de denuncias ciudadanas (capacidad 006-denuncia-intake).

Exige de forma irrestricta la aceptacion del descargo legal previo (CA-006-01).
Somete todo reporte a una maquina de estados de moderacion humana (RN-006-03).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Callable, Literal

from cajamarca_qhaway.models import ChannelType, CitizenReport, ModerationStatus, compute_report_id


class DenunciaIntakeService:
    """Gestiona la recepcion y moderacion de denuncias ciudadanas curadas."""

    def __init__(self) -> None:
        self._reports: dict[str, CitizenReport] = {}

    def submit_report(
        self,
        raw_text: str,
        legal_disclaimer_shown: bool,
        channel: ChannelType = "web",
        related_entity_id: str | None = None,
        submitted_at: datetime | None = None,
        tracking_token_hash: str | None = None,
        persist: Callable[[CitizenReport], None] | None = None,
    ) -> CitizenReport:
        """Registra una nueva denuncia ciudadana.

        Falla inmediatamente si no se mostro y acepto el descargo legal (CA-006-01).
        """
        if not legal_disclaimer_shown:
            raise ValueError(
                "La denuncia no puede ser aceptada sin previa confirmacion del descargo legal (CA-006-01)"
            )

        now = submitted_at or datetime.now(timezone.utc)
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)

        rep_id = compute_report_id(raw_text, now)
        report = CitizenReport(
            report_id=rep_id,
            submitted_at=now,
            channel=channel,
            raw_text=raw_text,
            related_entity_id=related_entity_id,
            moderation_status="pending",
            moderated_by=None,
            moderated_at=None,
            legal_disclaimer_shown=True,
            tracking_token_hash=tracking_token_hash,
        )
        # Confirmar la escritura antes de incorporar el reporte al estado local.
        if persist is not None:
            persist(report)
        self._reports[report.report_id] = report
        return report

    def moderate_report(
        self,
        report_id: str,
        new_status: Literal["accepted_as_lead", "rejected"],
        moderator_id: str,
        moderated_at: datetime | None = None,
        persist: Callable[[CitizenReport], None] | None = None,
    ) -> CitizenReport:
        """Modera una denuncia ciudadana pendiente asignandole un estado y moderador humano."""
        existing = self._reports.get(report_id)
        if not existing:
            raise KeyError(f"Reporte con ID '{report_id}' no encontrado")

        if existing.moderation_status != "pending":
            raise ValueError(
                f"El reporte '{report_id}' ya fue moderado con estado '{existing.moderation_status}'"
            )

        now = moderated_at or datetime.now(timezone.utc)
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)

        updated = CitizenReport(
            report_id=existing.report_id,
            submitted_at=existing.submitted_at,
            channel=existing.channel,
            raw_text=existing.raw_text,
            related_entity_id=existing.related_entity_id,
            moderation_status=new_status,
            moderated_by=moderator_id,
            moderated_at=now,
            legal_disclaimer_shown=True,
            tracking_token_hash=existing.tracking_token_hash,
        )
        # El cambio de estado solo se publica localmente tras confirmar la escritura.
        if persist is not None:
            persist(updated)
        self._reports[report_id] = updated
        return updated

    def list_reports(self, status: ModerationStatus | None = None) -> list[CitizenReport]:
        """Lista las denuncias registradas, opcionalmente filtradas por estado de moderacion."""
        if status is None:
            return list(self._reports.values())
        return [r for r in self._reports.values() if r.moderation_status == status]

    def get_report(self, report_id: str) -> CitizenReport | None:
        """Obtiene un reporte por su identificador."""
        return self._reports.get(report_id)
