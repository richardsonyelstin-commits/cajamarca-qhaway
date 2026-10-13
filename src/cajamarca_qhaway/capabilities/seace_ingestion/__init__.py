"""Capacidad 002-seace-ingestion — Ingesta de contrataciones publicas SEACE/OCDS."""

from __future__ import annotations

from cajamarca_qhaway.capabilities.seace_ingestion.ingester import SeaceIngester
from cajamarca_qhaway.capabilities.seace_ingestion.parser import (
    find_matching_entity,
    is_cajamarca_release,
    parse_ocds_release,
)

__all__ = [
    "SeaceIngester",
    "find_matching_entity",
    "is_cajamarca_release",
    "parse_ocds_release",
]
