"""Pilar 2: Base de Datos Operativa Conectada a Supabase (persistence).

Provee configuración, conexión transaccional, repositorios para los 6 modelos canónicos
y sincronización con spooling local fallback ante caídas de red.
"""

from __future__ import annotations

from cajamarca_qhaway.persistence.config import DatabaseConfig
from cajamarca_qhaway.persistence.connection import DatabaseManager
from cajamarca_qhaway.persistence.repositories import (
    AlertRepository,
    BudgetExecutionRepository,
    CitizenReportRepository,
    EntityRepository,
    ProcurementRepository,
    RedFlagRepository,
)
from cajamarca_qhaway.persistence.spool import LocalSpooler
from cajamarca_qhaway.persistence.sync import SyncManager

__all__ = [
    "DatabaseConfig",
    "DatabaseManager",
    "LocalSpooler",
    "SyncManager",
    "EntityRepository",
    "ProcurementRepository",
    "BudgetExecutionRepository",
    "RedFlagRepository",
    "AlertRepository",
    "CitizenReportRepository",
]
