"""Captura los maestros completos en staging antes de sustituir datos productivos."""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from cajamarca_qhaway.capabilities.entity_mapping.dataset import load_universe
from cajamarca_qhaway.capabilities.live_harvest.mef_consulta_amigable import (
    MefConsultaAmigableClient,
)


logger = logging.getLogger(__name__)


async def main() -> None:
    entities = [entry.entity for entry in load_universe().entities]
    directory = Path("context/snapshots/mef-v2-staging")
    directory.mkdir(parents=True, exist_ok=True)
    for year in (2026, 2025, 2024):
        path = directory / f"{year}.jsonl"
        if path.exists():
            logger.info("Staging existente: %s", path)
            continue
        async with MefConsultaAmigableClient() as client:
            records = await client.extract_reconciled(year, entities, checkpoint_directory=directory)
        if len(records) != 14 or len({record.entity_id for record in records}) != 14:
            raise ValueError(f"Cobertura institucional incompleta: {year}")
        temporary = path.with_suffix(".jsonl.tmp")
        temporary.write_text("".join(record.model_dump_json() + "\n" for record in records), encoding="utf-8")
        temporary.replace(path)
        logger.info("Maestros reconciliados: %s, %s registros", year, len(records))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)
    asyncio.run(main())
