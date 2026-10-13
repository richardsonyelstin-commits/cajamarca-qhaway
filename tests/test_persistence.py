"""Pruebas exhaustivas para la capa de persistencia y sincronizacion con Supabase/SQLite (Pilar 2).

Valida:
- TK-201 / Aplicacion de esquemas DDL relacionales y restricciones constitucionales
- TK-202 / Arquitectura de repositorios y patrones de acceso
- TK-203 / Implementacion de repositorios para los 6 modelos canonicos y siembra del universo
- TK-204 / Pruebas deterministas de persistencia, integridad referencial y fallback de spool local
- TK-205 / CLI db (status, seed, sync) e integracion con HarvesterDaemon
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from pydantic import SecretStr

from cajamarca_qhaway.capabilities.entity_mapping.dataset import load_universe
from cajamarca_qhaway.capabilities.live_harvest import CoverageGapLogger, HarvesterDaemon, WatermarkStore
from cajamarca_qhaway.capabilities.live_harvest.config import (
    HarvestConfig,
    MefHarvestConfig,
    SeaceHarvestConfig,
    StorageConfig,
)
from cajamarca_qhaway.cli import main as cli_main
from cajamarca_qhaway.models import (
    Alert,
    BudgetExecutionRecord,
    CitizenReport,
    ContractingEntity,
    ProcurementRecord,
    RedFlag,
)
from cajamarca_qhaway.persistence.config import DatabaseConfig
from cajamarca_qhaway.persistence.connection import DatabaseManager
from cajamarca_qhaway.persistence.repositories import (
    AlertRepository,
    BudgetExecutionRepository,
    CitizenReportRepository,
    EntityRepository,
    ProcurementRepository,
    RedFlagRepository,
)
from cajamarca_qhaway.persistence.spool import LocalSpooler
from cajamarca_qhaway.persistence.sync import SyncManager


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def tmp_spool_dir(tmp_path: Path) -> Path:
    spool_dir = tmp_path / "spool"
    spool_dir.mkdir(parents=True, exist_ok=True)
    return spool_dir


@pytest.fixture
def test_db_config(tmp_spool_dir: Path) -> DatabaseConfig:
    return DatabaseConfig(
        database_url=None,  # SQLite en memoria
        spool_dir=tmp_spool_dir,
        spool_enabled=True,
    )


@pytest.fixture
def db_manager(test_db_config: DatabaseConfig) -> DatabaseManager:
    return DatabaseManager(test_db_config)


@pytest.fixture
def sync_manager(test_db_config: DatabaseConfig) -> SyncManager:
    return SyncManager(test_db_config)


@pytest.fixture
def sample_entity() -> ContractingEntity:
    return ContractingEntity(
        entity_id="test-entity-chota",
        official_name="MUNICIPALIDAD PROVINCIAL DE CHOTA",
        entity_level="provincial_municipality",
        province="CHOTA",
        ruc="20167389201",
        consucode_id="060401",
        department="CAJAMARCA",
        verified_at=datetime.now(timezone.utc),
        active=True,
    )


@pytest.fixture
def sample_procurement(sample_entity: ContractingEntity) -> ProcurementRecord:
    return ProcurementRecord(
        procurement_id="pr-chota-001",
        ocid="ocds-dgv273-0012345",
        entity_id=sample_entity.entity_id,
        title="ADQUISICION DE MATERIALES PARA PUENTE CHOTA",
        procurement_method="direct",
        awarded_amount=150000.50,
        executed_amount=150000.50,
        number_of_bidders=1,
        supplier_name="CONSTRUCTORA NORTE SAC",
        supplier_ruc="20456789123",
        source="seace-ocds",
        raw_payload={"ocid": "ocds-dgv273-0012345", "tag": ["tender"]},
        retrieved_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def sample_budget(sample_entity: ContractingEntity) -> BudgetExecutionRecord:
    return BudgetExecutionRecord(
        execution_record_id="me-chota-2026",
        entity_id=sample_entity.entity_id,
        fiscal_year=2026,
        budgeted_amount=12500000.0,
        executed_amount=4500000.0,
        budget_category="Gasto de Capital",
        source="mef-datastore",
        raw_payload={"ANO_EJE": 2026, "MONTO_PIA": 12500000.0},
        retrieved_at=datetime.now(timezone.utc),
    )


# ============================================================================
# Tests: DatabaseConfig & DatabaseManager (TK-201, TK-202)
# ============================================================================


def test_database_config_defaults(tmp_path: Path) -> None:
    cfg = DatabaseConfig(spool_dir=tmp_path / "spool")
    assert cfg.database_url is None
    assert cfg.spool_enabled is True
    assert cfg.max_pool_size == 10
    assert cfg.min_pool_size == 1


def test_database_manager_sqlite_initialization(db_manager: DatabaseManager) -> None:
    assert not db_manager.is_postgres
    with db_manager.connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cursor.fetchall()}

    expected_tables = {
        "contracting_entities",
        "procurement_records",
        "budget_execution_records",
        "red_flags",
        "alerts",
        "citizen_reports",
    }
    assert expected_tables.issubset(tables)


def test_database_manager_postgres_flag() -> None:
    cfg = DatabaseConfig(database_url=SecretStr("postgresql://user:pass@host:5432/db"))
    mgr = DatabaseManager(cfg)
    assert mgr.is_postgres


# ============================================================================
# Tests: LocalSpooler (TK-202, TK-203)
# ============================================================================


def test_local_spooler_operations(
    tmp_spool_dir: Path, sample_procurement: ProcurementRecord, sample_budget: BudgetExecutionRecord
) -> None:
    spooler = LocalSpooler(tmp_spool_dir)

    # Inicialmente vacio
    assert len(spooler.list_pending_files()) == 0

    # Spool de compras
    file_p = spooler.spool_procurements([sample_procurement])
    assert file_p.exists()
    assert "procurements_" in file_p.name

    # Spool de ejecuciones presupuestales
    file_b = spooler.spool_budget_executions([sample_budget])
    assert file_b.exists()
    assert "budget_executions_" in file_b.name

    pending = spooler.list_pending_files()
    assert len(pending) == 2

    # Lectura y remocion atomica
    items_p = spooler.read_and_remove(file_p)
    assert len(items_p) == 1
    assert items_p[0]["procurement_id"] == sample_procurement.procurement_id
    assert not file_p.exists()

    assert len(spooler.list_pending_files()) == 1


# ============================================================================
# Tests: Repositories (TK-203, TK-204)
# ============================================================================


def test_entity_repository(db_manager: DatabaseManager, sample_entity: ContractingEntity) -> None:
    repo = EntityRepository(db_manager)

    # Insercion
    repo.upsert(sample_entity)
    found = repo.get_by_id(sample_entity.entity_id)
    assert found is not None
    assert found.entity_id == sample_entity.entity_id
    assert found.official_name == sample_entity.official_name
    assert found.ruc == sample_entity.ruc

    # Idempotencia de upsert
    repo.upsert(sample_entity)
    assert repo.get_by_id(sample_entity.entity_id) is not None

    # Consulta por RUC
    found_ruc = repo.get_by_ruc(sample_entity.ruc)
    assert found_ruc is not None
    assert found_ruc.entity_id == sample_entity.entity_id

    # Listado de entidades activas
    active = repo.list_active()
    assert len(active) == 1


def test_procurement_repository(
    db_manager: DatabaseManager, sample_entity: ContractingEntity, sample_procurement: ProcurementRecord
) -> None:
    entity_repo = EntityRepository(db_manager)
    entity_repo.upsert(sample_entity)

    proc_repo = ProcurementRepository(db_manager)
    assert proc_repo.count() == 0

    # Insercion y upsert idempotente
    count = proc_repo.upsert_many([sample_procurement])
    assert count == 1
    assert proc_repo.count() == 1

    # Re-insercion no duplica
    proc_repo.upsert_many([sample_procurement])
    assert proc_repo.count() == 1

    # Recuperacion
    rec = proc_repo.get_by_id(sample_procurement.procurement_id)
    assert rec is not None
    assert rec.ocid == sample_procurement.ocid
    assert rec.awarded_amount == sample_procurement.awarded_amount
    # Preservacion estricta de raw_payload (Art. 10)
    assert rec.raw_payload == sample_procurement.raw_payload

    # Filtro por entidad
    by_entity = proc_repo.list_by_entity(sample_entity.entity_id)
    assert len(by_entity) == 1


def test_budget_execution_repository(
    db_manager: DatabaseManager, sample_entity: ContractingEntity, sample_budget: BudgetExecutionRecord
) -> None:
    entity_repo = EntityRepository(db_manager)
    entity_repo.upsert(sample_entity)

    budget_repo = BudgetExecutionRepository(db_manager)
    assert budget_repo.count() == 0

    # Insercion
    count = budget_repo.upsert_many([sample_budget])
    assert count == 1
    assert budget_repo.count() == 1

    # Recuperacion
    rec = budget_repo.get_by_id(sample_budget.execution_record_id)
    assert rec is not None
    assert rec.fiscal_year == 2026
    assert rec.budgeted_amount == sample_budget.budgeted_amount
    assert rec.raw_payload == sample_budget.raw_payload

    # Filtro por entidad y anho
    by_entity = budget_repo.list_by_entity_year(sample_entity.entity_id, fiscal_year=2026)
    assert len(by_entity) == 1


def test_red_flag_repository(
    db_manager: DatabaseManager, sample_entity: ContractingEntity, sample_procurement: ProcurementRecord
) -> None:
    entity_repo = EntityRepository(db_manager)
    entity_repo.upsert(sample_entity)
    proc_repo = ProcurementRepository(db_manager)
    proc_repo.upsert_many([sample_procurement])

    flag_repo = RedFlagRepository(db_manager)
    flag = RedFlag(
        red_flag_id="flag-single-bidder-001",
        indicator_code="single-bidder",
        formula_description="Contratacion directa o competitiva con postor unico",
        threshold="<= 1 postor",
        observed_value="1 postor",
        procurement_ids=[sample_procurement.procurement_id],
        execution_record_ids=[],
        evidence_source="seace-ocds",
        evidence_retrieved_at=datetime.now(timezone.utc),
        generated_at=datetime.now(timezone.utc),
    )

    count = flag_repo.insert_candidates([flag])
    assert count == 1

    retrieved = flag_repo.get_by_id(flag.red_flag_id)
    assert retrieved is not None
    assert retrieved.indicator_code == "single-bidder"
    assert retrieved.procurement_ids == [sample_procurement.procurement_id]


def test_alert_repository(
    db_manager: DatabaseManager, sample_entity: ContractingEntity
) -> None:
    entity_repo = EntityRepository(db_manager)
    entity_repo.upsert(sample_entity)

    alert_repo = AlertRepository(db_manager)
    alert = Alert(
        alert_id="alert-pub-001",
        red_flag_ids=["flag-single-bidder-001"],
        entity_id=sample_entity.entity_id,
        status="published",
        reviewed_by="auditor_cajamarca",
        reviewed_at=datetime.now(timezone.utc),
        review_notes="Verificado conforme a ley",
        disclaimer="Indicador de riesgo automatizado, no constituye prueba ni acusación formal de corrupción.",
        published_at=datetime.now(timezone.utc),
    )

    alert_repo.save(alert)

    retrieved = alert_repo.get_by_id(alert.alert_id)
    assert retrieved is not None
    assert retrieved.status == "published"
    assert retrieved.reviewed_by == "auditor_cajamarca"

    published_list = alert_repo.list_published()
    assert len(published_list) == 1


def test_citizen_report_repository(
    db_manager: DatabaseManager, sample_entity: ContractingEntity
) -> None:
    entity_repo = EntityRepository(db_manager)
    entity_repo.upsert(sample_entity)

    report_repo = CitizenReportRepository(db_manager)
    report = CitizenReport(
        report_id="rep-wh-001",
        submitted_at=datetime.now(timezone.utc),
        channel="whatsapp",
        raw_text="Sobrevaloracion de combustible en Chota",
        related_entity_id=sample_entity.entity_id,
        moderation_status="pending",
        legal_disclaimer_shown=True,
    )

    report_repo.save(report)

    retrieved = report_repo.get_by_id(report.report_id)
    assert retrieved is not None
    assert retrieved.raw_text == "Sobrevaloracion de combustible en Chota"
    assert retrieved.legal_disclaimer_shown is True


# ============================================================================
# Tests: SyncManager & Fallback Spooling (TK-203, TK-205)
# ============================================================================


def test_sync_manager_seed_entities(sync_manager: SyncManager) -> None:
    count = sync_manager.seed_universe_entities()
    assert count == 14

    status = sync_manager.status()
    assert status["active_entities"] == 14


def test_sync_manager_spool_fallback_and_flush(
    sync_manager: SyncManager, sample_procurement: ProcurementRecord, sample_budget: BudgetExecutionRecord
) -> None:
    # Simular fallo en BD inyectando un error
    with patch.object(sync_manager.procurements, "upsert_many", side_effect=RuntimeError("DB Offline")):
        count, spooled = sync_manager.sync_procurements([sample_procurement])
        assert count == 1
        assert spooled is True

    with patch.object(sync_manager.budget_executions, "upsert_many", side_effect=RuntimeError("DB Offline")):
        count, spooled = sync_manager.sync_budget_executions([sample_budget])
        assert count == 1
        assert spooled is True

    # Validar que los archivos estan en spool pendiente
    status_mid = sync_manager.status()
    assert status_mid["pending_spool_files"] == 2

    # Siembra entidad previa para respetar FK al hacer flush
    sync_manager.seed_universe_entities()

    # Ejecutar flush hacia la BD restaurada
    flush_res = sync_manager.flush_spool()
    assert flush_res["flushed_procurements"] == 1
    assert flush_res["flushed_executions"] == 1
    assert flush_res["remaining_spool_files"] == 0

    status_final = sync_manager.status()
    assert status_final["pending_spool_files"] == 0
    assert status_final["total_procurements"] == 1
    assert status_final["total_budget_executions"] == 1


# ============================================================================
# Tests: HarvesterDaemon + SyncManager Integration (TK-205)
# ============================================================================


def test_harvester_daemon_with_sync_manager(
    tmp_path: Path, sync_manager: SyncManager
) -> None:
    async def _test():
        # Preparar seed
        sync_manager.seed_universe_entities()

        cfg = HarvestConfig(
            storage=StorageConfig(
                watermark_file_path=tmp_path / "data" / "state" / "watermarks.json",
                coverage_gap_log_path=tmp_path / "data" / "state" / "coverage_gaps.jsonl",
                records_storage_dir=tmp_path / "data" / "harvested",
            ),
            seace=SeaceHarvestConfig(poll_interval_seconds=10),
            mef=MefHarvestConfig(poll_interval_seconds=60),
        )

        store = WatermarkStore(tmp_path / "data" / "state" / "watermarks.json")
        logger = CoverageGapLogger(tmp_path / "data" / "state" / "coverage_gaps.jsonl")

        daemon = HarvesterDaemon(
            config=cfg,
            watermark_store=store,
            coverage_logger=logger,
            sync_manager=sync_manager,
        )

        # Simular poller responses con AsyncMock
        universe = load_universe()
        chota_entity = [e.entity for e in universe.entities if e.entity.province == "CHOTA"][0]

        sample_proc = ProcurementRecord(
            procurement_id="pr-daemon-001",
            ocid="ocds-dgv273-daemon-001",
            entity_id=chota_entity.entity_id,
            title="OBRA VIAL CHOTA",
            procurement_method="direct",
            awarded_amount=50000.0,
            executed_amount=50000.0,
            number_of_bidders=1,
            supplier_name="CONSORCIO CAJAMARCA",
            supplier_ruc="20123456789",
            source="seace-ocds",
            raw_payload={"id": "test"},
            retrieved_at=datetime.now(timezone.utc),
        )

        daemon.seace_poller.poll_cycle = AsyncMock(return_value=[sample_proc])  # type: ignore[method-assign]
        daemon.mef_poller.poll_cycle = AsyncMock(return_value=[])  # type: ignore[method-assign]

        procs, execs = await daemon.run_once(sources=["seace"])
        assert len(procs) == 1
        assert len(execs) == 0

        # Verificar que el registro llego a la base de datos a traves de SyncManager
        assert sync_manager.procurements.count() == 1
        stored = sync_manager.procurements.get_by_id(sample_proc.procurement_id)
        assert stored is not None
        assert stored.ocid == sample_proc.ocid

    asyncio.run(_test())


# ============================================================================
# Tests: CLI db Commands (TK-205)
# ============================================================================


def test_cli_db_status(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setattr("sys.argv", ["cajamarca-qhaway", "db", "status"])
    exit_code = cli_main()
    assert exit_code == 0
    captured = capsys.readouterr().out
    assert "Estado de la Base de Datos Operativa" in captured


def test_cli_db_seed(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setattr("sys.argv", ["cajamarca-qhaway", "db", "seed"])
    exit_code = cli_main()
    assert exit_code == 0
    captured = capsys.readouterr().out
    assert "Siembra completada con exito" in captured


def test_cli_db_sync(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setattr("sys.argv", ["cajamarca-qhaway", "db", "sync"])
    exit_code = cli_main()
    assert exit_code == 0
    captured = capsys.readouterr().out
    assert "Sincronizacion completada" in captured


def test_postgres_cursor_wrapper_and_adapt_sql() -> None:
    from cajamarca_qhaway.persistence.connection import (
        DatabaseManager,
        PostgresConnectionWrapper,
        PostgresCursorWrapper,
    )
    from pydantic import SecretStr

    mgr = DatabaseManager()
    assert mgr.adapt_sql("SELECT * FROM t WHERE a = ? AND b = ?") == "SELECT * FROM t WHERE a = ? AND b = ?"

    # Simular modo Postgres
    mgr._is_postgres = True
    assert mgr.adapt_sql("SELECT * FROM t WHERE a = ? AND b = ?") == "SELECT * FROM t WHERE a = %s AND b = %s"

    # Probar que PostgresCursorWrapper traduce '?' a '%s'
    class MockRawCursor:
        def __init__(self):
            self.last_query = None
            self.last_params = None

        def execute(self, query, params=None):
            self.last_query = query
            self.last_params = params
            return self

        def executemany(self, query, params_seq):
            self.last_query = query
            self.last_params = params_seq
            return self

    mock_cur = MockRawCursor()
    wrapper = PostgresCursorWrapper(mock_cur)
    wrapper.execute("INSERT INTO test (id, name) VALUES (?, ?)", ("1", "test"))
    assert mock_cur.last_query == "INSERT INTO test (id, name) VALUES (%s, %s)"
    assert mock_cur.last_params == ("1", "test")

    wrapper.executemany("UPDATE test SET x = ? WHERE id = ?", [("val", "1")])
    assert mock_cur.last_query == "UPDATE test SET x = %s WHERE id = %s"


def test_watermark_store_with_sqlite_schema(tmp_path: Path) -> None:
    from cajamarca_qhaway.capabilities.live_harvest import WatermarkStore
    from cajamarca_qhaway.persistence.connection import DatabaseManager

    mgr = DatabaseManager()
    store_file = tmp_path / "watermarks.json"
    store = WatermarkStore(store_file, db_manager=mgr)
    now = datetime.now(timezone.utc)
    store.update_seace_cursor(now, ["ocds-1", "ocds-2"])
    assert store.is_seace_ocid_seen("ocds-1")
    assert store.is_seace_ocid_seen("ocds-2")
    assert not store.is_seace_ocid_seen("ocds-3")

