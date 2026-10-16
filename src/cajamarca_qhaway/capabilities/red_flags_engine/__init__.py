"""Capacidad 004-red-flags-engine - Motor de banderas rojas anticorrupcion."""

from __future__ import annotations

from cajamarca_qhaway.capabilities.red_flags_engine.catalog import (
    ACTIVE_INDICATORS,
    UIT_BY_FISCAL_YEAR,
    IndicatorDefinition,
    uit_value,
)
from cajamarca_qhaway.capabilities.red_flags_engine.engine import RedFlagsEngine

__all__ = [
    "ACTIVE_INDICATORS",
    "UIT_BY_FISCAL_YEAR",
    "IndicatorDefinition",
    "RedFlagsEngine",
    "uit_value",
]
