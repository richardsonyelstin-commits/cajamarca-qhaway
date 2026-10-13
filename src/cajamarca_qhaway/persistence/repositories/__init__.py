"""Exportaciones de repositorios canónicos para Cajamarca Qhaway (Pilar 2)."""

from __future__ import annotations

from cajamarca_qhaway.persistence.repositories.alert_repository import AlertRepository
from cajamarca_qhaway.persistence.repositories.budget_execution_repository import BudgetExecutionRepository
from cajamarca_qhaway.persistence.repositories.citizen_report_repository import CitizenReportRepository
from cajamarca_qhaway.persistence.repositories.entity_repository import EntityRepository
from cajamarca_qhaway.persistence.repositories.procurement_repository import ProcurementRepository
from cajamarca_qhaway.persistence.repositories.red_flag_repository import RedFlagRepository

__all__ = [
    "EntityRepository",
    "ProcurementRepository",
    "BudgetExecutionRepository",
    "RedFlagRepository",
    "AlertRepository",
    "CitizenReportRepository",
]
