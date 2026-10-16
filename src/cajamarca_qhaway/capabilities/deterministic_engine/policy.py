"""Política heurística 011 versionada y sin parámetros ocultos."""

from __future__ import annotations

from dataclasses import dataclass
from math import gcd
from types import MappingProxyType
from typing import Literal

from .contracts import Rational

type RuleCode = Literal[
    "single-bidder",
    "contract-share",
    "hhi",
    "recurrent-direct",
    "budget-unspent",
    "budget-above-pim",
]
type State = Literal["INVALID", "NOT_EVALUABLE", "PASS", "SIGNAL"]


@dataclass(frozen=True, slots=True)
class Rule:
    formula_id: str
    numerator: int
    denominator: int
    operator: Literal["eq", "gt", "ge"]


POLICY = MappingProxyType(
    {
        "single-bidder": Rule("bidders-eq-v1", 1, 1, "eq"),
        "contract-share": Rule("max-award-share-v1", 2, 5, "gt"),
        "hhi": Rule("award-hhi-v1", 2500, 1, "ge"),
        "recurrent-direct": Rule("distinct-direct-processes-v1", 3, 1, "ge"),
        "budget-unspent": Rule("annual-unspent-v1", 1, 2, "ge"),
        "budget-above-pim": Rule("annual-above-pim-v1", 11, 10, "gt"),
    }
)
BUDGET_RULES = frozenset(("budget-unspent", "budget-above-pim"))


def cents(value: str) -> int:
    import re

    if re.fullmatch(r"(0|[1-9][0-9]{0,17})\.[0-9]{2}", value) is None:
        raise ValueError("Importe decimal no canónico")
    return int(value.replace(".", ""))


def ratio(numerator: int, denominator: int) -> Rational:
    if denominator <= 0:
        raise ValueError("Denominador no positivo")
    divisor = gcd(abs(numerator), denominator)
    return Rational(str(numerator // divisor), str(denominator // divisor))


def crossed(numerator: int, denominator: int, rule: Rule) -> bool:
    left, right = numerator * rule.denominator, rule.numerator * denominator
    if rule.operator == "eq":
        return left == right
    if rule.operator == "gt":
        return left > right
    return left >= right
