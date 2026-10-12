"""`RedFlag` — contrato canonico definido en `docs/sdd/constitution.md`, Articulo 19.

Representa un indicador de riesgo activado sobre contrataciones o ejecucion presupuestal.
Nunca es un score compuesto ni evalua personas individuales (Articulo 16).
Nunca posee campo status ni admite 'published' (CA-004-06).
"""

from __future__ import annotations

import hashlib
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


def compute_red_flag_id(indicator_code: str, target_ref: str, timestamp_str: str) -> str:
    """Deriva un identificador determinista para una bandera roja."""
    key = f"{indicator_code.strip()}:{target_ref.strip()}:{timestamp_str.strip()}"
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]
    return f"rf-{digest}"


class RedFlag(BaseModel):
    """Contrato canonico de indicador de riesgo (RedFlag).

    Campos segun Articulo 19 de docs/sdd/constitution.md.
    Invariante: Explicabilidad completa (Art. 15), Prohibicion de scoring a personas (Art. 16).
    """

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        str_strip_whitespace=True,
        validate_assignment=True,
    )

    red_flag_id: str
    indicator_code: str
    formula_description: str
    threshold: Any
    observed_value: Any
    procurement_ids: list[str] = Field(default_factory=list)
    execution_record_ids: list[str] = Field(default_factory=list)
    evidence_source: str
    evidence_retrieved_at: datetime
    generated_at: datetime

    @model_validator(mode="after")
    def _validate_invariants(self) -> RedFlag:
        if not self.red_flag_id.strip():
            raise ValueError("red_flag_id no puede ser vacio")
        if not self.indicator_code.strip():
            raise ValueError("indicator_code no puede ser vacio")
        if not self.formula_description.strip():
            raise ValueError("formula_description no puede ser vacio (Articulo 15)")
        if not self.procurement_ids and not self.execution_record_ids:
            raise ValueError("Debe incluir al menos un procurement_id o execution_record_id como evidencia")
        if self.evidence_retrieved_at.tzinfo is None:
            raise ValueError("evidence_retrieved_at debe incluir informacion de zona horaria (UTC)")
        if self.generated_at.tzinfo is None:
            raise ValueError("generated_at debe incluir informacion de zona horaria (UTC)")
        return self
