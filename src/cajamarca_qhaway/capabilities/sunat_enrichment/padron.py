"""Lectura selectiva del padron reducido publicado por SUNAT."""

from __future__ import annotations

from datetime import datetime, timezone
import os
from pathlib import Path
import tempfile
from typing import Iterable
import zipfile

import httpx

from cajamarca_qhaway.capabilities.sunat_enrichment.models import SunatRucProfile
from cajamarca_qhaway.capabilities.sunat_enrichment.validator import assert_constitutional_ruc_only

PADRON_URL = "https://www2.sunat.gob.pe/padron_reducido_ruc.zip"
PADRON_FILENAME = "padron_reducido_ruc.txt"
MAX_ARCHIVE_BYTES = 1_000_000_000


def download_target_profiles(
    target_rucs: Iterable[str],
    public_entity_rucs: Iterable[str] = (),
    retrieved_at: datetime | None = None,
    timeout: httpx.Timeout | None = None,
) -> list[SunatRucProfile]:
    """Descarga a temporal y conserva en memoria solo los RUC solicitados."""
    targets = {assert_constitutional_ruc_only(str(ruc)) for ruc in target_rucs}
    public_rucs = {assert_constitutional_ruc_only(str(ruc)) for ruc in public_entity_rucs}
    if not public_rucs.issubset(targets):
        raise ValueError("Los RUC de entidades publicas deben estar incluidos en el conjunto objetivo")
    if not targets:
        return []

    retrieved = retrieved_at or datetime.now(timezone.utc)
    if retrieved.tzinfo is None:
        retrieved = retrieved.replace(tzinfo=timezone.utc)
    profiles: dict[str, SunatRucProfile] = {}
    temp_path: Path | None = None
    request_timeout = timeout or httpx.Timeout(connect=10.0, read=30.0, write=10.0, pool=10.0)

    try:
        with tempfile.NamedTemporaryFile(prefix="sunat-padron-", suffix=".zip", delete=False) as archive:
            temp_path = Path(archive.name)
            with httpx.stream(
                "GET",
                PADRON_URL,
                follow_redirects=True,
                timeout=request_timeout,
                headers={"Accept": "application/zip", "User-Agent": "CajamarcaQhaway-Harvester/1.0"},
            ) as response:
                response.raise_for_status()
                content_length = response.headers.get("content-length")
                if content_length and int(content_length) > MAX_ARCHIVE_BYTES:
                    raise ValueError("El archivo oficial excede el limite configurado de descarga temporal")
                downloaded = 0
                for chunk in response.iter_bytes(chunk_size=1024 * 1024):
                    downloaded += len(chunk)
                    if downloaded > MAX_ARCHIVE_BYTES:
                        raise ValueError("El archivo oficial excede el limite configurado de descarga temporal")
                    archive.write(chunk)
                archive.flush()
                os.fsync(archive.fileno())
                last_modified = response.headers.get("last-modified")

        with zipfile.ZipFile(temp_path) as zipped:
            try:
                member = zipped.getinfo(PADRON_FILENAME)
            except KeyError as exc:
                raise ValueError(f"El ZIP oficial no contiene {PADRON_FILENAME}") from exc
            with zipped.open(member) as binary_stream:
                header_line = binary_stream.readline()
                header_text = header_line.rstrip(b"\r\n").decode("cp1252", errors="strict") if header_line else ""
                if header_text.endswith("|"):
                    header_text = header_text[:-1]
                headers = header_text.split("|") if header_text else []
                if not headers or any(not header for header in headers):
                    raise ValueError("El padrón oficial no contiene encabezados")
                indexes = {header.strip().upper(): index for index, header in enumerate(headers)}
                required_columns = {"RUC", "NOMBRE O RAZÓN SOCIAL", "ESTADO DEL CONTRIBUYENTE", "CONDICIÓN DE DOMICILIO", "UBIGEO"}
                missing = required_columns.difference(indexes)
                if missing:
                    raise ValueError(f"Faltan columnas oficiales requeridas: {sorted(missing)}")

                for source_line_bytes in binary_stream:
                    raw_line_bytes = source_line_bytes.rstrip(b"\r\n")
                    columns = raw_line_bytes[:-1].split(b"|") if raw_line_bytes.endswith(b"|") else raw_line_bytes.split(b"|")
                    if len(columns) != len(headers):
                        continue
                    try:
                        ruc = columns[indexes["RUC"]].decode("ascii").strip()
                    except UnicodeDecodeError:
                        continue
                    if ruc not in targets:
                        continue
                    values = [column.decode("cp1252", errors="replace") for column in columns]
                    raw_fields = dict(zip(headers, values, strict=True))
                    address_fields = (
                        "TIPO DE VÍA", "NOMBRE DE VÍA", "CÓDIGO DE ZONA", "TIPO DE ZONA",
                        "NÚMERO", "INTERIOR", "LOTE", "DEPARTAMENTO", "MANZANA", "KILÓMETRO",
                    )
                    address = " ".join(raw_fields[name].strip() for name in address_fields if name in raw_fields and raw_fields[name].strip() not in ("", "-"))
                    profiles[ruc] = SunatRucProfile(
                        ruc=ruc,
                        razon_social=values[indexes["NOMBRE O RAZÓN SOCIAL"]].strip(),
                        estado_contribuyente=values[indexes["ESTADO DEL CONTRIBUYENTE"]].strip().upper(),
                        condicion_domicilio=values[indexes["CONDICIÓN DE DOMICILIO"]].strip().upper(),
                        direccion_fiscal=address or None,
                        ubigeo=values[indexes["UBIGEO"]].strip() or None,
                        es_entidad_publica=ruc in public_rucs,
                        source_provider="sunat_padron_reducido",
                        queried_at=retrieved.isoformat(),
                        raw_payload={
                            "source_url": PADRON_URL,
                            "source_file": member.filename,
                            "source_last_modified": last_modified,
                            "source_headers": headers,
                            "source_values": values,
                            "source_row_hex": raw_line_bytes.hex(),
                        },
                    )
                    if len(profiles) == len(targets):
                        break
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)

    return [profiles[ruc] for ruc in sorted(profiles)]
