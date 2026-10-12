"""`Alert` — contrato canonico definido en `docs/sdd/constitution.md`, Articulo 19.

Lo unico que puede llegar al dashboard publico o publicarse.
Nunca existe sin revision humana explicita (Articulo 14 de la constitucion).
"""

from __future__ import annotations

import hashlib
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

STANDARD_ALERT_DISCLAIMER = (
    "Indicador de riesgo automatizado, no constituye prueba ni acusación formal de corrupción."
)

GENERIC_REVIEWERS = frozenset({"admin", "system", "root", "bot", "auto", "automated", "null", "none"})


def compute_alert_id(entity_id: str, red_flag_ids: list[str]) -> str:
    """Deriva un identificador determinista para la alerta."""
    sorted_ids = sorted(rf.strip() for rf in red_flag_ids)
    key = f"{entity_id.strip()}:{','.join(sorted_ids)}"
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]
    return f"al-{digest}"


class Alert(BaseModel):
    """Contrato canonico de Alerta ciudadana revisada.

    Campos segun Articulo 19 de docs/sdd/constitution.md.
    Invariantes:
    - RN-005-01: ninguna alerta existe sin accion humana explicita.
    - RN-005-02: reviewed_by no puede ser generico (CA-005-02).
    - RN-005-03: descargo legal obligatorio e inmutable.
    - RN-005-04: review_notes obligatorio si status == 'discarded'.
    """

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        str_strip_whitespace=True,
        validate_assignment=True,
    )

    alert_id: str
    red_flag_ids: list[str] = Field(min_length=1)
    entity_id: str
    status: Literal["published", "discarded"]
    reviewed_by: str
    reviewed_at: datetime
    review_notes: str | None = None
    disclaimer: str = STANDARD_ALERT_DISCLAIMER
    published_at: datetime | None = None

    @model_validator(mode="after")
    def _validate_invariants(self) -> Alert:
        if not self.alert_id.strip():
            raise ValueError("alert_id no puede ser vacio")
        if not self.entity_id.strip():
            raise ValueError("entity_id no puede ser vacio")
        if not self.red_flag_ids:
            raise ValueError("red_flag_ids debe contener al menos un identificador")

        # CA-005-02: reviewed_by no puede ser generico ni vacio
        cleaned_reviewer = self.reviewed_by.strip().lower()
        if not cleaned_reviewer or cleaned_reviewer in GENERIC_REVIEWERS:
            raise ValueError(
                f"reviewed_by debe identificar a un revisor humano valido, no admitido: '{self.reviewed_by}'"
            )

        if self.reviewed_at.tzinfo is None:
            raise ValueError("reviewed_at debe incluir informacion de zona horaria (UTC)")

        # CA-005-04: review_notes obligatorio si status == discarded
        if self.status == "discarded":
            if not self.review_notes or not self.review_notes.strip():
                raise ValueError("review_notes es obligatorio cuando el estado es 'discarded'")
            if self.published_at is not None:
                raise ValueError("published_at debe ser None cuando status == 'discarded'")

        # CA-005-03: si es published, published_at es obligatorio
        if self.status == "published":
            if self.published_at is None:
                raise ValueError("published_at es obligatorio cuando status == 'published'")
            if self.published_at.tzinfo is None:
                raise ValueError("published_at debe incluir informacion de zona horaria (UTC)")

        # RN-005-03: el disclaimer legal debe ser preservado
        if self.disclaimer != STANDARD_ALERT_DISCLAIMER:
            raise ValueError(f"disclaimer no coincide con el texto legal obligatorio: '{STANDARD_ALERT_DISCLAIMER}'")

        return self
