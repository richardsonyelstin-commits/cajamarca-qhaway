"""Pruebas unitarias para el mecanismo de extraccion de datos historicos y recientes (Pilar 1)."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from cajamarca_qhaway.capabilities.entity_mapping.dataset import load_universe
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
from cajamarca_qhaway.cli import main as cli_main
from cajamarca_qhaway.models import BudgetExecutionRecord, ProcurementRecord
from cajamarca_qhaway.web.exporter import build_verified_web_snapshot


@pytest.fixture
def tmp_harvest_env(tmp_path: Path):
    state_dir = tmp_path / "state"
    state_dir.mkdir(parents=True, exist_ok=True)
    harvested_dir = tmp_path / "harvested"
    harvested_dir.mkdir(parents=True, exist_ok=True)

    w_store = WatermarkStore(state_dir / "watermarks.json")
    c_logger = CoverageGapLogger(state_dir / "coverage_gaps.jsonl")

    universe = load_universe()
    by_ruc = {r.entity.ruc: r.entity for r in universe.entities}
    by_consucode = {r.entity.consucode_id: r.entity for r in universe.entities if r.entity.consucode_id}
    by_id = {r.entity.entity_id: r.entity for r in universe.entities}

    return w_store, c_logger, by_ruc, by_consucode, by_id, harvested_dir


def test_seace_poller_rejects_unverified_historical_endpoint(tmp_harvest_env):
    """Un lote mensual no documentado no debe producir registros ni cursor."""
    async def _run():
        w_store, c_logger, by_ruc, by_consucode, _, _ = tmp_harvest_env

        cfg = SeaceHarvestConfig()
        mock_client = AsyncMock(spec=httpx.AsyncClient)

        poller = SeacePoller(
            config=cfg,
            watermark_store=w_store,
            coverage_logger=c_logger,
            entities_by_ruc=by_ruc,
            entities_by_consucode=by_consucode,
            http_client=mock_client,
        )

        records = await poller.harvest_monthly_batch(year=2024, month=6)
        assert records == []
        assert not w_store.state.seen_seace_ocids
        windows = c_logger.read_records(record_type="coverage_window")
        assert windows[-1]["status"] == "FAILED"

    asyncio.run(_run())


def test_mef_poller_historical_csv_datasets(tmp_harvest_env):
    """Verifica que MefPoller extraiga registros historicos desde datasets oficiales del MEF."""
    async def _run():
        w_store, c_logger, by_ruc, _, by_id, _ = tmp_harvest_env

        csv_data = (
            "ANO_EJE,PLIEGO_NOMBRE,SEC_EJEC,EJECUTORA_NOMBRE,DEPARTAMENTO_EJECUTORA,DEPARTAMENTO_EJECUTORA_NOMBRE,PROVINCIA_EJECUTORA_NOMBRE,GENERICA_NOMBRE,MONTO_PIA,MONTO_PIM,MONTO_DEVENGADO\n"
            '2024,"GOBIERNO REGIONAL DEL DEPARTAMENTO DE CAJAMARCA","785","REGION CAJAMARCA-SEDE","06","CAJAMARCA","CAJAMARCA","BIENES Y SERVICIOS",100000,120000,95000\n'
            '2025,"MUNICIPALIDAD PROVINCIAL DE JAEN","300","MP JAEN","06","CAJAMARCA","JAEN","ADQUISICION DE ACTIVOS NO FINANCIEROS",500000,550000,480000\n'
            '2024,"MUNICIPALIDAD DE LIMA","100","MML","15","LIMA","LIMA","BIENES Y SERVICIOS",999,999,999\n'
        )

        cfg = MefHarvestConfig(
            annual_dataset_urls={
                "2024": ["https://fs.datosabiertos.mef.gob.pe/datastorefiles/2024.csv"],
                "2025": ["https://fs.datosabiertos.mef.gob.pe/datastorefiles/2025.csv"],
            },
            max_retries=1,
            enable_open_data_fallback=True,
        )
        def mock_request(request: httpx.Request) -> httpx.Response:
            if "datastore_search" in request.url.path:
                return httpx.Response(status_code=500, content=b"Server Error")
            return httpx.Response(
                status_code=200,
                content=csv_data.encode("utf-8-sig"),
                headers={"content-type": "text/csv; charset=utf-8"},
            )

        mock_client = httpx.AsyncClient(transport=httpx.MockTransport(mock_request))

        poller = MefPoller(
            config=cfg,
            watermark_store=w_store,
            coverage_logger=c_logger,
            entities_by_ruc=by_ruc,
            entities_by_id=by_id,
            http_client=mock_client,
        )

        records = await poller.harvest_historical_and_recent(years=[2024, 2025])
        assert len(records) >= 2
        assert poller.last_historical_status == "OK"
        ent_ids = {r.entity_id for r in records}
        assert by_ruc["20453744168"].entity_id in ent_ids
        assert by_ruc["20201987297"].entity_id in ent_ids
        await poller.aclose()

    asyncio.run(_run())


def test_mef_targeted_queries_use_only_verified_siaf_codes_and_log_gaps(tmp_harvest_env):
    """Las consultas puntuales usan el GORE y el SEC_EJEC provincial canónico."""
    async def _run():
        w_store, c_logger, by_ruc, _, by_id, _ = tmp_harvest_env
        requested_codes = []

        def mock_request(request: httpx.Request) -> httpx.Response:
            requested_codes.append(request.url.params.get("q"))
            return httpx.Response(200, json={"sucess": "true", "records": None})

        client = httpx.AsyncClient(transport=httpx.MockTransport(mock_request))
        poller = MefPoller(
            config=MefHarvestConfig(targeted_query_timeout_seconds=1),
            watermark_store=w_store,
            coverage_logger=c_logger,
            entities_by_ruc=by_ruc,
            entities_by_id=by_id,
            http_client=client,
        )
        poller._discovered_resource_ids[2024] = "official-2024-resource"

        assert await poller._collect_targeted_datastore_records([2024]) == []
        assert len(requested_codes) == 14
        assert set(requested_codes) == {
            "445", "300549", "300562", "300566", "300578", "300597", "300605",
            "300620", "300623", "300635", "300642", "300649", "300662", "300666",
        }
        assert "300601" not in requested_codes
        assert "300605" in requested_codes  # SEC_EJEC provincial válido de Cutervo.
        gaps = [
            item for item in c_logger.read_records(record_type="coverage_gap_incident")
            if "consulta puntual" in item.get("error_message", "")
        ]
        assert len(gaps) == 14
        await poller.aclose()

    asyncio.run(_run())


def test_mef_pnda_catalog_discovers_current_resources_by_fiscal_year(tmp_harvest_env):
    """El catálogo PNDA es la fuente primaria de IDs y enlaces de los CSV MEF."""
    async def _run():
        w_store, c_logger, by_ruc, _, by_id, _ = tmp_harvest_env
        page = b'''<ul>
          <li><div><a class="heading" title="2024-Gasto.csv" href="/dataset/mef/resource/11111111-1111-4111-8111-111111111111">2024-Gasto.csv</a>
          <a class="data-link" href="https://fs.datosabiertos.mef.gob.pe/datastorefiles/2024-Gasto.csv">Descargar</a></div></li>
          <li><div><a class="heading" title="2025-Gasto-Mensual.csv" href="/dataset/mef/resource/22222222-2222-4222-8222-222222222222">2025-Gasto-Mensual.csv</a>
          <a class="data-link" href="https://fs.datosabiertos.mef.gob.pe/datastorefiles/2025-Gasto-Mensual.csv">Descargar</a></div></li>
          <li><div><a class="heading" title="2025-Gasto-Diario.csv" href="/dataset/mef/resource/33333333-3333-4333-8333-333333333333">2025-Gasto-Diario.csv</a>
          <a class="data-link" href="https://fs.datosabiertos.mef.gob.pe/datastorefiles/2025-Gasto-Diario.csv">Descargar</a></div></li>
          <li><div><a class="heading" title="2026-Gasto-Diario.csv" href="/dataset/mef/resource/44444444-4444-4444-8444-444444444444">2026-Gasto-Diario.csv</a>
          <a class="data-link" href="https://fs.datosabiertos.mef.gob.pe/datastorefiles/2026-Gasto-Diario.csv">Descargar</a></div></li>
        </ul>'''
        client = httpx.AsyncClient(
            transport=httpx.MockTransport(
                lambda request: httpx.Response(200, content=page, headers={"content-type": "text/html"})
            )
        )
        poller = MefPoller(
            config=MefHarvestConfig(),
            watermark_store=w_store,
            coverage_logger=c_logger,
            entities_by_ruc=by_ruc,
            entities_by_id=by_id,
            http_client=client,
        )
        discovered = await poller._discover_official_csv_urls([2024, 2025, 2026])
        assert discovered == {
            2024: "https://fs.datosabiertos.mef.gob.pe/datastorefiles/2024-Gasto.csv",
            2025: "https://fs.datosabiertos.mef.gob.pe/datastorefiles/2025-Gasto-Diario.csv",
            2026: "https://fs.datosabiertos.mef.gob.pe/datastorefiles/2026-Gasto-Diario.csv",
        }
        assert poller._pnda_resource_ids == {
            2024: "11111111-1111-4111-8111-111111111111",
            2025: "33333333-3333-4333-8333-333333333333",
            2026: "44444444-4444-4444-8444-444444444444",
        }
        await poller.aclose()

    asyncio.run(_run())


def test_daemon_harvest_historical_and_recent(tmp_harvest_env):
    """Verifica que el orquestador persista durablemente registros de backfill historico."""
    async def _run():
        w_store, c_logger, _, _, _, harvested_dir = tmp_harvest_env

        cfg = HarvestConfig(
            storage=HarvestConfig().storage.model_copy(update={"records_storage_dir": harvested_dir})
        )
        daemon = HarvesterDaemon(
            config=cfg,
            watermark_store=w_store,
            coverage_logger=c_logger,
        )

        now = datetime.now(UTC)
        mock_proc = [
            ProcurementRecord(
                procurement_id="proc-test-2024",
                ocid="ocds-test-2024",
                entity_id="ce-f5f5d8fc32518855",
                title="Proceso de prueba 2024",
                raw_payload={"ocid": "ocds-test-2024"},
                source="seace-ocds",
                retrieved_at=now,
            )
        ]
        mock_exec = [
            BudgetExecutionRecord(
                execution_record_id="exec-test-2024",
                entity_id="ce-f5f5d8fc32518855",
                fiscal_year=2024,
                budgeted_amount=50000.0,
                executed_amount=40000.0,
                raw_payload={"fiscal_year": 2024},
                source="mef-datastore",
                retrieved_at=now,
            )
        ]

        daemon.seace_poller.harvest_historical_and_recent = AsyncMock(return_value=mock_proc)
        daemon.mef_poller.harvest_historical_and_recent = AsyncMock(return_value=mock_exec)

        p_res, e_res = await daemon.harvest_historical_and_recent(years=[2024, 2025, 2026])
        assert len(p_res) == 1
        assert len(e_res) == 1

        created_files = list(harvested_dir.glob("*.jsonl"))
        assert len(created_files) == 2

    asyncio.run(_run())


def test_cli_harvest_run_historical_reports_incomplete_coverage(monkeypatch):
    """Una respuesta vacia no debe reportar exito para una solicitud historica."""
    with patch("cajamarca_qhaway.capabilities.live_harvest.daemon.HarvesterDaemon.harvest_historical_and_recent") as mock_harvest:
        mock_harvest.return_value = ([], [])
        monkeypatch.setattr(
            "sys.argv",
            ["cajamarca-qhaway", "harvest", "run", "--historical", "--years", "2024,2025,2026", "--pages", "2"],
        )
        code = cli_main()
        assert code == 1
        mock_harvest.assert_called_once()
        kwargs = mock_harvest.call_args.kwargs
        assert kwargs["years"] == [2024, 2025, 2026]
        assert kwargs["page_limit"] == 2


def test_snapshot_integration_with_harvested_files(tmp_path):
    """Verifica que build_verified_web_snapshot cargue e integre registros reales cosechados."""
    snapshot = build_verified_web_snapshot()
    assert "metadata" in snapshot
    assert "contracting_entities" in snapshot
    assert "procurement_records" in snapshot
    assert "budget_execution_records" in snapshot
    assert len(snapshot["contracting_entities"]) == 14
