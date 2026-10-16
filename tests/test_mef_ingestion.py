"""Pruebas para la capacidad 003-mef-ingestion."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from cajamarca_qhaway.capabilities.entity_mapping.dataset import load_universe
from cajamarca_qhaway.capabilities.mef_ingestion import MefIngester
from cajamarca_qhaway.capabilities.mef_ingestion.parser import (
    MUNICIPAL_EXECUTOR_PROVINCES,
)
from cajamarca_qhaway.models import BudgetExecutionRecord

NOW_UTC = datetime.now(UTC)


@pytest.fixture
def entities():
    return list(load_universe().contracting_entities)


def test_crosswalk_mef_yaml_y_parser_permanece_sincronizado():
    universe = load_universe()
    crosswalk = {
        record.verification.siaf_sec_ejec: record.entity.province
        for record in universe.entities
        if record.entity.entity_level == "provincial_municipality"
    }
    assert crosswalk == MUNICIPAL_EXECUTOR_PROVINCES
    assert len({record.verification.ubigeo for record in universe.entities if record.entity.entity_level == "provincial_municipality"}) == 13


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


def test_no_convierte_montos_ausentes_en_ceros(entities):
    ingester = MefIngester(entities)
    regional = next(e for e in entities if e.ruc == "20453744168")
    missing = ingester.ingest_records(
        [{"ruc": regional.ruc, "fiscal_year": 2026, "budgeted_amount": 0}],
        retrieved_at=NOW_UTC,
    )
    explicit_zero = ingester.ingest_records(
        [{"ruc": regional.ruc, "fiscal_year": 2026, "budgeted_amount": 0, "executed_amount": 0}],
        retrieved_at=NOW_UTC,
    )
    assert missing == []
    assert len(explicit_zero) == 1
    assert explicit_zero[0].budgeted_amount == 0
    assert explicit_zero[0].executed_amount == 0


def test_mapea_pliego_regional_y_ruc_ejecutora(entities):
    ingester = MefIngester(entities)
    regional = next(entity for entity in entities if entity.ruc == "20453744168")
    raw = {
        "PLIEGO": "000445",
        "NIVEL_GOBIERNO": "R",
        "DEPARTAMENTO_EJECUTORA": "06",
        "ANO_EJE": 2026,
        "MONTO_PIM": 1000,
        "MONTO_DEVENGADO": 500,
    }
    matched = ingester.ingest_records([raw], retrieved_at=NOW_UTC)
    assert len(matched) == 1
    assert matched[0].entity_id == regional.entity_id

    by_ruc = ingester.ingest_records(
        [{**raw, "PLIEGO": "", "RUC_EJECUTORA": regional.ruc}],
        retrieved_at=NOW_UTC,
    )
    assert len(by_ruc) == 1
    assert by_ruc[0].entity_id == regional.entity_id


@pytest.mark.parametrize(
    "sec_ejec,province",
    [
        ("300549", "CAJAMARCA"),
        ("300562", "CAJABAMBA"),
        ("300566", "CELENDIN"),
        ("300578", "CHOTA"),
        ("300597", "CONTUMAZA"),
        ("300605", "CUTERVO"),
        ("300620", "HUALGAYOC"),
        ("300623", "JAEN"),
        ("300635", "SAN IGNACIO"),
        ("300642", "SAN MARCOS"),
        ("300649", "SAN MIGUEL"),
        ("300662", "SAN PABLO"),
        ("300666", "SANTA CRUZ"),
    ],
)
def test_mapea_municipalidad_por_sec_ejec_oficial_y_evidencia_provincial(entities, sec_ejec, province):
    ingester = MefIngester(entities)
    entity = next(
        candidate
        for candidate in entities
        if candidate.entity_level == "provincial_municipality"
        and candidate.province == province
    )
    raw = {
        "PLIEGO": "300",
        "SEC_EJEC": sec_ejec,
        "EJECUTORA_NOMBRE": f"MUNICIPALIDAD PROVINCIAL DE {province}",
        "PROVINCIA_EJECUTORA_NOMBRE": province,
        "NIVEL_GOBIERNO": "M",
        "DEPARTAMENTO_EJECUTORA": "06",
        "ANO_EJE": 2026,
        "MONTO_PIM": 1000,
        "MONTO_DEVENGADO": 500,
    }

    matched = ingester.ingest_records([raw], retrieved_at=NOW_UTC)
    assert len(matched) == 1
    assert matched[0].entity_id == entity.entity_id


def test_rechaza_unidad_ejecutora_distrital_aunque_comparta_provincia(entities):
    ingester = MefIngester(entities)
    raw = {
        "PLIEGO": "",
        "SEC_EJEC": "300611",
        "EJECUTORA_NOMBRE": "MUNICIPALIDAD DISTRITAL DE QUEROCOTILLO",
        "PROVINCIA_EJECUTORA_NOMBRE": "CUTERVO",
        "NIVEL_GOBIERNO": "M",
        "DEPARTAMENTO_EJECUTORA": "06",
        "ANO_EJE": 2026,
        "MONTO_PIM": 1000,
        "MONTO_DEVENGADO": 500,
    }
    assert ingester.ingest_records([raw], retrieved_at=NOW_UTC) == []


def test_rechaza_sec_ejec_fuera_de_universo_y_departamento_externo(entities):
    ingester = MefIngester(entities)
    raw = {
        "PLIEGO": "300",
        "SEC_EJEC": "300614",
        "NIVEL_GOBIERNO": "M",
        "DEPARTAMENTO_EJECUTORA": "06",
        "ANO_EJE": 2026,
        "MONTO_PIM": 1000,
        "MONTO_DEVENGADO": 500,
    }
    assert ingester.ingest_records([raw], retrieved_at=NOW_UTC) == []
    old_guess = {**raw, "SEC_EJEC": "300601", "EJECUTORA_NOMBRE": "MUNICIPALIDAD DISTRITAL DE SAN BENITO"}
    assert ingester.ingest_records([old_guess], retrieved_at=NOW_UTC) == []
    outside = {**raw, "SEC_EJEC": "300601", "DEPARTAMENTO_EJECUTORA": "15"}
    assert ingester.ingest_records([outside], retrieved_at=NOW_UTC) == []
