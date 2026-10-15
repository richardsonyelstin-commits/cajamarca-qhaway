from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from urllib.parse import parse_qs

import httpx
import pytest

from cajamarca_qhaway.capabilities.live_harvest.mef_consulta_amigable import (
    MefConsultaAmigableClient,
)
from cajamarca_qhaway.models import BudgetExecutionRecord
from cajamarca_qhaway.models.budget_breakdown import BudgetBreakdownContract
from cajamarca_qhaway.models.budget_reconciliation import (
    canonical_budget_records,
    validate_budget_breakdown,
)


def moments(pim: float, spent: float) -> dict[str, float]:
    return {
        "pia_amount": pim, "budgeted_amount": pim, "certified_amount": pim,
        "committed_annual_amount": pim, "monthly_commitment_amount": spent,
        "executed_amount": spent, "paid_amount": spent, "modification_amount": 0,
        "execution_pct": round(spent / pim * 100, 1) if pim else 0,
    }


def scope(name: str, pim: float, spent: float) -> dict:
    return {
        "scope": name, "moments": moments(pim, spent),
        "official_cut_date": "2026-10-13",
        "source_url": "https://apps5.mineco.gob.pe/transparencia/Navegador/Navegar_6.aspx?y=2026&ap=" + name,
        "raw_payload": {"PIM": str(pim), "DEVENGADO": str(spent)},
        "breakdown_by_funding_source": [],
    }


def contract() -> dict:
    return {
        "is_canonical_total": True, "cut_type": "daily",
        "total": scope("ActProy", 100, 50),
        "breakdown_by_scope": {
            "Proyecto": scope("Proyecto", 40, 20),
            "Actividad": scope("Actividad", 60, 30),
        }, "comparison_cuts": [],
    }


def test_scope_orthogonality_rejects_mismatch() -> None:
    data = contract()
    validate_budget_breakdown(BudgetBreakdownContract.model_validate(data))
    data["breakdown_by_scope"]["Proyecto"]["moments"] = moments(41, 20)
    data["breakdown_by_scope"]["Actividad"]["moments"] = moments(61, 30)
    with pytest.raises(ValueError, match="ortogonalidad"):
        validate_budget_breakdown(BudgetBreakdownContract.model_validate(data))


def test_moments_and_funding_reconcile() -> None:
    data = contract()
    data["total"]["breakdown_by_funding_source"] = [{
        "code": "1", "label": "RECURSOS ORDINARIOS", "moments": moments(90, 50),
        "rubros": [], "raw_payload": {"PIM": "90"},
    }]
    with pytest.raises(ValueError, match="fuentes"):
        validate_budget_breakdown(BudgetBreakdownContract.model_validate(data))
    data = contract()
    data["total"]["moments"]["modification_amount"] = 1
    with pytest.raises(ValueError, match="modificaciones"):
        validate_budget_breakdown(BudgetBreakdownContract.model_validate(data))
    data = contract()
    data["total"]["moments"]["paid_amount"] = 51
    with pytest.raises(ValueError, match="orden"):
        validate_budget_breakdown(BudgetBreakdownContract.model_validate(data))


def test_canonical_selection_rejects_duplicate_total() -> None:
    base = BudgetExecutionRecord(
        execution_record_id="me-one", entity_id="ce-one", fiscal_year=2026,
        budgeted_amount=100, executed_amount=50, budget_category="TOTAL",
        retrieved_at=datetime.now(UTC),
    )
    child = base.model_copy(update={"execution_record_id": "me-child", "budget_category": "Proyecto"})
    assert canonical_budget_records([base, child]) == [base]
    with pytest.raises(ValueError, match="duplicado"):
        canonical_budget_records([base, base.model_copy(update={"execution_record_id": "me-two"})])


def test_geographic_department_is_never_posted() -> None:
    html = '''<form id="aspnetForm">
      <input type="submit" name="ctl00$CPH1$BtnDepartamentoMeta" value="Departamento">
      <input type="submit" name="ctl00$CPH1$BtnDepartamento" value="Departamento">
      <table class="Data"><tr id="tr0"><td>
      <input type="radio" name="grp1" value="M/0"></td>
      <td>M: MUNICIPALIDADES</td></tr></table></form>'''

    def handler(request: httpx.Request) -> httpx.Response:
        body = parse_qs(request.content.decode())
        assert "ctl00$CPH1$BtnDepartamentoMeta" not in body
        assert body["ctl00$CPH1$BtnDepartamento"] == ["Departamento"]
        return httpx.Response(200, text=html)

    async def scenario() -> None:
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http, MefConsultaAmigableClient(http) as client:
            await client._postback(html, "https://official.test", "M:", "Departamento")

    asyncio.run(scenario())


def test_printed_rounding_never_relaxes_pim_partition() -> None:
    from cajamarca_qhaway.models.budget_breakdown import Moments
    from cajamarca_qhaway.models.budget_reconciliation import _assert_partition

    parent = Moments.model_validate(moments(100, 50))
    children = [Moments.model_validate(moments(20, 10)) for _ in range(5)]
    parent = parent.model_copy(update={"monthly_commitment_amount": 48})
    _assert_partition(parent, children, "fuentes")
    parent = parent.model_copy(update={"budgeted_amount": 102})
    with pytest.raises(ValueError, match="budgeted_amount"):
        _assert_partition(parent, children, "fuentes")


def test_canonical_budget_repository_preserves_all_nested_moments() -> None:
    import json
    from pathlib import Path

    from cajamarca_qhaway.persistence.connection import DatabaseManager
    from cajamarca_qhaway.persistence.repositories.budget_execution_repository import (
        BudgetExecutionRepository,
    )

    snapshot = json.loads(Path("web/src/data/verified-snapshot.json").read_text(encoding="utf-8"))
    record = BudgetExecutionRecord.model_validate(snapshot["budget_execution_records"][0])
    assert record.is_canonical_total
    repository = BudgetExecutionRepository(DatabaseManager())
    repository.upsert_many([record])
    assert repository.get_by_id(record.execution_record_id) == record
    repository.upsert_many([record])
    assert repository.count() == 1
