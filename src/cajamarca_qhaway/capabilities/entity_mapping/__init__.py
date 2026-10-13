"""`001-entity-mapping` -- universo verificado de entidades contratantes de Cajamarca.

Submodulos:

- `entity_id`: algoritmo determinista de `entity_id` a partir del RUC (RN-001-04).
- `dataset`: carga y valida el dataset versionado `data/entities/*.yaml` (ADR 0006),
  separando el contrato canonico `ContractingEntity` del registro de procedencia.
- `seed`: siembra el dataset validado a la tabla `contracting_entities` de PostgreSQL
  (ADR 0002/0003/0006). Solo este submodulo importa `psycopg` (extra `db`).
"""

from __future__ import annotations

__all__: list[str] = []
