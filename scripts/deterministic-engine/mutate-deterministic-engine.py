"""Ejecuta quince mutantes semánticos en copias temporales aisladas del paquete."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CORE = "capabilities/deterministic_engine/"
MUTANTS = [
    ("share-inclusive", CORE + "policy.py", '2, 5, "gt"', '2, 5, "ge"'),
    ("above-inclusive", CORE + "policy.py", '11, 10, "gt"', '11, 10, "ge"'),
    ("hhi-exclusive", CORE + "policy.py", '2500, 1, "ge"', '2500, 1, "gt"'),
    ("unspent-exclusive", CORE + "policy.py", '1, 2, "ge"', '1, 2, "gt"'),
    ("recurrence-exclusive", CORE + "policy.py", '3, 1, "ge"', '3, 1, "gt"'),
    ("bidder-greater-equal", CORE + "policy.py", '1, 1, "eq"', '1, 1, "ge"'),
    (
        "inclusive-end",
        CORE + "engine.py",
        "scope.start <= f.event_at < scope.end",
        "scope.start <= f.event_at <= scope.end",
    ),
    (
        "count-awards",
        CORE + "engine.py",
        "processes[f.supplier_ruc].add(f.process_id)",
        "processes[f.supplier_ruc].add(str(len(processes[f.supplier_ruc])))",
    ),
    (
        "float-money",
        CORE + "policy.py",
        'int(value.replace(".", ""))',
        "int(float(value) * 100)",
    ),
    (
        "missing-ruc-fallback",
        CORE + "engine.py",
        'f.supplier_ruc is None and f.supplier_allocation == "single"',
        "False",
    ),
    (
        "oldest-revision",
        CORE + "engine.py",
        "revision > latest[source, key].revision",
        "revision < latest[source, key].revision",
    ),
    (
        "partition-summed",
        CORE + "engine.py",
        'f.dimensions != "institution-total"',
        "False",
    ),
    (
        "missing-count",
        CORE + "engine.py",
        'scope.coverage != "complete" or scope.expected_count is None',
        'scope.coverage != "complete"',
    ),
    (
        "null-zero",
        CORE + "engine.py",
        'return stop("MISSING_FIELD")',
        'return "THRESHOLD_NOT_MATCH", ratio(0, 1), ratio(rule.numerator, rule.denominator)',
    ),
    (
        "legacy-approval",
        "deterministic_shadow.py",
        '"promotion": "disabled",',
        '"promotion": "disabled", "approved": True,',
    ),
]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    results = []
    for name, relative, old, new in MUTANTS:
        with tempfile.TemporaryDirectory(prefix="qhaway-mutant-") as folder:
            base = Path(folder)
            package = base / "cajamarca_qhaway"
            shutil.copytree(
                ROOT / "src/cajamarca_qhaway/capabilities/deterministic_engine",
                package / "capabilities/deterministic_engine",
            )
            (package / "__init__.py").write_text("")
            (package / "capabilities/__init__.py").write_text("")
            for module in ("deterministic_shadow.py", "deterministic_cli.py"):
                shutil.copy2(ROOT / "src/cajamarca_qhaway" / module, package / module)
            target = package / relative
            source = target.read_text(encoding="utf-8")
            if old not in source:
                raise RuntimeError(f"Mutante sin destino: {name}")
            target.write_text(source.replace(old, new), encoding="utf-8")
            process = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pytest",
                    str(ROOT / "tests/deterministic_engine"),
                    "-q",
                    "-x",
                    "--confcutdir",
                    str(ROOT / "tests/deterministic_engine"),
                    "--import-mode=importlib",
                    "-o",
                    f"pythonpath={base}",
                    "-k",
                    "not subprocesses and not pure_execution and not normalized_permutations",
                ],
                cwd=base,
                env={**os.environ, "PYTHONPATH": str(base), "PYTHONUTF8": "1"},
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            killed = (
                process.returncode == 1
                and "failed" in process.stdout
                and "ERROR collecting" not in process.stdout
            )
            results.append(
                {
                    "name": name,
                    "killed": killed,
                    "exit_code": process.returncode,
                    "summary": process.stdout.splitlines()[-1:],
                    "stderr": process.stderr[-2000:],
                }
            )
            print(json.dumps(results[-1]), flush=True)
    args.output.write_text(
        json.dumps(
            {
                "source": "ai",
                "generator": "codex",
                "generated_at": datetime.now(UTC).isoformat(),
                "confidence": "high",
                "baseline_commit": subprocess.run(
                    ["git", "rev-parse", "HEAD"],
                    cwd=ROOT,
                    capture_output=True,
                    text=True,
                    check=True,
                ).stdout.strip(),
                "worktree_dirty": True,
                "verified": False,
                "mutants": results,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return 0 if all(row["killed"] for row in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
