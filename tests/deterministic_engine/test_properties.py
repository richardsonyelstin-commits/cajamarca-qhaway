"""Metamorfismos con oráculos racionales independientes y semilla fija."""

import copy
import json
from dataclasses import replace
from fractions import Fraction

import pytest
from hypothesis import HealthCheck, given, seed, settings
from hypothesis import strategies as st

from cajamarca_qhaway.capabilities.deterministic_engine import cents, evaluate, ratio
from cajamarca_qhaway.capabilities.deterministic_engine.boundary import decode_request
from cajamarca_qhaway.capabilities.deterministic_engine.engine import state_for
from cajamarca_qhaway.capabilities.deterministic_engine.policy import POLICY, crossed


@pytest.mark.parametrize(
    "reason,state",
    [
        ("THRESHOLD_MATCH", "SIGNAL"),
        ("THRESHOLD_NOT_MATCH", "PASS"),
        ("INVALID_FACT", "INVALID"),
        ("MISSING_FIELD", "NOT_EVALUABLE"),
    ],
)
def test_state_mapping(reason, state):
    assert state_for(reason) == state


@pytest.mark.parametrize(
    "value", ["01.00", "-1.00", "1.001", "1", "1e2", "1000000000000000000.00"]
)
def test_noncanonical_money(value):
    with pytest.raises(ValueError):
        cents(value)


def test_denominator_and_operators():
    with pytest.raises(ValueError):
        ratio(1, 0)
    for rule in POLICY.values():
        assert crossed(rule.numerator, rule.denominator, rule) == (
            rule.operator != "gt"
        )
        assert crossed(rule.numerator + 1, rule.denominator, rule) == (
            rule.operator != "eq"
        )
        assert not crossed(rule.numerator - 1, rule.denominator, rule)


@seed(20261015)
@settings(max_examples=1000, deadline=None)
@given(
    st.integers(1, 10**15),
    st.integers(1, 10**15),
    st.integers(1, 10**15),
    st.integers(1, 100),
)
def test_market_scaling_and_rational_oracle(a, b, c, multiplier):
    from cajamarca_qhaway.capabilities.deterministic_engine.contracts import (
        Award,
        Evidence,
        Observation,
        Request,
        Scope,
    )

    scope = Scope(
        "s",
        "PE-RUC:20999999991",
        "CAJAMARCA",
        "all",
        "procurement",
        "2025-01-01T00:00:00Z",
        "2026-01-01T00:00:00Z",
        "complete",
        3,
        "e",
        ("contract-share", "hhi"),
    )
    ref = Evidence(
        "e",
        "synthetic",
        "https://example.invalid/1",
        "2026-01-02T00:00:00Z",
        "0" * 64,
        "application/json",
        "synthetic-1",
    )

    def make(factor):
        rows = tuple(
            Observation(
                "s",
                "synthetic",
                f"r-{i}",
                1,
                "2025-06-01T00:00:00Z",
                ref.retrieved_at,
                False,
                ("e",),
                Award(
                    "award",
                    scope.entity_id,
                    "all",
                    f"p-{i}",
                    "2025-06-01T00:00:00Z",
                    "active",
                    "competitive",
                    "PEN",
                    f"{value * factor}.00",
                    str(20999999990 + i),
                    "single",
                    1,
                ),
            )
            for i, value in enumerate((a, b, c))
        )
        return Request(
            "engine-2",
            "deterministic-2.0.0",
            "qhaway-exploratory-1",
            "2026-10-15T00:00:00Z",
            (scope,),
            (ref,),
            rows,
        )

    original, scaled = evaluate(make(1)), evaluate(make(multiplier))
    for one, two in zip(original.evaluations, scaled.evaluations, strict=True):
        assert (one.observed, one.state) == (two.observed, two.state)
    expected = (
        Fraction(max(a, b, c), a + b + c),
        Fraction(10000 * (a * a + b * b + c * c), (a + b + c) ** 2),
    )
    for row, oracle in zip(original.evaluations, expected, strict=True):
        assert (
            Fraction(int(row.observed.numerator), int(row.observed.denominator))
            == oracle
        )
    assert 0 <= expected[1] <= 10000


