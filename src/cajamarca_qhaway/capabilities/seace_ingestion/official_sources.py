"""Adaptadores del catalogo OECE y del buscador JSF, con evidencia independiente de OCDS."""

from __future__ import annotations

import csv
import hashlib
import json
import re
import tempfile
import xml.etree.ElementTree as ET
from collections.abc import AsyncIterator, Iterator, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from html.parser import HTMLParser
from typing import IO, Any, NoReturn, Self
from urllib.parse import parse_qs, urljoin, urlparse
from zipfile import ZipFile

import httpx

from cajamarca_qhaway.capabilities.live_harvest.coverage_logger import CoverageGapLogger
from cajamarca_qhaway.models import ContractingEntity, ProcurementRecord
from cajamarca_qhaway.models.procurement_source_record import ProcurementSourceRecord

PENTAHO_URL = "https://bi.seace.gob.pe/pentaho/api/repos/%3Apublic%3Aportal%3Adatosabiertos.html/content?userid=public&password=key"
PENTAHO_SCRIPT = "https://bi.seace.gob.pe/pentaho/plugin/pentaho-cdf-dd/api/resources/public/portal/js/renderhtmlv2.js"
SEACE_PUBLIC_URL = "https://prod2.seace.gob.pe/seacebus-uiwd-pub/buscadorPublico/buscadorPublico.xhtml"
JSF_FORM = "tbBuscador:idFormBuscarProceso"
XLSX_NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


class OfficialSourceUnavailable(RuntimeError):
    """La fuente no permite completar una consulta oficial verificable."""


class CAPTCHARequired(OfficialSourceUnavailable):
    """La fuente exige un desafio humano que el adaptador no evade."""


@dataclass(frozen=True)
class DownloadResource:
    dataset: str
    fiscal_year: int
    url: str


