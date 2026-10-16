"""Genera DTO inmutables y schemas empaquetables desde el contrato 011."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "specs/011-deterministic-engine/contracts"
TARGET = ROOT / "src/cajamarca_qhaway/capabilities/deterministic_engine"


def render() -> dict[str, str]:
    request = json.loads((SOURCE / "request.schema.json").read_text(encoding="utf-8"))
    result = json.loads((SOURCE / "result.schema.json").read_text(encoding="utf-8"))
    success, failure = result["oneOf"]
    definitions = {
        "Scope": request["$defs"]["scope"],
        "Evidence": request["$defs"]["evidence"],
        "Award": request["$defs"]["award"],
        "Budget": request["$defs"]["budget"],
        "Observation": request["$defs"]["observation"],
        "Request": request,
        "Rational": result["$defs"]["fraction"],
        "Evaluation": success["properties"]["evaluations"]["items"],
        "Diagnostic": success["properties"]["diagnostics"]["items"],
        "Problem": failure["properties"]["problems"]["items"],
        "BatchResult": success,
        "BatchInvalid": failure,
    }
    named = {id(value): key for key, value in definitions.items()}
    refs = {
        "scope": "Scope",
        "evidence": "Evidence",
        "observation": "Observation",
        "award": "Award",
        "budget": "Budget",
        "fraction": "Rational",
    }

    def annotation(node: dict[str, Any]) -> str:
        if id(node) in named:
            return named[id(node)]
        if "$ref" in node:
            return refs[node["$ref"].split("/")[-1]]
        if "const" in node:
            return f"Literal[{node['const']!r}]"
        if "enum" in node:
            return "Literal[" + ", ".join(repr(v) for v in node["enum"]) + "]"
        if "oneOf" in node or "anyOf" in node:
            return " | ".join(
                annotation(v) for v in node.get("oneOf", node.get("anyOf"))
            )
        kind = node["type"]
        if isinstance(kind, list):
            return " | ".join(annotation({"type": item}) for item in kind)
        if kind == "array":
            return f"tuple[{annotation(node['items'])}, ...]"
        if kind == "object" and set(node["properties"]) == {"numerator", "denominator"}:
            return "Rational"
        return {"string": "str", "integer": "int", "boolean": "bool", "null": "None"}[
            kind
        ]

    lines = [
        '"""Generado por generate-deterministic-contracts.py; editar el schema fuente."""',
        "from __future__ import annotations",
        "",
        "from dataclasses import dataclass",
        "from typing import Literal",
        "",
    ]
    for name, node in definitions.items():
        lines += ["", "@dataclass(frozen=True, slots=True)", f"class {name}:"]
        for field, schema in node["properties"].items():
            lines.append(f"    {field}: {annotation(schema)}")
        lines.append("")
    data = [
        '"""Schemas 011 generados; disponibles en wheels sin acceso al workspace."""',
        "import json",
        "from typing import cast",
        "",
        "from .serialization_types import JSONValue",
        "",
    ]
    for name, schema in (
        ("REQUEST_SCHEMA", request),
        ("RESULT_SCHEMA", result),
        (
            "SHADOW_SCHEMA",
            json.loads((SOURCE / "shadow.schema.json").read_text(encoding="utf-8")),
        ),
    ):
        encoded = json.dumps(schema, ensure_ascii=True, separators=(",", ":"))
        data += [f"{name} = cast(dict[str, JSONValue], json.loads({encoded!r}))", ""]
    return {"contracts.py": "\n".join(lines), "schema_data.py": "\n".join(data)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    TARGET.mkdir(parents=True, exist_ok=True)
    mismatches = []
    for name, content in render().items():
        path = TARGET / name
        if args.check:
            if not path.exists() or path.read_text(encoding="utf-8") != content:
                mismatches.append(name)
        else:
            path.write_text(content, encoding="utf-8", newline="\n")
    if mismatches:
        print("Contratos generados divergentes:", ", ".join(mismatches))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
