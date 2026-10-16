"""Protocolos e interfaces base para repositorios de persistencia (Pilar 2)."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, TypeVar

T = TypeVar("T")


class Repository(Protocol[T]):
    """Interfaz canónica para repositorios de entidades de Cajamarca Qhaway."""

    def get_by_id(self, record_id: str) -> T | None:
        ...

    def upsert(self, entity: T) -> None:
        ...

    def upsert_many(self, entities: Sequence[T]) -> int:
        ...
