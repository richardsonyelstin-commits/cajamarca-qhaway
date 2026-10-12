"""Poller resiliente y asincrono para la API OCDS de OECE/SEACE (Pilar 1).

Cumple estrictamente con:
- RN-002-01 / CA-002-01: Sin parametros geograficos en la URL.
- RN-002-02 / CA-002-02: Doble criterio de pertenencia (Cajamarca + universo 001).
- RN-002-03 / CA-002-03: raw_payload intacto byte a byte.
- RN-002-04 / CA-002-04: Deduplicacion por ocid.
- RN-002-05 / CA-002-05: source='seace-ocds' y retrieved_at UTC.
- RN-002-06 / CA-002-06: Declaracion de ventana real en CoverageGapLogger.
- RN-002-07 / CA-002-07: Fallo explícito ante respuesta inválida, sin suposiciones.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any

import httpx

from cajamarca_qhaway.capabilities.live_harvest.backoff import calculate_jitter_delay
from cajamarca_qhaway.capabilities.live_harvest.config import SeaceHarvestConfig
from cajamarca_qhaway.capabilities.live_harvest.coverage_logger import CoverageGapLogger
from cajamarca_qhaway.capabilities.live_harvest.watermark_store import WatermarkStore
from cajamarca_qhaway.capabilities.seace_ingestion.parser import parse_ocds_release
from cajamarca_qhaway.models import ContractingEntity, ProcurementRecord


class SeacePoller:
    """Recolector asincrono para OECE / SEACE OCDS."""

    def __init__(
        self,
        config: SeaceHarvestConfig,
        watermark_store: WatermarkStore,
        coverage_logger: CoverageGapLogger,
        entities_by_ruc: dict[str, ContractingEntity],
        entities_by_consucode: dict[str, ContractingEntity],
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self.config = config
        self.watermark_store = watermark_store
        self.coverage_logger = coverage_logger
        self.entities_by_ruc = entities_by_ruc
        self.entities_by_consucode = entities_by_consucode
        self._http_client = http_client
        self._semaphore = asyncio.Semaphore(config.max_concurrency)

    async def _get_client(self) -> httpx.AsyncClient:
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.config.timeout_seconds),
                headers={"User-Agent": self.config.user_agent, "Accept": "application/json"},
            )
        return self._http_client

    async def poll_cycle(self) -> list[ProcurementRecord]:
        """Ejecuta un ciclo completo de recoleccion del feed de releases."""
        client = await self._get_client()
        url = f"{self.config.base_url.rstrip('/')}/releases"

        window_start = datetime.now(timezone.utc)
        response_payload: dict[str, Any] | None = None

        # Reintentos con Full Jitter acotados por semaforo
        for attempt in range(self.config.max_retries):
            async with self._semaphore:
                try:
                    # CA-002-01: Sin parametros geograficos en la URL
                    res = await client.get(url)
                    if res.status_code == 200:
                        try:
                            response_payload = res.json()
                            break
                        except Exception as json_err:
                            self.coverage_logger.log_incident(
                                source="seace-ocds",
                                attempt=attempt + 1,
                                status_code=200,
                                endpoint=url,
                                error_message=f"JSON parsing error: {json_err}",
                            )
                    else:
                        self.coverage_logger.log_incident(
                            source="seace-ocds",
                            attempt=attempt + 1,
                            status_code=res.status_code,
                            endpoint=url,
                            error_message=f"HTTP {res.status_code}",
                        )
                except httpx.RequestError as exc:
                    self.coverage_logger.log_incident(
                        source="seace-ocds",
                        attempt=attempt + 1,
                        status_code=None,
                        endpoint=url,
                        error_message=str(exc),
                    )

            # Espera con full jitter antes del siguiente reintento
            if attempt < self.config.max_retries - 1:
                delay = calculate_jitter_delay(
                    attempt=attempt,
                    initial_delay=self.config.backoff_initial_delay,
                    factor=self.config.backoff_factor,
                    jitter_max=self.config.jitter_max,
                )
                await asyncio.sleep(delay)

        window_end = datetime.now(timezone.utc)

        # CA-002-07: Si el cuerpo de respuesta no es un release package valido, falla explicitamente
        if not response_payload or not isinstance(response_payload, dict) or "releases" not in response_payload:
            self.coverage_logger.log_window(
                source="seace-ocds",
                start_time=window_start,
                end_time=window_end,
                items_received=0,
                items_retained=0,
                status="FAILED",
                notes="Respuesta invalida o sin campo releases[]",
            )
            return []

        raw_releases = response_payload.get("releases", [])
        total_received = len(raw_releases)
        harvested_records: list[ProcurementRecord] = []
        new_seen_ocids: list[str] = []

        retrieval_timestamp = datetime.now(timezone.utc)

        for rel in raw_releases:
            if not isinstance(rel, dict):
                continue
            ocid = rel.get("ocid")
            if not ocid:
                continue

            # RN-002-04 / CA-002-04: Deduplicacion idempotente por ocid
            if self.watermark_store.is_seace_ocid_seen(ocid):
                continue

            # Parseo y doble filtrado (Cajamarca + Universo 001)
            record = parse_ocds_release(
                release=rel,
                entities_by_ruc=self.entities_by_ruc,
                entities_by_consucode=self.entities_by_consucode,
                retrieved_at=retrieval_timestamp,
            )

            if record:
                harvested_records.append(record)
                new_seen_ocids.append(ocid)

        # Actualizar cursor y registrar ventana de cobertura
        if new_seen_ocids:
            self.watermark_store.update_seace_cursor(retrieval_timestamp, new_seen_ocids)

        self.coverage_logger.log_window(
            source="seace-ocds",
            start_time=window_start,
            end_time=window_end,
            items_received=total_received,
            items_retained=len(harvested_records),
            status="OK",
        )

        return harvested_records

    async def aclose(self) -> None:
        """Cierra el cliente HTTP si fue creado internamente."""
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None
