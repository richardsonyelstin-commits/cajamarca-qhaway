#!/usr/bin/env python3
"""Punto de entrada de operador para sembrar el universo a PostgreSQL.

Uso:
    python scripts/seed_contracting_entities.py --dry-run
    CAJAMARCA_QHAWAY_DATABASE_URL=postgresql://... python scripts/seed_contracting_entities.py

La logica vive en `cajamarca_qhaway.capabilities.entity_mapping.seed`; este fichero
solo existe para que el comando sea descubrible desde `scripts/`, igual que
`scripts/verification/probe-oece-ocds.sh`.

source: ai | generator: claude-sonnet-5 | generated_at: 2026-08-20T00:00:00Z
confidence: medium | verified: false
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from cajamarca_qhaway.capabilities.entity_mapping.seed import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
