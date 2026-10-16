"""Siembra el universo versionado (`data/entities/*.yaml`) a la tabla PostgreSQL
`contracting_entities` (ADR 0002/0003/0006).

Este es el unico modulo del paquete que importa `psycopg` -- lo hace de forma perezosa,
dentro de `seed_to_postgres`, para que `import cajamarca_qhaway...` siga funcionando en
un entorno sin el extra `db` instalado (p. ej. para correr los tests de `dataset.py` y
`entity_id.py` sin PostgreSQL disponible).

ADR 0006 exige que este paso "falle ruidosamente si detecta una discrepancia entre el
fichero y la tabla" en vez de servir datos desactualizados sin avisar: por eso
`seed_to_postgres` verifica, tras el `COMMIT`, que la tabla tiene exactamente los
`entity_id` del dataset y lanza `SeedVerificationError` si no.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import LiteralString, cast

from cajamarca_qhaway.capabilities.entity_mapping.dataset import Universe, load_universe

DEFAULT_DATASET = Path(__file__).resolve().parents[4] / "data" / "entities" / "cajamarca-universe.yaml"

_UPSERT_SQL = """
INSERT INTO contracting_entities
    (entity_id, official_name, entity_level, province, ruc, consucode_id,
     department, verified_at, active)
VALUES
    (%(entity_id)s, %(official_name)s, %(entity_level)s, %(province)s, %(ruc)s,
     %(consucode_id)s, %(department)s, %(verified_at)s, %(active)s)
ON CONFLICT (entity_id) DO UPDATE SET
    official_name = EXCLUDED.official_name,
    entity_level  = EXCLUDED.entity_level,
    province      = EXCLUDED.province,
    ruc           = EXCLUDED.ruc,
    consucode_id  = EXCLUDED.consucode_id,
    department    = EXCLUDED.department,
    verified_at   = EXCLUDED.verified_at,
    active        = EXCLUDED.active
"""


class SeedVerificationError(RuntimeError):
    """La tabla `contracting_entities` no coincide con el dataset tras la siembra."""


def _rows_from_universe(universe: Universe) -> list[dict[str, object]]:
    return [
        {
            "entity_id": e.entity_id,
            "official_name": e.official_name,
            "entity_level": e.entity_level,
            "province": e.province,
            "ruc": e.ruc,
            "consucode_id": e.consucode_id,
            "department": e.department,
            "verified_at": e.verified_at,
            "active": e.active,
        }
        for e in universe.contracting_entities
    ]


def _mapping_summary(universe: Universe) -> str:
    """Describe the validated SIAF mapping without adding it to the canonical entity row."""
    regional = next(record for record in universe.entities if record.entity.entity_level == "regional")
    provinces = [
        record
        for record in universe.entities
        if record.entity.entity_level == "provincial_municipality"
    ]
    return (
        f"Mapeo oficial validado: GORE PLIEGO {regional.verification.siaf_pliego}; "
        f"{len(provinces)} municipalidades provinciales con SEC_EJEC y UBIGEO únicos."
    )


def seed_to_postgres(dataset_path: Path, dsn: str) -> int:
    """Siembra el dataset a PostgreSQL. Devuelve el numero de filas escritas.

    Lanza `SeedVerificationError` si, tras el commit, el conjunto de `entity_id` de la
    tabla no coincide exactamente con el del dataset (ADR 0006: fallar ruidosamente
    ante una discrepancia fichero/tabla, no servir datos desactualizados en silencio).
    """
    import psycopg  # import perezoso: unico punto del paquete que depende del extra `db`
    from psycopg.sql import SQL

    universe = load_universe(dataset_path)
    rows = _rows_from_universe(universe)
    expected_ids = {entity.entity_id for entity in universe.contracting_entities}

    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            migration_sql = (
                Path(__file__).resolve().parents[4]
                / "scripts"
                / "migrations"
                / "0001_create_contracting_entities.sql"
            ).read_text(encoding="utf-8")
            cur.execute(SQL(cast(LiteralString, migration_sql)))
            cur.executemany(_UPSERT_SQL, rows)
        conn.commit()

        with conn.cursor() as cur:
            cur.execute(
                "SELECT entity_id FROM contracting_entities WHERE entity_id = ANY(%s)",
                (list(expected_ids),),
            )
            found_ids = {r[0] for r in cur.fetchall()}

    missing = expected_ids - found_ids
    if missing:
        raise SeedVerificationError(
            f"Siembra incompleta: {len(missing)} entity_id del dataset no aparecen en "
            f"la tabla tras el commit: {sorted(missing)}"
        )

    return len(rows)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Siembra data/entities/*.yaml a la tabla contracting_entities de PostgreSQL."
    )
    parser.add_argument(
        "--dataset",
        type=Path,
        default=DEFAULT_DATASET,
        help=f"Ruta al YAML del universo (default: {DEFAULT_DATASET})",
    )
    parser.add_argument(
        "--dsn",
        default=os.environ.get("CAJAMARCA_QHAWAY_DATABASE_URL"),
        help="DSN de PostgreSQL. Default: variable de entorno CAJAMARCA_QHAWAY_DATABASE_URL.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Solo valida el dataset (carga + contrato); no se conecta a PostgreSQL.",
    )
    args = parser.parse_args(argv)

    universe = load_universe(args.dataset)
    print(f"Dataset valido: {len(universe.entities)} entidades cargadas de {args.dataset}")
    print(_mapping_summary(universe))

    if args.dry_run:
        print("--dry-run: no se sembro nada a PostgreSQL.")
        return 0

    if not args.dsn:
        print(
            "Error: falta --dsn o la variable de entorno CAJAMARCA_QHAWAY_DATABASE_URL.",
            file=sys.stderr,
        )
        return 2

    try:
        n = seed_to_postgres(args.dataset, args.dsn)
    except ImportError:
        print(
            "Error: falta el extra 'db' (psycopg). Instala con: pip install -e '.[db]'",
            file=sys.stderr,
        )
        return 2
    except SeedVerificationError as exc:
        print(f"Error de verificacion tras la siembra: {exc}", file=sys.stderr)
        return 1

    print(f"Sembradas {n} entidades en contracting_entities.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
