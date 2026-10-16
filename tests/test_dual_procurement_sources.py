from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from io import BytesIO
from pathlib import Path
from urllib.parse import parse_qs
from zipfile import ZipFile

import httpx
import pytest

from cajamarca_qhaway.capabilities.entity_mapping.dataset import load_universe
from cajamarca_qhaway.capabilities.live_harvest.coverage_logger import CoverageGapLogger
from cajamarca_qhaway.capabilities.seace_ingestion.official_sources import (
    CAPTCHARequired,
    DownloadResource,
    OECEPentahoClient,
    SEACEBuscadorPublicoClient,
    _source_record,
    link_procurement_evidence,
)
from cajamarca_qhaway.models import ProcurementRecord
from cajamarca_qhaway.models.procurement_source_record import ProcurementSourceRecord


def workbook(ruc: str) -> bytes:
    output = BytesIO()
    rows = [
        ["ENTIDAD_RUC", "CODIGOCONVOCATORIA", "CODIGOITEM", "DESCRIPCION_PROCESO"],
        [ruc, "1255489", "1", "Ejecucion de obra CUI 1234567"],
        ["20182786935", "999", "1", "Entidad fuera del universo"],
    ]
    xml = '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>'
    for index, row in enumerate(rows, 1):
        xml += f'<row r="{index}">'
        for column, value in zip("ABCD", row, strict=True):
            xml += f'<c r="{column}{index}" t="inlineStr"><is><t>{value}</t></is></c>'
        xml += '</row>'
    xml += '</sheetData></worksheet>'
    with ZipFile(output, "w") as archive:
        archive.writestr("xl/worksheets/sheet1.xml", xml)
    return output.getvalue()


def test_pentaho_session_discovery_and_ruc_filter() -> None:
    entity = load_universe().entities[0].entity

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.host == "bi.seace.gob.pe":
            if request.url.path.endswith('/content'):
                return httpx.Response(200, text='<script src="/catalog.js"></script>',
                                      headers={"set-cookie": "JSESSIONID=public-session; Path=/"})
            assert "JSESSIONID=public-session" in request.headers["cookie"]
            return httpx.Response(200, text='''const DOMAIN = "https://conosce.osce.gob.pe";
                const BASEPATH = "/buscador/assets/official/reportes";
                const template = `/convocatorias/CONOSCE_CONVOCATORIAS${y}_0.xlsx`;''')
        return httpx.Response(200, content=workbook(entity.ruc))

    async def scenario() -> list[ProcurementSourceRecord]:
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http, OECEPentahoClient(http) as client:
            resources = await client.discover([2026], datasets=("convocatorias",))
            assert len(resources) == 1
            return [record async for record in client.records(resources[0], [entity])]

    records = asyncio.run(scenario())
    assert len(records) == 1
    assert records[0].official_process_id == "1255489"
    assert records[0].cui == "1234567"
    assert records[0].raw_payload["source_system"] == "oece_pentaho_bi"
    assert records[0].raw_payload["record"]["ENTIDAD_RUC"] == entity.ruc


def test_pentaho_follows_official_iframe_and_nested_catalog_script() -> None:
    requested: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requested.append(request.url.path)
        if request.url.path.endswith('/content'):
            return httpx.Response(200, text='<script src="/jquery.js"></script>'
                                  '<iframe src="/nested.html"></iframe>')
        if request.url.path == '/nested.html':
            return httpx.Response(200, text='<script src="/catalog-nested.js"></script>')
        if request.url.path == '/catalog-nested.js':
            return httpx.Response(200, text='const DOMAIN="https://conosce.osce.gob.pe";'
                'const BASEPATH="/buscador/assets/official/reportes";'
                'generateSingleDownloadYears("contratos", "CONTRATOS");')
        return httpx.Response(200, text='/* recurso sin catálogo */')

    async def scenario() -> None:
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http:
            async with OECEPentahoClient(http) as client:
                resources = await client.discover([2024, 2025, 2026], datasets=('contratos',))
                assert [r.fiscal_year for r in resources] == [2024, 2025, 2026]
                assert all('/contratos/' in r.url for r in resources)
    asyncio.run(scenario())
    assert '/nested.html' in requested
    assert '/catalog-nested.js' in requested


