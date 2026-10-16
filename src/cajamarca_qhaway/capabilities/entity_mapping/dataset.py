"""Carga del universo versionado de `ContractingEntity` (ADR 0006).

El dataset vive en `data/entities/*.yaml`, versionado en el repo -- el historial de Git
de esos ficheros **es** el "diff legible" que exige `specs/001-entity-mapping/spec.md`
(seccion "Salidas"). Cada entrada del YAML trae dos partes:

1. Los campos del contrato canonico `ContractingEntity` (Articulo 19), que este modulo
   valida con pydantic tal cual.
2. Un bloque `verification` que **no** es parte del contrato canonico (Articulo 6: una
   capacidad no le anade campos por su cuenta) pero que la propia spec exige registrar
   por entidad: la fuente exacta consultada para el RUC, la fecha, y si corresponde la
   justificacion de inclusion de una distrital (RN-001-02). Vive aparte, en
   `EntityProvenance`.

`entity_id` no se guarda en el YAML: se deriva del RUC en tiempo de carga
(`entity_id.compute_entity_id`), para que no pueda desincronizarse del algoritmo
canonico (RN-001-04) por copiar-pegar un valor viejo.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field

from cajamarca_qhaway.capabilities.entity_mapping.entity_id import compute_entity_id
from cajamarca_qhaway.models.contracting_entity import ContractingEntity

# Universo obligatorio de RN-001-01: el Gobierno Regional y las 13 provinciales, sin
# excepcion. Esta ronda de `entity_mapping` no incorpora distritales (AC-001-01
# bloqueado) -- ver `specs/001-entity-mapping/plan.md`, paso 4.
REQUIRED_ENTITY_COUNT = 14


class VerificationSource(BaseModel):
    """Una fuente consultada para verificar el RUC/consucode_id de una entidad."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: str
    url: str | None = None
    retrieved_at: datetime
    note: str | None = None


