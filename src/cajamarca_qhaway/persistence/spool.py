"""Spooler local para almacenamiento temporal atómico ante desconexión de Supabase (Pilar 2)."""

from __future__ import annotations

import json
import os
import uuid
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from cajamarca_qhaway.models import BudgetExecutionRecord, ProcurementRecord


class LocalSpooler:
    """Gestiona el encolado y vaciado seguro de registros en disco."""

    def __init__(self, spool_dir: Path) -> None:
        self.spool_dir = spool_dir
        self.spool_dir.mkdir(parents=True, exist_ok=True)

    def spool_procurements(self, records: Sequence[ProcurementRecord]) -> Path | None:
        """Escribe un lote de contrataciones en un fichero .jsonl atómicamente."""
        if not records:
            return None
        items = [r.model_dump(mode="json") for r in records]
        return self._write_atomic("procurements", items)

    def spool_budget_executions(self, records: Sequence[BudgetExecutionRecord]) -> Path | None:
        """Escribe un lote de ejecuciones en un fichero .jsonl atómicamente."""
        if not records:
            return None
        items = [r.model_dump(mode="json") for r in records]
        return self._write_atomic("budget_executions", items)

    def _write_atomic(self, prefix: str, items: Sequence[dict[str, Any]]) -> Path:
        ts = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        rand_id = uuid.uuid4().hex[:8]
        target_file = self.spool_dir / f"spool_{prefix}_{ts}_{rand_id}.jsonl"
        tmp_file = target_file.with_suffix(f".tmp.{os.getpid()}")

        with open(tmp_file, "w", encoding="utf-8") as f:
            f.writelines(json.dumps(item, ensure_ascii=False) + "\n" for item in items)
            f.flush()
            os.fsync(f.fileno())

        os.replace(tmp_file, target_file)
        return target_file

    def list_pending_files(self) -> list[Path]:
        """Lista ficheros de spool pendientes ordenados por fecha de creación."""
        if not self.spool_dir.exists():
            return []
        files = [p for p in self.spool_dir.glob("spool_*.jsonl") if not p.name.endswith(".tmp")]
        return sorted(files)

    def read_and_remove(self, file_path: Path) -> list[dict[str, Any]]:
        """Lee el contenido de un archivo de spool y lo elimina de forma segura."""
        records: list[dict[str, Any]] = []
        if not file_path.exists():
            return records

        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                stripped = line.strip()
                if stripped:
                    try:
                        records.append(json.loads(stripped))
                    except json.JSONDecodeError:
                        continue

        try:
            file_path.unlink(missing_ok=True)
        except OSError:
            pass

        return records
