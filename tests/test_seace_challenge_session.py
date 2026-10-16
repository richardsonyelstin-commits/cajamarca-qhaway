from __future__ import annotations

import asyncio
from urllib.parse import parse_qs

import httpx

from cajamarca_qhaway.capabilities.entity_mapping.dataset import load_universe
from cajamarca_qhaway.capabilities.seace_ingestion.official_sources import (
    JSF_FORM,
    SEACEBuscadorPublicoClient,
)


def test_recaptcha_provider_retries_with_fresh_viewstate_and_same_session() -> None:
    calls: list[tuple[int, str]] = []
    posts: list[str] = []
    selection_steps: list[str] = []

    async def solve(html: str, client: httpx.AsyncClient, attempt: int) -> str:
        assert client.cookies.get('JSESSIONID') == 'session-a'
        calls.append((attempt, html))
        return f'token-{attempt}'

    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == 'GET':
            return httpx.Response(200, text=f'<form id="{JSF_FORM}">'
                '<input name="javax.faces.ViewState" value="s1">'
                f'<input name="{JSF_FORM}:txtRucEntidad"></form>'
                '<script src="https://www.google.com/recaptcha/api.js"></script>',
                headers={'set-cookie': 'JSESSIONID=session-a; Path=/'})
        fields = parse_qs(request.content.decode())
        assert 'session-a' in request.headers['cookie']
        requested_source = fields['javax.faces.source'][0]
        if requested_source.endswith(':btnBuscarEntidad'):
            selection_steps.append('lookup')
            assert fields[JSF_FORM + ':txtRucEntidad'] == ['20453744168']
            return httpx.Response(200, text='<partial-response><changes>'
                '<update id="picker"><![CDATA['
                f'<a id="{JSF_FORM}:dataTable:0:ajaxEntidad" '
                'onclick="PrimeFaces.ab({params:[{name:\'rucEntidad\',value:\'20453744168\'},'
                '{name:\'idOrganismo\',value:\'36\'},'
                '{name:\'descripcionEntidad\',value:\'GORE SEDE CENTRAL\'}]});">Entidad</a>'
                ']]></update></changes></partial-response>')
        if ':dataTable:' in requested_source:
            selection_steps.append('select')
            assert fields['idOrganismo'] == ['36']
            assert fields['rucEntidad'] == ['20453744168']
            return httpx.Response(200, text='<partial-response><changes>'
                f'<update id="{JSF_FORM}:nombreEntidad"><![CDATA['
                f'<input name="{JSF_FORM}:nombreEntidad" value="GORE SEDE CENTRAL">'
                ']]></update></changes></partial-response>')
        source = JSF_FORM + ':btnBuscarSel'
        assert fields[source] == [source]
        assert 'frmMesajes:gPrincipal' in fields['javax.faces.partial.render'][0]
        posts.append(fields['javax.faces.ViewState'][0])
        token = fields[JSF_FORM + ':tokenBusProSel'][0]
        if token == 'token-1':
            return httpx.Response(200, text='<partial-response><changes>'
                '<update id="javax.faces.ViewState">s2</update>'
                '<update id="messages">CAPTCHA incorrecto</update></changes></partial-response>')
        return httpx.Response(200, text='<partial-response><changes>'
            '<update id="javax.faces.ViewState">s3</update>'
            '<update id="results"><![CDATA[<tbody class="ui-datatable-data">'
            '<tr class="ui-datatable-empty-message"><td>Sin resultados</td></tr>'
            '</tbody>]]></update></changes></partial-response>')

    async def scenario() -> None:
        async with (
            httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http,
            SEACEBuscadorPublicoClient(http, captcha_solver=solve) as client,
        ):
            assert await client.search(load_universe().entities[0].entity, 2026) == []

    asyncio.run(scenario())
    assert [item[0] for item in calls] == [1, 2]
    assert posts == ['s1', 's2']
    assert selection_steps == ['lookup', 'select']


def test_captcha_retries_are_bounded_and_logged(tmp_path) -> None:
    import pytest

    from cajamarca_qhaway.capabilities.live_harvest.coverage_logger import (
        CoverageGapLogger,
    )
    from cajamarca_qhaway.capabilities.seace_ingestion.official_sources import (
        CAPTCHARequired,
    )

    attempts: list[int] = []

    async def solver(html: str, http: httpx.AsyncClient, attempt: int) -> str:
        attempts.append(attempt)
        return 'rejected-token'

    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == 'GET':
            return httpx.Response(200, text='<input name="javax.faces.ViewState" value="s1">recaptcha')
        return httpx.Response(200, text='<partial-response><changes>'
            '<update id="javax.faces.ViewState">s2</update>'
            '<update id="msg">CAPTCHA incorrecto</update></changes></partial-response>')

    async def scenario() -> None:
        gaps = CoverageGapLogger(tmp_path / 'gaps.jsonl')
        async with (
            httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http,
            SEACEBuscadorPublicoClient(http, captcha_solver=solver,
                                                 coverage_logger=gaps) as client,
        ):
            with pytest.raises(CAPTCHARequired):
                await client.search(load_universe().entities[0].entity, 2026)
        assert gaps.read_records()[-1]['attempt'] == 3

    asyncio.run(scenario())
    assert attempts == [1, 2, 3]
