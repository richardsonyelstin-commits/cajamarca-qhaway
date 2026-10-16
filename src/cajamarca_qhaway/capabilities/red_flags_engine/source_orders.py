"""Evalúa órdenes oficiales sin inventar OCID ni registros OCDS intermediarios."""

from __future__ import annotations

import math
from collections.abc import Sequence
from datetime import datetime

from cajamarca_qhaway.capabilities.red_flags_engine.legal_calibration import (
    official_datetime,
)
from cajamarca_qhaway.capabilities.red_flags_engine.semantic import (
    Observation,
    observation_flags,
)
from cajamarca_qhaway.capabilities.seace_ingestion.official_sources import _field
from cajamarca_qhaway.models import RedFlag
from cajamarca_qhaway.models.procurement_source_record import ProcurementSourceRecord


def evaluate_orders(records: Sequence[ProcurementSourceRecord], now: datetime) -> list[RedFlag]:
    observations = []
    for record in records:
        if record.dataset != 'ordenes' or record.source_system != 'oece_pentaho_bi':
            continue
        row = record.raw_payload.get('record', {})
        if not isinstance(row, dict):
            continue
        currency = _field(row, 'MONEDA').strip().upper()
        if currency not in {'SOLES', 'NUEVOS SOLES', 'SOL', 'PEN', 'S/'}:
            continue
        if any(word in _field(row, 'ESTADOCONTRATACION').upper() for word in ('ANUL', 'CANCEL')):
            continue
        when = official_datetime(_field(row, 'FECHA_DE_EMISION'))
        supplier = _field(row, 'RUC_CONTRATISTA')
        if when is None or when.year != record.fiscal_year or len(supplier) != 11 or not supplier.isdigit():
            continue
        try:
            amount = float(_field(row, 'MONTO_TOTAL_ORDEN_ORIGINAL').replace(',', ''))
        except ValueError:
            continue
        text = _field(row, 'DESCRIPCION_ORDEN')
        if not text or not math.isfinite(amount) or amount <= 0:
            continue
        observations.append(Observation(record.source_evidence_id, record.entity_id, supplier,
            amount, text, when, str(record.source_system), record.retrieved_at, True))
    return observation_flags(observations, now)