def test_jsf_rotates_viewstate_and_reports_challenge(tmp_path: Path) -> None:
    entity = load_universe().entities[0].entity
    form = 'tbBuscador:idFormBuscarProceso'
    html = f'''<form id="{form}"><input type="hidden" name="javax.faces.ViewState" value="state-1">
        <input name="{form}:hddNumeroRuc" value=""><select name="{form}:anioConvocatoria_input">
        <option value="2026" selected>2026</option></select></form>'''

    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "GET":
            return httpx.Response(200, text=html, headers={"set-cookie": "JSESSIONID=jsf-session"})
        values = parse_qs(request.content.decode())
        assert request.headers['faces-request'] == 'partial/ajax'
        assert values['javax.faces.ViewState'] == ['state-1']
        assert values[form + ':hddNumeroRuc'] == [entity.ruc]
        return httpx.Response(200, text='''<partial-response><changes>
          <update id="javax.faces.ViewState"><![CDATA[state-2]]></update>
          <update id="results"><![CDATA[<table><tbody class="ui-datatable-data">
          <tr data-ri="0"><td>1255489</td><td>Obra CUI 1234567</td></tr>
          </tbody></table>]]></update></changes></partial-response>''')

    async def scenario() -> None:
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http, SEACEBuscadorPublicoClient(http) as client:
            records = await client.search(entity, 2026)
            assert len(records) == 1
            assert client.view_state == 'state-2'
        async with httpx.AsyncClient(transport=httpx.MockTransport(
            lambda request: httpx.Response(200, text=html + '<script src="recaptcha/api.js"></script>')
        )) as http:
            gaps = CoverageGapLogger(tmp_path / 'gaps.jsonl')
            async with SEACEBuscadorPublicoClient(http, coverage_logger=gaps) as client:
                with pytest.raises(CAPTCHARequired):
                    await client.search(entity, 2026)
            assert gaps.read_records()[0]['error_message'] == 'CAPTCHA_REQUIRED'

    asyncio.run(scenario())


def test_cross_source_identity_preserves_procurement() -> None:
    entity = load_universe().entities[0].entity
    procurement = ProcurementRecord(
        procurement_id="pr-preserved", ocid="ocds-dgv273-seacev3-1255489",
        entity_id=entity.entity_id, title="Proceso oficial",
        raw_payload={"tender": {"id": "1255489"}}, retrieved_at=datetime.now(UTC),
    )
    evidence = ProcurementSourceRecord.model_validate({
        "source_evidence_id": "pe-one", "source_system": "oece_pentaho_bi",
        "dataset": "convocatorias", "fiscal_year": 2026, "entity_id": entity.entity_id,
        "source_record_id": "1255489:1", "official_process_id": "1255489",
        "source_url": "https://conosce.osce.gob.pe/dataset.xlsx",
        "retrieved_at": datetime.now(UTC), "raw_payload": {"record": {"CODIGOCONVOCATORIA": "1255489"}},
    })
    linked = link_procurement_evidence([evidence, evidence], [procurement])
    assert len(linked) == 1 and linked[0].procurement_id == procurement.procurement_id
    assert procurement.raw_payload == {"tender": {"id": "1255489"}}
    foreign = evidence.model_copy(update={"entity_id": "ce-another"})
    assert link_procurement_evidence([foreign], [procurement])[0].procurement_id is None


def test_orders_from_the_same_supplier_keep_distinct_official_numbers() -> None:
    entity = load_universe().entities[0].entity
    resource = DownloadResource("ordenes", 2024, "https://conosce.osce.gob.pe/orders.xlsx")
    row = {"ruc_entidad": entity.ruc, "ruc_contratista": "20100000001", "orden": "O/C-1-2024"}
    first = _source_record(row, entity, resource, "oece_pentaho_bi")
    second = _source_record({**row, "orden": "O/C-2-2024"}, entity, resource, "oece_pentaho_bi")
    assert first.source_evidence_id != second.source_evidence_id
    assert first.official_process_id is None and second.official_process_id is None


