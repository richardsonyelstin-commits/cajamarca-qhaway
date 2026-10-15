"""Separa la disponibilidad del buscador publico de la cosecha primaria OECE."""

from __future__ import annotations

from dataclasses import dataclass

from cajamarca_qhaway.capabilities.seace_ingestion.official_sources import (
    OfficialSourceUnavailable,
    SEACEBuscadorPublicoClient,
)
from cajamarca_qhaway.models import ContractingEntity
from cajamarca_qhaway.models.procurement_source_record import ProcurementSourceRecord


@dataclass(frozen=True)
class PublicSourceProbeResult:
    status: str
    records: list[ProcurementSourceRecord]


async def probe_public_source(
    client: SEACEBuscadorPublicoClient, entity: ContractingEntity, year: int,
) -> PublicSourceProbeResult:
    try:
        records = await client.search(entity, year)
    except OfficialSourceUnavailable as error:
        return PublicSourceProbeResult(status=str(error), records=[])
    return PublicSourceProbeResult(status="CAPTURED", records=records)
