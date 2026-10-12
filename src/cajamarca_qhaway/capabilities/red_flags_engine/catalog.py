"""Catalogo de indicadores de riesgo para red-flags-engine (capacidad 004).

Cumple estrictamente con:
- CA-004-01: El catalogo de indicadores activos tiene entre 5 y 10 entradas [5, 10].
- Articulo 15: Explicabilidad completa (formula publica y umbral verificable).
- Articulo 16: Prohibido cualquier scoring o clasificacion de personas individuales.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class IndicatorDefinition:
    """Definicion de un indicador de riesgo anticorrupcion."""

    code: str
    name: str
    formula_description: str
    default_threshold: Any
    unit: str


# Catalogo activo de 5 indicadores de riesgo para Fase 1 (CA-004-01)
ACTIVE_INDICATORS: dict[str, IndicatorDefinition] = {
    "single-bidder": IndicatorDefinition(
        code="single-bidder",
        name="Licitacion con postor unico",
        formula_description="Licitacion competitiva adjudicada con un unico postor participante (numberOfTenderers == 1)",
        default_threshold=1,
        unit="postores",
    ),
    "execution-overrun": IndicatorDefinition(
        code="execution-overrun",
        name="Sobrecosto o desvio presupuestal",
        formula_description="Monto ejecutado excede el presupuesto institucional modificado o adjudicado en mas del 10%",
        default_threshold=1.10,
        unit="ratio",
    ),
    "contract-concentration": IndicatorDefinition(
        code="contract-concentration",
        name="Concentracion de contratacion en un proveedor",
        formula_description="Un solo proveedor concentra mas del 40% del monto total adjudicado por la entidad en el periodo",
        default_threshold=0.40,
        unit="ratio",
    ),
    "short-tender-window": IndicatorDefinition(
        code="short-tender-window",
        name="Ventana anormalmente corta de licitacion",
        formula_description="Periodo de convocatoria y presentacion de ofertas inferior al plazo minimo prudencial de 5 dias",
        default_threshold=5,
        unit="dias",
    ),
    "direct-award-threshold": IndicatorDefinition(
        code="direct-award-threshold",
        name="Adjudicacion directa en umbral critico",
        formula_description="Contratacion directa cuyo monto roza sospechosamente el umbral limite de exoneracion legal",
        default_threshold=40000.0,
        unit="PEN",
    ),
    "direct-administration-equipment-rent": IndicatorDefinition(
        code="direct-administration-equipment-rent",
        name="Alquiler irregular de maquinaria en administracion directa",
        formula_description="Facturacion o cobro de alquiler de maquinaria propia en obras por administracion directa hacia RDR",
        default_threshold=1,
        unit="ocurrencias",
    ),
    "contract-splitting-orders": IndicatorDefinition(
        code="contract-splitting-orders",
        name="Fraccionamiento en ordenes consecutivas menores a 8 UIT",
        formula_description="Emision de 3 o mas ordenes de compra o servicio menores a 8 UIT al mismo proveedor en menos de 30 dias",
        default_threshold=3,
        unit="ordenes",
    ),
}

if not (5 <= len(ACTIVE_INDICATORS) <= 10):
    raise ValueError(
        f"CA-004-01 violado: el catalogo debe tener entre 5 y 10 indicadores, tiene {len(ACTIVE_INDICATORS)}"
    )
