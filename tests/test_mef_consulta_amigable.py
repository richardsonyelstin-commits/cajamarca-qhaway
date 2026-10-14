from cajamarca_qhaway.capabilities.live_harvest.mef_consulta_amigable import (
    _amount,
    _official_cut_date,
    _parse_page,
    _row_payload,
)
from cajamarca_qhaway.capabilities.mef_ingestion.parser import _normalize_text


def test_parse_webforms_state_and_table_row() -> None:
    html = """<form id="aspnetForm">
      <input type="hidden" name="__VIEWSTATE" value="state-1">
      <input type="hidden" name="__EVENTVALIDATION" value="valid-1">
      <input type="submit" name="ctl00$CPH1$BtnSector" value="Sector">
      <div id="pg_bd"><table class="Data"><tr id="tr0">
        <td><input type="radio" name="grp1" value="R/3820687023/4451746962/3142808938"></td>
        <td>R: GOBIERNO REGIONAL DEL DEPARTAMENTO DE CAJAMARCA</td>
        <td>3,820,687,023</td><td>4,451,746,962</td><td>4,000</td>
        <td>3,500</td><td>3,200</td><td>3,142,808,938</td>
        <td>3,100</td><td>70.6</td>
      </tr></table></div></form>"""
    page = _parse_page(html)

    assert page.hidden == {"__VIEWSTATE": "state-1", "__EVENTVALIDATION": "valid-1"}
    assert page.buttons == {"ctl00$CPH1$BtnSector": "Sector"}
    assert len(page.rows) == 1
    assert page.rows[0].label.startswith("R: GOBIERNO REGIONAL")
    assert page.rows[0].radio_value.startswith("R/")


def test_raw_payload_keeps_original_display_columns_and_route() -> None:
    page = _parse_page("""<form id="aspnetForm"><table class="Data"><tr id="tr0">
      <td><input type="radio" name="grp1" value="445/3820687023"></td>
      <td>445: GOBIERNO REGIONAL DEL DEPARTAMENTO DE CAJAMARCA</td>
      <td>3,820,687,023</td><td>4,451,746,962</td><td>4,000</td>
      <td>3,500</td><td>3,200</td><td>3,142,808,938</td><td>3,100</td><td>70.6</td>
    </tr></table></form>""")
    raw = _row_payload(page.rows[0], 2026, "https://official.test/?y=2026", ["445"], "2026-09-30")

    assert raw["codigo_entidad"] == "445"
    assert raw["nombre_entidad"] == "GOBIERNO REGIONAL DEL DEPARTAMENTO DE CAJAMARCA"
    assert raw["PIA"] == "3,820,687,023"
    assert raw["PIM"] == "4,451,746,962"
    assert raw["DEVENGADO"] == "3,142,808,938"
    assert raw["AVANCE_PCT"] == "70.6"
    assert raw["ANO_EJE"] == 2026
    assert raw["FECHA_CORTE_OFICIAL"] == "2026-09-30"
    assert raw["ruta_navegacion"] == ["445"]
    assert raw["FUENTE_URL"].startswith("https://official.test/")
    assert _amount(raw["PIM"]) == 4451746962.0


def test_extracts_official_cut_date_and_strips_em_dash() -> None:
    assert _official_cut_date(
        "<p>Última actualización: 30 de septiembre de 2026</p>"
    ) == "2026-09-30"
    assert "\u2014" not in _normalize_text("Municipalidad \u2014 Cajamarca")
