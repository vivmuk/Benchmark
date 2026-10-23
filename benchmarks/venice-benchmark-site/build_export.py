#!/usr/bin/env python3
"""Build the site's small, canonical dataset from data/results.json.

Every page reads data/results-lite.json. Raw model responses (91% of the old
payload) stay in results.json for the archive and are never shipped to a
chart. Run this after any benchmark run:

    python3 build_export.py
    python3 check_data.py

The export is the single place where a model's provider, a track's coverage
class and the displayed counts are decided. UI code reads them; it never
re-types them.
"""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from provider_colors import PROVIDER_COLORS, provider_of

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
SOURCE = DATA / "results.json"
TARGET = DATA / "results-lite.json"

# Track taxonomy. `coverage` is published so a partial track can never be
# silently mistaken for a full one; `in_vivindex` is the weight contract the
# methodology page documents.
BENCHMARKS = [
    {
        "id": "intent_understanding",
        "name": "Intent Understanding",
        "short": "Intent",
        "kind": "core",
        "in_vivindex": True,
        "weight": 0.20,
        "description": "Ambiguous and adversarial prompts, scored on clarifying questions and context inference.",
    },
    {
        "id": "one_shot_ui",
        "name": "One-Shot UI Generation",
        "short": "One-Shot UI",
        "kind": "core",
        "in_vivindex": True,
        "weight": 0.15,
        "description": "A single self-contained interface, graded on polish, accessibility and zero-fix runnability.",
    },
    {
        "id": "startup_in_a_weekend",
        "name": "Startup in a Weekend",
        "short": "Startup",
        "kind": "core",
        "in_vivindex": True,
        "weight": 0.25,
        "description": "A constrained SaaS brief turned into an execution-ready MVP plan.",
    },
    {
        "id": "pharma_drug_interaction",
        "name": "Pharma: Drug-Drug Interaction",
        "short": "Pharma DDI",
        "kind": "domain",
        "in_vivindex": False,
        "weight": None,
        "description": "Clinically significant interactions from a short medication list.",
    },
    {
        "id": "pharma_regulatory_comprehension",
        "name": "Pharma: Regulatory",
        "short": "Pharma Regulatory",
        "kind": "domain",
        "in_vivindex": False,
        "weight": None,
        "description": "ICH E6(R2) principles applied to a monitoring and consent scenario.",
    },
    {
        "id": "value_density",
        "name": "Value Density @1K",
        "short": "Value Density",
        "kind": "core",
        "in_vivindex": True,
        "weight": 0.20,
        "description": "Useful checklist score under a hard 1024-token cap.",
    },
    {
        "id": "reverse_prompt_vision",
        "name": "Reverse-Prompt Vision",
        "short": "Reverse-Prompt",
        "kind": "core",
        "in_vivindex": True,
        "weight": 0.20,
        "description": "Recover a complex image's generation prompt from the image alone.",
    },
    {
        "id": "agentic_tool_use",
        "name": "Agentic Tool Use",
        "short": "Agentic",
        "kind": "experimental",
        "in_vivindex": False,
        "weight": None,
        "description": "Simulated trip booking with function calls and forced error recovery. Tier-2, top-10 subset.",
    },
    {
        "id": "long_context_reasoning",
        "name": "Long-Context Reasoning",
        "short": "Long-Context",
        "kind": "experimental",
        "in_vivindex": False,
        "weight": None,
        "description": "Six cross-document questions over a ~15K-token clinical-trial pack. Tier-2, top-10 subset.",
    },
    {
        "id": "brick_breaker_realism",
        "name": "Brick Breaker (retired)",
        "short": "Brick Breaker",
        "kind": "retired",
        "in_vivindex": False,
        "weight": None,
        "retired": True,
        "description": "Retired from the board in July 2026. Two historical rows are kept for the record only.",
    },
]

SCORED_STATUSES = {"ok", "success", "completed"}

# Fields a page may use. raw_response, metrics and error text stay behind.
ROW_FIELDS = (
    "model_id",
    "benchmark_id",
    "status",
    "score",
    "latency",
    "prompt_tokens",
    "completion_tokens",
    "total_tokens",
    "estimated_cost_usd",
)


def main() -> None:
    raw = json.loads(SOURCE.read_text())
    rows = raw.get("results", [])
    counts = Counter(row.get("benchmark_id") for row in rows)

    models = []
    for model in raw.get("models", []):
        key = provider_of(model["id"])
        pretty = PROVIDER_COLORS.get(key, PROVIDER_COLORS["other"])[0]
        models.append({
            "id": model["id"],
            "display": model.get("display") or model["id"],
            "provider": key,
            "providerLabel": pretty,
        })

    benchmarks = []
    for spec in BENCHMARKS:
        scored = sum(
            1 for row in rows
            if row.get("benchmark_id") == spec["id"]
            and str(row.get("status", "ok")).lower() in SCORED_STATUSES
            and row.get("score") is not None
        )
        item = dict(spec)
        item["scoredRuns"] = scored
        item["totalRuns"] = counts.get(spec["id"], 0)
        item["coverage"] = (
            "full" if scored >= max(1, len(models) - 1)
            else "partial" if scored > 0
            else "none"
        )
        benchmarks.append(item)

    lite_rows = [{field: row.get(field) for field in ROW_FIELDS} for row in rows]

    payload = {
        "schema_version": "2.0.0",
        "generated_at": raw.get("generated_at") or datetime.now(timezone.utc).isoformat(),
        "source": "data/results.json",
        "raw_responses": "data/results.json (archive; not loaded by any page)",
        "models": models,
        "benchmarks": benchmarks,
        "vivindex": {
            "tracks": [b["id"] for b in benchmarks if b["in_vivindex"]],
            "weights": {b["id"]: b["weight"] for b in benchmarks if b["in_vivindex"]},
        },
        "totals": {
            "models": len(models),
            "activeTracks": sum(1 for b in benchmarks if b["kind"] in {"core", "domain"}),
            "scoredRuns": sum(
                1 for row in rows
                if str(row.get("status", "ok")).lower() in SCORED_STATUSES
                and row.get("score") is not None
            ),
            "attemptedRuns": len(rows),
            "estimatedCostUsd": raw.get("total_estimated_cost_usd"),
        },
        "results": lite_rows,
    }

    TARGET.write_text(json.dumps(payload, separators=(",", ":"), ensure_ascii=False) + "\n")

    before = SOURCE.stat().st_size
    after = TARGET.stat().st_size
    print(f"wrote {TARGET.relative_to(HERE)}  {after:,} bytes ({after / before:.1%} of results.json)")
    print(f"models={len(models)} tracks={len(benchmarks)} rows={len(lite_rows)}")


if __name__ == "__main__":
    main()
