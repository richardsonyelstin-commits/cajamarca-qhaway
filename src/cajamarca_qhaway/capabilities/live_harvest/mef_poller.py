"""Poller resiliente y asincrono para la API CKAN DataStore del MEF (Pilar 1).

Cumple estrictamente con:
- RN-003-01 / CA-003-01: Prohibicion terminante de acceso o scraping a Consulta Amigable.
- RN-003-02: Filtro geografico por departamento Cajamarca (codigo '06') en API DataStore.
- RN-003-03 / CA-003-02: raw_payload intacto.
- RN-003-04 / CA-003-03: Cruce por entity_id canonico.
- RN-003-05 / CA-003-04: source='mef-datastore' y retrieved_at UTC.
- RN-003-06 / CA-003-05: Fallo de API no sustituido silenciosamente, registrado como brecha.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any

import httpx

from cajamarca_qhaway.capabilities.live_harvest.backoff import calculate_jitter_delay
from cajamarca_qhaway.capabilities.live_harvest.config import MefHarvestConfig
from cajamarca_qhaway.capabilities.live_harvest.coverage_logger import CoverageGapLogger
from cajamarca_qhaway.capabilities.live_harvest.watermark_store import WatermarkStore
from cajamarca_qhaway.capabilities.mef_ingestion.parser import parse_mef_record
from cajamarca_qhaway.models import BudgetExecutionRecord, ContractingEntity


class MefPoller:
    """Recolector asincrono para MEF CKAN DataStore."""

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

        # CA-003-01: Validacion inquebrantable de prohibicion a Consulta Amigable
        self._assert_valid_endpoint(config.base_url)

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

        # CA-003-05: Si falla, registrar como brecha y no sustituir por scraping
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
            return []

        records_data = response_payload.get("result", {}).get("records", [])
        total_received = len(records_data)
        harvested_records: list[BudgetExecutionRecord] = []
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

        new_offset = current_offset + total_received
        self.watermark_store.update_mef_cursor(retrieval_timestamp, new_offset)

        self.coverage_logger.log_window(
            source="mef-datastore",
            start_time=window_start,
            end_time=window_end,
            items_received=total_received,
            items_retained=len(harvested_records),
            status="OK",
        )

        return harvested_records

    async def aclose(self) -> None:
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None