class EntityVerification(BaseModel):
    """Registro de procedencia de una entidad (RN-001-03, seccion "Evidencia y
    manifiesto" de la spec). No es parte del contrato canonico `ContractingEntity`."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    ruc_sources: list[VerificationSource] = Field(default_factory=list)
    ruc_cross_verified: bool
    consucode_verification_note: str | None = None
    inclusion_justification: str | None = None
    siaf_pliego: str | None = None
    siaf_sec_ejec: str | None = None
    ubigeo: str | None = None
    siaf_code_source: str | None = None
    ubigeo_source: str | None = None


@dataclass(frozen=True)
class EntityRecord:
    """Una fila del universo: el contrato canonico mas su procedencia."""

    entity: ContractingEntity
    verification: EntityVerification


@dataclass(frozen=True)
class Universe:
    """El universo completo cargado de un dataset, mas la lista de lo excluido."""

    entities: tuple[EntityRecord, ...] = field(default_factory=tuple)

    @property
    def contracting_entities(self) -> tuple[ContractingEntity, ...]:
        return tuple(record.entity for record in self.entities)

    def by_ruc(self, ruc: str) -> EntityRecord | None:
        for record in self.entities:
            if record.entity.ruc == ruc:
                return record
        return None


class DatasetFormatError(ValueError):
    """El documento de entidades no cumple la estructura YAML requerida."""


def _load_raw(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    if not isinstance(data, dict) or "entities" not in data:
        raise DatasetFormatError(
            f"{path}: se esperaba un mapeo con la clave 'entities' en la raiz del YAML"
        )
    entities = data["entities"]
    if not isinstance(entities, list):
        raise DatasetFormatError(f"{path}: 'entities' debe ser una lista")
    return entities


DEFAULT_UNIVERSE_PATH = Path(__file__).resolve().parents[4] / "data" / "entities" / "cajamarca-universe.yaml"


def load_universe(path: Path | None = None) -> Universe:
    """Carga y valida el universo de `ContractingEntity` desde un fichero YAML.

    Falla ruidosamente (excepcion, no valor por defecto) ante cualquier entrada que no
    cumpla el contrato canonico o cuyo RUC no normalice a 11 digitos -- silenciar un
    dato invalido en esta capacidad es exactamente el "supuesto silencioso" que el
    Articulo 3 de la constitucion prohibe.
    """
    target_path = path or DEFAULT_UNIVERSE_PATH
    raw_entries = _load_raw(target_path)
    records: list[EntityRecord] = []
    seen_rucs: set[str] = set()
    seen_siaf_codes: set[str] = set()
    seen_ubigeos: set[str] = set()
    has_siaf_metadata = any(
        isinstance(raw.get("verification"), dict)
        and any(
            raw["verification"].get(field)
            for field in ("siaf_pliego", "siaf_sec_ejec", "ubigeo")
        )
        for raw in raw_entries
    )

    for idx, raw in enumerate(raw_entries):
        if "verification" not in raw:
            raise ValueError(
                f"{path}: entrada #{idx} ({raw.get('official_name', '?')!r}) no trae "
                "bloque 'verification' -- RN-001-03 exige registrar la fuente"
            )
        raw = dict(raw)
        verification_raw = raw.pop("verification")

        ruc = str(raw.get("ruc", "")).strip()
        if ruc in seen_rucs:
            raise ValueError(f"{path}: RUC duplicado en el dataset: {ruc!r}")
        seen_rucs.add(ruc)

        entity_id = compute_entity_id(ruc)
        entity = ContractingEntity(entity_id=entity_id, **raw)
        verification = EntityVerification(**verification_raw)

        if entity.entity_level == "district_municipality" and not verification.inclusion_justification:
            raise ValueError(
                f"{path}: {entity.official_name!r} es district_municipality sin "
                "inclusion_justification -- RN-001-02 lo exige"
            )

        if has_siaf_metadata:
            if entity.entity_level == "regional":
                if verification.siaf_pliego != "445" or verification.siaf_sec_ejec or verification.ubigeo:
                    raise ValueError(f"{target_path}: mapeo SIAF invalido para {entity.official_name}")
                siaf_key = verification.siaf_pliego
            else:
                if (
                    not verification.siaf_sec_ejec
                    or not verification.ubigeo
                    or verification.siaf_pliego
                    or not verification.siaf_code_source
                    or not verification.ubigeo_source
                ):
                    raise ValueError(f"{target_path}: falta mapeo SIAF/UBIGEO para {entity.official_name}")
                if len(verification.siaf_sec_ejec) != 6 or not verification.siaf_sec_ejec.isdigit():
                    raise ValueError(f"{target_path}: SEC_EJEC invalido para {entity.official_name}")
                if len(verification.ubigeo) != 6 or not verification.ubigeo.isdigit():
                    raise ValueError(f"{target_path}: UBIGEO invalido para {entity.official_name}")
                siaf_key = verification.siaf_sec_ejec
            if siaf_key in seen_siaf_codes:
                raise ValueError(f"{target_path}: SEC_EJEC/PLIEGO duplicado: {siaf_key}")
            seen_siaf_codes.add(siaf_key)
            if verification.ubigeo:
                if verification.ubigeo in seen_ubigeos:
                    raise ValueError(f"{target_path}: UBIGEO duplicado: {verification.ubigeo}")
                seen_ubigeos.add(verification.ubigeo)

        records.append(EntityRecord(entity=entity, verification=verification))

    if has_siaf_metadata and (
        len(records) != REQUIRED_ENTITY_COUNT
        or len(seen_siaf_codes) != REQUIRED_ENTITY_COUNT
        or len(seen_ubigeos) != REQUIRED_ENTITY_COUNT - 1
    ):
        raise ValueError(f"{target_path}: el cruce SIAF/UBIGEO no cubre las 14 entidades")

    return Universe(entities=tuple(records))


__all__ = [
    "DEFAULT_UNIVERSE_PATH",
    "REQUIRED_ENTITY_COUNT",
    "EntityRecord",
    "EntityVerification",
    "Universe",
    "VerificationSource",
    "load_universe",
]
