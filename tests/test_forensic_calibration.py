from datetime import UTC, datetime

from cajamarca_qhaway.capabilities.red_flags_engine.engine import RedFlagsEngine
from cajamarca_qhaway.models import ProcurementRecord

NOW = datetime(2026, 10, 15, tzinfo=UTC)


def procurement(method: str | None, amount: float = 100000) -> ProcurementRecord:
    return ProcurementRecord(procurement_id='pr-calibration', ocid='ocds-calibration',
        entity_id='ce-calibration', title='Servicio de mantenimiento', procurement_method=method,
        awarded_amount=amount, number_of_bidders=1, retrieved_at=NOW,
        raw_payload={'tender': {'tenderPeriod': {'startDate': '2026-06-01T00:00:00Z',
                                               'endDate': '2026-06-02T00:00:00Z'}}})


def test_short_window_skips_direct_minor_and_unknown_methods() -> None:
    engine = RedFlagsEngine()
    for method in (None, 'direct', 'contratacion directa', 'contrato_menor'):
        flags = engine.evaluate([procurement(method)], now=NOW)
        assert not [f for f in flags if f.indicator_code in {'short-tender-window', 'single-bidder'}]
    assert not [f for f in engine.evaluate([procurement('open', 10000)], now=NOW)
                if f.indicator_code in {'short-tender-window', 'single-bidder'}]


def test_legal_uit_year_does_not_use_retrieval_timestamp() -> None:
    record = procurement('direct', 40000).model_copy(update={'raw_payload': {}})
    assert not [f for f in RedFlagsEngine().evaluate([record], now=NOW)
                if f.indicator_code == 'direct-award-threshold']


def test_offer_reception_window_is_not_assumed_to_be_call_date() -> None:
    flags = RedFlagsEngine().evaluate([procurement('open')], now=NOW)
    assert not [f for f in flags if f.indicator_code == 'short-tender-window']


def test_splitting_uses_ninety_days_sum_and_semantic_evidence() -> None:
    records = [procurement('contrato_menor', 25000).model_copy(update={
        'procurement_id': f'pr-splitting-{i}', 'ocid': f'ocds-{i}',
        'supplier_ruc': '20111111111',
        'title': title,
        'raw_payload': {'awards': [{'date': day}]},
    }) for i, (title, day) in enumerate([
        ('Orden de servicio alquiler de retroexcavadora para camino vecinal', '2026-06-01T00:00:00Z'),
        ('Orden de servicio arrendamiento de retroexcavadora para camino vecinal', '2026-07-30T00:00:00Z'),
    ])]
    flags = [f for f in RedFlagsEngine().evaluate(records, now=NOW)
             if f.indicator_code == 'contract-splitting-orders']
    assert len(flags) == 1
    assert flags[0].observed_value['total_pen'] == 50000
    assert flags[0].observed_value['cosine_similarity'] >= 0.78
    assert set(flags[0].procurement_ids) == {r.procurement_id for r in records}


def test_splitting_does_not_flag_small_total_or_mixed_fiscal_years() -> None:
    records = [procurement('contrato_menor', 1000).model_copy(update={
        'procurement_id': f'pr-small-{i}', 'supplier_ruc': '20111111111',
        'title': 'Orden de servicio alquiler de retroexcavadora',
        'raw_payload': {'awards': [{'date': f'{year}-12-15T00:00:00Z'}]},
    }) for i, year in enumerate([2024, 2025, 2026])]
    assert not [f for f in RedFlagsEngine().evaluate(records, now=NOW)
                if f.indicator_code == 'contract-splitting-orders']


def test_pentaho_orders_feed_the_engine_with_real_evidence_ids() -> None:
    from cajamarca_qhaway.models.procurement_source_record import (
        ProcurementSourceRecord,
    )
    orders = [ProcurementSourceRecord.model_validate({
        'source_evidence_id': f'pe-order-{i}', 'source_system': 'oece_pentaho_bi',
        'dataset': 'ordenes', 'fiscal_year': 2026, 'entity_id': 'ce-orders',
        'source_record_id': f'order-{i}', 'source_url': 'https://conosce.osce.gob.pe/orders.xlsx',
        'retrieved_at': NOW, 'raw_payload': {'record': {
            'moneda': 'Nuevos Soles', 'fecha_de_emision': day, 'ruc_contratista': '20111111111',
            'monto_total_orden_original': '25000.00',
            'descripcion_orden': 'Alquiler de retroexcavadora para camino vecinal',
        }},
    }) for i, day in enumerate(['2026-06-01', '2026-07-15'])]
    flags = RedFlagsEngine().evaluate([], now=NOW, source_evidence=orders)
    splitting = [f for f in flags if f.indicator_code == 'contract-splitting-orders']
    assert len(splitting) == 1
    assert splitting[0].source_evidence_ids == ['pe-order-0', 'pe-order-1']
    assert splitting[0].procurement_ids == []


def test_verified_full_competitive_call_date_supports_short_window() -> None:
    from cajamarca_qhaway.models.procurement_source_record import (
        ProcurementSourceRecord,
    )
    record = procurement('open')
    raw = record.raw_payload | {'tender': record.raw_payload['tender'] |
        {'procurementMethodDetails': 'Licitación Pública'}}
    source = ProcurementSourceRecord(source_evidence_id='pe-call', source_system='oece_pentaho_bi',
        dataset='convocatorias', fiscal_year=2026, entity_id=record.entity_id,
        source_record_id='official-call', source_url='https://bi.seace.gob.pe/official.xlsx',
        raw_payload={'record': {'FECHA_CONVOCATORIA': '25/05/2026'}}, retrieved_at=NOW)
    record = record.model_copy(update={'raw_payload': raw, 'source_evidence': [source]})
    flags = RedFlagsEngine().evaluate([record], now=NOW)
    assert len([f for f in flags if f.indicator_code == 'short-tender-window']) == 1


def test_semantic_families_do_not_lose_later_matching_objects() -> None:
    from cajamarca_qhaway.capabilities.red_flags_engine.semantic import (
        Observation,
        observation_flags,
    )
    rows = [Observation(str(i), 'ce-example', '20111111111', 25000, text, NOW,
                        'oece-pentaho', NOW, True) for i, text in enumerate([
        'Adquisición de víveres alimentos arroz',
        'Alquiler de retroexcavadora para camino vecinal',
        'Arrendamiento de retroexcavadora para camino vecinal',
    ])]
    flags = observation_flags(rows, NOW)
    assert len(flags) == 1
    assert flags[0].source_evidence_ids == ['1', '2']
