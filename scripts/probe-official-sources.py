"""Sondea los documentos oficiales sin conservar cookies ni tokens de sesion."""

from __future__ import annotations

import asyncio
import json
from datetime import UTC, datetime
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin

import httpx

from cajamarca_qhaway.capabilities.live_harvest.mef_consulta_amigable import (
    _official_cut_date,
    _parse_page,
)


class ProbeParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.inputs: list[dict[str, str]] = []
        self.forms: list[dict[str, str]] = []
        self.links: list[str] = []
        self.text: list[str] = []
        self.options: list[dict[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        a = {k: v or "" for k, v in attrs}
        if tag == "input":
            self.inputs.append({k: a.get(k, "") for k in ("name", "id", "type")})
        elif tag == "form":
            self.forms.append({
                "id": a.get("id", ""), "method": a.get("method", ""),
                "action": a.get("action", "").split(";", 1)[0],
            })
        elif tag == "option":
            self.options.append({k: a.get(k, "") for k in ("value", "selected")})
        if tag in ("a", "script", "iframe"):
            link = a.get("href") or a.get("src")
            if link and not link.startswith(("javascript:", "data:")):
                self.links.append(link)

    def handle_data(self, data: str) -> None:
        self.text.append(data)


async def probe(url: str, semaphore: asyncio.Semaphore) -> dict[str, object]:
    async with semaphore, httpx.AsyncClient(
        timeout=45,
        follow_redirects=True,
        headers={"User-Agent": "CajamarcaQhaway-Harvester/1.0"},
    ) as client:
        try:
            response = await client.get(url)
            parser = ProbeParser()
            parser.feed(response.text)
            page = _parse_page(response.text)
            text = " ".join(" ".join(parser.text).split())
            result: dict[str, object] = {
                "url": url,
                "status": response.status_code,
                "final_url": str(response.url),
                "content_type": response.headers.get("content-type"),
                "bytes": len(response.content),
                "session_cookie_present": any("session" in k.lower() for k in client.cookies),
                "official_cut_date": _official_cut_date(response.text),
                "forms": parser.forms,
                "inputs": parser.inputs,
                "options": parser.options,
                "buttons": page.buttons,
                "selected": page.selects,
                "first_rows": [{"label": r.label, "cells": r.cells} for r in page.rows[:4]],
                "resources": sorted({urljoin(str(response.url), x) for x in parser.links}),
                "captcha_marker": "captcha" in text.lower(),
                "view_state_present": "javax.faces.ViewState" in response.text,
            }
            print(json.dumps({k: result[k] for k in (
                "url", "status", "bytes", "official_cut_date", "selected",
                "captcha_marker", "view_state_present",
            )}, ensure_ascii=True), flush=True)
            return result
        except httpx.HTTPError as error:
            result = {"url": url, "error_type": type(error).__name__}
            print(json.dumps(result), flush=True)
            return result


async def main() -> None:
    urls = [
        f"https://apps5.mineco.gob.pe/transparencia/{module}/Navegar_6.aspx?y={year}&ap={scope}"
        for module in ("Navegador", "Mensual")
        for year in (2024, 2025, 2026)
        for scope in ("ActProy", "Proyecto", "Actividad")
    ]
    urls.extend([
        "https://bi.seace.gob.pe/pentaho/api/repos/%3Apublic%3Aportal%3Adatosabiertos.html/content?userid=public&password=key",
        "https://prod2.seace.gob.pe/seacebus-uiwd-pub/buscadorPublico/buscadorPublico.xhtml",
    ])
    semaphore = asyncio.Semaphore(2)
    results = await asyncio.gather(*(probe(url, semaphore) for url in urls))
    output = Path("context/snapshots/2026-10-15-official-source-probe.json")
    output.write_text(json.dumps({
        "source": "ai", "generator": "codex", "verified": False,
        "retrieved_at": datetime.now(UTC).isoformat(), "results": results,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    asyncio.run(main())
