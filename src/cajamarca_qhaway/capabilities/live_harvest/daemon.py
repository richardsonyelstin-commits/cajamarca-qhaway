"""Daemon orquestador del ciclo de vida de la cosecha continua (Pilar 1).

Coordina pollers concurrentes, manejo de senales para parada limpia (graceful shutdown),
y persistencia durable de registros canonicos.
"""

from __future__ import annotations

import asyncio
from collections.abc import Sequence
from datetime import datetime, timezone
import json
import logging
import os
from pathlib import Path
import signal
from typing import Any

from cajamarca_qhaway.capabilities.entity_mapping.dataset import load_universe
from cajamarca_qhaway.capabilities.live_harvest.config import HarvestConfig
from cajamarca_qhaway.capabilities.live_harvest.coverage_logger import CoverageGapLogger
from cajamarca_qhaway.capabilities.live_harvest.mef_poller import MefPoller
from cajamarca_qhaway.capabilities.live_harvest.seace_poller import SeacePoller
from cajamarca_qhaway.capabilities.live_harvest.watermark_store import WatermarkStore
from cajamarca_qhaway.models import BudgetExecutionRecord, ContractingEntity, ProcurementRecord

logger = logging.getLogger("cajamarca_qhaway.live_harvest")


def _upsert_jsonl(path: Path, records: Sequence[Any], id_field: str) -> None:
    """Replace spool rows by their deterministic identity, using an atomic file swap."""
    by_id: dict[str, dict[str, Any]] = {}
    if path.exists():
        with path.open("r", encoding="utf-8") as existing:
            for line_number, line in enumerate(existing, start=1):
                if not line.strip():
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ValueError(f"Spool JSONL invalido en {path}:{line_number}") from exc
                identity = row.get(id_field)
                if not identity:
                    raise ValueError(f"Spool sin {id_field} en {path}:{line_number}")
                by_id[str(identity)] = row

    for record in records:
        row = record.model_dump(mode="json")
        identity = row.get(id_field)
        if not identity:
            raise ValueError(f"Registro sin identidad determinista {id_field}")
        by_id[str(identity)] = row

    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_suffix(f".tmp.{os.getpid()}")
    try:
        with temporary_path.open("w", encoding="utf-8", newline="\n") as output:
            for identity in sorted(by_id):
                output.write(json.dumps(by_id[identity], ensure_ascii=False, sort_keys=True) + "\n")
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary_path, path)
    finally:
        if temporary_path.exists():
            temporary_path.unlink()


