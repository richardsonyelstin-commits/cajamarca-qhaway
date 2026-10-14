"""Modelos de datos tipados Pydantic v2 para el enriquecimiento SUNAT RUC.

Cumple con Art. 6 y Art. 19 (modelos canonicos intactos), Art. 10 (trazabilidad raw_payload)
y Art. 16 (invariante de no perfilamiento de personas naturales).
"""

from __future__ import annotations

from typing import Any
from pydantic import BaseModel, ConfigDict, Field, model_validator

from cajamarca_qhaway.capabilities.sunat_enrichment.validator import (
    assert_ruc_not_dni,
    validate_ruc_checksum,
)


class SunatRucProfile(BaseModel):
    """Perfil tributario y registral inmutable para entidades y proveedores de Cajamarca."""

    model_config = ConfigDict(frozen=True)

    ruc: str = Field(description="Numero de RUC de 11 digitos validado")
    razon_social: str = Field(description="Razon social o denominacion oficial registrada en SUNAT")
    estado_contribuyente: str = Field(description="Estado del contribuyente informado por SUNAT")
    condicion_domicilio: str = Field(description="Condicion de domicilio fiscal informada por SUNAT")
    tipo_contribuyente: str | None = Field(default=None, description="Tipo de contribuyente segun clasificacion SUNAT")
    direccion_fiscal: str | None = Field(default=None, description="Direccion fiscal registrada")
    ubigeo: str | None = Field(default=None, description="Codigo ubigeo INEI de 6 digitos")
    departamento: str | None = Field(default=None, description="Departamento del domicilio fiscal")
    provincia: str | None = Field(default=None, description="Provincia del domicilio fiscal")
    distrito: str | None = Field(default=None, description="Distrito del domicilio fiscal")
    es_entidad_publica: bool = Field(default=False, description="True si corresponde a una entidad estatal de Cajamarca")
    risk_signals: tuple[str, ...] = Field(default=(), description="Alertas objetivas sobre estado tributario o identificacion")
    source_provider: str = Field(description="Identificador de la fuente verificable")
    queried_at: str = Field(description="Fecha y hora de enriquecimiento en formato ISO 8601 UTC")
    raw_payload: dict[str, Any] = Field(description="Payload integro de origen para auditoria (Art. 10)")

    @model_validator(mode="before")
    @classmethod
    def validate_and_enrich_signals(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data

        raw_ruc = str(data.get("ruc", "")).strip().replace("PE-RUC-", "")
        # Guarda Art. 16: rechaza DNI terminantemente
        assert_ruc_not_dni(raw_ruc)

        if len(raw_ruc) != 11 or not raw_ruc.isdigit():
            raise ValueError(f"RUC debe ser un identificador de 11 digitos numericos, recibido: '{raw_ruc}'")

        data["ruc"] = raw_ruc

        signals: list[str] = list(data.get("risk_signals", ()))

        # Evaluar digito verificador modulo 11
        if not validate_ruc_checksum(raw_ruc):
            signal = "DIGITO_VERIFICADOR_INVALIDO"
            if signal not in signals:
                signals.append(signal)

        # Evaluar estado de contribuyente
        estado = str(data.get("estado_contribuyente", "ACTIVO")).strip().upper()
        if estado and estado != "ACTIVO":
            signal = f"ESTADO_NO_ACTIVO: {estado}"
            if signal not in signals:
                signals.append(signal)

        # Evaluar condicion de domicilio
        condicion = str(data.get("condicion_domicilio", "HABIDO")).strip().upper()
        if condicion and condicion in ("NO HABIDO", "NO HALLADO"):
            signal = f"CONDICION_IRREGULAR: {condicion}"
            if signal not in signals:
                signals.append(signal)

        data["risk_signals"] = tuple(signals)
        return data

    @property
    def has_risks(self) -> bool:
        """Indica si el perfil contiene al menos una senal de riesgo fiscal objetiva."""
        return len(self.risk_signals) > 0
