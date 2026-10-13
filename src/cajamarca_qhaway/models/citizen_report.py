"""`CitizenReport` - contrato canonico definido en `docs/sdd/constitution.md`, Articulo 19.

Representa una denuncia ciudadana entrante sujeta a moderacion humana.
Exige confirmacion obligatoria de lectura del aviso legal (CA-006-01).
"""

from __future__ import annotations

import hashlib
import re
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, model_validator

ChannelType = Literal["web", "sms", "whatsapp"]
ModerationStatus = Literal["pending", "accepted_as_lead", "rejected"]
GENERIC_MODERATORS = frozenset({"admin", "system", "root", "bot", "auto", "automated", "null", "none"})


def compute_report_id(raw_text: str, submitted_at: datetime) -> str:
    """Deriva un identificador unico para el reporte ciudadano."""
    key = f"{raw_text.strip()[:100]}:{submitted_at.isoformat()}"
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]
    return f"cr-{digest}"


class CitizenReport(BaseModel):
    """Contrato canonico de Denuncia Ciudadana.

    Campos segun Articulo 19 de docs/sdd/constitution.md.
    Invariantes:
    - RN-006-01: legal_disclaimer_shown debe ser True (CA-006-01).
    - RN-006-02: estado inicial 'pending'.
    - RN-006-03: moderacion exige moderador humano y fecha de moderacion.
    """

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        str_strip_whitespace=True,
        validate_assignment=True,
    )

    report_id: str
    submitted_at: datetime
    channel: ChannelType = "web"
    raw_text: str
    related_entity_id: str | None = None
    moderation_status: ModerationStatus = "pending"
    moderated_by: str | None = None
    moderated_at: datetime | None = None
    legal_disclaimer_shown: bool
    tracking_token_hash: str | None = None

    @model_validator(mode="after")
    def _validate_invariants(self) -> CitizenReport:
        if not self.report_id.strip():
            raise ValueError("report_id no puede ser vacio")
        if not self.raw_text.strip():
            raise ValueError("raw_text no puede ser vacio")
        if self.submitted_at.tzinfo is None:
            raise ValueError("submitted_at debe incluir informacion de zona horaria (UTC)")

        # CA-006-01: debe haberse mostrado y aceptado el descargo legal
        if not self.legal_disclaimer_shown:
            raise ValueError("legal_disclaimer_shown debe ser True para registrar la denuncia (CA-006-01)")
        if self.tracking_token_hash is not None and not re.fullmatch(
            r"[0-9a-f]{64}", self.tracking_token_hash
        ):
            raise ValueError("tracking_token_hash debe ser un digest SHA-256 hexadecimal")

        # RN-006-03: si esta moderada, exige moderador valido y fecha
        if self.moderation_status != "pending":
            if not self.moderated_by or not self.moderated_by.strip():
                raise ValueError("moderated_by es obligatorio cuando moderation_status != 'pending'")
            cleaned_moderator = self.moderated_by.strip().lower()
            if cleaned_moderator in GENERIC_MODERATORS:
                raise ValueError(f"moderated_by no puede ser un usuario generico: '{self.moderated_by}'")
            if self.moderated_at is None:
                raise ValueError("moderated_at es obligatorio cuando moderation_status != 'pending'")
            if self.moderated_at.tzinfo is None:
                raise ValueError("moderated_at debe incluir informacion de zona horaria (UTC)")
        else:
            if self.moderated_by is not None or self.moderated_at is not None:
                raise ValueError("moderated_by y moderated_at deben ser None cuando moderation_status es 'pending'")

        return self
