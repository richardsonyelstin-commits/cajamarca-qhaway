"""`Alert` - contrato canonico definido en `docs/sdd/constitution.md`, Articulo 19.

Lo unico que puede llegar al dashboard publico o publicarse.
Nunca existe sin revision humana explicita (Articulo 14 de la constitucion).
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timedelta
from typing import Literal

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, model_validator

STANDARD_ALERT_DISCLAIMER = (
    "Indicador de riesgo automatizado, no constituye prueba ni acusación formal de corrupción."
)

GENERIC_REVIEWERS = frozenset({"admin", "system", "root", "bot", "auto", "automated", "null", "none"})


class AlertEvidence(BaseModel):
    """Evidencia de un RedFlag, copiada en la alerta para conservar explicabilidad."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    red_flag_id: str
    formula_description: str = Field(min_length=1)
    observed_value: object
    threshold_value: object = Field(
        validation_alias=AliasChoices("threshold_value", "threshold")
    )
    retrieved_at: datetime = Field(
        validation_alias=AliasChoices("retrieved_at", "evidence_retrieved_at")
    )
    evidence_source: str = Field(min_length=1)

    @model_validator(mode="after")
    def _validate_retrieved_at(self) -> AlertEvidence:
        if self.retrieved_at.utcoffset() != timedelta(0):
            raise ValueError("retrieved_at debe estar expresado en UTC")
        return self


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
    - review_notes is required for every human decision.
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
    review_notes: str = Field(min_length=1)
    legal_disclaimer: str = Field(
        default=STANDARD_ALERT_DISCLAIMER,
        validation_alias=AliasChoices("legal_disclaimer", "disclaimer"),
    )
    evidence: list[AlertEvidence] = Field(default_factory=list)
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

        if self.reviewed_at.utcoffset() != timedelta(0):
            raise ValueError("reviewed_at debe estar expresado en UTC")

        if not self.review_notes.strip():
            raise ValueError("review_notes es obligatorio y no puede estar vacio")

        # CA-005-04: review_notes obligatorio si status == discarded
        if self.status == "discarded":
            if self.published_at is not None:
                raise ValueError("published_at debe ser None cuando status == 'discarded'")

        # CA-005-03: si es published, published_at es obligatorio
        evidence_ids = {item.red_flag_id for item in self.evidence}
        if not evidence_ids or evidence_ids != set(self.red_flag_ids):
            raise ValueError("Toda alerta exige evidencia completa de cada RedFlag asociado")

        if self.status == "published":
            if self.published_at is None:
                raise ValueError("published_at es obligatorio cuando status == 'published'")
            if self.published_at.utcoffset() != timedelta(0):
                raise ValueError("published_at debe estar expresado en UTC")

        # RN-005-03: el disclaimer legal debe ser preservado
        if self.legal_disclaimer != STANDARD_ALERT_DISCLAIMER:
            raise ValueError(
                "legal_disclaimer no coincide con el texto obligatorio: "
                f"'{STANDARD_ALERT_DISCLAIMER}'"
            )

        return self

    @property
    def disclaimer(self) -> str:
        """Compatibilidad de lectura con consumidores del campo canónico anterior."""
        return self.legal_disclaimer
