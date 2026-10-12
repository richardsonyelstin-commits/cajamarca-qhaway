"""Capacidad 003-mef-ingestion — Ingesta de ejecucion presupuestal (MEF)."""

from __future__ import annotations

from cajamarca_qhaway.capabilities.mef_ingestion.ingester import MefIngester
from cajamarca_qhaway.capabilities.mef_ingestion.parser import parse_mef_record

__all__ = [
    "MefIngester",
    "parse_mef_record",
]
