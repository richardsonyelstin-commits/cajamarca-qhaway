"""`BudgetExecutionRecord` - contrato canonico definido en `docs/sdd/constitution.md`, Articulo 19.

Representa un registro de ejecucion presupuestal, por entidad y periodo fiscal (MEF).
Conserva el payload original integro en `raw_payload` (Articulo 10 de la constitucion).
"""

from __future__ import annotations

import hashlib
import math
from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from cajamarca_qhaway.models.budget_breakdown import (
    BreakdownByScope,
    BudgetBreakdownContract,
    Cut,
    CutType,
    Funding,
    Moments,
    Scope,
    Scope1,
)
from cajamarca_qhaway.models.budget_reconciliation import (
    moments_from_payload,
    validate_budget_breakdown,
)


def compute_execution_record_id(entity_id: str, fiscal_year: int, budget_category: str | None = None) -> str:
    """Deriva un identificador determinista para el registro de ejecucion presupuestal."""
    key = f"{entity_id.strip()}:{fiscal_year}:{budget_category or 'general'}"
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]
    return f"me-{digest}"


class BudgetExecutionRecord(BaseModel):
    """Contrato canonico de ejecucion presupuestal (MEF).

    Campos segun Articulo 19 de docs/sdd/constitution.md.
    """

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        str_strip_whitespace=True,
        validate_assignment=True,
    )

    execution_record_id: str
    entity_id: str
    fiscal_year: int
    budgeted_amount: float
    executed_amount: float
    budget_category: str | None = None
    raw_payload: dict[str, Any] = Field(default_factory=dict)
    source: Literal["mef-datastore", "mef-consulta-amigable"] = "mef-datastore"
    retrieved_at: datetime
    is_canonical_total: bool = False
    pia_amount: float | None = None
    certified_amount: float | None = None
    committed_annual_amount: float | None = None
    monthly_commitment_amount: float | None = None
    paid_amount: float | None = None
    modification_amount: float | None = None
    execution_pct: float | None = None
    cut_type: Literal["daily", "monthly"] | None = None
    official_cut_date: date | None = None
    breakdown_by_scope: BreakdownByScope | None = None
    breakdown_by_funding_source: list[Funding] = Field(default_factory=list)
    comparison_cuts: list[Cut] = Field(default_factory=list)

    @model_validator(mode="after")
    def _validate_invariants(self) -> BudgetExecutionRecord:
        if not self.execution_record_id.strip():
            raise ValueError("execution_record_id no puede ser vacio")
        if not self.entity_id.strip():
            raise ValueError("entity_id no puede ser vacio")
        if self.fiscal_year < 2000 or self.fiscal_year > 2100:
            raise ValueError("fiscal_year fuera del rango admitido (2000-2100)")
        if not math.isfinite(self.budgeted_amount) or self.budgeted_amount < 0:
            raise ValueError("budgeted_amount no puede ser negativo")
        if not math.isfinite(self.executed_amount) or self.executed_amount < 0:
            raise ValueError("executed_amount no puede ser negativo")
        if self.retrieved_at.tzinfo is None:
            raise ValueError("retrieved_at debe incluir informacion de zona horaria (UTC)")
        if self.is_canonical_total:
            if self.breakdown_by_scope is None or self.official_cut_date is None or self.cut_type is None:
                raise ValueError("El maestro requiere ambitos, tipo y fecha de corte oficial")
            moments = Moments.model_validate({
                name: getattr(self, name) for name in Moments.model_fields
            })
            if moments != moments_from_payload(self.raw_payload):
                raise ValueError("Los momentos tipados difieren del payload oficial")
            if (
                self.raw_payload.get("SCOPE") != "ActProy"
                or self.raw_payload.get("CUT_TYPE") != self.cut_type
                or self.raw_payload.get("FECHA_CORTE_OFICIAL") != self.official_cut_date.isoformat()
            ):
                raise ValueError("El maestro no coincide con el ambito y corte de su fuente")
            contract = BudgetBreakdownContract(
                is_canonical_total=True, cut_type=CutType(self.cut_type),
                total=Scope(
                    scope=Scope1.ActProy, moments=moments, official_cut_date=self.official_cut_date,
                    source_url=self.raw_payload.get("FUENTE_URL", ""), raw_payload=self.raw_payload,
                    breakdown_by_funding_source=self.breakdown_by_funding_source,
                ),
                breakdown_by_scope=self.breakdown_by_scope, comparison_cuts=self.comparison_cuts,
            )
            validate_budget_breakdown(contract, require_funding=True)
        return self
