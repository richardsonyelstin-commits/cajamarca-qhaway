"""Verifica la paridad productiva y la publicacion de activos sin consultar secretos."""

from __future__ import annotations

import asyncio
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import httpx

from cajamarca_qhaway.models import BudgetExecutionRecord, ProcurementRecord

BASE_URL = "https://cajamarca-qhaway.vercel.app"


async def main() -> None:
    path = Path("web/src/data/verified-snapshot.json")
    expected = json.loads(path.read_text(encoding="utf-8"))
    async with httpx.AsyncClient(timeout=60, follow_redirects=True) as client:
        static = await client.get(BASE_URL + "/src/data/verified-snapshot.json")
        static.raise_for_status()
        if static.content != path.read_bytes():
            raise ValueError("El snapshot desplegado no coincide byte a byte con el commit local")
        response = await client.get(BASE_URL + "/api/snapshot")
        response.raise_for_status()
        actual = response.json()
        budgets = {row["execution_record_id"]: BudgetExecutionRecord.model_validate(row)
                   for row in actual["budget_execution_records"]}
        for row in expected["budget_execution_records"]:
            if budgets.get(row["execution_record_id"]) != BudgetExecutionRecord.model_validate(row):
                raise ValueError("Diferencia de presupuesto entre API y snapshot")
        procurements = {row["procurement_id"]: ProcurementRecord.model_validate(row)
                        for row in actual["procurement_records"]}
        for row in expected["procurement_records"]:
            if procurements.get(row["procurement_id"]) != ProcurementRecord.model_validate(row):
                raise ValueError("Diferencia de contratacion entre API y snapshot")
        if len(budgets) != 42 or len(procurements) != 475:
            raise ValueError("Cobertura productiva distinta del universo verificado")
        if actual.get("red_flags") or actual.get("citizen_reports") or actual.get("alerts"):
            raise ValueError("El snapshot publico contiene filas privadas o publicaciones inesperadas")
        routes = ["/", "/entidades", "/entidad?id=ce-f5f5d8fc32518855", "/alertas",
                  "/contrataciones", "/contrato?id=" + expected["procurement_records"][0]["procurement_id"],
                  "/presupuesto", "/proveedores", "/concentracion", "/georreferenciacion",
                  "/denuncia", "/admin/revision", "/login", "/transparencia", "/acerca", "/metodologia"]
        route_checks = []
        semaphore = asyncio.Semaphore(4)
        async def page(route: str) -> dict:
            async with semaphore:
                result = await client.get(BASE_URL + route)
                result.raise_for_status()
                if "/css/tokens.css" not in result.text or "2026-10-14" not in result.text:
                    raise ValueError("La pagina no tiene identidad o corte oficial prerenderizado")
                if result.headers.get("x-content-type-options") != "nosniff":
                    raise ValueError("Falta la cabecera de contenido seguro")
                return {"route": route, "status": result.status_code}
        route_checks = await asyncio.gather(*(page(route) for route in routes))
        assets = ["/css/tokens.css", "/css/fonts.css", "/css/brand.css", "/css/application.css",
                  "/fonts/PublicSans-variable.woff2", "/fonts/Fraunces-titulos.woff2",
                  "/fonts/JetBrainsMono-variable.woff2", "/media/logo/logo-horizontal-negativo.svg",
                  "/favicon.ico", "/site.webmanifest"]
        for asset in assets:
            result = await client.get(BASE_URL + asset)
            result.raise_for_status()
            local = Path("web" + asset).read_bytes()
            remote = result.content
            if asset.endswith((".css", ".svg", ".webmanifest")):
                local, remote = local.replace(b"\r\n", b"\n"), remote.replace(b"\r\n", b"\n")
            if local != remote:
                raise ValueError("Activo productivo diferente del activo local verificado")
        boundary = await client.get(BASE_URL + "/context/snapshots/mef-v2-staging/flags-0.sql")
        if boundary.status_code != 404:
            raise ValueError("El staging operativo resulta publicamente accesible")
    evidence = {"source": "ai", "generator": "codex-gpt-6.1-sol",
                "generated_at": datetime.now(UTC).isoformat(), "confidence": "high", "verified": False,
                "base_url": BASE_URL, "snapshot_sha256": hashlib.sha256(static.content).hexdigest(),
                "budget_records_equal": len(budgets), "procurement_records_equal": len(procurements),
                "routes": route_checks, "assets_equal": len(assets), "staging_status": boundary.status_code}
    Path("context/snapshots/2026-10-15-production-budget-check.json").write_text(
        json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in evidence.items() if key not in ("routes",)}))


if __name__ == "__main__":
    asyncio.run(main())
