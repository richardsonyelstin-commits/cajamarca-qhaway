"""Prueba de integracion End-to-End para el pipeline de Cajamarca Qhaway."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from cajamarca_qhaway.models import Alert, RedFlag
from cajamarca_qhaway.pipeline import CajamarcaPipeline

NOW_UTC = datetime.now(timezone.utc)


def test_pipeline_e2e_flujo_completo():
    pipeline = CajamarcaPipeline()
    assert len(pipeline.entities) == 14

    # Entidad de prueba del universo (Gobierno Regional)
    gob_reg = next(e for e in pipeline.entities if e.ruc == "20453744168")

    # Muestra de SEACE con un postor unico
    seace_sample = [
        {
            "ocid": "ocds-k50buh-e2e-001",
            "tender": {
                "title": "Pavimentacion en Chota",
                "procurementMethod": "open",
                "numberOfTenderers": 1,
            },
            "awards": [
                {
                    "value": {"amount": 500000.0, "currency": "PEN"},
                    "suppliers": [{"id": "20123456789", "name": "Constructora Chota"}],
                }
            ],
            "parties": [
                {
                    "id": "buyer-gobreg",
                    "roles": ["buyer"],
                    "address": {"department": "CAJAMARCA"},
                    "identifier": {"id": gob_reg.ruc},
                }
            ],
        }
    ]

    # Muestra de MEF con sobrecosto presupuestal
    mef_sample = [
        {
            "ruc": gob_reg.ruc,
            "fiscal_year": 2026,
            "budgeted_amount": 1000000.0,
            "executed_amount": 1250000.0,
            "budget_category": "Inversiones",
        }
    ]

    # Ejecutar pipeline
    result = pipeline.run_detection(seace_releases=seace_sample, mef_records=mef_sample, now=NOW_UTC)

    assert result.total_entities_monitored == 14
    assert len(result.procurement_records) == 1
    assert len(result.execution_records) == 1
    assert len(result.candidate_red_flags) >= 2  # single-bidder y execution-overrun

    # Invariante Art. 14: Los candidatos son RedFlag, NO Alert
    for flag in result.candidate_red_flags:
        assert isinstance(flag, RedFlag)
        assert not hasattr(flag, "status")

    # Pase formal a panel de revision humana
    single_bidder_flag = next(f for f in result.candidate_red_flags if f.indicator_code == "single-bidder")
    alert = pipeline.review_panel.publish_alert(
        entity_id=gob_reg.entity_id,
        red_flags=[single_bidder_flag],
        reviewer_id="auditor.veeduria@proetica.pe",
        review_notes="Validado en portal SEACE: proceso adjudicado con 1 solo participante.",
        reviewed_at=NOW_UTC,
    )

    assert isinstance(alert, Alert)
    assert alert.status == "published"
    assert alert.reviewed_by == "auditor.veeduria@proetica.pe"
    assert len(pipeline.review_panel.list_alerts("published")) == 1

    # Intake y moderacion de denuncia
    report = pipeline.denuncia_service.submit_report(
        raw_text="Testigo de direccion falsa de contratista",
        legal_disclaimer_shown=True,
        related_entity_id=gob_reg.entity_id,
        submitted_at=NOW_UTC,
    )
    assert report.moderation_status == "pending"

    mod_report = pipeline.denuncia_service.moderate_report(
        report_id=report.report_id,
        new_status="accepted_as_lead",
        moderator_id="coordinador.proetica@proetica.pe",
        moderated_at=NOW_UTC,
    )
    assert mod_report.moderation_status == "accepted_as_lead"
