"""Reconciliacion de momentos y particiones institucionales del MEF."""

from __future__ import annotations

import math
from collections.abc import Sequence
from decimal import Decimal, InvalidOperation
from itertools import pairwise
from typing import TYPE_CHECKING, Any

from cajamarca_qhaway.models.budget_breakdown import (
    BudgetBreakdownContract,
    Moments,
    Scope,
)

if TYPE_CHECKING:
    from cajamarca_qhaway.models.budget_execution_record import BudgetExecutionRecord

AMOUNT_COLUMNS = {
    "pia_amount": "PIA", "budgeted_amount": "PIM", "certified_amount": "CERTIFICACION",
    "committed_annual_amount": "COMPROMISO_ANUAL",
    "monthly_commitment_amount": "ATENCION_COMPROMISO_MENSUAL",
    "executed_amount": "DEVENGADO", "paid_amount": "GIRADO", "execution_pct": "AVANCE_PCT",
}
SUMMABLE_MOMENTS = tuple(name for name in AMOUNT_COLUMNS if name != "execution_pct")


def moments_from_payload(raw: dict[str, Any]) -> Moments:
    values: dict[str, float] = {}
    for field, column in AMOUNT_COLUMNS.items():
        try:
            number = Decimal(str(raw[column]).replace(",", "").strip())
        except (KeyError, InvalidOperation) as error:
            raise ValueError(f"Falta un momento MEF numerico: {column}") from error
        if not number.is_finite() or number < 0:
            raise ValueError(f"Momento MEF fuera de rango: {column}")
        values[field] = float(number)
    values["modification_amount"] = values["budgeted_amount"] - values["pia_amount"]
    result = Moments.model_validate(values)
    validate_moments(result)
    return result


def validate_moments(moments: Moments) -> None:
    values = moments.model_dump()
    if not all(math.isfinite(value) for value in values.values()):
        raise ValueError("Los momentos MEF deben ser finitos")
    if abs(moments.modification_amount - (moments.budgeted_amount - moments.pia_amount)) > 0.000001:
        raise ValueError("Las modificaciones no coinciden con PIM - PIA")
    ordered = [moments.budgeted_amount, moments.certified_amount,
               moments.committed_annual_amount, moments.executed_amount, moments.paid_amount]
    if any(a < b for a, b in pairwise(ordered)):
        raise ValueError("Los momentos MEF incumplen el orden financiero")
    expected = moments.executed_amount / moments.budgeted_amount * 100 if moments.budgeted_amount else 0
    if abs(round(expected, 1) - moments.execution_pct) > 0.100001:
        raise ValueError("Avance oficial inconsistente con devengado / PIM")


def _assert_partition(parent: Moments, children: Sequence[Moments], name: str) -> None:
    for field in SUMMABLE_MOMENTS:
        tolerance = (
            1 if name == "ortogonalidad" or field == "budgeted_amount"
            else max(1, (len(children) + 1) / 2)
        )
        total = sum(getattr(child, field) for child in children)
        delta = abs(getattr(parent, field) - total)
        if delta > tolerance + 0.000001:
            raise ValueError(f"Falla reconciliacion de {name}: {field}, diferencia {delta}")


def validate_scope(scope: Scope, *, require_funding: bool = False) -> None:
    validate_moments(scope.moments)
    if require_funding:
        if scope.moments != moments_from_payload(scope.raw_payload):
            raise ValueError("El desglose difiere de la fila fuente")
        if scope.raw_payload.get("FECHA_CORTE_OFICIAL") != scope.official_cut_date.isoformat():
            raise ValueError("Fecha de desglose distinta de su fuente")
    sources = scope.breakdown_by_funding_source
    if len({source.code for source in sources}) != len(sources):
        raise ValueError("Fuente de financiamiento duplicada")
    if require_funding and scope.moments.budgeted_amount and not sources:
        raise ValueError("Faltan las fuentes de financiamiento")
    if sources:
        _assert_partition(scope.moments, [source.moments for source in sources], "fuentes")
    rubro_codes: set[str] = set()
    for source in sources:
        validate_moments(source.moments)
        if require_funding and source.moments != moments_from_payload(source.raw_payload):
            raise ValueError("Los momentos de la fuente difieren del payload")
        if require_funding and source.moments.budgeted_amount and not source.rubros:
            raise ValueError("Faltan rubros de la fuente")
        if source.rubros:
            _assert_partition(source.moments, [rubro.moments for rubro in source.rubros], "rubros")
        for rubro in source.rubros:
            if rubro.code in rubro_codes:
                raise ValueError("Rubro de financiamiento duplicado")
            rubro_codes.add(rubro.code)
            validate_moments(rubro.moments)
            if require_funding and rubro.moments != moments_from_payload(rubro.raw_payload):
                raise ValueError("Los momentos del rubro difieren del payload")


def validate_budget_breakdown(
    contract: BudgetBreakdownContract, *, require_funding: bool = False
) -> None:
    total = contract.total
    if total.scope != "ActProy":
        raise ValueError("El maestro debe ser ActProy")
    children = contract.breakdown_by_scope
    scopes = [total, children.Proyecto, children.Actividad]
    if children.Proyecto.scope != "Proyecto" or children.Actividad.scope != "Actividad":
        raise ValueError("Ambitos MEF intercambiados")
    if len({scope.official_cut_date for scope in scopes}) != 1:
        raise ValueError("Los ambitos tienen fechas de corte distintas")
    for scope in scopes:
        validate_scope(scope, require_funding=require_funding)
    _assert_partition(total.moments, [scope.moments for scope in scopes[1:]], "ortogonalidad")
    for comparison in contract.comparison_cuts:
        if comparison.cut_type == contract.cut_type or comparison.total.scope != "ActProy":
            raise ValueError("Corte de comparacion duplicado o no institucional")
        validate_scope(comparison.total)


def canonical_budget_records(
    records: Sequence[BudgetExecutionRecord],
) -> list[BudgetExecutionRecord]:
    result: list[BudgetExecutionRecord] = []
    seen: set[tuple[str, int]] = set()
    for record in records:
        if not record.is_canonical_total and record.budget_category not in (
            "TOTAL", "TOTAL_INSTITUCIONAL_ACTPROY",
        ):
            continue
        key = (record.entity_id, record.fiscal_year)
        if key in seen:
            raise ValueError(f"Maestro institucional duplicado: {key}")
        seen.add(key)
        result.append(record)
    return result
