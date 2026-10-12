"""`BudgetExecutionRecord` — contrato canonico definido en `docs/sdd/constitution.md`, Articulo 19.

Representa un registro de ejecucion presupuestal, por entidad y periodo fiscal (MEF).
Conserva el payload original integro en `raw_payload` (Articulo 10 de la constitucion).
"""

from __future__ import annotations

import hashlib
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


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
    source: Literal["mef-datastore"] = "mef-datastore"
    retrieved_at: datetime

    @model_validator(mode="after")
    def _validate_invariants(self) -> BudgetExecutionRecord:
        if not self.execution_record_id.strip():
            raise ValueError("execution_record_id no puede ser vacio")
        if not self.entity_id.strip():
            raise ValueError("entity_id no puede ser vacio")
        if self.fiscal_year < 2000 or self.fiscal_year > 2100:
            raise ValueError("fiscal_year fuera del rango admitido (2000-2100)")
        if self.budgeted_amount < 0:
            raise ValueError("budgeted_amount no puede ser negativo")
        if self.executed_amount < 0:
            raise ValueError("executed_amount no puede ser negativo")
        if self.retrieved_at.tzinfo is None:
            raise ValueError("retrieved_at debe incluir informacion de zona horaria (UTC)")
        return self
