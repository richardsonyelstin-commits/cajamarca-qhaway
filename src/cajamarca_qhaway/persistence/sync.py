"""Gestor de sincronización idempotente con soporte de Spooling Fallback (Pilar 2)."""

from __future__ import annotations

import logging
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from cajamarca_qhaway.capabilities.entity_mapping.dataset import load_universe
from cajamarca_qhaway.models import BudgetExecutionRecord, ProcurementRecord
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

logger = logging.getLogger("cajamarca_qhaway.persistence")


class SyncManager:
    """Coordina la persistencia transaccional y el desahogo de spool local."""

    def __init__(self, config: DatabaseConfig | None = None) -> None:
        self.config = config or DatabaseConfig()
        self.db = DatabaseManager(self.config)
        self.spooler = LocalSpooler(self.config.spool_dir)

        # Repositorios
        self.entities = EntityRepository(self.db)
        self.procurements = ProcurementRepository(self.db)
        self.budget_executions = BudgetExecutionRepository(self.db)
        self.red_flags = RedFlagRepository(self.db)
        self.alerts = AlertRepository(self.db)
        self.citizen_reports = CitizenReportRepository(self.db)

    def sync_procurements(self, records: Sequence[ProcurementRecord]) -> tuple[int, bool]:
        """Sincroniza contrataciones a la base de datos o deriva a spool local si falla."""
        if not records:
            return 0, False

        try:
            count = self.procurements.upsert_many(records)
            return count, False
        except Exception as e:
            logger.warning("Fallo en BD al sincronizar contrataciones: %s. Derivando a spool local.", e)
            if self.config.spool_enabled:
                self.spooler.spool_procurements(records)
                return len(records), True
            raise

    def sync_budget_executions(self, records: Sequence[BudgetExecutionRecord]) -> tuple[int, bool]:
        """Sincroniza ejecuciones presupuestales a la BD o deriva a spool local si falla."""
        if not records:
            return 0, False

        try:
            count = self.budget_executions.upsert_many(records)
            return count, False
        except Exception as e:
            logger.warning("Fallo en BD al sincronizar ejecuciones presupuestales: %s. Derivando a spool local.", e)
            if self.config.spool_enabled:
                self.spooler.spool_budget_executions(records)
                return len(records), True
            raise

    def seed_universe_entities(self, universe_path: Path | None = None) -> int:
        """Siembra el universo dorado de 14 entidades en la tabla contracting_entities."""
        universe = load_universe(universe_path)
        count = self.entities.upsert_many(universe.contracting_entities)
        return count

    def flush_spool(self) -> dict[str, int]:
        """Desahoga ficheros de spool pendientes hacia la base de datos."""
        pending_files = self.spooler.list_pending_files()
        flushed_procurements = 0
        flushed_executions = 0

        for file_path in pending_files:
            items = self.spooler.read_and_remove(file_path)
            if not items:
                continue

            if "procurements" in file_path.name:
                recs = [ProcurementRecord(**it) for it in items]
                flushed_procurements += self.procurements.upsert_many(recs)
            elif "budget_executions" in file_path.name:
                recs = [BudgetExecutionRecord(**it) for it in items]
                flushed_executions += self.budget_executions.upsert_many(recs)

        return {
            "flushed_procurements": flushed_procurements,
            "flushed_executions": flushed_executions,
            "remaining_spool_files": len(self.spooler.list_pending_files()),
        }

    def status(self) -> dict[str, Any]:
        """Reporta el estado y conteos de la base de datos operativa."""
        active_entities = len(self.entities.list_active())
        total_procurements = self.procurements.count()
        total_executions = self.budget_executions.count()
        pending_spool = len(self.spooler.list_pending_files())

        return {
            "is_postgres": self.db.is_postgres,
            "active_entities": active_entities,
            "total_procurements": total_procurements,
            "total_budget_executions": total_executions,
            "pending_spool_files": pending_spool,
        }
