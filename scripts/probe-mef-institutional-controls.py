"""Extrae el cuadro institucional diario para contrastarlo con el corte mensual."""

from __future__ import annotations

import asyncio
from pathlib import Path

from cajamarca_qhaway.capabilities.entity_mapping.dataset import load_universe
from cajamarca_qhaway.capabilities.live_harvest.mef_consulta_amigable import (
    MefConsultaAmigableClient,
)


class DailyProbeClient(MefConsultaAmigableClient):
    async def _get(self, year: int) -> tuple[str, str]:
        assert self._client is not None
        url = f"https://apps5.mineco.gob.pe/transparencia/Navegador/Navegar_6.aspx?y={year}&ap=ActProy"
        response = await self._client.get(url)
        response.raise_for_status()
        return response.text, str(response.url)


async def extract_year(year: int) -> None:
    entities = [entry.entity for entry in load_universe().entities]
    async with DailyProbeClient() as client:
        records = await client.extract(year, entities)
    assert len(records) == 14
    path = Path(f"context/snapshots/2026-10-15-mef-daily-{year}.jsonl")
    path.write_text("".join(r.model_dump_json() + "\n" for r in records), encoding="utf-8")
    print({"year": year, "entities": len(records),
           "pim": sum(r.budgeted_amount for r in records),
           "devengado": sum(r.executed_amount for r in records)}, flush=True)


async def main() -> None:
    for year in (2024, 2025, 2026):
        await extract_year(year)


if __name__ == "__main__":
    asyncio.run(main())
