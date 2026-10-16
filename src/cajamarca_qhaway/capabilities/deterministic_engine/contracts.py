"""Generado por generate-deterministic-contracts.py; editar el schema fuente."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True, slots=True)
class Scope:
    scope_id: str
    entity_id: str
    region: Literal['CAJAMARCA']
    cohort: str
    kind: Literal['procurement', 'budget']
    start: str
    end: str
    coverage: Literal['complete', 'partial', 'unknown']
    expected_count: int | None
    coverage_evidence_id: str
    rules: tuple[Literal['single-bidder', 'contract-share', 'hhi', 'recurrent-direct', 'budget-unspent', 'budget-above-pim'], ...]


@dataclass(frozen=True, slots=True)
class Evidence:
    evidence_id: str
    source_id: str
    source_url: str
    retrieved_at: str
    payload_sha256: str
    media_type: Literal['application/json', 'text/csv', 'text/html', 'application/pdf']
    adapter_version: str


@dataclass(frozen=True, slots=True)
class Award:
    kind: Literal['award']
    entity_id: str
    cohort: str
    process_id: str
    event_at: str | None
    status: Literal['active', 'cancelled', 'unknown']
    method: Literal['competitive', 'direct', 'unknown']
    currency: Literal['PEN', 'unknown']
    amount: str | None
    supplier_ruc: str | None
    supplier_allocation: Literal['single', 'unallocated']
    bidders: int | None


@dataclass(frozen=True, slots=True)
class Budget:
    kind: Literal['budget']
    entity_id: str
    cohort: str
    event_at: str | None
    fiscal_year: int
    cut_at: str | None
    dimensions: Literal['institution-total', 'partition']
    currency: Literal['PEN', 'unknown']
    pim: str | None
    devengado: str | None


@dataclass(frozen=True, slots=True)
class Observation:
    scope_id: str
    source_id: str
    record_key: str
    revision: int
    effective_at: str
    retrieved_at: str
    deleted: bool
    evidence_ids: tuple[str, ...]
    fact: Award | Budget


@dataclass(frozen=True, slots=True)
class Request:
    schema_version: Literal['engine-2']
    engine_version: Literal['deterministic-2.0.0']
    policy_version: Literal['qhaway-exploratory-1']
    as_of: str
    scopes: tuple[Scope, ...]
    evidence: tuple[Evidence, ...]
    observations: tuple[Observation, ...]


@dataclass(frozen=True, slots=True)
class Rational:
    numerator: str
    denominator: str


@dataclass(frozen=True, slots=True)
class Evaluation:
    result_id: str
    scope_id: str
    rule_code: Literal['single-bidder', 'contract-share', 'hhi', 'recurrent-direct', 'budget-unspent', 'budget-above-pim']
    state: Literal['INVALID', 'NOT_EVALUABLE', 'PASS', 'SIGNAL']
    reason_code: Literal['THRESHOLD_MATCH', 'THRESHOLD_NOT_MATCH', 'EMPTY_SCOPE', 'MISSING_FIELD', 'INCOMPLETE_COVERAGE', 'INSUFFICIENT_SAMPLE', 'UNALLOCATED_SUPPLIERS', 'INAPPLICABLE', 'OPEN_FISCAL_YEAR', 'ZERO_DENOMINATOR', 'CONFLICTING_REVISION', 'SOURCE_DISAGREEMENT', 'MIXED_GRAIN', 'INVALID_INTERVAL', 'INVALID_CUT', 'INVALID_FACT', 'COVERAGE_MISMATCH']
    formula_id: str
    observed: Rational | None
    threshold: Rational | None
    record_keys: tuple[str, ...]
    evidence_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class Diagnostic:
    scope_id: str
    record_key: str
    code: Literal['FUTURE_REVISION_EXCLUDED', 'TOMBSTONE_SELECTED']


@dataclass(frozen=True, slots=True)
class Problem:
    pointer: str
    code: Literal['SCHEMA_VIOLATION', 'DUPLICATE_JSON_KEY', 'UNSUPPORTED_VERSION', 'DUPLICATE_ID', 'DANGLING_REFERENCE', 'RESOURCE_LIMIT']


@dataclass(frozen=True, slots=True)
class BatchResult:
    schema_version: Literal['engine-2']
    engine_version: Literal['deterministic-2.0.0']
    policy_version: Literal['qhaway-exploratory-1']
    kind: Literal['BatchResult']
    run_id: str
    as_of: str
    evaluations: tuple[Evaluation, ...]
    diagnostics: tuple[Diagnostic, ...]


@dataclass(frozen=True, slots=True)
class BatchInvalid:
    schema_version: Literal['engine-2']
    kind: Literal['BatchInvalid']
    problems: tuple[Problem, ...]
