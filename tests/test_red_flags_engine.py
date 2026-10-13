"""Pruebas para la capacidad 004-red-flags-engine."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from cajamarca_qhaway.capabilities.red_flags_engine import ACTIVE_INDICATORS, RedFlagsEngine
from cajamarca_qhaway.models import BudgetExecutionRecord, ProcurementRecord, RedFlag

NOW_UTC = datetime.now(timezone.utc)


@pytest.mark.contract
def test_catalogo_entre_5_y_10_indicadores():
    """CA-004-01: El catalogo de indicadores activos tiene entre 5 y 10 entradas."""
    assert 5 <= len(ACTIVE_INDICATORS) <= 10
    # Asegurar que los indicadores esenciales estan presentes
    expected = {
        "single-bidder",
        "execution-overrun",
        "contract-concentration",
        "short-tender-window",
        "direct-award-threshold",
        "direct-administration-equipment-rent",
        "contract-splitting-orders",
    }
    assert expected.issubset(set(ACTIVE_INDICATORS.keys()))
    assert len(ACTIVE_INDICATORS) == 7


@pytest.mark.contract
def test_explicabilidad_y_prohibicion_scoring_personas():
    """CA-004-04 y CA-004-05: Explicabilidad completa y prohibicion de scoring de personas."""
    engine = RedFlagsEngine()
    proc = ProcurementRecord(
        procurement_id="pr-test-1",
        ocid="ocds-test-1",
        entity_id="ce-test-1",
        title="Contratacion con unico postor",
        procurement_method="open",
        awarded_amount=100000.0,
        number_of_bidders=1,
        supplier_name="Empresa A",
        supplier_ruc="20111111111",
        raw_payload={},
        source="seace-ocds",
        retrieved_at=NOW_UTC,
    )
    flags = engine.evaluate([proc], now=NOW_UTC)
    assert len(flags) == 1
    flag = flags[0]
    assert isinstance(flag, RedFlag)

    # Explicabilidad completa (Art. 15)
    assert flag.formula_description != ""
    assert flag.threshold == 1
    assert flag.observed_value == 1
    assert flag.evidence_source == "seace-ocds"
    assert flag.evidence_retrieved_at == NOW_UTC

    # Prohibicion de scoring a personas (Art. 16): la unidad es el proceso/contrato
    assert flag.procurement_ids == ["pr-test-1"]
    assert not hasattr(flag, "person_name")
    assert not hasattr(flag, "risk_score")


def test_deteccion_execution_overrun():
    engine = RedFlagsEngine()
    # Presupuestado 1,000,000; ejecutado 1,250,000 (desvio 25% > 10% de umbral)
    budget = BudgetExecutionRecord(
        execution_record_id="me-test-1",
        entity_id="ce-test-1",
        fiscal_year=2026,
        budgeted_amount=1000000.0,
        executed_amount=1250000.0,
        budget_category="Obras",
        raw_payload={},
        source="mef-datastore",
        retrieved_at=NOW_UTC,
    )
    flags = engine.evaluate([], executions=[budget], now=NOW_UTC)
    overrun_flags = [f for f in flags if f.indicator_code == "execution-overrun"]
    assert len(overrun_flags) == 1
    f = overrun_flags[0]
    assert f.observed_value == 1.25
    assert f.execution_record_ids == ["me-test-1"]


def test_deteccion_contract_concentration():
    engine = RedFlagsEngine()
    # Entidad ce-test-1 adjudica 100,000 en total; 70,000 a un mismo proveedor (70% > 40%)
    p1 = ProcurementRecord(
        procurement_id="pr-conc-1",
        ocid="ocds-conc-1",
        entity_id="ce-test-1",
        title="Obra 1",
        awarded_amount=35000.0,
        supplier_ruc="20888888888",
        raw_payload={},
        retrieved_at=NOW_UTC,
    )
    p2 = ProcurementRecord(
        procurement_id="pr-conc-2",
        ocid="ocds-conc-2",
        entity_id="ce-test-1",
        title="Obra 2",
        awarded_amount=35000.0,
        supplier_ruc="20888888888",
        raw_payload={},
        retrieved_at=NOW_UTC,
    )
    p3 = ProcurementRecord(
        procurement_id="pr-conc-3",
        ocid="ocds-conc-3",
        entity_id="ce-test-1",
        title="Obra 3",
        awarded_amount=30000.0,
        supplier_ruc="20777777777",
        raw_payload={},
        retrieved_at=NOW_UTC,
    )
    flags = engine.evaluate([p1, p2, p3], now=NOW_UTC)
    conc_flags = [f for f in flags if f.indicator_code == "contract-concentration"]
    assert len(conc_flags) == 1
    assert conc_flags[0].observed_value == 0.70
    assert set(conc_flags[0].procurement_ids) == {"pr-conc-1", "pr-conc-2"}


def test_deteccion_direct_administration_equipment_rent():
    """Detecta cobro de maquinaria propia en obra por administracion directa."""
    engine = RedFlagsEngine()
    proc = ProcurementRecord(
        procurement_id="pr-rent-1",
        ocid="ocds-rent-1",
        entity_id="ce-test-1",
        title="Alquiler de maquinaria pesada para mantenimiento de trocha por administracion directa",
        procurement_method="directa",
        awarded_amount=38000.0,
        supplier_ruc="20143623042",
        raw_payload={"modality": "administracion directa"},
        retrieved_at=NOW_UTC,
    )
    flags = engine.evaluate([proc], now=NOW_UTC)
    rent_flags = [f for f in flags if f.indicator_code == "direct-administration-equipment-rent"]
    assert len(rent_flags) == 1
    flag = rent_flags[0]
    assert flag.threshold == 1
    assert flag.observed_value == 1
    assert flag.procurement_ids == ["pr-rent-1"]


def test_deteccion_contract_splitting_orders():
    """Detecta fraccionamiento de compras/servicios menores a 8 UIT al mismo proveedor."""
    engine = RedFlagsEngine()
    procs = [
        ProcurementRecord(
            procurement_id=f"pr-split-{i}",
            ocid=f"ocds-split-{i}",
            entity_id="ce-test-1",
            title=f"Servicio de consultoria tecnica parte {i}",
            awarded_amount=25000.0,
            supplier_ruc="20999888777",
            raw_payload={},
            retrieved_at=NOW_UTC,
        )
        for i in range(1, 4)
    ]
    flags = engine.evaluate(procs, now=NOW_UTC)
    split_flags = [f for f in flags if f.indicator_code == "contract-splitting-orders"]
    assert len(split_flags) == 1
    flag = split_flags[0]
    assert flag.observed_value == 3
    assert len(flag.procurement_ids) == 3
