"""CLI privada 011: archivos explícitos y salida exclusiva sin sobrescritura."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .capabilities.deterministic_engine import evaluate_json
from .deterministic_shadow import MigrationBlocked, shadow_report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Evaluación privada determinista 011")
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument(
        "--shadow-payloads",
        type=Path,
        help="Mapa JSON evidence_id a archivo preservado",
    )
    args = parser.parse_args(argv)
    try:
        raw = args.input.read_bytes()
        if args.shadow_payloads is None:
            result = evaluate_json(raw)
        else:
            manifest = json.loads(args.shadow_payloads.read_bytes())
            payloads = {
                key: (args.shadow_payloads.parent / value).read_bytes()
                for key, value in manifest.items()
            }
            result = shadow_report(json.loads(raw), payloads)
        with args.output.open("xb") as output:
            output.write(result)
        return 0 if json.loads(result).get("kind") != "BatchInvalid" else 2
    except (OSError, ValueError, MigrationBlocked):
        print(
            "No se generó la salida: entrada inválida, evidencia insuficiente o destino existente.",
            file=sys.stderr,
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
