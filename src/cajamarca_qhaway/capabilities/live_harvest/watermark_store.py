"""Almacenamiento y persistencia atomica de marcas de agua (WatermarkStore).

Implementa Two-Phase Write con fichero temporal y `os.replace` para garantizar
resiliencia ante caidas abruptas o cortes de suministro tanto en Linux como en Windows.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence


@dataclass
class WatermarkData:
    """Estado persistente del cursor de recoleccion continua."""

    last_seace_timestamp: datetime | None = None
    seen_seace_ocids: set[str] = field(default_factory=set)
    last_mef_timestamp: datetime | None = None
    last_mef_offset: int = 0
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        return {
            "last_seace_timestamp": self.last_seace_timestamp.isoformat() if self.last_seace_timestamp else None,
            "seen_seace_ocids": sorted(list(self.seen_seace_ocids)),
            "last_mef_timestamp": self.last_mef_timestamp.isoformat() if self.last_mef_timestamp else None,
            "last_mef_offset": self.last_mef_offset,
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> WatermarkData:
        last_seace = None
        if data.get("last_seace_timestamp"):
            try:
                last_seace = datetime.fromisoformat(data["last_seace_timestamp"])
            except ValueError:
                pass

        last_mef = None
        if data.get("last_mef_timestamp"):
            try:
                last_mef = datetime.fromisoformat(data["last_mef_timestamp"])
            except ValueError:
                pass

        updated_at = datetime.now(timezone.utc)
        if data.get("updated_at"):
            try:
                updated_at = datetime.fromisoformat(data["updated_at"])
            except ValueError:
                pass

        seen = set(data.get("seen_seace_ocids", []))
        offset = int(data.get("last_mef_offset", 0))

        return cls(
            last_seace_timestamp=last_seace,
            seen_seace_ocids=seen,
            last_mef_timestamp=last_mef,
            last_mef_offset=offset,
            updated_at=updated_at,
        )


class WatermarkStore:
    """Gestor de persistencia transaccional del cursor de cosecha."""

    def __init__(self, file_path: Path) -> None:
        self.file_path = file_path
        self._state: WatermarkData = self._load()

    @property
    def state(self) -> WatermarkData:
        return self._state

    def _load(self) -> WatermarkData:
        if not self.file_path.exists():
            return WatermarkData()
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return WatermarkData.from_dict(data)
        except (json.JSONDecodeError, OSError):
            return WatermarkData()

    def save_atomic(self) -> None:
        """Escribe atomicamente el estado a disco.

        Cierra el archivo antes de llamar a `os.replace` para evitar errores
        de bloqueo en sistemas Windows (WinError 32).
        """
        self._state.updated_at = datetime.now(timezone.utc)
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = self.file_path.with_suffix(f".tmp.{os.getpid()}")

        payload = self._state.to_dict()
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
            f.flush()
            os.fsync(f.fileno())

        # En Windows os.replace reemplaza atómicamente si el archivo destino existe
        os.replace(tmp_path, self.file_path)

    def is_seace_ocid_seen(self, ocid: str) -> bool:
        return ocid in self._state.seen_seace_ocids

    def update_seace_cursor(self, timestamp: datetime, new_ocids: Sequence[str]) -> None:
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)
        self._state.last_seace_timestamp = timestamp
        self._state.seen_seace_ocids.update(new_ocids)
        self.save_atomic()

    def update_mef_cursor(self, timestamp: datetime, offset: int) -> None:
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)
        self._state.last_mef_timestamp = timestamp
        self._state.last_mef_offset = offset
        self.save_atomic()