def test_jsf_official_nomenclature_is_stable_and_links_without_fuzzy_names() -> None:
    entity = load_universe().entities[0].entity
    resource = DownloadResource('procedimientos', 2026, 'https://prod2.seace.gob.pe/search')
    row = {'column_0': '1', 'column_3': 'LP-ABR-21-2026-GR.CAJ-1'}
    first = _source_record(row, entity, resource, 'seace_buscador_publico')
    second = _source_record({**row, 'column_0': '16'}, entity, resource, 'seace_buscador_publico')
    assert first.source_evidence_id == second.source_evidence_id
    assert first.official_process_id == row['column_3']
    p = ProcurementRecord(procurement_id='pr-stable', ocid='ocds-real',entity_id=entity.entity_id,
        title=row['column_3'], raw_payload={}, retrieved_at=datetime.now(UTC))
    assert link_procurement_evidence([first], [p])[0].procurement_id == p.procurement_id
    ambiguous = p.model_copy(update={'procurement_id': 'pr-other', 'ocid': 'ocds-other'})
    assert link_procurement_evidence([first], [p, ambiguous])[0].procurement_id is None
    restarted = _source_record({**row, 'column_2': '06/03/2026 12:06',
                               'column_4': 'Admisión de propuesta técnica'},
                              entity, resource, 'seace_buscador_publico')
    assert restarted.source_evidence_id != first.source_evidence_id


def test_jsf_pagination_uses_fresh_state_and_explicit_process_identity() -> None:
    entity = load_universe().entities[0].entity
    form = "tbBuscador:idFormBuscarProceso"
    table = form + ":dtProcesos"
    posted = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "GET":
            return httpx.Response(200, text=f'<form id="{form}"><input name="javax.faces.ViewState" value="state-1"></form>')
        values = parse_qs(request.content.decode())
        posted.append(values)
        page = len(posted)
        if page == 2:
            assert form + ':btnBuscarSel' not in values
            assert 'submit' not in values
            assert values["javax.faces.ViewState"] == ["state-2"]
            assert values[table + "_first"] == ["1"]
            assert values[table + "_rows"] == ["1"]
            assert values[table + "_encodeFeature"] == ["true"]
        fragment = (f'<table><tbody class="ui-datatable-data"><tr data-codigoconvocatoria="125548{page}">'
                    f'<td>Proceso oficial {page}</td></tr></tbody></table>'
                    f'<script>id:"{table}",paginator:{{rows:1,rowCount:2}}</script>')
        if page == 2:
            fragment = f'<tr data-codigoconvocatoria="125548{page}"><td>Proceso oficial {page}</td></tr>'
        update_id = table if page == 2 else "results"
        return httpx.Response(200, text=f'<partial-response><changes><update id="{update_id}"><![CDATA[{fragment}]]></update>'
                              f'<update id="javax.faces.ViewState">state-{page + 1}</update></changes></partial-response>')

    async def scenario() -> None:
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http, SEACEBuscadorPublicoClient(http) as client:
            rows = await client.search(entity, 2026)
            assert {row.official_process_id for row in rows} == {"1255481", "1255482"}
            assert client.view_state == "state-3"
    asyncio.run(scenario())


@pytest.mark.parametrize("status", [403, 429, 503])
def test_jsf_http_denial_is_recorded_without_erasing_primary_source(tmp_path: Path, status: int) -> None:
    from cajamarca_qhaway.capabilities.seace_ingestion.official_sources import (
        OfficialSourceUnavailable,
    )
    entity = load_universe().entities[0].entity
    gaps = CoverageGapLogger(tmp_path / "jsf-gaps.jsonl")
    async def scenario() -> None:
        async with httpx.AsyncClient(transport=httpx.MockTransport(
            lambda request: httpx.Response(status, text="Access unavailable")
        )) as http, SEACEBuscadorPublicoClient(http, coverage_logger=gaps) as client:
            with pytest.raises(OfficialSourceUnavailable, match=f"HTTP_{status}"):
                await client.search(entity, 2026)
    asyncio.run(scenario())
    incident = gaps.read_records()[0]
    assert incident["status_code"] == status
    assert incident["error_message"] == f"HTTP_{status}"


def test_live_probe_reports_http_denial_as_a_coverage_gap(tmp_path: Path) -> None:
    from cajamarca_qhaway.capabilities.live_harvest.official_source_probe import (
        probe_public_source,
    )
    entity = load_universe().entities[0].entity
    gaps = CoverageGapLogger(tmp_path / "probe-gaps.jsonl")
    async def scenario() -> None:
        async with httpx.AsyncClient(transport=httpx.MockTransport(
            lambda request: httpx.Response(403, text="Forbidden")
        )) as http, SEACEBuscadorPublicoClient(http, coverage_logger=gaps) as client:
            probe = await probe_public_source(client, entity, 2026)
            assert probe.status == "HTTP_403" and probe.records == []
    asyncio.run(scenario())
    assert gaps.read_records()[0]["status_code"] == 403
