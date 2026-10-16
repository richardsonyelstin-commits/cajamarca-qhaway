"""Poller resiliente y asincrono para la API OCDS de OECE/SEACE (Pilar 1).

Cumple estrictamente con:
- RN-002-01 / CA-002-01: Sin parametros geograficos en la URL.
- RN-002-02 / CA-002-02: Doble criterio de pertenencia (Cajamarca + universo 001).
- RN-002-03 / CA-002-03: raw_payload intacto byte a byte.
- RN-002-04 / CA-002-04: Deduplicacion por ocid.
- RN-002-05 / CA-002-05: source='seace-ocds' y retrieved_at UTC.
- RN-002-06 / CA-002-06: Declaracion de ventana real en CoverageGapLogger.
- RN-002-07 / CA-002-07: Fallo explicito ante respuesta invalida, sin suposiciones.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime
from urllib.parse import urlparse

import httpx

from cajamarca_qhaway.capabilities.live_harvest.backoff import calculate_jitter_delay
from cajamarca_qhaway.capabilities.live_harvest.config import SeaceHarvestConfig
from cajamarca_qhaway.capabilities.live_harvest.coverage_logger import CoverageGapLogger
from cajamarca_qhaway.capabilities.live_harvest.watermark_store import WatermarkStore
from cajamarca_qhaway.capabilities.seace_ingestion.parser import parse_ocds_release
from cajamarca_qhaway.models import ContractingEntity, ProcurementRecord

logger = logging.getLogger("cajamarca_qhaway.seace_poller")


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
        self._pending_seen_ocids: set[str] = set()
        self._pending_records: dict[str, ProcurementRecord] = {}
        self.last_cycle_status = "NOT_RUN"
        self.last_historical_status = "NOT_RUN"

    def acknowledge_persisted(self) -> None:
        """Advance deduplication cursor only after durable record persistence succeeds."""
        if self._pending_seen_ocids:
            self.watermark_store.update_seace_cursor(
                datetime.now(UTC), sorted(self._pending_seen_ocids)
            )
            self._pending_seen_ocids.clear()
            self._pending_records.clear()

    def _has_seen(self, ocid: str) -> bool:
        return ocid in self._pending_seen_ocids or self.watermark_store.is_seace_ocid_seen(ocid)

    async def _get_client(self) -> httpx.AsyncClient:
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(
                timeout=httpx.Timeout(connect=10.0, read=30.0, write=10.0, pool=10.0),
                headers={"User-Agent": self.config.user_agent, "Accept": "application/json"},
            )
        return self._http_client

    async def _fetch_url_with_retries(self, url: str) -> httpx.Response | None:
        """Descarga una URL aplicando reintentos, semaforo y backoff exponencial con jitter."""
        client = await self._get_client()
        for attempt in range(self.config.max_retries):
            async with self._semaphore:
                try:
                    res = await client.get(url)
                    if res.status_code == 200:
                        return res
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

            if attempt < self.config.max_retries - 1:
                delay = calculate_jitter_delay(
                    attempt=attempt,
                    initial_delay=self.config.backoff_initial_delay,
                    factor=self.config.backoff_factor,
                    jitter_max=self.config.jitter_max,
                )
                await asyncio.sleep(delay)
        return None

    async def poll_cycle(self, page_limit: int | None = None) -> list[ProcurementRecord]:
        """Ejecuta un ciclo completo de recoleccion del feed de releases.

        Si page_limit es None o 1, realiza una sola peticion al endpoint base /releases.
        Si page_limit > 1, pagina secuencialmente desde page=1 hasta page=page_limit.
        """
        self.last_cycle_status = "FAILED"
        effective_pages = page_limit or 1
        window_start = datetime.now(UTC)
        all_harvested_records: list[ProcurementRecord] = list(self._pending_records.values())
        new_seen_ocids: list[str] = []
        total_items_received = 0
        cycle_failed = False

        url = f"{self.config.base_url.rstrip('/')}/releases"
        expected_host = urlparse(self.config.base_url).hostname
        for page_idx in range(1, effective_pages + 1):

            res = await self._fetch_url_with_retries(url)
            if not res:
                cycle_failed = True
                break

            try:
                response_payload = res.json()
            except (ValueError, TypeError, KeyError) as json_err:
                self.coverage_logger.log_incident(
                    source="seace-ocds",
                    attempt=1,
                    status_code=200,
                    endpoint=url,
                    error_message=f"JSON parsing error: {json_err}",
                )
                cycle_failed = True
                break

            # CA-002-07: Si el cuerpo de respuesta no es un release package valido, falla explicitamente
            if not isinstance(response_payload, dict) or "releases" not in response_payload:
                cycle_failed = True
                break

            raw_releases = response_payload.get("releases", [])
            total_items_received += len(raw_releases)
            retrieval_timestamp = datetime.now(UTC)

            for rel in raw_releases:
                if not isinstance(rel, dict):
                    continue
                ocid = rel.get("ocid")
                if not ocid:
                    continue

                # RN-002-04 / CA-002-04: Deduplicacion idempotente por ocid
                if self._has_seen(ocid) or ocid in new_seen_ocids:
                    continue

                # Parseo y doble filtrado (Cajamarca + Universo 001)
                record = parse_ocds_release(
                    release=rel,
                    entities_by_ruc=self.entities_by_ruc,
                    entities_by_consucode=self.entities_by_consucode,
                    retrieved_at=retrieval_timestamp,
                )

                if record:
                    all_harvested_records.append(record)
                    new_seen_ocids.append(ocid)

            # Si no hay enlace siguiente, salir del bucle paginado
            next_link = response_payload.get("links", {}).get("next")
            if not next_link:
                break
            parsed_next = urlparse(next_link)
            if (
                parsed_next.scheme != "https"
                or parsed_next.hostname != expected_host
                or parsed_next.path != f"{urlparse(self.config.base_url).path.rstrip('/')}/releases"
            ):
                self.coverage_logger.log_incident(
                    source="seace-ocds",
                    attempt=page_idx,
                    status_code=200,
                    endpoint=url,
                    error_message="El enlace de paginacion OCDS apunta fuera del endpoint oficial configurado",
                )
                cycle_failed = True
                break
            url = next_link

        window_end = datetime.now(UTC)

        if cycle_failed and total_items_received == 0:
            self.coverage_logger.log_window(
                source="seace-ocds",
                start_time=window_start,
                end_time=window_end,
                items_received=0,
                items_retained=0,
                status="FAILED",
                notes="La API OCDS no devolvio una pagina verificable",
            )
            return []

        if cycle_failed and not all_harvested_records:
            self.coverage_logger.log_window(
                source="seace-ocds",
                start_time=window_start,
                end_time=window_end,
                items_received=total_items_received,
                items_retained=0,
                status="FAILED",
                notes="Respuesta invalida o fallo en releases",
            )
            return []

        # Actualizar cursor y registrar ventana de cobertura
        if new_seen_ocids and not cycle_failed:
            self._pending_seen_ocids.update(new_seen_ocids)
            self._pending_records.update(
                (record.ocid, record) for record in all_harvested_records
                if record.ocid in new_seen_ocids
            )

        self.coverage_logger.log_window(
            source="seace-ocds",
            start_time=window_start,
            end_time=window_end,
            items_received=total_items_received,
            items_retained=len(all_harvested_records),
            status="FAILED" if cycle_failed else "OK",
            notes=("Paginacion incompleta; se conservan solo registros de paginas validas" if cycle_failed else None),
        )
        self.last_cycle_status = "FAILED" if cycle_failed else "OK"

        return all_harvested_records

    async def harvest_monthly_batch(self, year: int, month: int) -> list[ProcurementRecord]:
        """Descarga y procesa un paquete mensual OCDS de contrataciones de OECE."""
        self.last_historical_status = "FAILED"
        self.coverage_logger.log_window(
            source="seace-ocds",
            start_time=datetime.now(UTC),
            end_time=datetime.now(UTC),
            items_received=0,
            items_retained=0,
            status="FAILED",
            notes=f"No se ejecuta el lote {year}-{month:02d}: endpoint historico sin verificar",
        )
        return []

    async def harvest_historical_and_recent(
        self,
        years: list[int] | None = None,
        months: list[int] | None = None,
        page_limit: int = 5,
    ) -> list[ProcurementRecord]:
        """Cosecha contrataciones tanto recientes (feed en vivo) como historicas (lotes mensuales)."""
        self.last_historical_status = "FAILED"
        harvested: list[ProcurementRecord] = []

        # 1. Feed reciente
        recent_records = await self.poll_cycle(page_limit=page_limit)
        harvested.extend(recent_records)

        # 2. Lotes mensuales historicos y recientes (por defecto 2024 a 2026)
        target_years = years or [2024, 2025, 2026]
        for yr in target_years:
            target_months = months or ([10] if yr == 2026 else [6, 12])
            for m in target_months:
                batch_records = await self.harvest_monthly_batch(year=yr, month=m)
                harvested.extend(batch_records)

        return harvested

    async def aclose(self) -> None:
        """Cierra el cliente HTTP si fue creado internamente."""
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None
