"""Contratos privados de prioridad y asistencia cognitiva; no son dictámenes humanos."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class CasePriority(BaseModel):
    model_config = ConfigDict(extra='forbid', frozen=True)
    score: float = Field(ge=0, le=100, allow_inf_nan=False)
    severity_component: float = Field(ge=0, le=50, allow_inf_nan=False)
    amount_component: float = Field(ge=0, le=30, allow_inf_nan=False)
    convergence_component: float = Field(ge=0, le=20, allow_inf_nan=False)
    source_families: list[str]
    version: str = 'case-priority-1'

    @model_validator(mode='after')
    def validate_sum(self) -> CasePriority:
        expected = round(self.severity_component+self.amount_component+self.convergence_component, 2)
        if abs(self.score-expected) > 0.011:
            raise ValueError('La prioridad no coincide con sus componentes')
        return self


class EvidenceNode(BaseModel):
    model_config = ConfigDict(extra='forbid', frozen=True)
    node_id: str
    kind: Literal['case', 'signal', 'procurement', 'budget', 'supplier', 'site', 'observation', 'source']
    facts: dict[str, str | int | float | bool | None]


class EvidenceEdge(BaseModel):
    model_config = ConfigDict(extra='forbid', frozen=True)
    source_id: str
    target_id: str
    relation: str


class EvidenceGraph(BaseModel):
    model_config = ConfigDict(extra='forbid', frozen=True)
    nodes: list[EvidenceNode] = Field(default_factory=list)
    edges: list[EvidenceEdge] = Field(default_factory=list)

    @model_validator(mode='after')
    def validate_references(self) -> EvidenceGraph:
        identifiers = {node.node_id for node in self.nodes}
        if len(identifiers) != len(self.nodes):
            raise ValueError('Nodos de evidencia duplicados')
        if any(edge.source_id not in identifiers or edge.target_id not in identifiers
               for edge in self.edges):
            raise ValueError('Arista sin evidencia de origen o destino')
        return self


class CopilotAnalysis(BaseModel):
    model_config = ConfigDict(extra='forbid', frozen=True)
    executive_summary: str = Field(min_length=1)
    risk_hypothesis: str = Field(min_length=1)
    legal_counter_hypothesis: str = Field(min_length=1)
    verification_checklist: list[str] = Field(min_length=1)
    evidence_refs: list[str] = Field(min_length=1)
    limitations: list[str]
    mode: Literal['deterministic', 'structured']
    generated_at: datetime
    version: str = 'review-copilot-1'
    evidence_graph: EvidenceGraph = Field(default_factory=lambda: EvidenceGraph())

    @model_validator(mode='after')
    def validate_utc(self) -> CopilotAnalysis:
        if self.generated_at.utcoffset() != timedelta(0):
            raise ValueError('El análisis requiere fecha UTC')
        return self


class ReviewCaseAnalysis(BaseModel):
    model_config = ConfigDict(extra='forbid', frozen=True)
    alert_id: str = Field(min_length=1)
    entity_id: str = Field(min_length=1)
    case_priority_score: float = Field(ge=0, le=100, allow_inf_nan=False)
    priority_components: CasePriority
    ai_copilot_analysis: CopilotAnalysis
    generated_at: datetime

    @model_validator(mode='after')
    def validate_priority(self) -> ReviewCaseAnalysis:
        if self.case_priority_score != self.priority_components.score:
            raise ValueError('El puntaje no coincide con el desglose de prioridad')
        if self.generated_at.utcoffset() != timedelta(0):
            raise ValueError('El expediente requiere fecha UTC')
        return self
