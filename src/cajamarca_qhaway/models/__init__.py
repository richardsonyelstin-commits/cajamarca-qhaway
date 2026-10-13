"""Contratos canonicos de cajamarca-qhaway (Articulo 19 de `docs/sdd/constitution.md`).

Exporta los seis modelos canonicos compartidos:
- `ContractingEntity`
- `ProcurementRecord`
- `BudgetExecutionRecord`
- `RedFlag`
- `Alert`
- `CitizenReport`
"""

from __future__ import annotations

from cajamarca_qhaway.models.alert import Alert, STANDARD_ALERT_DISCLAIMER, compute_alert_id
from cajamarca_qhaway.models.budget_execution_record import (
    BudgetExecutionRecord,
    compute_execution_record_id,
)
from cajamarca_qhaway.models.citizen_report import (
    ChannelType,
    CitizenReport,
    ModerationStatus,
    compute_report_id,
)
from cajamarca_qhaway.models.contracting_entity import ContractingEntity, EntityLevel
from cajamarca_qhaway.models.procurement_record import ProcurementRecord, compute_procurement_id
from cajamarca_qhaway.models.red_flag import RedFlag, compute_red_flag_id

__all__ = [
    "Alert",
    "BudgetExecutionRecord",
    "ChannelType",
    "CitizenReport",
    "ContractingEntity",
    "EntityLevel",
    "ModerationStatus",
    "ProcurementRecord",
    "RedFlag",
    "STANDARD_ALERT_DISCLAIMER",
    "compute_alert_id",
    "compute_execution_record_id",
    "compute_procurement_id",
    "compute_red_flag_id",
    "compute_report_id",
]
