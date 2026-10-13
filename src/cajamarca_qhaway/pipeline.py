"""Pipeline end-to-end para Cajamarca Qhaway.

Conecta el universo verificado de entidades (001), ingesta SEACE (002), ingesta MEF (003),
y el motor de banderas rojas (004) produciendo candidatos para el panel de revision humana (005).

Invariante estricto (Articulo 14 de la constitucion):
El pipeline automatizado genera unicamente candidatos de `RedFlag`. NUNCA publica
automaticamente una `Alert`. Toda Alerta requiere la intervencion del `ReviewPanelService`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from cajamarca_qhaway.capabilities.denuncia_intake import DenunciaIntakeService
from cajamarca_qhaway.capabilities.entity_mapping.dataset import Universe, load_universe
from cajamarca_qhaway.capabilities.mef_ingestion import MefIngester
from cajamarca_qhaway.capabilities.red_flags_engine import RedFlagsEngine
from cajamarca_qhaway.capabilities.review_panel import ReviewPanelService
from cajamarca_qhaway.capabilities.seace_ingestion import SeaceIngester
from cajamarca_qhaway.models import BudgetExecutionRecord, ContractingEntity, ProcurementRecord, RedFlag


@dataclass(frozen=True)
class PipelineResult:
    """Resultado del ciclo de ingesta y evaluacion de candidatos de riesgo."""

    total_entities_monitored: int
    procurement_records: tuple[ProcurementRecord, ...]
    execution_records: tuple[BudgetExecutionRecord, ...]
    candidate_red_flags: tuple[RedFlag, ...]
    executed_at: datetime


class CajamarcaPipeline:
    """Orquestador del pipeline de monitoreo ciudadano de Cajamarca Qhaway."""

    def __init__(self, universe: Universe | None = None) -> None:
        self.universe = universe or load_universe()
        self.entities: list[ContractingEntity] = list(self.universe.contracting_entities)
        self.seace_ingester = SeaceIngester(self.entities)
        self.mef_ingester = MefIngester(self.entities)
        self.engine = RedFlagsEngine()
        self.review_panel = ReviewPanelService()
        self.denuncia_service = DenunciaIntakeService()

    def run_detection(
        self,
        seace_releases: list[dict[str, Any]] | None = None,
        mef_records: list[dict[str, Any]] | None = None,
        now: datetime | None = None,
    ) -> PipelineResult:
        """Ejecuta la ingesta de fuentes y la evaluacion de banderas rojas.

        Retorna unicamente candidatos de `RedFlag` listos para ser presentados al panel humano.
        """
        current_time = now or datetime.now(timezone.utc)
        if current_time.tzinfo is None:
            current_time = current_time.replace(tzinfo=timezone.utc)

        # 1. Ingesta SEACE
        procs: list[ProcurementRecord] = []
        if seace_releases:
            procs = self.seace_ingester.ingest_releases(seace_releases, retrieved_at=current_time)

        # 2. Ingesta MEF
        execs: list[BudgetExecutionRecord] = []
        if mef_records:
            execs = self.mef_ingester.ingest_records(mef_records, retrieved_at=current_time)

        # 3. Evaluacion de Red Flags
        flags = self.engine.evaluate(procs, executions=execs, now=current_time)

        return PipelineResult(
            total_entities_monitored=len(self.entities),
            procurement_records=tuple(procs),
            execution_records=tuple(execs),
            candidate_red_flags=tuple(flags),
            executed_at=current_time,
        )
