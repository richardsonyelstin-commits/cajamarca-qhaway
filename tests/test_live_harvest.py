"""Pruebas exhaustivas para el subsistema de Cosecha Continua de Datos en Vivo (live_harvest).

Valida:
- TK-101 / CA-002-01 a CA-002-07 (SEACE OCDS Poller)
- TK-102 / CA-003-01 a CA-003-05 (MEF CKAN Poller & Veto a Consulta Amigable)
- TK-103 / Persistencia Atomica (WatermarkStore) y Auditoria (CoverageGapLogger)
- TK-104 / Resiliencia, reintentos con Jitter y tolerancia a fallos
- TK-105 / HarvesterDaemon y CLI
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import httpx
import pytest

from cajamarca_qhaway.capabilities.entity_mapping.dataset import load_universe
from cajamarca_qhaway.capabilities.live_harvest.backoff import calculate_jitter_delay
from cajamarca_qhaway.capabilities.live_harvest.config import (
    HarvestConfig,
    MefHarvestConfig,
    SeaceHarvestConfig,
)
from cajamarca_qhaway.capabilities.live_harvest.coverage_logger import CoverageGapLogger
from cajamarca_qhaway.capabilities.live_harvest.daemon import HarvesterDaemon
from cajamarca_qhaway.capabilities.live_harvest.mef_poller import MefPoller
from cajamarca_qhaway.capabilities.live_harvest.seace_poller import SeacePoller
from cajamarca_qhaway.capabilities.live_harvest.watermark_store import WatermarkStore
from cajamarca_qhaway.models import ContractingEntity


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def tmp_harvest_dir(tmp_path: Path) -> Path:
    state_dir = tmp_path / "state"
    state_dir.mkdir(parents=True, exist_ok=True)
    return tmp_path


@pytest.fixture
def watermark_store(tmp_harvest_dir: Path) -> WatermarkStore:
    return WatermarkStore(tmp_harvest_dir / "state" / "watermarks.json")


@pytest.fixture
def coverage_logger(tmp_harvest_dir: Path) -> CoverageGapLogger:
    return CoverageGapLogger(tmp_harvest_dir / "state" / "coverage_gaps.jsonl")


@pytest.fixture
def test_entities() -> tuple[dict[str, ContractingEntity], dict[str, ContractingEntity], dict[str, ContractingEntity]]:
    universe = load_universe()
    by_ruc = {r.entity.ruc: r.entity for r in universe.entities}
    by_consucode = {r.entity.consucode_id: r.entity for r in universe.entities if r.entity.consucode_id}
    by_id = {r.entity.entity_id: r.entity for r in universe.entities}
    return by_ruc, by_consucode, by_id


# ============================================================================
# 1. Config & Backoff Tests
# ============================================================================


def test_harvest_config_defaults_and_immutability():
    cfg = HarvestConfig()
    assert cfg.seace.max_concurrency == 2
    assert cfg.seace.rate_limit_per_second == 3.0
    assert cfg.mef.cajamarca_dep_code == "06"

    # Inmutabilidad (frozen=True)
    with pytest.raises(Exception):
        cfg.seace.poll_interval_seconds = 10  # type: ignore


def test_calculate_jitter_delay_bounds():
    delay_0 = calculate_jitter_delay(attempt=0, initial_delay=1.0, factor=2.0, jitter_max=0.5)
    assert 0.1 <= delay_0 <= 2.0

    delay_3 = calculate_jitter_delay(attempt=3, initial_delay=1.0, factor=2.0, jitter_max=1.0)
    assert 0.1 <= delay_3 <= 30.0

    assert calculate_jitter_delay(-1) == 0.0


# ============================================================================
# 2. WatermarkStore Tests (Atomic Two-Phase Write)
# ============================================================================


def test_watermark_store_atomic_save_and_reload(tmp_harvest_dir: Path):
    store_file = tmp_harvest_dir / "state" / "watermarks.json"
    store = WatermarkStore(store_file)

    assert store.state.seen_seace_ocids == set()
    assert store.state.last_mef_offset == 0

    now = datetime.now(timezone.utc)
    store.update_seace_cursor(timestamp=now, new_ocids=["ocds-dgv273-001", "ocds-dgv273-002"])
    store.update_mef_cursor(timestamp=now, offset=250)

    assert store.is_seace_ocid_seen("ocds-dgv273-001")
    assert not store.is_seace_ocid_seen("ocds-dgv273-999")

    # Recargar desde disco y verificar integridad
    reloaded_store = WatermarkStore(store_file)
    assert "ocds-dgv273-001" in reloaded_store.state.seen_seace_ocids
    assert "ocds-dgv273-002" in reloaded_store.state.seen_seace_ocids
    assert reloaded_store.state.last_mef_offset == 250


# ============================================================================
# 3. CoverageGapLogger Tests (RN-002-06, RN-002-07, RN-003-06)
# ============================================================================


def test_coverage_logger_append_and_read(coverage_logger: CoverageGapLogger):
    t1 = datetime(2026, 10, 12, 10, 0, tzinfo=timezone.utc)
    t2 = datetime(2026, 10, 12, 10, 5, tzinfo=timezone.utc)

    coverage_logger.log_window(
        source="seace-ocds",
        start_time=t1,
        end_time=t2,
        items_received=20,
        items_retained=2,
        status="OK",
    )

    coverage_logger.log_incident(
        source="seace-ocds",
        attempt=1,
        status_code=503,
        endpoint="https://contratacionesabiertas.oece.gob.pe/api/v1/releases",
        error_message="Service Unavailable",
    )

    records = coverage_logger.read_records()
    assert len(records) == 2
    assert records[0]["type"] == "coverage_window"
    assert records[0]["items_retained"] == 2
    assert records[1]["type"] == "coverage_gap_incident"
    assert records[1]["status_code"] == 503


# ============================================================================
# 4. SeacePoller Tests (CA-002-01 a CA-002-07)
# ============================================================================


def test_seace_poller_harvests_cajamarca_release(
    watermark_store: WatermarkStore,
    coverage_logger: CoverageGapLogger,
    test_entities: tuple,
):
    import asyncio

    async def _test():
        by_ruc, by_consucode, _ = test_entities

        mock_release_package = {
            "version": "1.1",
            "publishedDate": "2026-10-12T10:00:00Z",
            "releases": [
                # Release 1: Cajamarca (Municipalidad Provincial de Cajamarca - RUC 20148154563)
                {
                    "ocid": "ocds-dgv273-2026-CAJ-001",
                    "id": "rel-001",
                    "tender": {
                        "title": "Adquisicion de combustible para maquinaria",
                        "procurementMethod": "open",
                        "numberOfTenderers": 1,
                        "value": {"amount": 750000.0, "currency": "PEN"},
                    },
                    "parties": [
                        {
                            "id": "PE-CONSUCODE-200701",
                            "name": "MUNICIPALIDAD PROVINCIAL DE CAJAMARCA",
                            "identifier": {"id": "20143623042", "scheme": "PE-RUC"},
                            "address": {
                                "department": "CAJAMARCA",
                                "region": "CAJAMARCA",
                            },
                            "roles": ["buyer", "procuringEntity"],
                        }
                    ],
                },
                # Release 2: Lima (debe ser descartado por filtro regional)
                {
                    "ocid": "ocds-dgv273-2026-LIM-002",
                    "id": "rel-002",
                    "tender": {"title": "Obras en Lima Metropolitana"},
                    "parties": [
                        {
                            "id": "PE-CONSUCODE-100000",
                            "name": "MUNICIPALIDAD METROPOLITANA DE LIMA",
                            "identifier": {"id": "20131380951", "scheme": "PE-RUC"},
                            "address": {"department": "LIMA"},
                            "roles": ["buyer"],
                        }
                    ],
                },
            ],
        }

        recorded_urls = []

        def mock_handler(request: httpx.Request) -> httpx.Response:
            recorded_urls.append(str(request.url))
            return httpx.Response(200, json=mock_release_package)

        client = httpx.AsyncClient(transport=httpx.MockTransport(mock_handler))

        config = SeaceHarvestConfig()
        poller = SeacePoller(
            config=config,
            watermark_store=watermark_store,
            coverage_logger=coverage_logger,
            entities_by_ruc=by_ruc,
            entities_by_consucode=by_consucode,
            http_client=client,
        )

        records = await poller.poll_cycle()

        # CA-002-01: Sin parametros en la URL
        assert len(recorded_urls) == 1
        assert "?" not in recorded_urls[0]

        # CA-002-02: Solo Cajamarca pasa
        assert len(records) == 1
        assert records[0].ocid == "ocds-dgv273-2026-CAJ-001"
        assert records[0].source == "seace-ocds"
        assert records[0].awarded_amount == 750000.0

        # CA-002-03: raw_payload intacto
        assert records[0].raw_payload["ocid"] == "ocds-dgv273-2026-CAJ-001"

        # CA-002-04: Deduplicacion en segunda corrida
        second_run = await poller.poll_cycle()
        assert len(second_run) == 0, "No debe duplicar registros ya vistos"

        await poller.aclose()

    asyncio.run(_test())


def test_seace_poller_failure_logs_coverage_incident(
    watermark_store: WatermarkStore,
    coverage_logger: CoverageGapLogger,
    test_entities: tuple,
):
    import asyncio

    async def _test():
        by_ruc, by_consucode, _ = test_entities

        def mock_503(request: httpx.Request) -> httpx.Response:
            return httpx.Response(503, text="Service Unavailable")

        client = httpx.AsyncClient(transport=httpx.MockTransport(mock_503))
        config = SeaceHarvestConfig(max_retries=2, backoff_initial_delay=0.1)

        poller = SeacePoller(
            config=config,
            watermark_store=watermark_store,
            coverage_logger=coverage_logger,
            entities_by_ruc=by_ruc,
            entities_by_consucode=by_consucode,
            http_client=client,
        )

        records = await poller.poll_cycle()
        assert len(records) == 0

        logs = coverage_logger.read_records()
        incidents = [l for l in logs if l.get("type") == "coverage_gap_incident"]
        windows = [l for l in logs if l.get("type") == "coverage_window"]

        assert len(incidents) == 2
        assert incidents[0]["status_code"] == 503
        assert len(windows) == 1
        assert windows[0]["status"] == "FAILED"

        await poller.aclose()

    asyncio.run(_test())


# ============================================================================
# 5. MefPoller Tests (CA-003-01 a CA-003-05)
# ============================================================================


def test_mef_poller_rejects_consulta_amigable_url(
    watermark_store: WatermarkStore,
    coverage_logger: CoverageGapLogger,
    test_entities: tuple,
):
    by_ruc, _, by_id = test_entities
    forbidden_cfg = MefHarvestConfig(base_url="https://apps5.mineco.gob.pe/transparencia/Navegador/default.aspx")

    # CA-003-01: Prohibicion absoluta a Consulta Amigable
    with pytest.raises(ValueError, match="RN-003-01 / CA-003-01"):
        MefPoller(
            config=forbidden_cfg,
            watermark_store=watermark_store,
            coverage_logger=coverage_logger,
            entities_by_ruc=by_ruc,
            entities_by_id=by_id,
        )


def test_mef_poller_harvests_budget_execution(
    watermark_store: WatermarkStore,
    coverage_logger: CoverageGapLogger,
    test_entities: tuple,
):
    import asyncio

    async def _test():
        by_ruc, _, by_id = test_entities

        mock_ckan_response = {
            "success": True,
            "result": {
                "resource_id": "35bdc5b5-017c-42c1-ba20-8820bf1248b7",
                "records": [
                    {
                        "_id": 1,
                        "ano_eje": 2026,
                        "mes_eje": 10,
                        "ruc": "20143623042",
                        "pliego_nombre": "MUNICIPALIDAD PROVINCIAL DE CAJAMARCA",
                        "monto_pim": 150000000.0,
                        "monto_devengado": 82000000.0,
                        "departamento_ejecutora": "06",
                    }
                ],
            },
        }

        def mock_handler(request: httpx.Request) -> httpx.Response:
            assert "resource_id" in str(request.url)
            return httpx.Response(200, json=mock_ckan_response)

        client = httpx.AsyncClient(transport=httpx.MockTransport(mock_handler))
        config = MefHarvestConfig()

        poller = MefPoller(
            config=config,
            watermark_store=watermark_store,
            coverage_logger=coverage_logger,
            entities_by_ruc=by_ruc,
            entities_by_id=by_id,
            http_client=client,
        )

        records = await poller.poll_cycle(limit=10)

        # CA-003-02 & CA-003-04
        assert len(records) == 1
        assert records[0].fiscal_year == 2026
        assert records[0].budgeted_amount == 150000000.0
        assert records[0].executed_amount == 82000000.0
        assert records[0].source == "mef-datastore"
        assert records[0].raw_payload["pliego_nombre"] == "MUNICIPALIDAD PROVINCIAL DE CAJAMARCA"

        # Verificar avance de offset
        assert watermark_store.state.last_mef_offset == 1

        await poller.aclose()

    asyncio.run(_test())


# ============================================================================
# 6. HarvesterDaemon Tests
# ============================================================================


def test_harvester_daemon_run_once_persists_records(tmp_harvest_dir: Path):
    import asyncio

    async def _test():
        cfg = HarvestConfig(
            storage={
                "watermark_file_path": tmp_harvest_dir / "state" / "watermarks.json",
                "coverage_gap_log_path": tmp_harvest_dir / "state" / "coverage_gaps.jsonl",
                "records_storage_dir": tmp_harvest_dir / "data" / "harvested",
            }
        )

        daemon = HarvesterDaemon(config=cfg)

        # Simular pollers mockeados que devuelven resultados
        mock_oece_json = {
            "releases": [
                {
                    "ocid": "ocds-dgv273-2026-TEST-99",
                    "tender": {"title": "Obra Provincial", "value": {"amount": 50000.0}},
                    "parties": [
                        {
                            "id": "PE-CONSUCODE-200701",
                            "identifier": {"id": "20143623042"},
                            "address": {"department": "CAJAMARCA"},
                            "roles": ["buyer"],
                        }
                    ],
                }
            ]
        }
        daemon.seace_poller._http_client = httpx.AsyncClient(
            transport=httpx.MockTransport(lambda req: httpx.Response(200, json=mock_oece_json))
        )

        mock_mef_json = {
            "success": True,
            "result": {
                "records": [
                    {
                        "ano_eje": 2026,
                        "ruc": "20143623042",
                        "monto_pim": 100000.0,
                        "monto_devengado": 45000.0,
                    }
                ]
            },
        }
        daemon.mef_poller._http_client = httpx.AsyncClient(
            transport=httpx.MockTransport(lambda req: httpx.Response(200, json=mock_mef_json))
        )

        procurements, executions = await daemon.run_once()

        assert len(procurements) == 1
        assert len(executions) == 1

        # Verificar persistencia en fichero JSONL en disco
        today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        seace_file = tmp_harvest_dir / "data" / "harvested" / f"procurements_{today_str}.jsonl"
        mef_file = tmp_harvest_dir / "data" / "harvested" / f"budget_executions_{today_str}.jsonl"

        assert seace_file.exists()
        assert mef_file.exists()

        with open(seace_file, "r", encoding="utf-8") as f:
            line = json.loads(f.readline())
            assert line["ocid"] == "ocds-dgv273-2026-TEST-99"

        await daemon.aclose()

    asyncio.run(_test())
