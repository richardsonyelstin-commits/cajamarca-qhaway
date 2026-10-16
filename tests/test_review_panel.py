"""Pruebas para la capacidad 005-review-panel."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from cajamarca_qhaway.capabilities.review_panel import ReviewPanelService
from cajamarca_qhaway.models import Alert, RedFlag

NOW_UTC = datetime.now(UTC)


@pytest.fixture
def sample_flag():
    return RedFlag(
        red_flag_id="rf-sample-1",
        indicator_code="single-bidder",
        formula_description="Licitacion con unico postor",
        threshold=1,
        observed_value=1,
        procurement_ids=["pr-100"],
        evidence_source="seace-ocds",
        evidence_retrieved_at=NOW_UTC,
        generated_at=NOW_UTC,
    )


def test_publicar_alerta_con_revisor_valido(sample_flag):
    service = ReviewPanelService()
    alert = service.publish_alert(
        entity_id="ce-20160759086",
        red_flags=[sample_flag],
        reviewer_id="monica.sanchez@veeduria.pe",
        review_notes="Verificado en SEACE: no hubo observaciones en bases pero solo 1 postor",
        reviewed_at=NOW_UTC,
    )
    assert isinstance(alert, Alert)
    assert alert.status == "published"
    assert alert.reviewed_by == "monica.sanchez@veeduria.pe"
    assert alert.published_at == NOW_UTC
    assert alert.entity_id == "ce-20160759086"
    assert alert.red_flag_ids == ["rf-sample-1"]


def test_descartar_alerta_exige_motivo(sample_flag):
    service = ReviewPanelService()
    with pytest.raises(ValueError, match="review_notes es obligatorio"):
        service.discard_alert(
            entity_id="ce-20160759086",
            red_flags=[sample_flag],
            reviewer_id="monica.sanchez@veeduria.pe",
            review_notes="",  # Vacio: debe fallar
            reviewed_at=NOW_UTC,
        )

    # Con motivo valido
    alert = service.discard_alert(
        entity_id="ce-20160759086",
        red_flags=[sample_flag],
        reviewer_id="monica.sanchez@veeduria.pe",
        review_notes="Falso positivo: proceso correspondio a adquisicion de patente exclusiva",
        reviewed_at=NOW_UTC,
    )
    assert alert.status == "discarded"
    assert alert.published_at is None
    assert "patente exclusiva" in alert.review_notes


def test_rechazo_revisor_generico(sample_flag):
    service = ReviewPanelService()
    with pytest.raises(ValueError, match="revisor humano valido"):
        service.publish_alert(
            entity_id="ce-20160759086",
            red_flags=[sample_flag],
            reviewer_id="system",  # Invalido (CA-005-02)
            review_notes="Nota de prueba para evaluar el rechazo de identidad.",
            reviewed_at=NOW_UTC,
        )


def test_filtrado_por_estado(sample_flag):
    service = ReviewPanelService()
    service.publish_alert(
        entity_id="ce-20160759086",
        red_flags=[sample_flag],
        reviewer_id="revisor1@ong.pe",
        review_notes="Proceso revisado contra el expediente de contratacion.",
        reviewed_at=NOW_UTC,
    )
    service.discard_alert(
        entity_id="ce-20160759086",
        red_flags=[sample_flag.model_copy(update={"red_flag_id": "rf-otro-2"})],
        reviewer_id="revisor2@ong.pe",
        review_notes="Descartado",
        reviewed_at=NOW_UTC,
    )
    assert len(service.list_alerts()) == 2
    assert len(service.list_alerts("published")) == 1
    assert len(service.list_alerts("discarded")) == 1
