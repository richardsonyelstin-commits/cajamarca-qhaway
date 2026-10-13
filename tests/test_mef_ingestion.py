"""Pruebas para la capacidad 003-mef-ingestion."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from cajamarca_qhaway.capabilities.entity_mapping.dataset import load_universe
from cajamarca_qhaway.capabilities.mef_ingestion import MefIngester
from cajamarca_qhaway.models import BudgetExecutionRecord

NOW_UTC = datetime.now(timezone.utc)


@pytest.fixture
def entities():
    return list(load_universe().contracting_entities)


def test_rechaza_registro_entidad_desconocida(entities):
    ingester = MefIngester(entities)
    raw = {
        "ruc": "20999999999",
        "fiscal_year": 2026,
        "budgeted_amount": 100000.0,
        "executed_amount": 50000.0,
    }
    records = ingester.ingest_records([raw], retrieved_at=NOW_UTC)
    assert len(records) == 0


def test_rechaza_registro_ano_invalido(entities):
    ingester = MefIngester(entities)
    gob_reg = next(e for e in entities if e.ruc == "20453744168")
    raw = {
        "ruc": gob_reg.ruc,
        "fiscal_year": "no-es-ano",
        "budgeted_amount": 100000.0,
        "executed_amount": 50000.0,
    }
    records = ingester.ingest_records([raw], retrieved_at=NOW_UTC)
    assert len(records) == 0


def test_ingesta_mef_formato_ckan_datastore(entities):
    ingester = MefIngester(entities)
    mp_cajamarca = next(e for e in entities if e.official_name == "MUNICIPALIDAD PROVINCIAL DE CAJAMARCA")

    payload = {
        "help": "https://api.datosabiertos.mef.gob.pe/help",
        "success": True,
        "result": {
            "resource_id": "mef-presupuesto-2026",
            "records": [
                {
                    "ruc": mp_cajamarca.ruc,
                    "ano_eje": 2026,
                    "pim": 12500000.0,
                    "devengado": 8750000.0,
                    "generica": "Adquisicion de activos no financieros",
                }
            ],
        },
    }

    records = ingester.ingest_payload(payload, retrieved_at=NOW_UTC)
    assert len(records) == 1
    rec = records[0]
    assert isinstance(rec, BudgetExecutionRecord)
    assert rec.entity_id == mp_cajamarca.entity_id
    assert rec.fiscal_year == 2026
    assert rec.budgeted_amount == 12500000.0
    assert rec.executed_amount == 8750000.0
    assert rec.budget_category == "Adquisicion de activos no financieros"
    assert rec.source == "mef-datastore"
