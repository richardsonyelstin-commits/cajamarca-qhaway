"""Evaluación pura de hechos normalizados con identidad reproducible."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import replace
from datetime import datetime
from hashlib import sha256
from typing import Literal, cast

from .boundary import decode_request, normalize_request
from .contracts import (
    Award,
    BatchInvalid,
    BatchResult,
    Budget,
    Diagnostic,
    Evaluation,
    Observation,
    Rational,
    Request,
    Scope,
)
from .policy import POLICY, RuleCode, State, cents, crossed, ratio
from .serialization import canonical_bytes, object_document

type Reason = Literal[
    "THRESHOLD_MATCH",
    "THRESHOLD_NOT_MATCH",
    "EMPTY_SCOPE",
    "MISSING_FIELD",
    "INCOMPLETE_COVERAGE",
    "INSUFFICIENT_SAMPLE",
    "UNALLOCATED_SUPPLIERS",
    "INAPPLICABLE",
    "OPEN_FISCAL_YEAR",
    "ZERO_DENOMINATOR",
    "CONFLICTING_REVISION",
    "SOURCE_DISAGREEMENT",
    "MIXED_GRAIN",
    "INVALID_INTERVAL",
    "INVALID_CUT",
    "INVALID_FACT",
    "COVERAGE_MISMATCH",
]
INVALID = frozenset(
    (
        "CONFLICTING_REVISION",
        "SOURCE_DISAGREEMENT",
        "MIXED_GRAIN",
        "INVALID_INTERVAL",
        "INVALID_CUT",
        "INVALID_FACT",
        "COVERAGE_MISMATCH",
    )
)


def select(
    scope: Scope, rows: list[Observation], as_of: str
) -> tuple[
    list[Observation], tuple[str, ...], tuple[str, ...], str | None, set[Diagnostic]
]:
    diagnostics = set()
    eligible = []
    groups = defaultdict(list)
    for row in rows:
        if row.effective_at > as_of or row.retrieved_at > as_of:
            diagnostics.add(
                Diagnostic(scope.scope_id, row.record_key, "FUTURE_REVISION_EXCLUDED")
            )
        else:
            eligible.append(row)
            groups[(row.source_id, row.record_key, row.revision)].append(row)
    conflict = any(
        len({(r.fact, r.deleted, r.effective_at, r.retrieved_at) for r in group}) > 1
        for group in groups.values()
    )
    latest = {}
    for (source, key, revision), group in groups.items():
        row = replace(
            group[0],
            evidence_ids=tuple(sorted({ref for r in group for ref in r.evidence_ids})),
        )
        if (source, key) not in latest or revision > latest[source, key].revision:
            latest[source, key] = row
    records = defaultdict(list)
    for row in latest.values():
        records[row.record_key].append(row)
    disagreement = any(
        len({(r.fact, r.deleted) for r in group}) > 1 for group in records.values()
    )
    reason = (
        "CONFLICTING_REVISION"
        if conflict
        else "SOURCE_DISAGREEMENT"
        if disagreement
        else None
    )
    refs = {scope.coverage_evidence_id}
    active = []
    if reason:
        refs.update(ref for row in eligible for ref in row.evidence_ids)
        keys = sorted({row.record_key for row in eligible})
    else:
        for group in records.values():
            refs.update(ref for row in group for ref in row.evidence_ids)
            row = group[0]
            if row.deleted:
                diagnostics.add(
                    Diagnostic(scope.scope_id, row.record_key, "TOMBSTONE_SELECTED")
                )
            else:
                active.append(row)
        keys = sorted(row.record_key for row in active)
    return (
        sorted(active, key=lambda r: r.record_key),
        tuple(keys),
        tuple(sorted(refs)),
        reason,
        diagnostics,
    )


def calculate(
    scope: Scope,
    code: RuleCode,
    rows: list[Observation],
    as_of: str,
    selection_reason: str | None,
) -> tuple[Reason, Rational | None, Rational | None]:
    facts = [r.fact for r in rows]
    awards = [f for f in facts if isinstance(f, Award)]
    budgets = [f for f in facts if isinstance(f, Budget)]
    rule = POLICY[code]

    def stop(reason: Reason) -> tuple[Reason, None, None]:
        return cast(Reason, reason), None, None

    if scope.start >= scope.end or (scope.kind == "procurement" and scope.end > as_of):
        return stop("INVALID_INTERVAL")
    if (
        code == "recurrent-direct"
        and (
            datetime.fromisoformat(scope.end) - datetime.fromisoformat(scope.start)
        ).total_seconds()
        != 365 * 86400
    ):
        return stop("INVALID_INTERVAL")
    if selection_reason:
        return stop(cast(Reason, selection_reason))
    if (
        any(f.entity_id != scope.entity_id or f.cohort != scope.cohort for f in facts)
        or (
            scope.kind == "budget"
            and (
                awards
                or len(budgets) > 1
                or any(f.dimensions != "institution-total" for f in budgets)
            )
        )
        or (scope.kind == "procurement" and budgets)
        or (code == "single-bidder" and len({f.process_id for f in awards}) > 1)
    ):
        return stop("MIXED_GRAIN")
    if any(r.record_key != r.record_key.strip() for r in rows) or any(
        f.status != "active" or f.process_id != f.process_id.strip() for f in awards
    ):
        return stop("INVALID_FACT")
    if any(
        f.event_at is not None and not scope.start <= f.event_at < scope.end
        for f in facts
    ):
        return stop("INVALID_FACT")
    bidders_by_process: dict[str, set[int]] = defaultdict(set)
    for award in awards:
        if award.bidders is not None:
            bidders_by_process[award.process_id].add(award.bidders)
    if any(len(values) > 1 for values in bidders_by_process.values()) or (
        code == "single-bidder" and any(f.bidders == 0 for f in awards)
    ):
        return stop("INVALID_FACT")
    for f in budgets:
        if f.cut_at is not None and int(f.cut_at[:4]) != f.fiscal_year:
            return stop("INVALID_FACT")
        if f.fiscal_year < int(as_of[:4]) and (
            (f.cut_at is not None and f.cut_at != f"{f.fiscal_year}-12-31T00:00:00Z")
            or (
                f.event_at is not None
                and f.cut_at is not None
                and f.event_at != f.cut_at
            )
            or scope.start != f"{f.fiscal_year}-01-01T00:00:00Z"
            or scope.end != f"{f.fiscal_year + 1}-01-01T00:00:00Z"
        ):
            return stop("INVALID_CUT")
    if not facts:
        return stop("EMPTY_SCOPE")
    missing = any(f.event_at is None for f in facts)
    if code == "single-bidder":
        missing |= any(f.bidders is None for f in awards)
    elif code in {"contract-share", "hhi"}:
        missing |= any(
            f.amount is None
            or f.currency != "PEN"
            or (f.supplier_ruc is None and f.supplier_allocation == "single")
            for f in awards
        )
    elif code == "recurrent-direct":
        missing |= any(
            f.supplier_ruc is None and f.supplier_allocation == "single" for f in awards
        )
    else:
        missing |= any(
            f.cut_at is None
            or f.pim is None
            or f.devengado is None
            or f.currency != "PEN"
            for f in budgets
        )
    if missing:
        return stop("MISSING_FIELD")
    if scope.coverage != "complete" or scope.expected_count is None:
        return stop("INCOMPLETE_COVERAGE")
    if scope.expected_count != len(facts):
        return stop("COVERAGE_MISMATCH")
    if code in {"contract-share", "hhi", "recurrent-direct"} and any(
        f.supplier_allocation == "unallocated" for f in awards
    ):
        return stop("UNALLOCATED_SUPPLIERS")
    if (code == "single-bidder" and any(f.method != "competitive" for f in awards)) or (
        code == "recurrent-direct" and any(f.method == "unknown" for f in awards)
    ):
        return stop("INAPPLICABLE")
    if any(f.fiscal_year >= int(as_of[:4]) for f in budgets):
        return stop("OPEN_FISCAL_YEAR")
    numerator, denominator = 0, 1
    if code == "single-bidder":
        numerator = cast(int, awards[0].bidders)
    elif code in {"contract-share", "hhi"}:
        amounts = [cents(cast(str, f.amount)) for f in awards]
        if any(value == 0 for value in amounts):
            return stop("ZERO_DENOMINATOR")
        if len({f.process_id for f in awards}) < 3:
            return stop("INSUFFICIENT_SAMPLE")
        suppliers = defaultdict(int)
        for f, value in zip(awards, amounts, strict=True):
            suppliers[f.supplier_ruc] += value
        total = sum(amounts)
        numerator, denominator = (
            (max(suppliers.values()), total)
            if code == "contract-share"
            else (
                10000 * sum(value * value for value in suppliers.values()),
                total * total,
            )
        )
    elif code == "recurrent-direct":
        processes = defaultdict(set)
        for f in awards:
            if f.method == "direct":
                processes[f.supplier_ruc].add(f.process_id)
        numerator = max((len(value) for value in processes.values()), default=0)
    else:
        f = budgets[0]
        denominator = cents(cast(str, f.pim))
        if denominator == 0:
            return stop("ZERO_DENOMINATOR")
        spent = cents(cast(str, f.devengado))
        numerator = denominator - spent if code == "budget-unspent" else spent
    return (
        cast(
            Reason,
            "THRESHOLD_MATCH"
            if crossed(numerator, denominator, rule)
            else "THRESHOLD_NOT_MATCH",
        ),
        ratio(numerator, denominator),
        ratio(rule.numerator, rule.denominator),
    )


def state_for(reason: Reason) -> State:
    if reason == "THRESHOLD_MATCH":
        return "SIGNAL"
    if reason == "THRESHOLD_NOT_MATCH":
        return "PASS"
    if reason in INVALID:
        return "INVALID"
    return "NOT_EVALUABLE"


def evaluate(request: Request) -> BatchResult | BatchInvalid:
    normalized = normalize_request(request)
    if isinstance(normalized, BatchInvalid):
        return normalized
    request = normalized
    run_id = sha256(
        b"qhaway-run-v2\n" + canonical_bytes(object_document(request))
    ).hexdigest()
    indexed = defaultdict(list)
    for row in request.observations:
        indexed[row.scope_id].append(row)
    evaluations = []
    diagnostics = set()
    for scope in request.scopes:
        rows, keys, refs, selection_reason, messages = select(
            scope, indexed[scope.scope_id], request.as_of
        )
        diagnostics.update(messages)
        for code in scope.rules:
            reason, observed, threshold = calculate(
                scope, code, rows, request.as_of, selection_reason
            )
            state = state_for(reason)
            row = Evaluation(
                "",
                scope.scope_id,
                code,
                state,
                reason,
                POLICY[code].formula_id,
                observed,
                threshold,
                keys,
                refs,
            )
            identity = object_document(row)
            del identity["result_id"]
            result_id = sha256(
                b"qhaway-result-v2\n"
                + canonical_bytes({"run_id": run_id, "evaluation": identity})
            ).hexdigest()
            evaluations.append(replace(row, result_id=result_id))
    return BatchResult(
        request.schema_version,
        request.engine_version,
        request.policy_version,
        "BatchResult",
        run_id,
        request.as_of,
        tuple(evaluations),
        tuple(sorted(diagnostics, key=lambda d: (d.scope_id, d.record_key, d.code))),
    )


def evaluate_json(raw: bytes) -> bytes:
    request = decode_request(raw)
    result = request if isinstance(request, BatchInvalid) else evaluate(request)
    return canonical_bytes(object_document(result))
