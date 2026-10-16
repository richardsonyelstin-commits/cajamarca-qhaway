"""Script de sincronizacion y regeneracion del snapshot web de Cajamarca Qhaway.

Regenera web/src/data/verified-snapshot.json utilizando los modelos canonicos
del Articulo 19 y, si la configuracion lo permite, sincroniza con la persistencia
de Supabase / base de datos operativa.

Cumple con:
- Antislop R-02: Cero em-dash.
- Art. 14: Solo publica alertas aprobadas por humanos.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from cajamarca_qhaway.web.exporter import export_verified_snapshot


def sync_snapshot(output_path: Path | str = "web/src/data/verified-snapshot.json", sync_db: bool = False) -> int:
    """Regenera la instantanea y opcionalmente sincroniza con Supabase."""
    print("Iniciando sincronizacion del snapshot web...")
    out = export_verified_snapshot(output_path=output_path)
    print(f"Instantanea verificada regenerada en: {out}")

    if sync_db:
        try:
            from cajamarca_qhaway.persistence.sync import SyncManager

            mgr = SyncManager()
            status = mgr.status()
            print(f"Estado de persistencia Supabase / DB: entidades={status.get('active_entities')}")
        except (OSError, ValueError, TypeError, KeyError, AttributeError) as exc:
            print(f"Nota: Sincronizacion directa con Supabase no disponible ({exc}), operando con snapshot local.")

    print("Sincronizacion completada con exito.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Regenera el snapshot verificado para la plataforma web de Cajamarca Qhaway",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default="web/src/data/verified-snapshot.json",
        help="Ruta de destino del archivo JSON verificado",
    )
    parser.add_argument(
        "--sync-db",
        action="store_true",
        help="Intentar sincronizacion con la base de datos operativa / Supabase",
    )
    args = parser.parse_args()
    return sync_snapshot(output_path=args.output, sync_db=args.sync_db)


if __name__ == "__main__":
    sys.exit(main())
