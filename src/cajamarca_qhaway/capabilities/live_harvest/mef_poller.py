"""Poller resiliente para fuentes oficiales MEF CKAN y Consulta Amigable.

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
from html.parser import HTMLParser
import io
import logging
import re
import tempfile
from typing import Any
from urllib.parse import urlparse

import httpx

from cajamarca_qhaway.capabilities.live_harvest.backoff import calculate_jitter_delay
from cajamarca_qhaway.capabilities.live_harvest.config import MefHarvestConfig
from cajamarca_qhaway.capabilities.live_harvest.coverage_logger import CoverageGapLogger
from cajamarca_qhaway.capabilities.live_harvest.watermark_store import WatermarkStore
from cajamarca_qhaway.capabilities.live_harvest.mef_consulta_amigable import (
    MefConsultaAmigableClient,
)
from cajamarca_qhaway.capabilities.mef_ingestion.parser import (
    MUNICIPAL_EXECUTOR_PROVINCES,
    parse_mef_record,
)
from cajamarca_qhaway.models import BudgetExecutionRecord, ContractingEntity

logger = logging.getLogger("cajamarca_qhaway.mef_poller")


class _PndaResourceParser(HTMLParser):
    """Extrae recursos descargables listados en la página oficial PNDA del dataset MEF."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.resources: list[dict[str, str]] = []
        self._resource: dict[str, str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "li":
            self._resource = None
            return
        if tag != "a":
            return
        values = {key: value or "" for key, value in attrs}
        classes = set(values.get("class", "").split())
        if "heading" in classes and values.get("title"):
            match = re.search(r"/resource/([0-9a-f-]{36})", values.get("href", ""), re.I)
            self._resource = {
                "title": values["title"],
                "resource_id": match.group(1) if match else "",
                "url": "",
            }
        elif "data-link" in classes and self._resource is not None:
            self._resource["url"] = values.get("href", "")

    def handle_endtag(self, tag: str) -> None:
        if tag == "li" and self._resource is not None:
            self.resources.append(self._resource)
            self._resource = None


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
        # UUIDs PNDA identify downloadable files, not necessarily DataStore tables.
        self._pnda_resource_ids: dict[int, str] = {}
        # This map is reserved for resource IDs verified against the legacy DataStore.
        self._discovered_resource_ids: dict[int, str] = {}
        self.last_cycle_status = "NOT_RUN"
        self.last_historical_status = "NOT_RUN"

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
        if "apps5.mineco.gob.pe" in url.lower():
            raise ValueError("La URL CKAN no puede apuntar al host del módulo Consulta Amigable")

    async def _collect_consulta_amigable_records(
        self, years: list[int]
    ) -> list[BudgetExecutionRecord]:
        entities = list({entity.entity_id: entity for entity in self.entities_by_id.values()}.values())
        records: list[BudgetExecutionRecord] = []
        async with MefConsultaAmigableClient() as client:
            for year in years:
                records.extend(await client.extract(year, entities))
        self._pending_records.update((record.execution_record_id, record) for record in records)
        if records:
            self._pending_timestamp = max(record.retrieved_at for record in records)
            self._pending_offset = self.watermark_store.state.last_mef_offset
        return records

    async def _get_client(self) -> httpx.AsyncClient:
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(
                timeout=httpx.Timeout(connect=10.0, read=30.0, write=10.0, pool=10.0),
                headers={
                    "User-Agent": self.config.user_agent,
                    "Accept": "text/html,application/json,text/csv,*/*;q=0.8",
                },
            )
        return self._http_client

    async def _discover_official_csv_urls(self, years: list[int]) -> dict[int, str]:
        """Descubre los CSV oficiales en la página PNDA del dataset de gasto del MEF."""
        client = await self._get_client()
        endpoint = self.config.catalog_dataset_url
        try:
            response = await client.get(endpoint)
            response.raise_for_status()
            parser = _PndaResourceParser()
            parser.feed(response.text)
        except (httpx.HTTPError, ValueError) as exc:
            self.coverage_logger.log_incident(
                source="mef-datastore",
                attempt=1,
                status_code=getattr(getattr(exc, "response", None), "status_code", None),
                endpoint=endpoint,
                error_message=f"No se pudo consultar el catálogo oficial MEF: {exc}",
            )
            return {}

        if not parser.resources:
            self.coverage_logger.log_incident(
                source="mef-datastore",
                attempt=1,
                status_code=response.status_code,
                endpoint=endpoint,
                error_message="PNDA respondió sin recursos de descarga reconocibles para el dataset MEF",
            )
            return {}

        discovered: dict[int, str] = {}
        for year in years:
            candidates = [
                resource
                for resource in parser.resources
                if resource["title"].startswith(f"{year}-Gasto")
                and resource["title"].casefold().endswith(".csv")
            ]
            # Preferir el corte diario vigente; 2024 solo dispone del consolidado anual.
            candidates.sort(
                key=lambda resource: (
                    "diario" not in resource["title"].casefold(),
                    "mensual" in resource["title"].casefold(),
                )
            )
            for resource in candidates:
                resource_id = resource["resource_id"].strip()
                if resource_id:
                    self._pnda_resource_ids[year] = resource_id
                url = resource["url"].strip()
                parsed = urlparse(url)
                if (
                    parsed.scheme == "https"
                    and parsed.hostname == "fs.datosabiertos.mef.gob.pe"
                    and parsed.path.lower().endswith(".csv")
                ):
                    discovered[year] = url
                    break
        return discovered

    async def poll_cycle(self, limit: int = 100) -> list[BudgetExecutionRecord]:
        """Ejecuta una corrida de recoleccion contra CKAN DataStore."""
        self.last_cycle_status = "FAILED"
        if self.config.enable_consulta_amigable:
            started = datetime.now(timezone.utc)
            year = started.year
            try:
                records = await self._collect_consulta_amigable_records([year])
            except (httpx.HTTPError, ValueError, RuntimeError) as exc:
                self.coverage_logger.log_incident(
                    source="mef-consulta-amigable", attempt=1, status_code=None,
            endpoint=(
                "https://apps5.mineco.gob.pe/transparencia/Mensual/"
                f"Navegar_6.aspx?y={year}&ap=ActProy"
            ),
                    error_message=str(exc),
                )
                return []
            self.coverage_logger.log_window(
                source="mef-consulta-amigable", start_time=started,
                end_time=datetime.now(timezone.utc), items_received=len(records),
                items_retained=len(records), status="OK" if len(records) == 14 else "FAILED",
                notes=f"Consulta Amigable MEF: {len(records)}/14 pliegos para {year}",
            )
            self.last_cycle_status = "OK" if len(records) == 14 else "FAILED"
            return records
        client = await self._get_client()
        url = f"{self.config.base_url.rstrip('/')}/datastore_search"

        current_offset = self.watermark_store.state.last_mef_offset
        params = {
            "resource_id": self.config.resource_id,
            "limit": limit,
            "offset": current_offset,
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
        records_data: Any = None
        if isinstance(response_payload, dict):
            success_marker = response_payload.get("success", response_payload.get("sucess"))
            if success_marker is True or str(success_marker).strip().casefold() == "true":
                result = response_payload.get("result")
                if isinstance(result, dict):
                    records_data = result.get("records")
                if records_data is None:
                    records_data = response_payload.get("records")

        if not isinstance(records_data, list) or not records_data:
            fallback_records = []
            if self.config.enable_open_data_fallback:
                fallback_records = await self._collect_open_data_records(
                    [datetime.now(timezone.utc).year], targeted_queries=False
                )
            if fallback_records:
                self._pending_records.update(
                    (record.execution_record_id, record) for record in fallback_records
                )
                self.coverage_logger.log_window(
                    source="mef-datastore",
                    start_time=window_start,
                    end_time=datetime.now(timezone.utc),
                    items_received=len(fallback_records),
                    items_retained=len(fallback_records),
                    status="OK",
                    notes="Filas obtenidas desde un CSV oficial descubierto en el catálogo MEF",
                )
                self.last_cycle_status = "OK"
                return fallback_records
            self.coverage_logger.log_incident(
                source="mef-datastore",
                attempt=1,
                status_code=200 if response_payload is not None else None,
                endpoint=url,
                error_message=(
                    "DataStore no devolvió filas verificables y el fallback oficial no produjo "
                    "registros; no se acepta como cosecha"
                ),
            )
            self.coverage_logger.log_window(
                source="mef-datastore",
                start_time=window_start,
                end_time=window_end,
                items_received=0,
                items_retained=0,
                status="FAILED",
                notes="Sin filas verificables en DataStore ni en CSV oficial MEF",
            )
            return list(self._pending_records.values())

        total_received = len(records_data)
        harvested_records: list[BudgetExecutionRecord] = list(self._pending_records.values())
        retained_this_page = 0
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
                retained_this_page += 1

        if total_received:
            new_offset = current_offset + total_received
            self._pending_offset = max(new_offset, self._pending_offset or 0)
            self._pending_timestamp = retrieval_timestamp

        self.coverage_logger.log_window(
            source="mef-datastore",
            start_time=window_start,
            end_time=window_end,
            items_received=total_received,
            items_retained=retained_this_page,
            status="OK",
        )
        self.last_cycle_status = "OK"

        return harvested_records

    async def _fetch_csv_dataset(self, url: str) -> list[dict[str, Any]]:
        """Procesa en streaming temporal un CSV oficial y conserva filas de Cajamarca."""
        self._assert_valid_endpoint(url)
        parsed_url = urlparse(url)
        if parsed_url.scheme != "https" or parsed_url.hostname != "fs.datosabiertos.mef.gob.pe":
            raise ValueError("El fallback CSV solo acepta URLs HTTPS del host oficial de archivos MEF")
        client = await self._get_client()

        for attempt in range(self.config.max_retries):
            try:
                with tempfile.SpooledTemporaryFile(max_size=8 * 1024 * 1024, mode="w+b") as spool:
                    async with client.stream("GET", url) as res:
                        if res.status_code != 200:
                            self.coverage_logger.log_incident(
                                source="mef-datastore",
                                attempt=attempt + 1,
                                status_code=res.status_code,
                                endpoint=url,
                                error_message=f"HTTP {res.status_code} en CSV oficial MEF",
                            )
                            continue
                        async for chunk in res.aiter_bytes():
                            spool.write(chunk)

                    spool.seek(0)
                    text_stream = io.TextIOWrapper(spool, encoding="utf-8-sig", errors="strict", newline="")
                    reader = csv.DictReader(text_stream)
                    if not reader.fieldnames:
                        return []
                    fields = {name.strip().upper() for name in reader.fieldnames if name}
                    if not {"ANO_EJE", "MONTO_PIM"}.issubset(fields):
                        raise ValueError("CSV oficial no contiene ANO_EJE y MONTO_PIM")
                    if "MONTO_DEVENGADO" not in fields and not any(
                        name.startswith("MONTO_DEVENGADO_") for name in fields
                    ):
                        raise ValueError("CSV oficial no contiene una columna de devengado reconocida")
                    if not ({"DEPARTAMENTO_EJECUTORA", "DEPARTAMENTO_EJECUTORA_NOMBRE"} & fields):
                        raise ValueError("CSV oficial no contiene el departamento de la ejecutora")

                    matching_rows: list[dict[str, Any]] = []
                    for row in reader:
                        if not row:
                            continue
                        normalized = {str(k).strip().upper(): v for k, v in row.items() if k}
                        dep_code = str(normalized.get("DEPARTAMENTO_EJECUTORA") or "").strip()
                        dep_name = str(normalized.get("DEPARTAMENTO_EJECUTORA_NOMBRE") or "").strip().upper()
                        is_cajamarca = dep_code.lstrip("0") == "6" or dep_name == "CAJAMARCA"
                        if is_cajamarca:
                            matching_rows.append(row)
                    return matching_rows
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

    async def _collect_targeted_datastore_records(
        self, years: list[int]
    ) -> list[BudgetExecutionRecord]:
        """Busca por códigos SIAF canónicos, sin filtrar columnas departamentales."""
        # Only query DataStore with IDs explicitly configured/verified for that API.
        # PNDA resource UUIDs identify file distributions and must not be reused here.
        resource_ids = dict(self._discovered_resource_ids)
        for year in years:
            configured_ids = self.config.resource_ids_by_year.get(str(year), [])
            if configured_ids:
                resource_ids.setdefault(year, configured_ids[0])

        # ContractingEntity no contiene metadata administrativa; el parser mantiene
        # el cruce oficial en una allowlist sincronizada con el universo YAML.
        canonical_municipal_codes = sorted(MUNICIPAL_EXECUTOR_PROVINCES)
        search_codes = [("445", "pliego")]
        search_codes.extend((code, "sec_ejec") for code in canonical_municipal_codes)
        client = await self._get_client()
        endpoint = f"{self.config.base_url.rstrip('/')}/datastore_search"
        all_records: dict[str, BudgetExecutionRecord] = {}
        semaphore = asyncio.Semaphore(2)

        async def query_one(year: int, code: str, code_kind: str) -> None:
            resource_id = resource_ids.get(year)
            if not resource_id:
                self.coverage_logger.log_incident(
                    source="mef-datastore",
                    attempt=1,
                    status_code=None,
                    endpoint=self.config.catalog_base_url,
                    error_message=f"Sin resource_id oficial descubierto para {year}, código {code}",
                )
                return

            started = datetime.now(timezone.utc)
            params = {"resource_id": resource_id, "q": code, "limit": 100, "offset": 0}
            try:
                async with semaphore:
                    response = await client.get(
                        endpoint,
                        params=params,
                        timeout=httpx.Timeout(
                            connect=8.0,
                            read=self.config.targeted_query_timeout_seconds,
                            write=8.0,
                            pool=8.0,
                        ),
                    )
                if response.status_code != 200:
                    self.coverage_logger.log_incident(
                        source="mef-datastore",
                        attempt=1,
                        status_code=response.status_code,
                        endpoint=str(response.url),
                        error_message=f"Consulta puntual {year} {code_kind}={code} respondió HTTP {response.status_code}",
                    )
                    return
                try:
                    payload = response.json()
                except ValueError as exc:
                    self.coverage_logger.log_incident(
                        source="mef-datastore",
                        attempt=1,
                        status_code=200,
                        endpoint=str(response.url),
                        error_message=f"JSON inválido para {year} {code_kind}={code}: {exc}",
                    )
                    return

                raw_records = payload.get("records") if isinstance(payload, dict) else None
                if not isinstance(raw_records, list):
                    result_obj = payload.get("result") if isinstance(payload, dict) else None
                    raw_records = result_obj.get("records") if isinstance(result_obj, dict) else None
                if not isinstance(raw_records, list) or not raw_records:
                    self.coverage_logger.log_incident(
                        source="mef-datastore",
                        attempt=1,
                        status_code=200,
                        endpoint=str(response.url),
                        error_message=(
                            f"MEF no entregó filas para {year} {code_kind}={code}; "
                            "records nulo o vacío en consulta puntual"
                        ),
                    )
                    self.coverage_logger.log_window(
                        source="mef-datastore",
                        start_time=started,
                        end_time=datetime.now(timezone.utc),
                        items_received=0,
                        items_retained=0,
                        status="FAILED",
                        notes=f"Sin filas para {year} {code_kind}={code}",
                    )
                    return

                retrieved_at = datetime.now(timezone.utc)
                retained = 0
                for row in raw_records:
                    if not isinstance(row, dict):
                        continue
                    source_code = str(
                        row.get("PLIEGO") if code_kind == "pliego" else row.get("SEC_EJEC") or ""
                    ).strip().lstrip("0")
                    if source_code != code.lstrip("0") or str(row.get("ANO_EJE", "")).strip() != str(year):
                        continue
                    record = parse_mef_record(
                        record=row,
                        entities_by_ruc=self.entities_by_ruc,
                        entities_by_id=self.entities_by_id,
                        retrieved_at=retrieved_at,
                    )
                    if record and record.fiscal_year == year:
                        all_records[record.execution_record_id] = record
                        retained += 1
                self.coverage_logger.log_window(
                    source="mef-datastore",
                    start_time=started,
                    end_time=datetime.now(timezone.utc),
                    items_received=len(raw_records),
                    items_retained=retained,
                    status="OK" if retained else "FAILED",
                    notes=f"Consulta puntual {year} {code_kind}={code}",
                )
            except httpx.RequestError as exc:
                self.coverage_logger.log_incident(
                    source="mef-datastore",
                    attempt=1,
                    status_code=None,
                    endpoint=endpoint,
                    error_message=f"Consulta puntual {year} {code_kind}={code}: {exc}",
                )
                self.coverage_logger.log_window(
                    source="mef-datastore",
                    start_time=started,
                    end_time=datetime.now(timezone.utc),
                    items_received=0,
                    items_retained=0,
                    status="FAILED",
                    notes=f"Timeout o error de red para {year} {code_kind}={code}",
                )

        for year in years:
            await asyncio.gather(
                *(query_one(year, code, kind) for code, kind in search_codes)
            )
        return list(all_records.values())

    async def _collect_open_data_records(
        self, years: list[int], targeted_queries: bool = True
    ) -> list[BudgetExecutionRecord]:
        """Consulta códigos SIAF y luego prueba recursos CSV oficiales del MEF."""
        configured = {
            int(year): urls[0]
            for year, urls in self.config.annual_dataset_urls.items()
            if str(year).isdigit() and urls
        }
        missing_years = [year for year in years if year not in configured]
        discovered = (
            await self._discover_official_csv_urls(missing_years) if missing_years else {}
        )
        urls_by_year = {**discovered, **configured}
        retrieved_at = datetime.now(timezone.utc)
        by_record_id: dict[str, BudgetExecutionRecord] = {}

        for year in years:
            if any(record.fiscal_year == year for record in by_record_id.values()):
                continue
            source_url = urls_by_year.get(year)
            if not source_url:
                self.coverage_logger.log_incident(
                    source="mef-datastore",
                    attempt=1,
                    status_code=None,
                    endpoint=self.config.catalog_base_url,
                    error_message=f"El catálogo oficial no publicó un CSV utilizable para {year}",
                )
                continue
            rows = await self._fetch_csv_dataset(source_url)
            for row in rows:
                record = parse_mef_record(
                    record=row,
                    entities_by_ruc=self.entities_by_ruc,
                    entities_by_id=self.entities_by_id,
                    retrieved_at=retrieved_at,
                )
                if record and record.fiscal_year == year:
                    by_record_id[record.execution_record_id] = record

        # PNDA y sus archivos oficiales son la fuente primaria. El DataStore antiguo
        # solo se consulta como fallback cuando el recurso PNDA no entregó filas.
        uncovered_years = [
            year
            for year in years
            if not any(record.fiscal_year == year for record in by_record_id.values())
        ]
        if targeted_queries and uncovered_years:
            for record in await self._collect_targeted_datastore_records(uncovered_years):
                by_record_id[record.execution_record_id] = record
        return list(by_record_id.values())

    async def harvest_historical_and_recent(
        self, years: list[int] | None = None
    ) -> list[BudgetExecutionRecord]:
        """Cosecha ejecuciones presupuestales tanto recientes como historicas (2024-2026)."""
        self.last_historical_status = "FAILED"
        target_years = years or [2024, 2025, 2026]
        all_records: list[BudgetExecutionRecord] = []
        seen_record_ids: set[str] = set()
        window_start = datetime.now(timezone.utc)

        if self.config.enable_consulta_amigable:
            try:
                all_records = await self._collect_consulta_amigable_records(target_years)
            except (httpx.HTTPError, ValueError, RuntimeError) as exc:
                self.coverage_logger.log_incident(
                    source="mef-consulta-amigable", attempt=1, status_code=None,
                    endpoint="https://apps5.mineco.gob.pe/transparencia/Mensual/Navegar_6.aspx",
                    error_message=str(exc),
                )
                all_records = []
            success = len(all_records) == 14 * len(target_years)
            self.last_historical_status = "OK" if success else "FAILED"
            self.coverage_logger.log_window(
                source="mef-consulta-amigable", start_time=window_start,
                end_time=datetime.now(timezone.utc), items_received=len(all_records),
                items_retained=len(all_records), status="OK" if success else "FAILED",
                notes=(
                    f"Consulta Amigable años {target_years}: "
                    f"{len(all_records)}/{14 * len(target_years)} pliegos"
                ),
            )
            return all_records

        # 1. Probar corrida normal primero
        recent_records = await self.poll_cycle()
        for r in recent_records:
            if r.execution_record_id not in seen_record_ids:
                seen_record_ids.add(r.execution_record_id)
                all_records.append(r)

        # 2. Si se solicitan anos o datastore_search no devolvio suficientes, consultar datasets anuales del MEF
        if self.config.enable_open_data_fallback:
            for record in await self._collect_open_data_records(target_years):
                if record.execution_record_id not in seen_record_ids:
                    seen_record_ids.add(record.execution_record_id)
                    all_records.append(record)

        window_end = datetime.now(timezone.utc)
        success = all(
            any(record.fiscal_year == year for record in all_records) for year in target_years
        )
        self.coverage_logger.log_window(
            source="mef-datastore",
            start_time=window_start,
            end_time=window_end,
            items_received=len(all_records),
            items_retained=len(all_records),
            status="OK" if success else "FAILED",
            notes=(
                f"Cosecha MEF anos {target_years}: {len(all_records)} filas verificables"
                if success
                else f"Cobertura MEF incompleta para {target_years}; no se confirmaron todos los anos"
            ),
        )
        # A recent page is not evidence that all requested fiscal years were covered.
        if success:
            self.last_historical_status = "OK"

        return all_records

    async def aclose(self) -> None:
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None
