"""Capacidad 004-red-flags-engine — Motor de banderas rojas anticorrupcion."""

from __future__ import annotations

from cajamarca_qhaway.capabilities.red_flags_engine.catalog import (
    ACTIVE_INDICATORS,
    IndicatorDefinition,
)
from cajamarca_qhaway.capabilities.red_flags_engine.engine import RedFlagsEngine

__all__ = [
    "ACTIVE_INDICATORS",
    "IndicatorDefinition",
    "RedFlagsEngine",
]
