"""Modulo web de Cajamarca Qhaway.

Provee integracion backend, servidor HTTP local y exportacion del
snapshot verificado de datos canonicos.
"""

from __future__ import annotations

from cajamarca_qhaway.web.exporter import (
    build_verified_web_snapshot,
    export_verified_snapshot,
)
from cajamarca_qhaway.web.server import run_server

__all__ = [
    "build_verified_web_snapshot",
    "export_verified_snapshot",
    "run_server",
]