@pytest.mark.parametrize(
    "defect,code,index",
    [
        ("allocation", "UNALLOCATED_SUPPLIERS", 4),
        ("zero", "ZERO_DENOMINATOR", 4),
        ("sample", "INSUFFICIENT_SAMPLE", 4),
        ("cut", "INVALID_CUT", 17),
        ("year", "INVALID_FACT", 17),
        ("duration", "INVALID_INTERVAL", 13),
        ("no-direct", "THRESHOLD_NOT_MATCH", 13),
    ],
)
def test_remaining_admission_reasons(corpus, evaluate, defect, code, index):
    value = copy.deepcopy(corpus[index]["input"])
    fact = value["observations"][0]["fact"]
    if defect == "allocation":
        fact["supplier_allocation"] = "unallocated"
        fact["supplier_ruc"] = None
    if defect == "zero":
        fact["amount"] = "0.00"
    if defect == "sample":
        for row in value["observations"]:
            row["fact"]["process_id"] = "one-process"
    if defect == "cut":
        fact["cut_at"] = fact["event_at"] = "2025-12-30T00:00:00Z"
    if defect == "year":
        fact["cut_at"] = "2024-12-31T00:00:00Z"
    if defect == "duration":
        value["scopes"][0]["start"] = "2025-01-02T00:00:00Z"
    if defect == "no-direct":
        for row in value["observations"]:
            row["fact"]["method"] = "competitive"
    assert evaluate(value)["evaluations"][0]["reason_code"] == code


@seed(20261015)
@settings(
    max_examples=1000,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
@given(st.integers(1, 10**17), st.integers(0, 10**17), st.integers(0, 10**17))
def test_budget_monotonicity(corpus, pim, spent, increment):
    request = decode_request(json.dumps(corpus[17]["input"]).encode())
    request = replace(
        request,
        scopes=(
            replace(request.scopes[0], rules=("budget-above-pim", "budget-unspent")),
        ),
    )

    def run(value):
        row = request.observations[0]
        return evaluate(
            replace(
                request,
                observations=(
                    replace(
                        row,
                        fact=replace(
                            row.fact, pim=f"{pim}.00", devengado=f"{value}.00"
                        ),
                    ),
                ),
            )
        )

    low, high = run(spent), run(spent + increment)

    def fractions(result):
        return [
            Fraction(int(row.observed.numerator), int(row.observed.denominator))
            for row in result.evaluations
        ]

    low_above, low_unspent = fractions(low)
    high_above, high_unspent = fractions(high)
    assert high_above >= low_above
    assert high_unspent <= low_unspent


@seed(20261015)
@settings(
    max_examples=1000,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
@given(st.permutations(range(3)), st.integers(1, 8), st.integers(1, 1000000))
def test_duplicate_permutation_and_lot_split(corpus, order, copies, scale):
    request = decode_request(json.dumps(corpus[4]["input"]).encode())
    request = replace(
        request,
        observations=tuple(
            replace(
                row,
                fact=replace(
                    row.fact, amount=f"{cents(row.fact.amount) * scale // 100}.00"
                ),
            )
            for row in request.observations
        ),
    )
    baseline = evaluate(request)
    changed = replace(
        request,
        observations=tuple(request.observations[i] for i in order) * copies,
        evidence=request.evidence * copies,
    )
    assert evaluate(changed) == baseline
    original = request.observations[0]
    amount = cents(original.fact.amount)

    def money(value):
        return f"{value // 100}.{value % 100:02}"

    first = replace(original, fact=replace(original.fact, amount=money(amount // 2)))
    second = replace(
        original,
        record_key=original.record_key + "-lot",
        fact=replace(original.fact, amount=money(amount - amount // 2)),
    )
    split = replace(
        request,
        scopes=(replace(request.scopes[0], expected_count=4),),
        observations=(first, second, *request.observations[1:]),
    )
    assert evaluate(split).evaluations[0].observed == baseline.evaluations[0].observed


def test_budget_cut_precedes_missing(corpus, evaluate):
    value = copy.deepcopy(corpus[17]["input"])
    fact = value["observations"][0]["fact"]
    fact["cut_at"] = "2025-12-30T00:00:00Z"
    fact["event_at"] = None
    assert evaluate(value)["evaluations"][0]["reason_code"] == "INVALID_CUT"
