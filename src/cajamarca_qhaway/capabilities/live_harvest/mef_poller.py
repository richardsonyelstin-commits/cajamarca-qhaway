"""Poller resiliente y asincrono para la API CKAN DataStore y Datasets Abiertos del MEF (Pilar 1).

Cumple estrictamente con:
- RN-003-01 / CA-003-01: Prohibicion terminante de acceso o scraping a Consulta Amigable.
- RN-003-02: Filtro geografico por departamento Cajamarca (codigo '06') en API DataStore.
- RN-003-03 / CA-003-02: raw_payload intacto byte a byte.
- RN-003-04 / CA-003-03: Cruce por entity_id canonico.
- RN-003-05 / CA-003-04: source='mef-datastore' y retrieved_at UTC.
- RN-003-06 / CA-003-05: Fallo de API no sustituido silenciosamente, registrado como brecha.
"""

from __future__ import annotations

import asyncio
import csv
from datetime import datetime, timezone
import io
import logging
from typing import Any

import httpx

from cajamarca_qhaway.capabilities.live_harvest.backoff import calculate_jitter_delay
from cajamarca_qhaway.capabilities.live_harvest.config import MefHarvestConfig
from cajamarca_qhaway.capabilities.live_harvest.coverage_logger import CoverageGapLogger
from cajamarca_qhaway.capabilities.live_harvest.watermark_store import WatermarkStore
from cajamarca_qhaway.capabilities.mef_ingestion.parser import parse_mef_record
from cajamarca_qhaway.models import BudgetExecutionRecord, ContractingEntity

logger = logging.getLogger("cajamarca_qhaway.mef_poller")


