#!/usr/bin/env python3
"""Fail the build when the published dataset contradicts itself.

Guards the classes of drift that produced the old site's visible errors:
a benchmark_id with no declared track, a track that claims full coverage
while most models are missing, a model with no provider, and raw responses
leaking into the page payload.
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
LITE = HERE / "data" / "results-lite.json"
RAW = HERE / "data" / "results.json"

SCORED = {"ok", "success", "completed"}


def fail(problems: list[str]) -> None:
    print("data check failed:")
    for problem in problems:
        print(f"  - {problem}")
    sys.exit(1)


def main() -> None:
    if not LITE.exists():
        fail(["data/results-lite.json is missing — run build_export.py first"])

    lite = json.loads(LITE.read_text())
    raw = json.loads(RAW.read_text())
    problems: list[str] = []

    declared = {b["id"] for b in lite["benchmarks"]}
    used = {row["benchmark_id"] for row in lite["results"]}
    undeclared = sorted(used - declared)
    if undeclared:
        problems.append(f"results reference undeclared tracks: {undeclared}")

    if "raw_response" in json.dumps(lite["results"][:5]):
        problems.append("results-lite.json still contains raw_response")

    unknown = [m["display"] for m in lite["models"] if m["provider"] == "other"]
    # 'other' is legitimate only for explicitly unknown models; every model in
    # the roster must resolve to a provider once the roster is mapped.
    if unknown:
        problems.append(f"models with no provider mapping: {unknown}")

    model_ids = {m["id"] for m in lite["models"]}
    orphan_rows = sorted({r["model_id"] for r in lite["results"]} - model_ids)
    if orphan_rows:
        problems.append(f"results reference models absent from the roster: {orphan_rows}")

    counts = Counter(
        row["benchmark_id"] for row in lite["results"]
        if str(row.get("status", "ok")).lower() in SCORED and row.get("score") is not None
    )
    total_models = len(model_ids)
    for bench in lite["benchmarks"]:
        scored = counts.get(bench["id"], 0)
        if bench["kind"] in {"core", "domain"} and scored == 0:
            problems.append(f"declared track {bench['id']} has no scored runs")
        if bench.get("coverage") == "full" and scored < total_models - 1:
            problems.append(
                f"{bench['id']} claims full coverage but only {scored}/{total_models} models scored"
            )
        if bench["coverage"] == "partial" and bench["kind"] == "core":
            # A core track at partial coverage is allowed (non-vision models
            # skip reverse-prompt) but must be visible, not silent.
            print(f"note: core track {bench['id']} is partial ({scored}/{total_models})")

    if lite["totals"]["scoredRuns"] != sum(counts.values()):
        problems.append("totals.scoredRuns disagrees with the scored row count")

    raw_rows = len(raw.get("results", []))
    if len(lite["results"]) != raw_rows:
        problems.append(f"export has {len(lite['results'])} rows, archive has {raw_rows}")

    if problems:
        fail(problems)
    print(
        f"data check ok: {total_models} models, {len(declared)} declared tracks, "
        f"{lite['totals']['scoredRuns']} scored runs"
    )


if __name__ == "__main__":
    main()
