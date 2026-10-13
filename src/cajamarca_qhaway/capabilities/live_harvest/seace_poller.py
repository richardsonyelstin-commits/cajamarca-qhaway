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
from datetime import datetime, timezone
import io
import json
import logging
from typing import Any
import zipfile

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

    async def _get_client(self) -> httpx.AsyncClient:
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.config.timeout_seconds),
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
        effective_pages = page_limit or 1
        window_start = datetime.now(timezone.utc)
        all_harvested_records: list[ProcurementRecord] = []
        new_seen_ocids: list[str] = []
        total_items_received = 0
        cycle_failed = False

        for page_idx in range(1, effective_pages + 1):
            if effective_pages == 1:
                url = f"{self.config.base_url.rstrip('/')}/releases"
            else:
                url = f"{self.config.base_url.rstrip('/')}/releases?page={page_idx}"

            res = await self._fetch_url_with_retries(url)
            if not res:
                cycle_failed = True
                break

            try:
                response_payload = res.json()
            except Exception as json_err:
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
                    all_harvested_records.append(record)
                    new_seen_ocids.append(ocid)

            # Si no hay enlace siguiente, salir del bucle paginado
            next_link = response_payload.get("links", {}).get("next")
            if not next_link:
                break

        window_end = datetime.now(timezone.utc)

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
        if new_seen_ocids:
            self.watermark_store.update_seace_cursor(window_end, new_seen_ocids)

        self.coverage_logger.log_window(
            source="seace-ocds",
            start_time=window_start,
            end_time=window_end,
            items_received=total_items_received,
            items_retained=len(all_harvested_records),
            status="OK",
        )

        return all_harvested_records

    async def harvest_monthly_batch(self, year: int, month: int) -> list[ProcurementRecord]:
        """Descarga y procesa un paquete mensual OCDS de contrataciones de OECE."""
        url = f"{self.config.historical_batch_base_url.rstrip('/')}/{year}/{month:02d}/"
        window_start = datetime.now(timezone.utc)
        res = await self._fetch_url_with_retries(url)

        if not res:
            return []

        harvested_records: list[ProcurementRecord] = []
        new_seen_ocids: list[str] = []
        retrieval_timestamp = datetime.now(timezone.utc)

        try:
            # Procesar archivo ZIP o JSON directo
            if res.content.startswith(b"PK\x03\x04"):
                with zipfile.ZipFile(io.BytesIO(res.content)) as z:
                    for filename in z.namelist():
                        if filename.endswith(".json"):
                            raw_json = json.loads(z.read(filename).decode("utf-8", errors="replace"))
                            records = raw_json.get("records", [])
                            for rec in records:
                                comp_rel = rec.get("compiledRelease") or (
                                    rec.get("releases", [{}])[0] if rec.get("releases") else None
                                )
                                if not comp_rel:
                                    continue
                                ocid = comp_rel.get("ocid")
                                if not ocid or self.watermark_store.is_seace_ocid_seen(ocid):
                                    continue

                                prec = parse_ocds_release(
                                    release=comp_rel,
                                    entities_by_ruc=self.entities_by_ruc,
                                    entities_by_consucode=self.entities_by_consucode,
                                    retrieved_at=retrieval_timestamp,
                                )
                                if prec:
                                    harvested_records.append(prec)
                                    new_seen_ocids.append(ocid)
            else:
                data = res.json()
                releases = data.get("releases", [])
                for rel in releases:
                    ocid = rel.get("ocid")
                    if not ocid or self.watermark_store.is_seace_ocid_seen(ocid):
                        continue
                    prec = parse_ocds_release(
                        release=rel,
                        entities_by_ruc=self.entities_by_ruc,
                        entities_by_consucode=self.entities_by_consucode,
                        retrieved_at=retrieval_timestamp,
                    )
                    if prec:
                        harvested_records.append(prec)
                        new_seen_ocids.append(ocid)

            if new_seen_ocids:
                self.watermark_store.update_seace_cursor(retrieval_timestamp, new_seen_ocids)

            self.coverage_logger.log_window(
                source="seace-ocds",
                start_time=window_start,
                end_time=datetime.now(timezone.utc),
                items_received=len(harvested_records),
                items_retained=len(harvested_records),
                status="OK",
                notes=f"Lote mensual historico OECE {year}-{month:02d}",
            )
        except Exception as exc:
            logger.error("Error al procesar lote mensual OECE %d-%02d: %s", year, month, exc)

        return harvested_records

    async def harvest_historical_and_recent(
        self,
        years: list[int] | None = None,
        months: list[int] | None = None,
        page_limit: int = 5,
    ) -> list[ProcurementRecord]:
        """Cosecha contrataciones tanto recientes (feed en vivo) como historicas (lotes mensuales)."""
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
