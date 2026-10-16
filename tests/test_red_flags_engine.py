"""Pruebas para la capacidad 004-red-flags-engine."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from cajamarca_qhaway.capabilities.red_flags_engine import ACTIVE_INDICATORS, RedFlagsEngine, uit_value
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
    assert len(ACTIVE_INDICATORS) == 10
    assert {"mef-underspending", "recurrent-direct-award", "hhi-concentration"}.issubset(ACTIVE_INDICATORS)


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
            title=f"Orden de servicio de consultoria tecnica parte {i}",
            awarded_amount=25000.0,
            supplier_ruc="20999888777",
            raw_payload={"awards": [{"date": "2026-06-01T00:00:00Z"}]},
            retrieved_at=NOW_UTC,
        )
        for i in range(1, 4)
    ]
    flags = engine.evaluate(procs, now=NOW_UTC)
    split_flags = [f for f in flags if f.indicator_code == "contract-splitting-orders"]
    assert len(split_flags) == 1
    flag = split_flags[0]
    assert flag.observed_value["count"] == 3
    assert flag.observed_value["total_pen"] == 75000
    assert len(flag.procurement_ids) == 3


@pytest.mark.parametrize("year,expected", [(2024, 5150), (2025, 5350), (2026, 5500)])
def test_uit_se_resuelve_por_ejercicio_fiscal(year: int, expected: int) -> None:
    assert uit_value(year) == expected


def test_uit_rechaza_ejercicio_sin_valor_verificado() -> None:
    with pytest.raises(ValueError, match="No hay valor de UIT verificado"):
        uit_value(2027)


def test_mef_underspending_evalua_ejercicio_cerrado_y_omite_pim_cero() -> None:
    engine = RedFlagsEngine()
    records = [
        BudgetExecutionRecord(
            execution_record_id=f"me-close-{idx}", entity_id="ce-test-1", fiscal_year=2025,
            budgeted_amount=pim, executed_amount=spent, budget_category="Obras",
            raw_payload={"PIM": pim, "DEVENGADO": spent}, retrieved_at=NOW_UTC,
        )
        for idx, pim, spent in ((1, 1000, 200), (2, 0, 0))
    ]
    current = engine.evaluate([], records, now=datetime(2026, 6, 1, tzinfo=timezone.utc))
    flags = [flag for flag in current if flag.indicator_code == "mef-underspending"]
    assert len(flags) == 1
    assert flags[0].observed_value == 0.8
    assert flags[0].threshold_value == 0.5
    assert set(flags[0].execution_record_ids) == {"me-close-1", "me-close-2"}
    open_year = engine.evaluate([], records, now=datetime(2025, 12, 31, tzinfo=timezone.utc))
    assert not [flag for flag in open_year if flag.indicator_code == "mef-underspending"]


def test_mef_underspending_admite_corte_oficial_vencido_del_ejercicio_abierto() -> None:
    engine = RedFlagsEngine()
    record = BudgetExecutionRecord(
        execution_record_id="me-open-official-cut",
        entity_id="ce-test-open-year",
        fiscal_year=2026,
        budgeted_amount=100,
        executed_amount=25,
        budget_category="TOTAL",
        source="mef-consulta-amigable",
        raw_payload={"FECHA_CORTE_OFICIAL": "2026-09-30"},
        retrieved_at=datetime(2026, 10, 1, tzinfo=timezone.utc),
    )
    flags = engine.evaluate(
        [], [record], now=datetime(2026, 10, 14, tzinfo=timezone.utc)
    )
    underspending = [flag for flag in flags if flag.indicator_code == "mef-underspending"]
    assert len(underspending) == 1
    assert underspending[0].observed_value == 0.75
    assert underspending[0].execution_record_ids == [record.execution_record_id]


def test_mef_underspending_omite_ejercicio_abierto_sin_corte_oficial() -> None:
    engine = RedFlagsEngine()
    record = BudgetExecutionRecord(
        execution_record_id="me-open-no-cut",
        entity_id="ce-test-open-year",
        fiscal_year=2026,
        budgeted_amount=100,
        executed_amount=25,
        budget_category="TOTAL",
        raw_payload={},
        retrieved_at=datetime(2026, 10, 1, tzinfo=timezone.utc),
    )
    flags = engine.evaluate(
        [], [record], now=datetime(2026, 10, 14, tzinfo=timezone.utc)
    )
    assert not [flag for flag in flags if flag.indicator_code == "mef-underspending"]


def test_recurrent_direct_award_requires_confirmed_method_date_and_ruc() -> None:
    engine = RedFlagsEngine()
    records = [
        ProcurementRecord(
            procurement_id=f"pr-rec-{idx}", ocid=f"ocds-rec-{idx}", entity_id="ce-test-1",
            title="Servicio directo", procurement_method="contratación directa",
            awarded_amount=1000, supplier_ruc="20111111111",
            raw_payload={"awards": [{"date": f"2025-0{idx}-10T00:00:00Z"}]},
            retrieved_at=NOW_UTC,
        ) for idx in range(1, 4)
    ]
    result = engine.evaluate(records, now=NOW_UTC)
    flags = [flag for flag in result if flag.indicator_code == "recurrent-direct-award"]
    assert len(flags) == 1
    assert flags[0].observed_value == 3
    assert len(flags[0].procurement_ids) == 3

    no_ruc = records[0].model_copy(update={"procurement_id": "pr-no-ruc", "supplier_ruc": None})
    assert not [flag for flag in engine.evaluate([*records[:2], no_ruc], now=NOW_UTC) if flag.indicator_code == "recurrent-direct-award"]


def test_hhi_usa_escala_cero_a_diez_mil_y_omite_cero_y_cobertura_incompleta() -> None:
    engine = RedFlagsEngine()
    awards = [
        ProcurementRecord(
            procurement_id=f"pr-hhi-{idx}", ocid=f"ocds-hhi-{idx}", entity_id="ce-test-1",
            title="Adjudicacion", procurement_method="open", awarded_amount=amount,
            supplier_ruc=ruc, raw_payload={"awards": [{"date": "2025-06-10T00:00:00Z"}]},
            retrieved_at=NOW_UTC,
        ) for idx, amount, ruc in ((1, 60, "20111111111"), (2, 20, "20222222222"), (3, 20, "20333333333"))
    ]
    result = engine.evaluate(awards, now=NOW_UTC)
    flags = [flag for flag in result if flag.indicator_code == "hhi-concentration"]
    assert len(flags) == 1
    assert flags[0].observed_value == 4400
    assert flags[0].threshold_value == 2500
    incomplete = [*awards, awards[0].model_copy(update={"procurement_id": "pr-unknown", "awarded_amount": 10, "supplier_ruc": None})]
    assert not [flag for flag in engine.evaluate(incomplete, now=NOW_UTC) if flag.indicator_code == "hhi-concentration"]
