"""Consulta el modulo oficial MEF mediante su formulario ASP.NET WebForms."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from html.parser import HTMLParser
import re
from typing import Any

import httpx

from cajamarca_qhaway.capabilities.mef_ingestion.parser import (
    MUNICIPAL_EXECUTOR_PROVINCES,
    _normalize_text,
)
from cajamarca_qhaway.models import (
    BudgetExecutionRecord,
    ContractingEntity,
    compute_execution_record_id,
)

BASE_URL = "https://apps5.mineco.gob.pe/transparencia/Mensual/Navegar_6.aspx"
SOURCE = "mef-consulta-amigable"
MUNICIPALITY_LABELS = {
    "CAJAMARCA": "01", "CAJABAMBA": "02", "CELENDIN": "03", "CHOTA": "04",
    "CONTUMAZA": "05", "CUTERVO": "06", "HUALGAYOC": "07", "JAEN": "08",
    "SAN IGNACIO": "09", "SAN MARCOS": "10", "SAN MIGUEL": "11",
    "SAN PABLO": "12", "SANTA CRUZ": "13",
}


@dataclass
class _Row:
    label: str = ""
    radio_value: str = ""
    cells: list[str] = field(default_factory=list)


class _WebFormsParser(HTMLParser):
    """Lee campos hidden, botones y filas de la tabla presupuestal."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.hidden: dict[str, str] = {}
        self.selects: dict[str, str] = {}
        self.buttons: dict[str, str] = {}
        self.rows: list[_Row] = []
        self.page_text: list[str] = []
        self._form = False
        self._select: str | None = None
        self._option_selected = False
        self._data_table = False
        self._row: _Row | None = None
        self._cell: list[str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        a = dict(attrs)
        if tag == "form" and a.get("id") == "aspnetForm":
            self._form = True
        if self._form and tag == "input" and a.get("name"):
            name, value = a["name"], a.get("value", "") or ""
            if a.get("type") == "hidden":
                self.hidden[name] = value
            elif a.get("type") == "submit":
                self.buttons[name] = value
            elif a.get("type") == "radio" and name == "grp1" and self._row:
                self._row.radio_value = value
        if self._form and tag == "select" and a.get("name"):
            self._select = a["name"]
        if tag == "option" and self._select:
            self._option_selected = "selected" in a
            if self._option_selected:
                self.selects[self._select] = a.get("value", "") or ""
        if tag == "table" and "Data" in (a.get("class") or "").split():
            self._data_table = True
        if self._data_table and tag == "tr" and (a.get("id") or "").startswith("tr"):
            self._row = _Row()
        if self._row and self._data_table and tag == "td":
            self._cell = []

    def handle_data(self, data: str) -> None:
        self.page_text.append(data)
        if self._cell is not None:
            self._cell.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "td" and self._cell is not None and self._row:
            self._row.cells.append(" ".join("".join(self._cell).split()))
            self._cell = None
        elif tag == "tr" and self._row:
            if self._row.cells:
                self._row.label = next((cell for cell in self._row.cells if cell), "")
                self.rows.append(self._row)
            self._row = None
        elif tag == "table" and self._data_table:
            self._data_table = False
        elif tag == "select":
            self._select = None
        elif tag == "form":
            self._form = False


def _parse_page(content: str) -> _WebFormsParser:
    parser = _WebFormsParser()
    parser.feed(content)
    return parser


def _amount(value: str) -> float:
    normalized = value.replace(",", "").strip()
    return float(normalized) if normalized else 0.0


def _row_payload(
    row: _Row, year: int, page_url: str, navigation: list[str], cut_date: str | None
) -> dict[str, Any]:
    if len(row.cells) < 10:
        raise ValueError(f"Fila MEF incompleta: {row.label!r}")
    labels = (
        "PIA", "PIM", "CERTIFICACION", "COMPROMISO_ANUAL",
        "ATENCION_COMPROMISO_MENSUAL", "DEVENGADO", "GIRADO", "AVANCE_PCT",
    )
    data: dict[str, Any] = {"codigo_entidad": row.radio_value.split("/", 1)[0]}
    data["nombre_entidad"] = row.label.split(":", 1)[-1].strip()
    label_index = row.cells.index(row.label)
    data.update(
        {
            name: value
            for name, value in zip(
                labels, row.cells[label_index + 1 :], strict=True
            )
        }
    )
    data["ANO_EJE"] = year
    data["FECHA_CORTE_OFICIAL"] = cut_date
    data["FUENTE_URL"] = page_url
    data["ruta_navegacion"] = list(navigation)
    return data


def _official_cut_date(content: str) -> str | None:
    text = " ".join(_parse_page(content).page_text)
    match = re.search(
        r"(?:Última actualización|Ultima actualizacion)\s*:\s*"
        r"(\d{1,2})\s+de\s+([a-záéíóú]+)\s+de\s+(\d{4})",
        text,
        re.IGNORECASE,
    )
    if not match:
        return None
    months = {
        "enero": "01", "febrero": "02", "marzo": "03", "abril": "04",
        "mayo": "05", "junio": "06", "julio": "07", "agosto": "08",
        "septiembre": "09", "setiembre": "09", "octubre": "10",
        "noviembre": "11", "diciembre": "12",
    }
    month = months.get(match.group(2).casefold())
    if month is None:
        return None
    return f"{match.group(3)}-{month}-{int(match.group(1)):02d}"


class MefConsultaAmigableClient:
    """Cliente stateful de los postbacks ASP.NET del modulo mensual del MEF."""

    def __init__(self, http_client: httpx.AsyncClient | None = None) -> None:
        self._client = http_client
        self._owns_client = http_client is None

    async def __aenter__(self) -> MefConsultaAmigableClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                headers={
                    "User-Agent": "Mozilla/5.0 (compatible; CajamarcaQhaway/1.0)",
                    "Accept": "text/html,application/xhtml+xml",
                },
                timeout=httpx.Timeout(30.0),
                follow_redirects=True,
            )
        return self

    async def __aexit__(self, *_: object) -> None:
        if self._owns_client and self._client:
            await self._client.aclose()

    async def _get(self, year: int) -> tuple[str, str]:
        assert self._client is not None
        url = f"{BASE_URL}?y={year}&ap=ActProy"
        response = await self._client.get(url)
        response.raise_for_status()
        return response.text, str(response.url)

    async def _postback(
        self, content: str, url: str, row_match: str, button_label: str
    ) -> tuple[str, str]:
        assert self._client is not None
        page = _parse_page(content)
        row = next((item for item in page.rows if row_match in item.label), None)
        if row is None or not row.radio_value:
            raise ValueError(f"No se encontro fila MEF {row_match!r} en {url}")
        button = next(
            ((name, value) for name, value in page.buttons.items() if value == button_label),
            None,
        )
        if button is None:
            raise ValueError(f"No se encontro boton MEF {button_label!r} en {url}")
        payload = dict(page.hidden)
        payload.update(page.selects)
        payload["grp1"] = row.radio_value
        payload[button[0]] = button[1]
        response = await self._client.post(url, data=payload)
        response.raise_for_status()
        return response.text, str(response.url)

    async def _navigate(
        self, content: str, url: str, selection: str, button: str
    ) -> tuple[str, str]:
        return await self._postback(content, url, selection, button)

    async def extract(
        self, year: int, entities: list[ContractingEntity]
    ) -> list[BudgetExecutionRecord]:
        """Extrae un total oficial por pliego: GORE y 13 municipalidades provinciales."""
        if year not in (2024, 2025, 2026):
            raise ValueError("El corte admite únicamente 2024, 2025 y 2026")
        if self._client is None:
            raise RuntimeError("Usa MefConsultaAmigableClient dentro de un context manager")
        entities_by_province = {
            _normalize_text(entity.province or ""): entity
            for entity in entities
            if entity.entity_level == "provincial_municipality"
        }
        regional = next(
            (entity for entity in entities if entity.entity_level == "regional"), None
        )
        if regional is None or len(entities_by_province) != 13:
            raise ValueError("El universo debe tener 1 entidad regional y 13 provinciales")
        content, url = await self._get(year)
        navigation = [
            "TOTAL", "Nivel de Gobierno", "R: GOBIERNOS REGIONALES", "Sector",
            "99: GOBIERNOS REGIONALES", "Pliego", "445",
        ]
        content, url = await self._navigate(content, url, "TOTAL", "Nivel de Gobierno")
        content, url = await self._navigate(content, url, "R: GOBIERNOS REGIONALES", "Sector")
        content, url = await self._navigate(content, url, "99: GOBIERNOS REGIONALES", "Pliego")
        page = _parse_page(content)
        regional_row = next((r for r in page.rows if r.label.startswith("445:")), None)
        if regional_row is None:
            raise ValueError(f"El MEF no devolvio el pliego 445 para {year}")
        records = [
            _to_record(
                regional_row, regional, year, url, navigation,
                _official_cut_date(content),
            )
        ]

        content, url = await self._get(year)
        for selection, button in (
            ("TOTAL", "Nivel de Gobierno"),
            ("M: GOBIERNOS LOCALES", "Gob.Loc./Mancom."),
            ("M: MUNICIPALIDADES", "Departamento"),
            ("06: CAJAMARCA", "Provincia"),
        ):
            navigation.append(selection)
            content, url = await self._navigate(content, url, selection, button)
        province_rows = _parse_page(content).rows
        province_items = list(MUNICIPALITY_LABELS.items())
        for province_index, (province_name, province_code) in enumerate(province_items):
            province = next(
                (r for r in province_rows if r.label.startswith(f"06{province_code}:")), None
            )
            if province is None:
                raise ValueError(f"Falta provincia MEF {province_name} ({year})")
            province_entity = entities_by_province.get(province_name)
            if province_entity is None:
                raise ValueError(f"Provincia no mapeada al universo: {province_name}")
            navigation = [
                "TOTAL", "Nivel de Gobierno", "M: GOBIERNOS LOCALES", "Gob.Loc./Mancom.",
                "M: MUNICIPALIDADES", "Departamento", "06: CAJAMARCA", "Provincia",
                province.label, "Municipalidad",
            ]
            content, url = await self._navigate(content, url, province.label, "Municipalidad")
            executor = next(
                (
                    r for r in _parse_page(content).rows
                    if r.radio_value.split("/", 1)[0] in MUNICIPAL_EXECUTOR_PROVINCES
                    and MUNICIPAL_EXECUTOR_PROVINCES[
                        r.radio_value.split("/", 1)[0]
                    ] == province_name
                    and "PROVINCIAL" in _normalize_text(r.label)
                    and "DISTRITAL" not in _normalize_text(r.label)
                ),
                None,
            )
            if executor is None:
                raise ValueError(f"No se verifico ejecutora provincial {province_name} ({year})")
            records.append(
                _to_record(
                    executor, province_entity, year, url, navigation,
                    _official_cut_date(content),
                )
            )
            if province_index < len(province_items) - 1:
                content, url = await self._get(year)
                for selection, button in (
                    ("TOTAL", "Nivel de Gobierno"),
                    ("M: GOBIERNOS LOCALES", "Gob.Loc./Mancom."),
                    ("M: MUNICIPALIDADES", "Departamento"),
                    ("06: CAJAMARCA", "Provincia"),
                ):
                    content, url = await self._navigate(content, url, selection, button)
                province_rows = _parse_page(content).rows
        return records


def _to_record(
    row: _Row,
    entity: ContractingEntity,
    year: int,
    page_url: str,
    navigation: list[str],
    cut_date: str | None,
) -> BudgetExecutionRecord:
    raw_payload = _row_payload(row, year, page_url, navigation, cut_date)
    category = "TOTAL"
    return BudgetExecutionRecord(
        execution_record_id=compute_execution_record_id(entity.entity_id, year, category),
        entity_id=entity.entity_id,
        fiscal_year=year,
        budgeted_amount=_amount(str(raw_payload["PIM"])),
        executed_amount=_amount(str(raw_payload["DEVENGADO"])),
        budget_category=category,
        raw_payload=raw_payload,
        source=SOURCE,
        retrieved_at=datetime.now(timezone.utc),
    )
