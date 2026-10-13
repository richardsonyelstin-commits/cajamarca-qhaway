"""Pruebas de contrato para los modelos canonicos de Cajamarca Qhaway.

Cubre los 6 contratos canonicos especificados en el Articulo 19 de `docs/sdd/constitution.md`.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from cajamarca_qhaway.models import (
    Alert,
    BudgetExecutionRecord,
    CitizenReport,
    ContractingEntity,
    ProcurementRecord,
    RedFlag,
    STANDARD_ALERT_DISCLAIMER,
    compute_alert_id,
    compute_execution_record_id,
    compute_procurement_id,
    compute_red_flag_id,
    compute_report_id,
)

NOW_UTC = datetime.now(timezone.utc)


@pytest.mark.contract
def test_procurement_record_valido() -> None:
    rec = ProcurementRecord(
        procurement_id=compute_procurement_id("ocds-k50buh-12345"),
        ocid="ocds-k50buh-12345",
        entity_id="ce-20160759086",
        title="Mejoramiento del servicio de agua potable",
        procurement_method="open",
        awarded_amount=150000.0,
        executed_amount=148000.0,
        number_of_bidders=2,
        supplier_name="Consorcio Norte",
        supplier_ruc="20456789012",
        raw_payload={"ocid": "ocds-k50buh-12345"},
        retrieved_at=NOW_UTC,
    )
    assert rec.source == "seace-ocds"
    assert rec.awarded_amount == 150000.0

    # Inmutabilidad
    with pytest.raises(ValidationError):
        rec.title = "Nuevo titulo"  # type: ignore

    # Extra forbid
    with pytest.raises(ValidationError):
        ProcurementRecord(
            procurement_id="pr-123",
            ocid="ocds-123",
            entity_id="ce-123",
            title="T",
            retrieved_at=NOW_UTC,
            campo_inventado="invalido",  # type: ignore
        )


@pytest.mark.contract
def test_procurement_record_exige_utc() -> None:
    naive_dt = datetime.now()  # sin tzinfo
    with pytest.raises(ValidationError, match="zona horaria"):
        ProcurementRecord(
            procurement_id="pr-123",
            ocid="ocds-123",
            entity_id="ce-123",
            title="T",
            retrieved_at=naive_dt,
        )


@pytest.mark.contract
def test_budget_execution_record_valido() -> None:
    rec_id = compute_execution_record_id("ce-20160759086", 2026, "inversiones")
    rec = BudgetExecutionRecord(
        execution_record_id=rec_id,
        entity_id="ce-20160759086",
        fiscal_year=2026,
        budgeted_amount=5000000.0,
        executed_amount=4200000.0,
        budget_category="inversiones",
        raw_payload={"pim": 5000000.0},
        retrieved_at=NOW_UTC,
    )
    assert rec.source == "mef-datastore"
    assert rec.fiscal_year == 2026

    # Fiscal year invalido
    with pytest.raises(ValidationError, match="fiscal_year"):
        BudgetExecutionRecord(
            execution_record_id=rec_id,
            entity_id="ce-20160759086",
            fiscal_year=1999,
            budgeted_amount=100.0,
            executed_amount=50.0,
            retrieved_at=NOW_UTC,
        )


@pytest.mark.contract
def test_red_flag_prohibe_status_y_scoring_de_personas() -> None:
    # CA-004-06: RedFlag no debe admitir campo status
    with pytest.raises(ValidationError):
        RedFlag(
            red_flag_id="rf-1",
            indicator_code="single-bidder",
            formula_description="Un solo postor",
            threshold=1,
            observed_value=1,
            procurement_ids=["pr-1"],
            evidence_source="seace-ocds",
            evidence_retrieved_at=NOW_UTC,
            generated_at=NOW_UTC,
            status="published",  # type: ignore
        )

    # Exige al menos un identificador de evidencia
    with pytest.raises(ValidationError, match="evidencia"):
        RedFlag(
            red_flag_id="rf-1",
            indicator_code="single-bidder",
            formula_description="Un solo postor",
            threshold=1,
            observed_value=1,
            evidence_source="seace-ocds",
            evidence_retrieved_at=NOW_UTC,
            generated_at=NOW_UTC,
        )

    # RedFlag valido
    rf = RedFlag(
        red_flag_id=compute_red_flag_id("single-bidder", "pr-1", NOW_UTC.isoformat()),
        indicator_code="single-bidder",
        formula_description="Licitacion adjudicada con un unico postor participante",
        threshold=1,
        observed_value=1,
        procurement_ids=["pr-1"],
        evidence_source="seace-ocds",
        evidence_retrieved_at=NOW_UTC,
        generated_at=NOW_UTC,
    )
    assert rf.indicator_code == "single-bidder"
    assert rf.procurement_ids == ["pr-1"]


@pytest.mark.contract
def test_alert_compuerta_humana_y_validaciones() -> None:
    alert_id = compute_alert_id("ce-20160759086", ["rf-123"])

    # Rechaza revisor generico (CA-005-02)
    with pytest.raises(ValidationError, match="revisor humano valido"):
        Alert(
            alert_id=alert_id,
            red_flag_ids=["rf-123"],
            entity_id="ce-20160759086",
            status="published",
            reviewed_by="admin",
            reviewed_at=NOW_UTC,
            review_notes="Prueba de revisor inválido.",
            evidence=[{"red_flag_id": "rf-123", "formula_description": "f", "observed_value": 1, "threshold_value": 1, "retrieved_at": NOW_UTC, "evidence_source": "seace"}],
            published_at=NOW_UTC,
        )

    # Revisor valido publicado exige published_at
    with pytest.raises(ValidationError, match="published_at es obligatorio"):
        Alert(
            alert_id=alert_id,
            red_flag_ids=["rf-123"],
            entity_id="ce-20160759086",
            status="published",
            reviewed_by="maria.rodriguez@ong-aliada.pe",
            reviewed_at=NOW_UTC,
            review_notes="Decision registrada y sustentada por el expediente del proceso.",
            evidence=[{"red_flag_id": "rf-123", "formula_description": "f", "observed_value": 1, "threshold_value": 1, "retrieved_at": NOW_UTC, "evidence_source": "seace"}],
            published_at=None,
        )

    # Estado descartado exige review_notes (CA-005-04)
    with pytest.raises(ValidationError, match="review_notes"):
        Alert(
            alert_id=alert_id,
            red_flag_ids=["rf-123"],
            entity_id="ce-20160759086",
            status="discarded",
            reviewed_by="carlos.mendoza@ong-aliada.pe",
            reviewed_at=NOW_UTC,
            review_notes=None,
        )

    # Alerta descartada valida
    alert_discarded = Alert(
        alert_id=alert_id,
        red_flag_ids=["rf-123"],
        entity_id="ce-20160759086",
        status="discarded",
        reviewed_by="carlos.mendoza@ong-aliada.pe",
        reviewed_at=NOW_UTC,
        review_notes="Falso positivo: hubo proceso de emergencia previo con 3 postores",
        evidence=[{"red_flag_id": "rf-123", "formula_description": "f", "observed_value": 1, "threshold_value": 1, "retrieved_at": NOW_UTC, "evidence_source": "seace"}],
    )
    assert alert_discarded.status == "discarded"
    assert alert_discarded.published_at is None

    # Alerta publicada valida
    alert_published = Alert(
        alert_id=alert_id,
        red_flag_ids=["rf-123"],
        entity_id="ce-20160759086",
        status="published",
        reviewed_by="maria.rodriguez@ong-aliada.pe",
        reviewed_at=NOW_UTC,
        review_notes="Proceso verificado contra la evidencia de la convocatoria.",
        evidence=[{"red_flag_id": "rf-123", "formula_description": "f", "observed_value": 1, "threshold_value": 1, "retrieved_at": NOW_UTC, "evidence_source": "seace"}],
        published_at=NOW_UTC,
    )
    assert alert_published.status == "published"
    assert alert_published.disclaimer == STANDARD_ALERT_DISCLAIMER


@pytest.mark.contract
def test_citizen_report_aviso_legal_y_moderacion() -> None:
    rep_id = compute_report_id("Denuncia sobre obra en Jaen", NOW_UTC)

    # Rechazo si no se mostro aviso legal (CA-006-01)
    with pytest.raises(ValidationError, match="legal_disclaimer_shown"):
        CitizenReport(
            report_id=rep_id,
            submitted_at=NOW_UTC,
            channel="web",
            raw_text="Sobrevaloracion de materiales en la obra del puente",
            legal_disclaimer_shown=False,
        )

    # Reporte pendiente valido
    rep_pending = CitizenReport(
        report_id=rep_id,
        submitted_at=NOW_UTC,
        channel="web",
        raw_text="Sobrevaloracion de materiales en la obra del puente",
        related_entity_id="ce-20160759086",
        legal_disclaimer_shown=True,
    )
    assert rep_pending.moderation_status == "pending"
    assert rep_pending.moderated_by is None

    # Moderacion exige moderador humano y fecha
    with pytest.raises(ValidationError, match="moderated_by es obligatorio"):
        CitizenReport(
            report_id=rep_id,
            submitted_at=NOW_UTC,
            channel="web",
            raw_text="Sobrevaloracion de materiales en la obra del puente",
            moderation_status="accepted_as_lead",
            legal_disclaimer_shown=True,
        )

    # Reporte moderado valido
    rep_moderated = CitizenReport(
        report_id=rep_id,
        submitted_at=NOW_UTC,
        channel="web",
        raw_text="Sobrevaloracion de materiales en la obra del puente",
        related_entity_id="ce-20160759086",
        moderation_status="accepted_as_lead",
        moderated_by="juan.perez@veeduria.pe",
        moderated_at=NOW_UTC,
        legal_disclaimer_shown=True,
    )
    assert rep_moderated.moderation_status == "accepted_as_lead"
    assert rep_moderated.moderated_by == "juan.perez@veeduria.pe"