def _column_key(value: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", value.upper())


def _field(row: dict[str, str], *names: str) -> str:
    normalized = {_column_key(key): value.strip() for key, value in row.items()}
    return next((normalized[_column_key(name)] for name in names if normalized.get(_column_key(name))), "")


def _cui(row: dict[str, str]) -> str | None:
    explicit = _field(row, "CUI", "CODIGOUNICODEINVERSION", "CODIGOUNICOINVERSION")
    if re.fullmatch(r"\d{7}", explicit):
        return explicit
    matches = set(re.findall(r"\bCUI\s*(?:N[°º.]?\s*)?[:#-]?\s*(\d{7})\b", " ".join(row.values()), re.IGNORECASE))
    return next(iter(matches)) if len(matches) == 1 else None


def _source_record(
    row: dict[str, str], entity: ContractingEntity, resource: DownloadResource,
    system: str, process_id: str | None = None,
) -> ProcurementSourceRecord:
    process = process_id or _field(row, "CODIGOCONVOCATORIA", "CODIGOPROCESO") or None
    document = _field(row, "N_COD_CONTRATO", "CODIGO_CONTRATO", "NUM_CONTRATO", "NUMEROCONTRATO",
                      "ORDEN", "NRO_DE_ORDEN", "NUMEROORDEN", "NUMEROORDENCOMPRA")
    identity = [process or "", _field(row, "CODIGOITEM", "NITEM", "NUMITEM"),
                _field(row, "RUCPROVEEDOR", "RUCPOSTOR", "PROVEEDORRUC", "RUC_CONTRATISTA"),
                document]
    if process or document:
        source_id = ":".join(identity)
    else:
        source_id = "sha256:" + hashlib.sha256(json.dumps(row, sort_keys=True).encode()).hexdigest()
    key = f"{system}:{resource.dataset}:{resource.fiscal_year}:{entity.entity_id}:{source_id}"
    return ProcurementSourceRecord.model_validate({
        "source_evidence_id": "pe-" + hashlib.sha256(key.encode()).hexdigest()[:24],
        "source_system": system, "dataset": resource.dataset, "fiscal_year": resource.fiscal_year,
        "entity_id": entity.entity_id, "source_record_id": source_id,
        "official_process_id": process, "cui": _cui(row), "source_url": resource.url,
        "retrieved_at": datetime.now(UTC),
        "raw_payload": {"source_system": system, "identity_version": 2, "record": row},
    })


def iter_xlsx_rows(file: IO[bytes]) -> Iterator[dict[str, str]]:
    """Lee las filas sin cargar el libro nacional completo ni ejecutar formulas."""
    with ZipFile(file) as archive:
        if sum(info.file_size for info in archive.infolist()) > 1_500_000_000:
            raise ValueError("El libro OECE excede el limite de expansion")
        strings: list[str] = []
        if "xl/sharedStrings.xml" in archive.namelist():
            with archive.open("xl/sharedStrings.xml") as source:
                for _, element in ET.iterparse(source, events=("end",)):
                    if element.tag.endswith("}si"):
                        strings.append("".join(node.text or "" for node in element.findall(".//m:t", XLSX_NS)))
                        element.clear()
        sheets = sorted(name for name in archive.namelist() if re.fullmatch(r"xl/worksheets/sheet\d+\.xml", name))
        if not sheets:
            raise ValueError("El archivo OECE no contiene hojas XLSX")
        for sheet in sheets:
            headers: dict[str, str] = {}
            with archive.open(sheet) as source:
                for _, element in ET.iterparse(source, events=("end",)):
                    if not element.tag.endswith("}row"):
                        continue
                    values: dict[str, str] = {}
                    for cell in element.findall("m:c", XLSX_NS):
                        column = re.sub(r"\d", "", cell.attrib.get("r", ""))
                        value = cell.findtext("m:v", default="", namespaces=XLSX_NS)
                        if cell.attrib.get("t") == "s" and value:
                            value = strings[int(value)]
                        elif cell.attrib.get("t") == "inlineStr":
                            value = "".join(node.text or "" for node in cell.findall(".//m:t", XLSX_NS))
                        values[column] = value
                    if not headers:
                        headers = {key: value.strip() for key, value in values.items() if value.strip()}
                    else:
                        yield {label: values.get(column, "") for column, label in headers.items()}
                    element.clear()


class _PublicClient:
    def __init__(self, http_client: httpx.AsyncClient | None = None) -> None:
        self.http = http_client
        self.owns_http = http_client is None

    async def __aenter__(self) -> Self:
        if self.http is None:
            self.http = httpx.AsyncClient(timeout=90, follow_redirects=True, headers={
                "User-Agent": "CajamarcaQhaway-Harvester/1.0 (+https://github.com/richardsonyelstin-commits/cajamarca-qhaway)",
            })
        return self

    async def __aexit__(self, *_: object) -> None:
        if self.http is not None and self.owns_http:
            await self.http.aclose()


class OECEPentahoClient(_PublicClient):
    def __init__(self, http_client: httpx.AsyncClient | None = None) -> None:
        super().__init__(http_client)
        self.entity_codes: dict[str, str] = {}
        self.entity_catalog_url: str | None = None

    async def _load_entity_codes(self, entities: Sequence[ContractingEntity]) -> None:
        assert self.http is not None
        if not self.entity_catalog_url:
            raise ValueError("El catalogo no expone la tabla oficial de identidad institucional")
        allowed = {entity.ruc for entity in entities}
        async with self.http.stream("GET", self.entity_catalog_url) as response:
            response.raise_for_status()
            headers: list[str] = []
            async for line in response.aiter_lines():
                if not line.strip():
                    continue
                values = next(csv.reader([line], delimiter="|"))
                if not headers:
                    headers = [value.lstrip("\ufeff") for value in values]
                    if "RUC" not in headers or "CODCONSUCODE" not in headers:
                        raise ValueError("El catalogo institucional OECE cambio de esquema")
                    continue
                row = dict(zip(headers, values, strict=True))
                if row["RUC"] in allowed:
                    code = row["CODCONSUCODE"].lstrip("0")
                    if code in self.entity_codes and self.entity_codes[code] != row["RUC"]:
                        raise ValueError("Codigo institucional OECE ambiguo")
                    self.entity_codes[code] = row["RUC"]
        if set(self.entity_codes.values()) != allowed:
            raise ValueError("El catalogo OECE no acredita los 14 RUC institucionales")

    async def discover(
        self, years: Sequence[int], *, datasets: Sequence[str] = (
            "convocatorias", "adjudicaciones", "contratos", "ordenes",
        ),
    ) -> list[DownloadResource]:
        assert self.http is not None
        response = await self.http.get(PENTAHO_URL)
        response.raise_for_status()
        scripts = re.findall(r'<script[^>]+src=["\']([^"\']+)', response.text, re.IGNORECASE)
        script_url = next((urljoin(PENTAHO_URL, value) for value in scripts if value.startswith("/") or "renderhtml" in value), PENTAHO_SCRIPT)
        if urlparse(script_url).hostname != "bi.seace.gob.pe":
            raise ValueError("El catalogo no apunta a un recurso oficial OECE")
        script = await self.http.get(script_url)
        script.raise_for_status()
        domain = re.search(r'const\s+DOMAIN\s*=\s*["\']([^"\']+)', script.text)
        path = re.search(r'const\s+BASEPATH\s*=\s*["\']([^"\']+)', script.text)
        if not domain or domain.group(1) != "https://conosce.osce.gob.pe" or not path:
            raise ValueError("No se verifico el catalogo de descargas OECE")
        base_path = path.group(1)
        if not re.fullmatch(r"/buscador/assets/[A-Za-z0-9-]+/reportes", base_path):
            raise ValueError("Ruta de catalogo OECE fuera del contrato verificado")
        if "entidadescontratantes/entidades_contratantes.csv" in script.text:
            self.entity_catalog_url = domain.group(1) + base_path + "/entidadescontratantes/entidades_contratantes.csv"
        result: list[DownloadResource] = []
        for dataset in datasets:
            if dataset not in ("convocatorias", "adjudicaciones", "contratos", "ordenes"):
                raise ValueError(f"Dataset OECE no admitido: {dataset}")
            prefix = "ORDENESCOMPRA" if dataset == "ordenes" else dataset.upper()
            generator = re.search(
                rf'generateSingleDownloadYears\(["\']{dataset}["\']\s*,\s*["\']{prefix}["\']',
                script.text,
            )
            if f"CONOSCE_{prefix}" not in script.text and not generator:
                raise ValueError(f"No se encontro la plantilla oficial de {dataset}")
            for year in years:
                if year not in (2024, 2025, 2026):
                    raise ValueError("Ejercicio OECE fuera del alcance")
                months = re.findall(r'sufijo:\s*["\']([A-Z]+)["\']', script.text) if dataset == "ordenes" else [""]
                if dataset == "ordenes":
                    months = list(dict.fromkeys(months))
                    if len(months) != 12:
                        raise ValueError("El catalogo de ordenes no expone doce meses")
                    now = datetime.now(UTC)
                    if year == now.year:
                        months = months[:now.month]
                for month in months:
                    url = f"{domain.group(1)}{base_path}/{dataset}/{year}/CONOSCE_{prefix}{month}{year}_0.xlsx"
                    result.append(DownloadResource(dataset, year, url))
        return result

    async def records(
        self, resource: DownloadResource, entities: Sequence[ContractingEntity],
    ) -> AsyncIterator[ProcurementSourceRecord]:
        assert self.http is not None
        if urlparse(resource.url).hostname != "conosce.osce.gob.pe":
            raise ValueError("Descarga OECE fuera del host oficial")
        by_ruc = {entity.ruc: entity for entity in entities}
        with tempfile.TemporaryFile() as file:
            size = 0
            async with self.http.stream("GET", resource.url) as response:
                response.raise_for_status()
                async for chunk in response.aiter_bytes():
                    size += len(chunk)
                    if size > 256_000_000:
                        raise ValueError("Descarga OECE excede el limite de 256 MB")
                    file.write(chunk)
            file.seek(0)
            if file.read(4) != b"PK\x03\x04":
                raise ValueError("La descarga OECE no es un libro XLSX")
            file.seek(0)
            checked_headers = False
            for row in iter_xlsx_rows(file):
                if not checked_headers:
                    keys = {_column_key(key) for key in row}
                    if not keys.intersection({"ENTIDADRUC", "RUCENTIDAD", "CODIGOENTIDAD"}):
                        raise ValueError("El libro OECE no contiene RUC institucional verificable")
                    if not keys.intersection({"ENTIDADRUC", "RUCENTIDAD"}) and set(self.entity_codes.values()) != set(by_ruc):
                        await self._load_entity_codes(entities)
                    checked_headers = True
                ruc = _field(row, "ENTIDAD_RUC", "RUC_ENTIDAD")
                code = _field(row, "CODIGOENTIDAD").lstrip("0")
                if not ruc and code:
                    ruc = self.entity_codes.get(code, "")
                entity = by_ruc.get(ruc)
                if entity:
                    if code:
                        if code in self.entity_codes and self.entity_codes[code] != entity.ruc:
                            raise ValueError("Codigo institucional con RUC contradictorio")
                        self.entity_codes[code] = entity.ruc
                    yield _source_record(row, entity, resource, "oece_pentaho_bi")
            if not checked_headers:
                raise ValueError("El libro OECE no contiene registros verificables")


class _JSFParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.form = ""
        self.fields: dict[str, str] = {}
        self.view_state = ""
        self.select = ""
        self.rows: list[dict[str, str]] = []
        self.row: dict[str, str] | None = None
        self.cell: list[str] | None = None
        self.table = False
        self.table_seen = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        a = {key: value or "" for key, value in attrs}
        if tag == "form":
            self.form = a.get("id", "")
        if tag == "input" and a.get("name") == "javax.faces.ViewState":
            self.view_state = a.get("value", "")
        if self.form == JSF_FORM and tag == "input" and a.get("name"):
            self.fields[a["name"]] = a.get("value", "")
        if self.form == JSF_FORM and tag == "select":
            self.select = a.get("name", "")
        if tag == "option" and self.select and ("selected" in a or self.select not in self.fields):
            self.fields[self.select] = a.get("value", "")
        if tag == "tbody" and "ui-datatable-data" in a.get("class", "").split():
            self.table = True
            self.table_seen = True
        if tag == "tr" and self.table:
            self.row = None if "ui-datatable-empty-message" in a.get("class", "") else {}
            if self.row is not None:
                explicit = a.get("data-codigoconvocatoria")
                if explicit:
                    self.row["CODIGOCONVOCATORIA"] = explicit
        if self.row is not None and tag == "a":
            query = parse_qs(urlparse(a.get("href", "")).query)
            for key in ("codigoConvocatoria", "idProceso"):
                if query.get(key):
                    self.row["CODIGOCONVOCATORIA"] = query[key][0]
        if tag == "td" and self.row is not None:
            self.cell = []

    def handle_data(self, data: str) -> None:
        if self.cell is not None:
            self.cell.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "form":
            self.form = ""
        if tag == "select":
            self.select = ""
        if tag == "td" and self.row is not None and self.cell is not None:
            self.row[f"column_{len(self.row)}"] = " ".join("".join(self.cell).split())
            self.cell = None
        if tag == "tr" and self.row is not None:
            if self.row:
                self.rows.append(self.row)
            self.row = None
        if tag == "tbody":
            self.table = False


class SEACEBuscadorPublicoClient(_PublicClient):
    def __init__(
        self, http_client: httpx.AsyncClient | None = None, *,
        coverage_logger: CoverageGapLogger | None = None,
    ) -> None:
        super().__init__(http_client)
        self.coverage_logger = coverage_logger
        self.view_state = ""

    def _challenge(self, message: str, status_code: int | None = None) -> NoReturn:
        if self.coverage_logger:
            self.coverage_logger.log_incident(
                source="seace-buscador-publico", attempt=1, status_code=status_code,
                endpoint=SEACE_PUBLIC_URL, error_message=message,
            )
        if "CAPTCHA" in message:
            raise CAPTCHARequired(message)
        raise OfficialSourceUnavailable(message)

    async def _request(self, method: str, **kwargs: Any) -> httpx.Response:
        assert self.http is not None
        try:
            response = await self.http.request(method, SEACE_PUBLIC_URL, **kwargs)
            response.raise_for_status()
        except httpx.HTTPError as error:
            status = getattr(getattr(error, "response", None), "status_code", None)
            self._challenge(f"HTTP_{status}" if status else "NETWORK_UNAVAILABLE", status)
        return response

    async def search(
        self, entity: ContractingEntity, year: int, *, captcha_token: str | None = None,
    ) -> list[ProcurementSourceRecord]:
        assert self.http is not None
        response = await self._request("GET")
        parser = _JSFParser()
        parser.feed(response.text)
        self.view_state = parser.view_state
        if not self.view_state:
            self._challenge("SESSION_EXPIRED")
        if "recaptcha" in response.text.lower() and not captcha_token:
            self._challenge("CAPTCHA_REQUIRED")
        source = JSF_FORM + ":btnBuscarSel"
        fields = {**parser.fields, JSF_FORM: JSF_FORM,
                  JSF_FORM + ":hddNumeroRuc": entity.ruc,
                  JSF_FORM + ":anioConvocatoria_input": str(year),
                  "javax.faces.partial.ajax": "true", "javax.faces.source": source,
                  "javax.faces.partial.execute": "@all",
                  "javax.faces.partial.render": JSF_FORM + ":pnlGrdResultadosProcesos",
                  "javax.faces.ViewState": self.view_state, "submit": "S"}
        if captcha_token:
            fields[JSF_FORM + ":tokenBusProSel"] = captcha_token
        table_id = JSF_FORM + ":dtProcesos"
        result: list[ProcurementSourceRecord] = []
        offset = 0
        expected: int | None = None
        page_size = 15
        while True:
            fields["javax.faces.ViewState"] = self.view_state
            response = await self._request("POST", data=fields, headers={
                "Faces-Request": "partial/ajax",
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            })
            try:
                root = ET.fromstring(response.text)
            except ET.ParseError:
                self._challenge("SESSION_OR_RESPONSE_INVALID")
            if root.tag != "partial-response" or root.find("redirect") is not None or root.find("error") is not None:
                self._challenge("SESSION_EXPIRED")
            if re.search(r"captcha.{0,80}(?:inval|incorrect|requer)|(?:inval|incorrect).{0,50}captcha", response.text, re.IGNORECASE):
                self._challenge("CAPTCHA_REQUIRED")
            rows: list[dict[str, str]] = []
            table_seen = False
            for update in root.findall("./changes/update"):
                if "javax.faces.ViewState" in update.attrib.get("id", ""):
                    self.view_state = update.text or ""
                else:
                    fragment = _JSFParser()
                    fragment.feed(update.text or "")
                    table_seen |= fragment.table_seen
                    rows.extend(fragment.rows)
                    config = re.search(r'id:"' + re.escape(table_id) + r'",paginator:.*?rows:(\d+),rowCount:(\d+)', update.text or "", re.DOTALL)
                    if config:
                        page_size, expected = map(int, config.groups())
            if not self.view_state or not table_seen:
                self._challenge("SESSION_OR_TABLE_UNAVAILABLE")
            resource = DownloadResource("procedimientos", year, SEACE_PUBLIC_URL)
            result.extend(_source_record(row, entity, resource, "seace_buscador_publico") for row in rows)
            offset += len(rows)
            if expected is None or offset >= expected:
                break
            if not rows or page_size <= 0 or offset > 100_000:
                self._challenge("PAGINATION_INCOMPLETE")
            fields.update({"javax.faces.source": table_id, "javax.faces.partial.execute": table_id,
                           "javax.faces.partial.render": table_id, "javax.faces.behavior.event": "page",
                           table_id + "_pagination": "true", table_id + "_first": str(offset),
                           table_id + "_rows": str(page_size), table_id + "_skipChildren": "true"})
        unique = {record.source_evidence_id: record for record in result}
        if len(unique) != len(result):
            self._challenge("DUPLICATE_PAGE_OR_IDENTITY")
        return list(unique.values())



def link_procurement_evidence(
    records: Sequence[ProcurementSourceRecord], procurements: Sequence[ProcurementRecord],
) -> list[ProcurementSourceRecord]:
    identities: dict[tuple[str, str], str] = {}
    for procurement in procurements:
        process = str(procurement.raw_payload.get("tender", {}).get("id", ""))
        if not process:
            match = re.fullmatch(r"ocds-dgv273-seacev3-(\d+)", procurement.ocid)
            process = match.group(1) if match else ""
        if process:
            key = (procurement.entity_id, process)
            if key in identities and identities[key] != procurement.procurement_id:
                raise ValueError("Identidad de proceso ambigua en OCDS")
            identities[key] = procurement.procurement_id
    result: dict[str, ProcurementSourceRecord] = {}
    for record in records:
        procurement_id = identities.get((record.entity_id, record.official_process_id or ""))
        result[record.source_evidence_id] = record.model_copy(update={"procurement_id": procurement_id})
    return list(result.values())