class HarvesterDaemon:
    """Orquestador del trabajador en segundo plano para cosecha continua."""

    def __init__(
        self,
        config: HarvestConfig | None = None,
        universe_path: Path | None = None,
        watermark_store: WatermarkStore | None = None,
        coverage_logger: CoverageGapLogger | None = None,
        sync_manager: Any | None = None,
    ) -> None:
        self.config = config or HarvestConfig()
        db_mgr = getattr(sync_manager, "db", None) if sync_manager else None
        self.watermark_store = watermark_store or WatermarkStore(
            self.config.storage.watermark_file_path, db_manager=db_mgr
        )
        self.coverage_logger = coverage_logger or CoverageGapLogger(self.config.storage.coverage_gap_log_path)

        universe = load_universe(universe_path)
        self.entities_by_ruc: dict[str, ContractingEntity] = {r.entity.ruc: r.entity for r in universe.entities}
        self.entities_by_consucode: dict[str, ContractingEntity] = {
            r.entity.consucode_id: r.entity for r in universe.entities if r.entity.consucode_id
        }
        self.entities_by_id: dict[str, ContractingEntity] = {r.entity.entity_id: r.entity for r in universe.entities}

        self.seace_poller = SeacePoller(
            config=self.config.seace,
            watermark_store=self.watermark_store,
            coverage_logger=self.coverage_logger,
            entities_by_ruc=self.entities_by_ruc,
            entities_by_consucode=self.entities_by_consucode,
        )

        self.mef_poller = MefPoller(
            config=self.config.mef,
            watermark_store=self.watermark_store,
            coverage_logger=self.coverage_logger,
            entities_by_ruc=self.entities_by_ruc,
            entities_by_id=self.entities_by_id,
        )

        self.stop_event = asyncio.Event()
        self.sync_manager = sync_manager

    def _persist_records(
        self,
        procurements: Sequence[ProcurementRecord],
        executions: Sequence[BudgetExecutionRecord],
    ) -> None:
        storage_dir = self.config.storage.records_storage_dir
        storage_dir.mkdir(parents=True, exist_ok=True)

        if procurements:
            _upsert_jsonl(storage_dir / "procurements_all.jsonl", procurements, "procurement_id")

        if executions:
            _upsert_jsonl(storage_dir / "budget_executions_all.jsonl", executions, "execution_record_id")

        # Sincronizacion transaccional con base de datos operativa / Supabase (Pilar 2)
        if self.sync_manager:
            if procurements:
                self.sync_manager.sync_procurements(procurements)
            if executions:
                self.sync_manager.sync_budget_executions(executions)

    async def run_once(
        self, sources: Sequence[str] = ("seace", "mef")
    ) -> tuple[list[ProcurementRecord], list[BudgetExecutionRecord]]:
        """Ejecuta una corrida puntual sobre las fuentes seleccionadas."""
        new_procurements: list[ProcurementRecord] = []
        new_executions: list[BudgetExecutionRecord] = []

        if "seace" in sources:
            new_procurements = await self.seace_poller.poll_cycle()

        if "mef" in sources:
            new_executions = await self.mef_poller.poll_cycle()

        self._persist_records(new_procurements, new_executions)
        if "seace" in sources:
            self.seace_poller.acknowledge_persisted()
        if "mef" in sources:
            self.mef_poller.acknowledge_persisted()
        return new_procurements, new_executions

    async def harvest_historical_and_recent(
        self,
        years: list[int] | None = None,
        sources: Sequence[str] = ("seace", "mef"),
        page_limit: int = 5,
    ) -> tuple[list[ProcurementRecord], list[BudgetExecutionRecord]]:
        """Ejecuta cosecha integral historica (2024-2025) y reciente (2026)."""
        new_procurements: list[ProcurementRecord] = []
        new_executions: list[BudgetExecutionRecord] = []

        if "seace" in sources:
            new_procurements = await self.seace_poller.harvest_historical_and_recent(
                years=years, page_limit=page_limit
            )

        if "mef" in sources:
            new_executions = await self.mef_poller.harvest_historical_and_recent(years=years)

        self._persist_records(new_procurements, new_executions)
        if "seace" in sources:
            self.seace_poller.acknowledge_persisted()
        if "mef" in sources:
            self.mef_poller.acknowledge_persisted()
        return new_procurements, new_executions

    async def _seace_loop(self) -> None:
        interval = self.config.seace.poll_interval_seconds
        while not self.stop_event.is_set():
            try:
                records = await self.seace_poller.poll_cycle()
                self._persist_records(records, [])
                self.seace_poller.acknowledge_persisted()
                if self.seace_poller.last_cycle_status != "OK":
                    logger.error("Ciclo SEACE fallido; revise la bitacora de brechas de cobertura")
            except Exception as e:
                logger.error("Error en ciclo de SEACE: %s", e)

            try:
                await asyncio.wait_for(self.stop_event.wait(), timeout=interval)
            except asyncio.TimeoutError:
                pass

    async def _mef_loop(self) -> None:
        interval = self.config.mef.poll_interval_seconds
        while not self.stop_event.is_set():
            try:
                records = await self.mef_poller.poll_cycle()
                self._persist_records([], records)
                self.mef_poller.acknowledge_persisted()
                if self.mef_poller.last_cycle_status != "OK":
                    logger.error("Ciclo MEF fallido; revise la bitacora de brechas de cobertura")
            except Exception as e:
                logger.error("Error en ciclo de MEF: %s", e)

            try:
                await asyncio.wait_for(self.stop_event.wait(), timeout=interval)
            except asyncio.TimeoutError:
                pass

    async def run_daemon(self, sources: Sequence[str] = ("seace", "mef")) -> None:
        """Inicia el daemon en segundo plano con tareas concurrentes."""
        self._setup_signal_handlers()

        tasks = []
        if "seace" in sources:
            tasks.append(asyncio.create_task(self._seace_loop(), name="seace_poller_task"))
        if "mef" in sources:
            tasks.append(asyncio.create_task(self._mef_loop(), name="mef_poller_task"))

        logger.info("Daemon de cosecha continua iniciado para fuentes: %s", sources)

        try:
            await self.stop_event.wait()
        finally:
            logger.info("Iniciando parada ordenada (graceful shutdown)...")
            for t in tasks:
                t.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
            await self.aclose()
            logger.info("Daemon detenido exitosamente.")

    def _setup_signal_handlers(self) -> None:
        """Registra manejadores de senal compatibles con Windows y POSIX."""
        def _trigger_stop(*_: object) -> None:
            self.stop_event.set()

        try:
            loop = asyncio.get_running_loop()
            for sig in (signal.SIGINT, signal.SIGTERM):
                try:
                    loop.add_signal_handler(sig, _trigger_stop)
                except NotImplementedError:
                    # Windows no soporta add_signal_handler en ProactorEventLoop
                    signal.signal(sig, _trigger_stop)
        except RuntimeError:
            pass

    async def aclose(self) -> None:
        """Libera clientes HTTP y asegura almacenamiento de cursores."""
        await self.seace_poller.aclose()
        await self.mef_poller.aclose()
        self.watermark_store.save_atomic()
