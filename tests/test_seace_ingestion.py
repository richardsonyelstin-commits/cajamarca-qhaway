"""Pruebas para la capacidad 002-seace-ingestion."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from cajamarca_qhaway.capabilities.entity_mapping.dataset import load_universe
from cajamarca_qhaway.capabilities.seace_ingestion import (
    SeaceIngester,
)
from cajamarca_qhaway.models import ProcurementRecord

NOW_UTC = datetime.now(UTC)


@pytest.fixture
def entities():
    return list(load_universe().contracting_entities)


def test_rechaza_release_fuera_de_cajamarca(entities):
    ingester = SeaceIngester(entities)
    rel_lima = {
        "ocid": "ocds-k50buh-lima-001",
        "tender": {"title": "Obra en Lima", "procurementMethod": "open"},
        "parties": [
            {
                "id": "PE-RUC-20131380951",
                "roles": ["buyer"],
                "address": {"department": "LIMA"},
                "identifier": {"id": "20131380951"},
            }
        ],
    }
    records = ingester.ingest_releases([rel_lima], retrieved_at=NOW_UTC)
    assert len(records) == 0


def test_rechaza_entidad_de_cajamarca_no_en_universo(entities):
    ingester = SeaceIngester(entities)
    rel_desconocida = {
        "ocid": "ocds-k50buh-caj-desconocida",
        "tender": {"title": "Compra papel", "procurementMethod": "direct"},
        "parties": [
            {
                "id": "PE-RUC-20999999999",
                "roles": ["buyer"],
                "address": {"department": "CAJAMARCA"},
                "identifier": {"id": "20999999999"},
            }
        ],
    }
    records = ingester.ingest_releases([rel_desconocida], retrieved_at=NOW_UTC)
    assert len(records) == 0


def test_acepta_y_parsea_release_valido_de_cajamarca(entities):
    ingester = SeaceIngester(entities)
    # Gobierno Regional de Cajamarca: RUC 20453744168
    gob_reg = next(e for e in entities if e.ruc == "20453744168")

    rel_cajamarca = {
        "ocid": "ocds-k50buh-caj-1001",
        "tender": {
            "title": "Construccion de camino vecinal en Celendin",
            "procurementMethod": "open",
            "numberOfTenderers": 1,
            "value": {"amount": 750000.0, "currency": "PEN"},
        },
        "awards": [
            {
                "id": "award-1",
                "value": {"amount": 745000.0, "currency": "PEN"},
                "suppliers": [{"id": "20555666777", "name": "Constructora del Valle SAC"}],
            }
        ],
        "parties": [
            {
                "id": gob_reg.consucode_id or "buyer-gobreg",
                "name": "GOBIERNO REGIONAL CAJAMARCA",
                "roles": ["buyer"],
                "address": {"department": "CAJAMARCA"},
                "identifier": {"id": "20453744168"},
            },
            {
                "id": "20555666777",
                "name": "Constructora del Valle SAC",
                "roles": ["supplier"],
                "identifier": {"id": "20555666777"},
            },
        ],
    }

    records = ingester.ingest_payload({"releases": [rel_cajamarca]}, retrieved_at=NOW_UTC)
    assert len(records) == 1
    rec = records[0]
    assert isinstance(rec, ProcurementRecord)
    assert rec.entity_id == gob_reg.entity_id
    assert rec.ocid == "ocds-k50buh-caj-1001"
    assert rec.title == "Construccion de camino vecinal en Celendin"
    assert rec.awarded_amount == 745000.0
    assert rec.number_of_bidders == 1
    assert rec.supplier_name == "Constructora del Valle SAC"
    assert rec.supplier_ruc == "20555666777"
    assert rec.raw_payload == rel_cajamarca  # Preservacion integra
