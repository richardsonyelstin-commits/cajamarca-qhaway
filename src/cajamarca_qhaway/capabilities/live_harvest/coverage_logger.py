"""Bitacora de auditoria de ventanas de cobertura y registro de incidentes de red (CoverageGapLogger).

Cumple estrictamente con RN-002-06, RN-002-07, RN-003-06, CA-002-06, CA-002-07 y CA-003-05
declarando las ventanas temporales reales muestreadas e impidiendo el silenciamiento de errores.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


class CoverageGapLogger:
    """Registrador append-only de eventos de cobertura e incidentes de red."""

    def __init__(self, log_path: Path) -> None:
        self.log_path = log_path

    def _append(self, record: dict[str, Any]) -> None:
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps(record, ensure_ascii=False) + "\n"
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(line)

    def log_window(
        self,
        source: str,
        start_time: datetime,
        end_time: datetime,
        items_received: int,
        items_retained: int,
        status: str = "OK",
        notes: str | None = None,
    ) -> dict[str, Any]:
        """Registra la ventana de tiempo real muestreada (RN-002-06)."""
        if start_time.tzinfo is None:
            start_time = start_time.replace(tzinfo=UTC)
        if end_time.tzinfo is None:
            end_time = end_time.replace(tzinfo=UTC)

        record = {
            "type": "coverage_window",
            "source": source,
            "logged_at": datetime.now(UTC).isoformat(),
            "window_start": start_time.isoformat(),
            "window_end": end_time.isoformat(),
            "items_received": items_received,
            "items_retained": items_retained,
            "status": status,
            "notes": notes,
        }
        self._append(record)
        return record

    def log_incident(
        self,
        source: str,
        attempt: int,
        status_code: int | None,
        endpoint: str,
        error_message: str,
    ) -> dict[str, Any]:
        """Registra un fallo de red o caida de servicio como brecha de cobertura (RN-002-07, RN-003-06)."""
        record = {
            "type": "coverage_gap_incident",
            "source": source,
            "logged_at": datetime.now(UTC).isoformat(),
            "attempt": attempt,
            "status_code": status_code,
            "endpoint": endpoint,
            "error_message": error_message,
        }
        self._append(record)
        return record

    def read_records(self, record_type: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
        """Lee los ultimos registros del log."""
        if not self.log_path.exists():
            return []
        results: list[dict[str, Any]] = []
        try:
            with open(self.log_path, "r", encoding="utf-8") as f:
                for line in f:
                    stripped = line.strip()
                    if not stripped:
                        continue
                    try:
                        entry = json.loads(stripped)
                        if record_type is None or entry.get("type") == record_type:
                            results.append(entry)
                    except json.JSONDecodeError:
                        continue
        except OSError:
            return []
        return results[-limit:]
