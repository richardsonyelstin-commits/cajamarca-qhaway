"""Pruebas del contrato `ContractingEntity` -- CA-001-02, CA-001-04, CA-001-05, CA-001-06."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from cajamarca_qhaway.models.contracting_entity import ContractingEntity

NOW = datetime(2026, 8, 20, tzinfo=UTC)


def _base_kwargs(**overrides: object) -> dict[str, object]:
    kwargs: dict[str, object] = {
        "entity_id": "ce-0000000000000000",
        "official_name": "MUNICIPALIDAD PROVINCIAL DE CAJAMARCA",
        "entity_level": "provincial_municipality",
        "province": "CAJAMARCA",
        "ruc": "20143623042",
        "consucode_id": None,
        "verified_at": NOW,
        "active": True,
    }
    kwargs.update(overrides)
    return kwargs


@pytest.mark.contract
def test_department_es_siempre_cajamarca() -> None:
    """CA-001-05: toda ContractingEntity tiene department == "CAJAMARCA"."""
    entity = ContractingEntity(**_base_kwargs())
    assert entity.department == "CAJAMARCA"


@pytest.mark.contract
def test_department_distinto_de_cajamarca_es_rechazado() -> None:
    with pytest.raises(ValidationError):
        ContractingEntity(**_base_kwargs(department="LIMA"))


@pytest.mark.contract
def test_province_no_nulo_para_municipalidad_provincial() -> None:
    """CA-001-06: entity_level != "regional" exige province no nulo y de la lista fija."""
    entity = ContractingEntity(**_base_kwargs())
    assert entity.province == "CAJAMARCA"


def test_province_debe_estar_en_lista_fija_de_13_provincias() -> None:
    with pytest.raises(ValidationError):
        ContractingEntity(**_base_kwargs(province="LIMA"))


def test_province_nulo_en_no_regional_es_rechazado() -> None:
    with pytest.raises(ValidationError):
        ContractingEntity(**_base_kwargs(province=None))


@pytest.mark.contract
def test_province_es_null_solo_para_gobierno_regional() -> None:
    """RN-001-08: province es null unicamente para el Gobierno Regional."""
    entity = ContractingEntity(
        **_base_kwargs(
            entity_level="regional",
            province=None,
            official_name="GOBIERNO REGIONAL DE CAJAMARCA",
            ruc="20453744168",
        )
    )
    assert entity.province is None


def test_regional_con_province_no_nulo_es_rechazado() -> None:
    with pytest.raises(ValidationError):
        ContractingEntity(**_base_kwargs(entity_level="regional", province="CAJAMARCA"))


@pytest.mark.contract
def test_ruc_debe_tener_11_digitos() -> None:
    """CA-001-02: el RUC tiene 11 digitos."""
    with pytest.raises(ValidationError):
        ContractingEntity(**_base_kwargs(ruc="123"))
    with pytest.raises(ValidationError):
        ContractingEntity(**_base_kwargs(ruc="201436230421"))
    with pytest.raises(ValidationError):
        ContractingEntity(**_base_kwargs(ruc="2014362304a"))


@pytest.mark.contract
def test_entidad_inactiva_no_se_elimina_sigue_siendo_construible() -> None:
    """CA-001-04: una entidad active=False sigue siendo un ContractingEntity valido --
    esta capacidad nunca borra el registro, solo lo marca inactivo (RN-001-05)."""
    entity = ContractingEntity(**_base_kwargs(active=False))
    assert entity.active is False
    # El modelo sigue exponiendo todos los demas campos: "marcar inactivo" no equivale
    # a "vaciar el registro".
    assert entity.ruc == "20143623042"
    assert entity.official_name


def test_entity_id_vacio_es_rechazado() -> None:
    with pytest.raises(ValidationError):
        ContractingEntity(**_base_kwargs(entity_id=""))


def test_verified_at_sin_zona_horaria_es_rechazado() -> None:
    with pytest.raises(ValidationError):
        ContractingEntity(**_base_kwargs(verified_at=datetime(2026, 8, 20)))


def test_modelo_es_inmutable() -> None:
    entity = ContractingEntity(**_base_kwargs())
    with pytest.raises(ValidationError):
        entity.official_name = "OTRO NOMBRE"


def test_campo_desconocido_es_rechazado() -> None:
    """Articulo 6: una capacidad no le anade campos al contrato canonico por su cuenta."""
    with pytest.raises(ValidationError):
        ContractingEntity(**_base_kwargs(risk_score=42))
