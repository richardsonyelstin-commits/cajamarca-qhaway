"""Benchmark sintético local: núcleo tipado separado de la frontera de bytes."""

from __future__ import annotations

import argparse
import gc
import json
import os
import platform
import statistics
import subprocess
import time
import tracemalloc
from dataclasses import replace
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path

from cajamarca_qhaway.capabilities.deterministic_engine import evaluate
from cajamarca_qhaway.capabilities.deterministic_engine.boundary import decode_request
from cajamarca_qhaway.capabilities.deterministic_engine.contracts import Request
from cajamarca_qhaway.capabilities.deterministic_engine.serialization import (
    canonical_bytes,
    object_document,
)

ROOT = Path(__file__).resolve().parents[2]


def corpus(count: int) -> Request:
    template = json.loads(
        (
            ROOT / "specs/011-deterministic-engine/fixtures/golden-vectors.json"
        ).read_text(encoding="utf-8")
    )["vectors"][0]["input"]
    request = decode_request(json.dumps(template).encode())
    if not isinstance(request, Request):
        raise TypeError("Fixture inválida")
    number_scopes = count // 100
    scopes = tuple(
        replace(
            request.scopes[0],
            scope_id=f"scope-{i:04}",
            expected_count=100,
            coverage_evidence_id="e-000000",
            rules=("contract-share", "hhi", "recurrent-direct"),
        )
        for i in range(number_scopes)
    )
    evidence = tuple(
        replace(request.evidence[1], evidence_id=f"e-{i:06}") for i in range(count)
    )
    rows = tuple(
        replace(
            request.observations[0],
            scope_id=f"scope-{i // 100:04}",
            record_key=f"r-{i:06}",
            evidence_ids=(f"e-{i:06}",),
            fact=replace(
                request.observations[0].fact, process_id=f"p-{i:06}", method="direct"
            ),
        )
        for i in range(count)
    )
    scopes = tuple(replace(s, rules=("single-bidder", *s.rules)) for s in scopes)
    return replace(request, scopes=scopes, evidence=evidence, observations=rows)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--runs", type=int, default=5)
    args = parser.parse_args()
    report = {
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
        "python": platform.python_version(),
        "platform": platform.platform(),
        "logical_cpus": os.cpu_count(),
        "reference_host_certified": False,
        "seed": 20261015,
        "results": [],
    }
    for count in (10000, 100000):
        request = corpus(count)
        raw = canonical_bytes(object_document(request))
        digest = sha256(raw).hexdigest()
        size = len(raw)
        del raw
        evaluate(request)
        times = []
        for _ in range(args.runs):
            gc.collect()
            started = time.perf_counter()
            evaluate(request)
            times.append(time.perf_counter() - started)
        gc.collect()
        tracemalloc.start()
        evaluate(request)
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        report["results"].append(
            {
                "observations": count,
                "scopes": len(request.scopes),
                "evidence": len(request.evidence),
                "corpus_sha256": digest,
                "json_bytes": size,
                "seconds": times,
                "median_seconds": statistics.median(times),
                "peak_bytes": peak,
            }
        )
        print(json.dumps(report["results"][-1]), flush=True)
    report["scaling_ratio"] = (
        report["results"][1]["median_seconds"] / report["results"][0]["median_seconds"]
    )
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