class MefPoller:
    """Recolector asincrono para MEF CKAN DataStore y Datasets Abiertos Oficiales."""

    def __init__(
        self,
        config: MefHarvestConfig,
        watermark_store: WatermarkStore,
        coverage_logger: CoverageGapLogger,
        entities_by_ruc: dict[str, ContractingEntity],
        entities_by_id: dict[str, ContractingEntity],
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self.config = config
        self.watermark_store = watermark_store
        self.coverage_logger = coverage_logger
        self.entities_by_ruc = entities_by_ruc
        self.entities_by_id = entities_by_id
        self._http_client = http_client
        self._pending_offset: int | None = None
        self._pending_timestamp: datetime | None = None
        self._pending_records: dict[str, BudgetExecutionRecord] = {}

        # CA-003-01: Validacion inquebrantable de prohibicion a Consulta Amigable
        self._assert_valid_endpoint(config.base_url)

    def acknowledge_persisted(self) -> None:
        """Advance the CKAN offset only after records are durable."""
        if self._pending_offset is not None and self._pending_timestamp is not None:
            self.watermark_store.update_mef_cursor(self._pending_timestamp, self._pending_offset)
            self._pending_offset = None
            self._pending_timestamp = None
            self._pending_records.clear()

    @staticmethod
    def _assert_valid_endpoint(url: str) -> None:
        forbidden = "apps5.mineco.gob.pe"
        if forbidden in url.lower():
            raise ValueError(
                f"Violacion constitucional RN-003-01 / CA-003-01: Prohibido interactuar con Consulta Amigable ({forbidden})."
            )

    async def _get_client(self) -> httpx.AsyncClient:
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.config.timeout_seconds),
                headers={"User-Agent": self.config.user_agent, "Accept": "application/json"},
            )
        return self._http_client

    async def poll_cycle(self, limit: int = 100) -> list[BudgetExecutionRecord]:
        """Ejecuta una corrida de recoleccion contra CKAN DataStore."""
        client = await self._get_client()
        url = f"{self.config.base_url.rstrip('/')}/datastore_search"

        current_offset = self.watermark_store.state.last_mef_offset
        params = {
            "resource_id": self.config.resource_id,
            "limit": limit,
            "offset": current_offset,
            "filters": f'{{"DEPARTAMENTO_EJECUTORA": "{self.config.cajamarca_dep_code}"}}',
        }

        window_start = datetime.now(timezone.utc)
        response_payload: dict[str, Any] | None = None

        for attempt in range(self.config.max_retries):
            try:
                res = await client.get(url, params=params)
                if res.status_code == 200:
                    try:
                        response_payload = res.json()
                        break
                    except Exception as json_err:
                        self.coverage_logger.log_incident(
                            source="mef-datastore",
                            attempt=attempt + 1,
                            status_code=200,
                            endpoint=url,
                            error_message=f"JSON parsing error: {json_err}",
                        )
                else:
                    self.coverage_logger.log_incident(
                        source="mef-datastore",
                        attempt=attempt + 1,
                        status_code=res.status_code,
                        endpoint=url,
                        error_message=f"HTTP {res.status_code}",
                    )
            except httpx.RequestError as exc:
                self.coverage_logger.log_incident(
                    source="mef-datastore",
                    attempt=attempt + 1,
                    status_code=None,
                    endpoint=url,
                    error_message=str(exc),
                )

            if attempt < self.config.max_retries - 1:
                delay = calculate_jitter_delay(
                    attempt=attempt,
                    initial_delay=self.config.backoff_initial_delay,
                    factor=self.config.backoff_factor,
                    jitter_max=1.0,
                )
                await asyncio.sleep(delay)

        window_end = datetime.now(timezone.utc)

        # Si datastore_search falla, registrar incidente de brecha
        if (
            not response_payload
            or not isinstance(response_payload, dict)
            or not response_payload.get("success", False)
            or "result" not in response_payload
        ):
            self.coverage_logger.log_window(
                source="mef-datastore",
                start_time=window_start,
                end_time=window_end,
                items_received=0,
                items_retained=0,
                status="FAILED",
                notes="Respuesta invalida o fallo en datastore_search",
            )
            return list(self._pending_records.values())

        records_data = response_payload.get("result", {}).get("records", [])
        total_received = len(records_data)
        harvested_records: list[BudgetExecutionRecord] = list(self._pending_records.values())
        retrieval_timestamp = datetime.now(timezone.utc)

        for row in records_data:
            if not isinstance(row, dict):
                continue
            rec = parse_mef_record(
                record=row,
                entities_by_ruc=self.entities_by_ruc,
                entities_by_id=self.entities_by_id,
                retrieved_at=retrieval_timestamp,
            )
            if rec:
                harvested_records.append(rec)
                self._pending_records[rec.execution_record_id] = rec

        new_offset = current_offset + total_received
        self._pending_offset = max(new_offset, self._pending_offset or 0)
        self._pending_timestamp = retrieval_timestamp

        self.coverage_logger.log_window(
            source="mef-datastore",
            start_time=window_start,
            end_time=window_end,
            items_received=total_received,
            items_retained=len(harvested_records),
            status="OK",
        )

        return harvested_records

    async def _fetch_csv_dataset(self, url: str) -> list[dict[str, Any]]:
        """Descarga un dataset CSV oficial del MEF y extrae registros de Cajamarca."""
        self._assert_valid_endpoint(url)
        client = await self._get_client()

        for attempt in range(self.config.max_retries):
            try:
                res = await client.get(url)
                if res.status_code == 200:
                    text_content = res.content.decode("utf-8-sig", errors="replace")
                    reader = csv.reader(io.StringIO(text_content))
                    header = next(reader, None)
                    if not header:
                        return []

                    matching_rows: list[dict[str, Any]] = []
                    dep_col_idx = None
                    dep_name_idx = None
                    for idx, h in enumerate(header):
                        if h.upper() == "DEPARTAMENTO_EJECUTORA":
                            dep_col_idx = idx
                        elif "DEPARTAMENTO" in h.upper():
                            dep_name_idx = idx

                    for row in reader:
                        if not row or len(row) < len(header):
                            continue
                        is_cajamarca = False
                        if dep_col_idx is not None and row[dep_col_idx].strip() == self.config.cajamarca_dep_code:
                            is_cajamarca = True
                        elif dep_name_idx is not None and "CAJAMARCA" in row[dep_name_idx].upper():
                            is_cajamarca = True
                        elif any("CAJAMARCA" in str(val).upper() for val in row):
                            is_cajamarca = True

                        if is_cajamarca:
                            matching_rows.append(dict(zip(header, row)))

                    return matching_rows

                self.coverage_logger.log_incident(
                    source="mef-datastore",
                    attempt=attempt + 1,
                    status_code=res.status_code,
                    endpoint=url,
                    error_message=f"HTTP {res.status_code}",
                )
            except httpx.RequestError as exc:
                self.coverage_logger.log_incident(
                    source="mef-datastore",
                    attempt=attempt + 1,
                    status_code=None,
                    endpoint=url,
                    error_message=str(exc),
                )

            if attempt < self.config.max_retries - 1:
                delay = calculate_jitter_delay(
                    attempt=attempt,
                    initial_delay=self.config.backoff_initial_delay,
                    factor=self.config.backoff_factor,
                    jitter_max=1.0,
                )
                await asyncio.sleep(delay)

        return []

    async def harvest_historical_and_recent(
        self, years: list[int] | None = None
    ) -> list[BudgetExecutionRecord]:
        """Cosecha ejecuciones presupuestales tanto recientes como historicas (2024-2026)."""
        target_years = years or [2024, 2025, 2026]
        all_records: list[BudgetExecutionRecord] = []
        seen_record_ids: set[str] = set()
        window_start = datetime.now(timezone.utc)
        retrieval_timestamp = datetime.now(timezone.utc)

        # 1. Probar corrida normal primero
        recent_records = await self.poll_cycle()
        for r in recent_records:
            if r.execution_record_id not in seen_record_ids:
                seen_record_ids.add(r.execution_record_id)
                all_records.append(r)

        # 2. Si se solicitan anos o datastore_search no devolvio suficientes, consultar datasets anuales del MEF
        if self.config.enable_open_data_fallback:
            for yr in target_years:
                yr_str = str(yr)
                urls = self.config.annual_dataset_urls.get(yr_str, [])
                for url in urls:
                    raw_rows = await self._fetch_csv_dataset(url)
                    for row in raw_rows:
                        rec = parse_mef_record(
                            record=row,
                            entities_by_ruc=self.entities_by_ruc,
                            entities_by_id=self.entities_by_id,
                            retrieved_at=retrieval_timestamp,
                        )
                        if rec and rec.execution_record_id not in seen_record_ids:
                            seen_record_ids.add(rec.execution_record_id)
                            all_records.append(rec)

        window_end = datetime.now(timezone.utc)
        self.coverage_logger.log_window(
            source="mef-datastore",
            start_time=window_start,
            end_time=window_end,
            items_received=len(all_records),
            items_retained=len(all_records),
            status="OK",
            notes=f"Cosecha historica MEF anos {target_years}",
        )

        return all_records

    async def aclose(self) -> None:
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None
