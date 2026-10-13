"""Pruebas de `entity_id` -- CA-001-03 (RN-001-04)."""

from __future__ import annotations

import pytest

from cajamarca_qhaway.capabilities.entity_mapping.entity_id import (
    compute_entity_id,
    normalize_ruc,
)


@pytest.mark.contract
def test_mismo_ruc_produce_el_mismo_entity_id() -> None:
    """CA-001-03: dado el mismo RUC procesado dos veces, el entity_id es identico."""
    ruc = "20143623042"
    assert compute_entity_id(ruc) == compute_entity_id(ruc)


@pytest.mark.contract
def test_entity_id_es_estable_entre_procesos_distintos() -> None:
    """RN-001-04: el entity_id no depende de estado de proceso ni de orden de llamada."""
    a = compute_entity_id("20143623042")
    # Se recalcula tras computar otros RUC de por medio, para probar que no hay estado
    # compartido oculto (p. ej. un contador o una cache con efectos colaterales).
    compute_entity_id("20148289825")
    compute_entity_id("20220499767")
    b = compute_entity_id("20143623042")
    assert a == b


def test_entity_id_distinto_para_ruc_distinto() -> None:
    assert compute_entity_id("20143623042") != compute_entity_id("20148289825")


def test_normalize_ruc_quita_espacios_y_separadores() -> None:
    assert normalize_ruc(" 20143623042 ") == "20143623042"
    assert normalize_ruc("2014-3623-042") == "20143623042"


def test_entity_id_igual_pese_a_formato_de_entrada_distinto() -> None:
    """Dos representaciones del mismo RUC deben producir el mismo entity_id."""
    assert compute_entity_id("20143623042") == compute_entity_id(" 20143623042 ")


@pytest.mark.parametrize("bad_ruc", ["", "123", "201436230421", "abcdefghijk", "2014362304a"])
def test_normalize_ruc_rechaza_longitud_invalida(bad_ruc: str) -> None:
    with pytest.raises(ValueError):
        normalize_ruc(bad_ruc)


def test_compute_entity_id_tiene_prefijo_legible() -> None:
    assert compute_entity_id("20143623042").startswith("ce-")
