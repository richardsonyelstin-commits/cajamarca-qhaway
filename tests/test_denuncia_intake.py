"""Pruebas para la capacidad 006-denuncia-intake."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from cajamarca_qhaway.capabilities.denuncia_intake import DenunciaIntakeService
from cajamarca_qhaway.models import CitizenReport

NOW_UTC = datetime.now(UTC)


def test_rechazo_sin_descargo_legal():
    """CA-006-01: No se acepta reporte si legal_disclaimer_shown es False."""
    service = DenunciaIntakeService()
    with pytest.raises(ValueError, match="descargo legal"):
        service.submit_report(
            raw_text="Sospecha de sobrecosto en obra de saneamiento",
            legal_disclaimer_shown=False,
            submitted_at=NOW_UTC,
        )


def test_intake_exitoso_estado_pending():
    """CA-006-02: El reporte entrante se crea en estado pending."""
    service = DenunciaIntakeService()
    report = service.submit_report(
        raw_text="Sospecha de sobrecosto en obra de saneamiento en Chota",
        legal_disclaimer_shown=True,
        channel="web",
        related_entity_id="ce-20160759086",
        submitted_at=NOW_UTC,
    )
    assert isinstance(report, CitizenReport)
    assert report.moderation_status == "pending"
    assert report.moderated_by is None
    assert report.moderated_at is None
    assert report.legal_disclaimer_shown is True


def test_moderacion_exitosa():
    service = DenunciaIntakeService()
    rep = service.submit_report(
        raw_text="Empresa ganadora comparte direccion con funcionario",
        legal_disclaimer_shown=True,
        submitted_at=NOW_UTC,
    )

    moderated = service.moderate_report(
        report_id=rep.report_id,
        new_status="accepted_as_lead",
        moderator_id="lucia.torres@proetica-cajamarca.org",
        moderated_at=NOW_UTC,
    )
    assert moderated.moderation_status == "accepted_as_lead"
    assert moderated.moderated_by == "lucia.torres@proetica-cajamarca.org"
    assert moderated.moderated_at == NOW_UTC

    # Intentar re-moderar debe fallar
    with pytest.raises(ValueError, match="ya fue moderado"):
        service.moderate_report(
            report_id=rep.report_id,
            new_status="rejected",
            moderator_id="otro.moderador@ong.pe",
        )


def test_rechazo_moderador_generico():
    service = DenunciaIntakeService()
    rep = service.submit_report(
        raw_text="Denuncia test",
        legal_disclaimer_shown=True,
        submitted_at=NOW_UTC,
    )
    with pytest.raises(ValueError, match="moderated_by no puede ser un usuario generico"):
        service.moderate_report(
            report_id=rep.report_id,
            new_status="accepted_as_lead",
            moderator_id="admin",
            moderated_at=NOW_UTC,
        )


def test_filtrado_reportes_por_estado():
    service = DenunciaIntakeService()
    r1 = service.submit_report(raw_text="D1", legal_disclaimer_shown=True, submitted_at=NOW_UTC)
    service.submit_report(raw_text="D2", legal_disclaimer_shown=True, submitted_at=NOW_UTC)
    service.moderate_report(r1.report_id, "accepted_as_lead", "mod1@ong.pe", NOW_UTC)

    assert len(service.list_reports()) == 2
    assert len(service.list_reports("pending")) == 1
    assert len(service.list_reports("accepted_as_lead")) == 1
    assert len(service.list_reports("rejected")) == 0
