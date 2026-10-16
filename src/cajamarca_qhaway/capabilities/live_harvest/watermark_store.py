"""Almacenamiento y persistencia atomica de marcas de agua (WatermarkStore).

Implementa Two-Phase Write con fichero temporal y `os.replace` para garantizar
resiliencia ante caidas abruptas o cortes de suministro tanto en Linux como en Windows.
"""

from __future__ import annotations

import json
import os
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


@dataclass
class WatermarkData:
    """Estado persistente del cursor de recoleccion continua."""

    last_seace_timestamp: datetime | None = None
    seen_seace_ocids: set[str] = field(default_factory=set)
    last_mef_timestamp: datetime | None = None
    last_mef_offset: int = 0
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def to_dict(self) -> dict[str, Any]:
        return {
            "last_seace_timestamp": self.last_seace_timestamp.isoformat() if self.last_seace_timestamp else None,
            "seen_seace_ocids": sorted(self.seen_seace_ocids),
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

        updated_at = datetime.now(UTC)
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

    def __init__(self, file_path: Path, db_manager: Any = None) -> None:
        self.file_path = file_path
        self.db = db_manager
        self._state: WatermarkData = self._load()

    @property
    def state(self) -> WatermarkData:
        return self._state

    def _load(self) -> WatermarkData:
        if self.db is not None and getattr(self.db, "is_postgres", False):
            with self.db.connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT source_name, last_timestamp, last_offset, seen_ids, updated_at FROM harvest_watermarks"
                )
                rows = cursor.fetchall()
                data: dict[str, Any] = {}
                for row in rows:
                    source = row["source_name"]
                    timestamp = row["last_timestamp"]
                    timestamp_text = (
                        timestamp.isoformat()
                        if hasattr(timestamp, "isoformat")
                        else (str(timestamp) if timestamp else None)
                    )
                    if source == "seace":
                        data["last_seace_timestamp"] = timestamp_text
                        seen_ids = row["seen_ids"]
                        if isinstance(seen_ids, str):
                            data["seen_seace_ocids"] = json.loads(seen_ids)
                        elif isinstance(seen_ids, (list, tuple)):
                            data["seen_seace_ocids"] = list(seen_ids)
                    elif source == "mef":
                        data["last_mef_timestamp"] = timestamp_text
                        data["last_mef_offset"] = int(row["last_offset"] or 0)
                    updated_at = row["updated_at"]
                    if updated_at:
                        data["updated_at"] = (
                            updated_at.isoformat() if hasattr(updated_at, "isoformat") else str(updated_at)
                        )
                return WatermarkData.from_dict(data)

        if not self.file_path.exists():
            return WatermarkData()
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return WatermarkData.from_dict(data)
        except (json.JSONDecodeError, OSError):
            return WatermarkData()

    def save_atomic(self) -> None:
        """Escribe atomicamente el estado a disco y a PostgreSQL si esta disponible."""
        self._state.updated_at = datetime.now(UTC)
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = self.file_path.with_suffix(f".tmp.{os.getpid()}")

        payload = self._state.to_dict()
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
            f.flush()
            os.fsync(f.fileno())

        # En Windows os.replace reemplaza atómicamente si el archivo destino existe
        os.replace(tmp_path, self.file_path)

        if self.db is not None and getattr(self.db, "is_postgres", False):
            with self.db.connection() as conn:
                cursor = conn.cursor()
                seace_sql = """
                    INSERT INTO harvest_watermarks
                        (source_name, last_timestamp, last_offset, seen_ids, updated_at)
                    VALUES
                        ('seace', ?, 0, ?, ?)
                    ON CONFLICT (source_name) DO UPDATE SET
                        last_timestamp = excluded.last_timestamp,
                        seen_ids = excluded.seen_ids,
                        updated_at = excluded.updated_at
                """
                seace_ts = (
                    self._state.last_seace_timestamp.isoformat()
                    if self._state.last_seace_timestamp
                    else None
                )
                seace_seen = json.dumps(sorted(self._state.seen_seace_ocids))
                cursor.execute(
                    seace_sql,
                    (seace_ts, seace_seen, self._state.updated_at.isoformat()),
                )

                mef_sql = """
                    INSERT INTO harvest_watermarks
                        (source_name, last_timestamp, last_offset, seen_ids, updated_at)
                    VALUES
                        ('mef', ?, ?, '[]', ?)
                    ON CONFLICT (source_name) DO UPDATE SET
                        last_timestamp = excluded.last_timestamp,
                        last_offset = excluded.last_offset,
                        updated_at = excluded.updated_at
                """
                mef_ts = (
                    self._state.last_mef_timestamp.isoformat()
                    if self._state.last_mef_timestamp
                    else None
                )
                cursor.execute(
                    mef_sql,
                    (mef_ts, self._state.last_mef_offset, self._state.updated_at.isoformat()),
                )
                conn.commit()

    def is_seace_ocid_seen(self, ocid: str) -> bool:
        return ocid in self._state.seen_seace_ocids

    def update_seace_cursor(self, timestamp: datetime, new_ocids: Sequence[str]) -> None:
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=UTC)
        self._state.last_seace_timestamp = timestamp
        self._state.seen_seace_ocids.update(new_ocids)
        self.save_atomic()

    def update_mef_cursor(self, timestamp: datetime, offset: int) -> None:
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=UTC)
        self._state.last_mef_timestamp = timestamp
        self._state.last_mef_offset = offset
        self.save_atomic()
