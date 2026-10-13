"""Servicio del panel de revision humana (capacidad 005-review-panel).

Implementa la compuerta humana mandatoria (Articulo 14 de la constitucion).
Ningun RedFlag se publica de forma automatica; toda Alerta requiere decision
explícita de un revisor humano autenticado.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from cajamarca_qhaway.models import Alert, RedFlag, compute_alert_id


class ReviewPanelService:
    """Gestiona la cola de candidatos de banderas rojas y las decisiones de revision humana."""

    def __init__(self) -> None:
        self._decisions: dict[str, Alert] = {}

    def publish_alert(
        self,
        entity_id: str,
        red_flags: list[RedFlag] | list[str],
        reviewer_id: str,
        review_notes: str | None = None,
        reviewed_at: datetime | None = None,
    ) -> Alert:
        """Aprueba y publica una Alerta para su consumo en el dashboard publico."""
        flag_ids = [rf.red_flag_id if isinstance(rf, RedFlag) else rf for rf in red_flags]
        if not flag_ids:
            raise ValueError("Debe proporcionarse al menos un RedFlag para publicar una alerta")

        now = reviewed_at or datetime.now(timezone.utc)
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)

        alert_id = compute_alert_id(entity_id, flag_ids)
        alert = Alert(
            alert_id=alert_id,
            red_flag_ids=flag_ids,
            entity_id=entity_id,
            status="published",
            reviewed_by=reviewer_id,
            reviewed_at=now,
            review_notes=review_notes,
            published_at=now,
        )
        self._decisions[alert.alert_id] = alert
        return alert

    def discard_alert(
        self,
        entity_id: str,
        red_flags: list[RedFlag] | list[str],
        reviewer_id: str,
        review_notes: str,
        reviewed_at: datetime | None = None,
    ) -> Alert:
        """Descarta un candidato de Alerta registrando el motivo obligatorio del descarte."""
        flag_ids = [rf.red_flag_id if isinstance(rf, RedFlag) else rf for rf in red_flags]
        if not flag_ids:
            raise ValueError("Debe proporcionarse al menos un RedFlag para registrar una alerta descartada")

        now = reviewed_at or datetime.now(timezone.utc)
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)

        alert_id = compute_alert_id(entity_id, flag_ids)
        alert = Alert(
            alert_id=alert_id,
            red_flag_ids=flag_ids,
            entity_id=entity_id,
            status="discarded",
            reviewed_by=reviewer_id,
            reviewed_at=now,
            review_notes=review_notes,
            published_at=None,
        )
        self._decisions[alert.alert_id] = alert
        return alert

    def list_alerts(self, status: Literal["published", "discarded"] | None = None) -> list[Alert]:
        """Retorna las alertas decididas, opcionalmente filtradas por estado."""
        if status is None:
            return list(self._decisions.values())
        return [a for a in self._decisions.values() if a.status == status]

    def get_alert(self, alert_id: str) -> Alert | None:
        """Obtiene una alerta por su ID."""
        return self._decisions.get(alert_id)
