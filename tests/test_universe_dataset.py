"""Pruebas del universo versionado `data/entities/cajamarca-universe.yaml`.

CA-001-01 (RN-001-01): el universo contiene exactamente el Gobierno Regional y las 13
provinciales. CA-001-02, CA-001-03, CA-001-05, CA-001-06: se verifican tambien aqui,
sobre el dataset real, no solo sobre fixtures sinteticos.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from cajamarca_qhaway.capabilities.entity_mapping.dataset import load_universe
from cajamarca_qhaway.capabilities.entity_mapping.entity_id import compute_entity_id
from cajamarca_qhaway.models.contracting_entity import PROVINCIAS_CAJAMARCA

DATASET_PATH = Path(__file__).resolve().parents[1] / "data" / "entities" / "cajamarca-universe.yaml"


@pytest.fixture(scope="module")
def universe():
    return load_universe(DATASET_PATH)


@pytest.mark.contract
def test_universo_tiene_exactamente_14_entidades(universe) -> None:
    """CA-001-01: Gobierno Regional + 13 provinciales, sin excepcion, sin distritales."""
    assert len(universe.entities) == 14


def test_universo_no_incluye_distritales_en_esta_ronda(universe) -> None:
    """specs/001-entity-mapping/plan.md, paso 4: bloqueado por AC-001-01, no implementado."""
    levels = {r.entity.entity_level for r in universe.entities}
    assert "district_municipality" not in levels


@pytest.mark.contract
def test_exactamente_un_gobierno_regional(universe) -> None:
    regionales = [r for r in universe.entities if r.entity.entity_level == "regional"]
    assert len(regionales) == 1
    assert regionales[0].entity.province is None


@pytest.mark.contract
def test_exactamente_las_13_provinciales_de_cajamarca(universe) -> None:
    provinciales = {
        r.entity.province for r in universe.entities if r.entity.entity_level == "provincial_municipality"
    }
    assert provinciales == PROVINCIAS_CAJAMARCA
    assert len(provinciales) == 13


@pytest.mark.contract
def test_todas_las_entidades_son_de_cajamarca(universe) -> None:
    """CA-001-05: department == "CAJAMARCA" para toda entidad del universo."""
    assert all(r.entity.department == "CAJAMARCA" for r in universe.entities)


def test_ningun_ruc_repetido(universe) -> None:
    rucs = [r.entity.ruc for r in universe.entities]
    assert len(rucs) == len(set(rucs))


@pytest.mark.contract
def test_todos_los_ruc_tienen_11_digitos(universe) -> None:
    """CA-001-02, sobre el dataset real."""
    for record in universe.entities:
        assert len(record.entity.ruc) == 11
        assert record.entity.ruc.isdigit()


@pytest.mark.contract
def test_entity_id_coincide_con_el_algoritmo_canonico(universe) -> None:
    """RN-001-04: el entity_id cargado del dataset es el que produce compute_entity_id
    sobre el mismo RUC -- no hay una segunda fuente de verdad para el identificador."""
    for record in universe.entities:
        assert record.entity.entity_id == compute_entity_id(record.entity.ruc)


def test_toda_entidad_tiene_al_menos_una_fuente_de_verificacion_de_ruc(universe) -> None:
    """RN-001-03: RUC verificado contra al menos una fuente oficial, registrada."""
    for record in universe.entities:
        assert len(record.verification.ruc_sources) >= 1


def test_todas_las_14_obligatorias_tienen_ruc_cruzado_verificado(universe) -> None:
    """RN-001-03: no se acepta un RUC sin verificacion cruzada contra dos fuentes para
    el subconjunto obligatorio (Gobierno Regional + 13 provinciales, RN-001-01)."""
    for record in universe.entities:
        assert record.verification.ruc_cross_verified is True
        assert len(record.verification.ruc_sources) >= 2


def test_ninguna_entidad_district_municipality_sin_justificacion(universe) -> None:
    """RN-001-02, aplicado por dataset.load_universe al cargar (deberia no dispararse
    en esta ronda porque no hay distritales, pero prueba la regla igual)."""
    for record in universe.entities:
        if record.entity.entity_level == "district_municipality":
            assert record.verification.inclusion_justification
