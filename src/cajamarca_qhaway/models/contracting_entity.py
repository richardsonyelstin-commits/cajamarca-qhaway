"""`ContractingEntity` - contrato canonico definido en `docs/sdd/constitution.md`, Articulo 19.

Este modulo implementa **exactamente** los campos que el Articulo 19 declara para
`ContractingEntity`, ni uno mas: el Articulo 6 de la constitucion prohibe que una
capacidad le anada campos por su cuenta. El registro de procedencia por entidad
(fuentes consultadas, notas de verificacion cruzada, justificacion de inclusion de una
distrital) vive en el dataset versionado (`data/entities/*.yaml`), no en este contrato
-- ver `cajamarca_qhaway.capabilities.entity_mapping.dataset` para esa capa aparte.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, model_validator

EntityLevel = Literal["regional", "provincial_municipality", "district_municipality"]

# RN-001-07: en Fase 1 el unico departamento admitido es Cajamarca (Articulo 18 de la
# constitucion: ninguna spec generaliza a otra region del Peru).
Department = Literal["CAJAMARCA"]


class ContractingEntity(BaseModel):
    """La entidad contratante verificada -- producida por `001-entity-mapping`.

    Reglas de negocio que este modelo hace cumplir estructuralmente (no solo por
    convencion de quien lo llena):

    - RN-001-04: `entity_id` es un campo opaco de solo lectura para el modelo; la
      capacidad `entity_mapping` es quien garantiza que se deriva del RUC normalizado
      (ver `cajamarca_qhaway.capabilities.entity_mapping.entity_id`). Este modelo no
      recalcula el hash: validar aqui otra vez duplicaria la fuente de verdad.
    - RN-001-05: no existe ningun metodo de borrado en este modelo. Una entidad que deja
      de operar se representa con `active=False`, nunca eliminando el registro.
    - RN-001-07: `department` es el literal fijo `"CAJAMARCA"` -- un valor distinto no
      pasa la validacion de tipo de pydantic, no hace falta un validador aparte.
    - RN-001-08: `province` es `None` unicamente cuando `entity_level == "regional"`;
      lo exige el validador `_province_solo_null_para_regional` de mas abajo.
    """

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        str_strip_whitespace=True,
        validate_assignment=True,
    )

    entity_id: str
    official_name: str
    entity_level: EntityLevel
    province: str | None
    ruc: str
    consucode_id: str | None = None
    department: Department = "CAJAMARCA"
    verified_at: datetime
    active: bool = True

    @model_validator(mode="after")
    def _ruc_es_de_once_digitos(self) -> "ContractingEntity":
        """CA-001-02: el RUC tiene exactamente 11 digitos numericos."""
        if not (len(self.ruc) == 11 and self.ruc.isdigit()):
            raise ValueError(
                f"ruc debe tener exactamente 11 digitos numericos, recibido: {self.ruc!r}"
            )
        return self

    @model_validator(mode="after")
    def _province_solo_null_para_regional(self) -> "ContractingEntity":
        """RN-001-08 / CA-001-06: `province` es `None` solo para el Gobierno Regional."""
        if self.entity_level == "regional":
            if self.province is not None:
                raise ValueError(
                    "una entidad entity_level='regional' debe tener province=None "
                    f"(recibido province={self.province!r})"
                )
        else:
            if not self.province:
                raise ValueError(
                    f"entity_level={self.entity_level!r} exige province no nulo (RN-001-08)"
                )
            if self.province not in PROVINCIAS_CAJAMARCA:
                raise ValueError(
                    f"province={self.province!r} no esta en la lista fija de las 13 "
                    "provincias de Cajamarca"
                )
        return self

    @model_validator(mode="after")
    def _entity_id_no_vacio(self) -> "ContractingEntity":
        if not self.entity_id:
            raise ValueError("entity_id no puede estar vacio")
        return self

    @model_validator(mode="after")
    def _verified_at_con_zona_horaria(self) -> "ContractingEntity":
        """`verified_at` es ISO 8601 UTC (Articulo 19): un `datetime` ingenuo no dice
        si es UTC u hora local de Peru, y eso rompe la trazabilidad que exige el
        Articulo 10 de la constitucion."""
        if self.verified_at.tzinfo is None or self.verified_at.tzinfo.utcoffset(self.verified_at) is None:
            raise ValueError("verified_at debe llevar zona horaria explicita (ISO 8601 con offset)")
        return self


# Las 13 provincias de Cajamarca, tal como las enumera `specs/001-entity-mapping/spec.md`
# (seccion "Entradas") y como aparecen en `parties[].address.region` del feed OCDS de
# OECE (sin tildes, en mayusculas -- ver
# `docs/research/2026-08-20-verificacion-tecnica-fuentes.md`, S1.2).
PROVINCIAS_CAJAMARCA: frozenset[str] = frozenset(
    {
        "CAJAMARCA",
        "CAJABAMBA",
        "CELENDIN",
        "CHOTA",
        "CONTUMAZA",
        "CUTERVO",
        "HUALGAYOC",
        "JAEN",
        "SAN IGNACIO",
        "SAN MARCOS",
        "SAN MIGUEL",
        "SAN PABLO",
        "SANTA CRUZ",
    }
)

__all__ = ["ContractingEntity", "Department", "EntityLevel", "PROVINCIAS_CAJAMARCA"]
