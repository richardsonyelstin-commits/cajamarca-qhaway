"""Fechas oficiales y dominio conservador de la regla de plazos de selección."""

from __future__ import annotations

import math
from datetime import UTC, datetime, timedelta, timezone

from cajamarca_qhaway.models import ProcurementRecord

LIMA = timezone(timedelta(hours=-5))
REGIME_TRANSITION = datetime(2025, 4, 22, tzinfo=LIMA)


def official_datetime(value: object) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    text = value.strip()
    for format_string in ('%d/%m/%Y %H:%M', '%d/%m/%Y', '%Y-%m-%d %H:%M:%S'):
        try:
            return datetime.strptime(text, format_string).replace(tzinfo=LIMA).astimezone(UTC)
        except ValueError:
            continue
    try:
        result = datetime.fromisoformat(text)
        return (result.replace(tzinfo=LIMA) if result.tzinfo is None else result).astimezone(UTC)
    except ValueError:
        try:
            serial = float(text)
            if math.isfinite(serial) and 45000 <= serial <= 47000:
                return (datetime(1899, 12, 30, tzinfo=LIMA) + timedelta(days=serial)).astimezone(UTC)
        except ValueError:
            return None
    return None


def call_date(record: ProcurementRecord) -> datetime | None:
    dates: set[datetime] = set()
    for evidence in record.source_evidence:
        row = evidence.raw_payload.get('record', {})
        value = row.get('FECHA_CONVOCATORIA') if evidence.dataset == 'convocatorias' else (
            row.get('column_2') if evidence.dataset == 'procedimientos' else None
        )
        parsed = official_datetime(value)
        if parsed:
            dates.add(parsed)
    # La precisión impresa puede variar; solo se aceptan fuentes del mismo día local.
    if len({value.astimezone(LIMA).date() for value in dates}) != 1:
        return None
    return min(dates) if dates else None


def full_competitive_minimum(record: ProcurementRecord, called_at: datetime) -> int | None:
    details = record.raw_payload.get('tender', {}).get('procurementMethodDetails')
    if details not in {'Licitación Pública', 'Concurso Público', 'Licitacion Publica', 'Concurso Publico'}:
        return None
    # DS 009-2025-EF art. 64.1; DS 344-2018-EF art. 70.1, dominio no abreviado.
    return 22
