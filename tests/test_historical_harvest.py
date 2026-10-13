"""Pruebas unitarias para el mecanismo de extraccion de datos historicos y recientes (Pilar 1)."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
import io
import json
from pathlib import Path
from unittest.mock import AsyncMock, patch
import zipfile

import httpx
import pytest

from cajamarca_qhaway.capabilities.entity_mapping.dataset import load_universe
from cajamarca_qhaway.capabilities.live_harvest.config import HarvestConfig, MefHarvestConfig, SeaceHarvestConfig
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


def test_seace_poller_historical_batch_zip(tmp_harvest_env):
    """Verifica que SeacePoller descomprima y extraiga procesos reales de lotes mensuales."""
    async def _run():
        w_store, c_logger, by_ruc, by_consucode, _, _ = tmp_harvest_env

        ocds_record_data = {
            "records": [
                {
                    "compiledRelease": {
                        "ocid": "ocds-dgv273-seacev3-historical-2024-001",
                        "id": "rel-2024-001",
                        "parties": [
                            {
                                "id": "party-gore",
                                "name": "GOBIERNO REGIONAL DE CAJAMARCA - SEDE CENTRAL",
                                "roles": ["buyer", "procuringEntity"],
                                "identifier": {"id": "20453744168"},
                                "address": {"department": "CAJAMARCA"},
                            }
                        ],
                        "tender": {
                            "title": "Adquisicion historica de maquinaria pesada 2024",
                            "procurementMethod": "open",
                            "numberOfTenderers": 3,
                            "value": {"amount": 1500000.0},
                        },
                        "awards": [{"value": {"amount": 1490000.0}}],
                    }
                }
            ]
        }
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as z:
            z.writestr("2024-06_seace_v3.json", json.dumps(ocds_record_data))
        zip_bytes = zip_buffer.getvalue()

        cfg = SeaceHarvestConfig()
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_resp = httpx.Response(status_code=200, content=zip_bytes)
        mock_client.get.return_value = mock_resp

        poller = SeacePoller(
            config=cfg,
            watermark_store=w_store,
            coverage_logger=c_logger,
            entities_by_ruc=by_ruc,
            entities_by_consucode=by_consucode,
            http_client=mock_client,
        )

        records = await poller.harvest_monthly_batch(year=2024, month=6)
        assert len(records) == 1
        rec = records[0]
        assert rec.ocid == "ocds-dgv273-seacev3-historical-2024-001"
        assert rec.entity_id == by_ruc["20453744168"].entity_id
        assert rec.awarded_amount == 1490000.0
        assert w_store.is_seace_ocid_seen("ocds-dgv273-seacev3-historical-2024-001")

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

        cfg = MefHarvestConfig()
        mock_client = AsyncMock(spec=httpx.AsyncClient)

        async def _mock_get(url, **kwargs):
            if "datastore_search" in str(url):
                return httpx.Response(status_code=500, content=b"Server Error")
            return httpx.Response(status_code=200, content=csv_data.encode("utf-8-sig"))

        mock_client.get.side_effect = _mock_get

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
        ent_ids = {r.entity_id for r in records}
        assert by_ruc["20453744168"].entity_id in ent_ids
        assert by_ruc["20201987297"].entity_id in ent_ids

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

        now = datetime.now(timezone.utc)
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


def test_cli_harvest_run_historical(monkeypatch):
    """Verifica que el comando CLI acepte las flags --historical y --years."""
    with patch("cajamarca_qhaway.capabilities.live_harvest.daemon.HarvesterDaemon.harvest_historical_and_recent") as mock_harvest:
        mock_harvest.return_value = ([], [])
        monkeypatch.setattr(
            "sys.argv",
            ["cajamarca-qhaway", "harvest", "run", "--historical", "--years", "2024,2025,2026", "--pages", "2"],
        )
        code = cli_main()
        assert code == 0
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
