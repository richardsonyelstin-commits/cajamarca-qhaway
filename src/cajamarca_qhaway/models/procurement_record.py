"""`ProcurementRecord` - contrato canonico definido en `docs/sdd/constitution.md`, Articulo 19.

Representa un proceso o contrato de contratacion publica, alineado a OCDS.
Conserva el payload original integro en `raw_payload` (Articulo 10 de la constitucion).
"""

from __future__ import annotations

import hashlib
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from cajamarca_qhaway.models.procurement_source_record import ProcurementSourceRecord


def compute_procurement_id(ocid: str) -> str:
    """Deriva un identificador determinista estable a partir del OCID."""
    digest = hashlib.sha256(ocid.strip().encode("utf-8")).hexdigest()[:16]
    return f"pr-{digest}"


class ProcurementRecord(BaseModel):
    """Contrato canonico de contratacion publica (SEACE/OCDS).

    Campos segun Articulo 19 de docs/sdd/constitution.md.
    """

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        str_strip_whitespace=True,
        validate_assignment=True,
    )

    procurement_id: str
    ocid: str
    entity_id: str
    title: str
    procurement_method: str | None = None
    awarded_amount: float | None = None
    executed_amount: float | None = None
    number_of_bidders: int | None = None
    supplier_name: str | None = None
    supplier_ruc: str | None = None
    raw_payload: dict[str, Any] = Field(default_factory=dict)
    source: Literal["seace-ocds"] = "seace-ocds"
    retrieved_at: datetime
    source_evidence: list[ProcurementSourceRecord] = Field(default_factory=list)

    @model_validator(mode="after")
    def _validate_invariants(self) -> ProcurementRecord:
        for evidence in self.source_evidence:
            if evidence.entity_id != self.entity_id or evidence.procurement_id != self.procurement_id:
                raise ValueError("La evidencia no corresponde al proceso y entidad canonicos")
        if len({item.source_evidence_id for item in self.source_evidence}) != len(self.source_evidence):
            raise ValueError("Evidencia de contratacion duplicada")
        if not self.procurement_id.strip():
            raise ValueError("procurement_id no puede ser vacio")
        if not self.ocid.strip():
            raise ValueError("ocid no puede ser vacio")
        if not self.entity_id.strip():
            raise ValueError("entity_id no puede ser vacio")
        if self.retrieved_at.tzinfo is None:
            raise ValueError("retrieved_at debe incluir informacion de zona horaria (UTC)")
        if self.awarded_amount is not None and self.awarded_amount < 0:
            raise ValueError("awarded_amount no puede ser negativo")
        if self.executed_amount is not None and self.executed_amount < 0:
            raise ValueError("executed_amount no puede ser negativo")
        if self.number_of_bidders is not None and self.number_of_bidders < 0:
            raise ValueError("number_of_bidders no puede ser negativo")
        return self
