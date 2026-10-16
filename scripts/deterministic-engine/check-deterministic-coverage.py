"""Exige todas las ramas de estados y operadores, además del porcentaje global."""

import ast
import json
import sys
from pathlib import Path


def main() -> int:
    data = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    for suffix, function in (("engine.py", "state_for"), ("policy.py", "crossed")):
        candidates = [
            (path, record)
            for path, record in data["files"].items()
            if path.replace("\\", "/").endswith("/deterministic_engine/" + suffix)
        ]
        if len(candidates) != 1:
            return 1
        path, record = candidates[0]
        tree = ast.parse(Path(path).read_text(encoding="utf-8"))
        node = next(
            item
            for item in tree.body
            if isinstance(item, ast.FunctionDef) and item.name == function
        )
        missing = [
            branch
            for branch in record["missing_branches"]
            if node.lineno <= branch[0] <= node.end_lineno
        ]
        executed = [
            branch
            for branch in record["executed_branches"]
            if node.lineno <= branch[0] <= node.end_lineno
        ]
        if missing or not executed:
            print(f"Ramas incompletas: {function}: {missing}")
            return 1
    print("Estados y comparadores: 100% de ramas ejecutadas")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
